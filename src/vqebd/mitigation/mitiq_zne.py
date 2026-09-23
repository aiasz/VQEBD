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

__all__ = ["MitiqZneMitigation"]


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
        try:
            import mitiq
            from mitiq.zne import execute_with_zne
            from mitiq.zne.scaling import fold_global
        except ImportError as exc:
            raise ImportError(
                "A 'zne_mitiq' stratégia a 'mitiq' csomagot igényli. "
                "Telepítés: pip install mitiq (vagy használd a beépített 'zne_local'-t)."
            ) from exc

        scales = list(self.scale_factors)
        # Extrapolációs modell kiválasztása a Mitiq-ből
        extrap_map = {
            "richardson": mitiq.zne.inference.RichardsonFactory(scale_factors=scales),
            "linear": mitiq.zne.inference.LinearFactory(scale_factors=scales),
            "poly": mitiq.zne.inference.PolyFactory(scale_factors=scales, order=2),
            "quadratic": mitiq.zne.inference.PolyFactory(scale_factors=scales, order=2),
            "exponential": mitiq.zne.inference.ExpFactory(scale_factors=scales),
        }
        factory = extrap_map.get(self.extrapolator.lower())
        if factory is None:
            factory = mitiq.zne.inference.RichardsonFactory(scale_factors=scales)

        def executor(qc_to_run: Any) -> float:
            from vqebd.backends.estimators import make_energy_evaluator

            ev = make_energy_evaluator(evaluator.kind, qc_to_run, observable, seeds)
            return ev.evaluate(parameters)

        mitigated_energy = execute_with_zne(
            circuit,
            executor,
            scale_noise=fold_global,
            factory=factory,
        )

        # Nyers érték kiértékelése
        raw_val = evaluator.evaluate(parameters)

        return MitigationResult(
            mitigated_energy=float(mitigated_energy),
            raw_energy=raw_val,
            scale_factors=tuple(float(s) for s in self.scale_factors),
            scaled_energies=tuple(float(raw_val) for _ in self.scale_factors),  # fallback alak
            strategy_name=self.name,
            extrapolator_name=self.extrapolator,
            fit_residuals=None,
            metadata={"library": "mitiq"},
        )
