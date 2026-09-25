"""Mitiq ZNE hibaenyhítési referencia-stratégia (ADR-0003).

A Mitiq nyílt forráskódú (GPL-3.0) hibaenyhítési könyvtár. Ez a modul
**opcionális, logikai szintű referenciaként** szolgál a saját ``zne_local``
implementáció ellenőrzésére (M4).

Fontos architekturális megjegyzések (ADR-0003):
1. **Opcionális betöltés:** A ``mitiq`` importja csak a függvényen belül történik.
   A rendszer a ``mitiq`` nélkül is teljes értékűen működik a ``zne_local``-lal.
2. **Logikai szintű hajtogatás:** A Mitiq a transzpilálás előtti logikai áramkört
   hajtogatja, megkerülve a fizikai layout M3 qubit-vesztési hibáját.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from vqebd.mitigation.base import MitigationResult, MitigationStrategy
from vqebd.seeds import SeedSet

__all__ = ["MITIQ_LOGICAL_BASIS", "MitiqZneMitigation"]

MITIQ_LOGICAL_BASIS: tuple[str, ...] = ("rz", "sx", "x", "cx")
"""A Mitiq-nek átadott logikai áramkör kapukészlete (QASM 2-ben kifejezhető)."""


class MitiqZneMitigation(MitigationStrategy):
    """Mitiq-alapú ZNE referencia-stratégia."""

    def __init__(
        self,
        scale_factors: Sequence[int] = (1, 3, 5),
        extrapolator: str = "richardson",
    ) -> None:
        self.scale_factors = tuple(scale_factors)
        self.extrapolator = extrapolator

    @property
    def name(self) -> str:
        return "zne_mitiq"

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
        """Mitiq ZNE a megadott paramétereknél.

        Lépések (a TR-000 spike M1 lépésének módszere):

        1. A paraméterek **bekötése** — a Mitiq QASM-en át konvertál, ami kötetlen
           paramétert nem visz át.
        2. Logikai kapukészletre fordítás (``rz, sx, x, cx``, ``level=1``).
        3. ``mitiq.zne.scaling.fold_global`` hajtogat; az executor a hajtogatott
           logikai áramkört **optimalizálás nélkül** (``level=0``) fordítja a
           célhardverre, hogy a hajtogatás megmaradjon.
        4. A skálázott energiákat és a zajszorzókat a Mitiq ``Factory``-ból
           olvassuk ki — **valódi** mért értékek, nem helykitöltők.
        """
        try:
            import mitiq
            from mitiq.zne.scaling import fold_global
        except ImportError as exc:
            raise ImportError(
                "A 'zne_mitiq' stratégia a 'mitiq' csomagot igényli. "
                "Telepítés: pip install -r requirements-mitiq.txt "
                "(vagy használd a beépített 'zne_local'-t)."
            ) from exc

        from qiskit import transpile

        from vqebd.backends.estimators import IsaEnergyEvaluator, make_energy_evaluator
        from vqebd.mitigation.folding import count_two_qubit_gates

        scales = [float(s) for s in self.scale_factors]
        inference = mitiq.zne.inference
        extrap_map = {
            "richardson": lambda: inference.RichardsonFactory(scale_factors=scales),
            "linear": lambda: inference.LinearFactory(scale_factors=scales),
            "poly": lambda: inference.PolyFactory(scale_factors=scales, order=2),
            "quadratic": lambda: inference.PolyFactory(scale_factors=scales, order=2),
            "exponential": lambda: inference.ExpFactory(scale_factors=scales),
        }
        make_factory = extrap_map.get(self.extrapolator.lower())
        if make_factory is None:
            raise ValueError(
                f"ismeretlen extrapolátor a zne_mitiq számára: {self.extrapolator!r} "
                f"(ismert: {', '.join(sorted(extrap_map))})"
            )
        factory = make_factory()

        bound = circuit.assign_parameters(list(parameters))
        logical = transpile(
            bound,
            basis_gates=list(MITIQ_LOGICAL_BASIS),
            optimization_level=1,
            seed_transpiler=seeds.transpiler,
        )

        if isinstance(evaluator, IsaEnergyEvaluator):

            def executor(qc_to_run: Any) -> float:
                return float(evaluator.evaluate_logical(qc_to_run))

        else:

            def executor(qc_to_run: Any) -> float:
                ev = make_energy_evaluator(evaluator.kind, qc_to_run, observable, seeds)
                return float(ev.evaluate(()))

        # A Mitiq az executor visszatérési ANNOTÁCIÓJÁBÓL következtet a kimenet
        # típusára. A modul `from __future__ import annotations` miatt az annotáció
        # itt a "float" SZÖVEG lenne, amit a Mitiq nem ismer fel (mért hiba:
        # "Could not parse executed results from executor with type float").
        executor.__annotations__["return"] = float
        factory.run(logical, executor, scale_noise=fold_global)
        mitigated_energy = float(factory.reduce())
        measured_scales = [float(x) for x in factory.get_scale_factors()]
        scaled_energies = [float(x) for x in factory.get_expectation_values()]

        two_q_counts = [count_two_qubit_gates(fold_global(logical, scale_factor=s)) for s in scales]
        raw_val = (
            scaled_energies[measured_scales.index(1.0)]
            if 1.0 in measured_scales
            else float(evaluator.evaluate(parameters))
        )

        return MitigationResult(
            mitigated_energy=mitigated_energy,
            raw_energy=raw_val,
            scale_factors=tuple(measured_scales),
            scaled_energies=tuple(scaled_energies),
            strategy_name=self.name,
            extrapolator_name=self.extrapolator,
            fit_residuals=None,
            metadata={
                "library": "mitiq",
                "mitiq_version": str(mitiq.__version__),
                "folding_level": "logical",
                "two_qubit_gate_counts": two_q_counts,
            },
        )
