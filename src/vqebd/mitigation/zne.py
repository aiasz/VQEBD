r"""Saját, ISA-biztos Zero-Noise Extrapolation (ZNE) stratégia (ADR-0003).

Ez a modul valósítja meg a VQEBD natív ZNE eljárását:
1. Globális unitáris hajtogatással skálázza a zajt ($U \to U (U^\dagger U)^n$),
   **a lefordított ISA-áramkörön**, újraoptimalizálás nélkül. Így a fizikai
   qubitkiosztás megmarad, és a tényleges zajszorzó pontosan a névleges λ
   (TR-F03 1. javítási kör; a TR-000 spike N2 lépésének módszere).
2. Kiértékeli az energiát a megadott skálafaktorokon ($\lambda \in \{1, 3, 5, \dots\}$).
3. A kiválasztott extrapolációs modellel (Richardson, lineáris, polinom, exponenciális)
   meghatározza a zajmentes határértéket ($\lambda \to 0$).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from vqebd.backends.estimators import make_energy_evaluator
from vqebd.mitigation.base import MitigationResult, MitigationStrategy
from vqebd.mitigation.extrapolation import extrapolate
from vqebd.mitigation.folding import count_two_qubit_gates, fold_global_unitary
from vqebd.seeds import SeedSet

__all__ = ["ZneLocalMitigation"]


class ZneLocalMitigation(MitigationStrategy):
    """Saját, ISA-biztos ZNE stratégia."""

    def __init__(
        self,
        scale_factors: Sequence[int] = (1, 3, 5),
        extrapolator: str = "richardson",
    ) -> None:
        for s in scale_factors:
            if s < 1 or s % 2 != 1:
                raise ValueError(
                    f"minden ZNE skálafaktornak páratlan pozitív egésznek kell lennie, kapott: {s}"
                )
        self.scale_factors = tuple(scale_factors)
        self.extrapolator = extrapolator

    @property
    def name(self) -> str:
        return "zne_local"

    def describe(self) -> dict[str, Any]:
        return {
            "strategy": self.name,
            "scale_factors": list(self.scale_factors),
            "extrapolator": self.extrapolator,
        }

    def execute(
        self,
        circuit: Any,
        observable: Any,
        evaluator: Any,
        parameters: Sequence[float],
        seeds: SeedSet,
    ) -> MitigationResult:
        """ZNE végrehajtása a megadott paramétereknél.

        **Transzpiláló kiértékelőn** (:class:`~vqebd.backends.estimators.IsaEnergyEvaluator`:
        zajos szimulátor, QPU) a hajtogatás a már lefordított **ISA-áramkörön**
        történik, és a hajtogatott áramkör ``optimization_level=0``-val kerül a
        kapukészletre. Így a tényleges zajszorzó **pontosan** a névleges λ (a
        kétqubites kapuk száma λ-szoros) — ezt a metaadat ``effective_scale_factors``
        mezője minden futásnál rögzíti.

        **Zajmentes kiértékelőn** (állapotvektor) nincs ISA-áramkör: a logikai
        áramkör hajtogatódik. Itt a ZNE definíció szerint hatástalan (E(λ) állandó),
        a futás csak a láncolat működését igazolja.
        """
        from vqebd.backends.estimators import IsaEnergyEvaluator

        scaled_energies: list[float] = []
        gate_counts: list[int] = []
        two_q_gate_counts: list[int] = []
        isa_level = isinstance(evaluator, IsaEnergyEvaluator)

        for scale in self.scale_factors:
            if isa_level:
                base = evaluator.isa_circuit
                folded_c = (
                    base
                    if scale == 1
                    else evaluator.to_isa_unoptimized(fold_global_unitary(base, scale))
                )
                energy = evaluator.evaluate_isa(folded_c, parameters)
            elif scale == 1:
                folded_c = circuit
                energy = evaluator.evaluate(parameters)
            else:
                folded_c = fold_global_unitary(circuit, scale)
                folded_evaluator = make_energy_evaluator(
                    evaluator.kind, folded_c, observable, seeds
                )
                energy = folded_evaluator.evaluate(parameters)

            scaled_energies.append(energy)
            gate_counts.append(len(folded_c.data))
            two_q_gate_counts.append(count_two_qubit_gates(folded_c))

        float_scales = [float(s) for s in self.scale_factors]
        mitigated_val, residuals = extrapolate(self.extrapolator, float_scales, scaled_energies)

        base_2q = two_q_gate_counts[0] if self.scale_factors[0] == 1 else None
        effective = [c / base_2q for c in two_q_gate_counts] if base_2q else None
        metadata = {
            "folding_level": "isa" if isa_level else "logical",
            "gate_counts": gate_counts,
            "two_qubit_gate_counts": two_q_gate_counts,
            "effective_scale_factors": effective,
        }

        return MitigationResult(
            mitigated_energy=mitigated_val,
            raw_energy=scaled_energies[0],
            scale_factors=tuple(float_scales),
            scaled_energies=tuple(scaled_energies),
            strategy_name=self.name,
            extrapolator_name=self.extrapolator,
            fit_residuals=residuals,
            metadata=metadata,
        )
