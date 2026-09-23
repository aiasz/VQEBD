"""Alapértelmezett (mitigáció nélküli) stratégia (ADR-0003).

A nyers (λ=1) kiértékelést adja vissza, biztosítva az egységes felületet
és az összehasonlíthatóságot a mitigált szintekkel.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from vqebd.mitigation.base import MitigationResult, MitigationStrategy
from vqebd.seeds import SeedSet

__all__ = ["NoMitigation"]


class NoMitigation(MitigationStrategy):
    """Mitigáció nélküli, nyers végrehajtási stratégia."""

    @property
    def name(self) -> str:
        return "none"

    def describe(self) -> dict[str, Any]:
        return {"strategy": "none"}

    def execute(
        self,
        _circuit: Any,
        _observable: Any,
        evaluator: Any,
        parameters: Sequence[float],
        _seeds: SeedSet,
    ) -> MitigationResult:
        val = evaluator.evaluate(parameters)
        return MitigationResult(
            mitigated_energy=val,
            raw_energy=val,
            scale_factors=(1.0,),
            scaled_energies=(val,),
            strategy_name=self.name,
            extrapolator_name="none",
            fit_residuals=None,
            metadata={},
        )
