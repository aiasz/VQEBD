"""A hibaenyhítési réteg alapjai — protokoll és eredményrekord (ADR-0003).

A VQEBD hibaenyhítési architektúrája pluginalapú: minden stratégia ugyanazt a
:class:`MitigationStrategy` protokollt valósítja meg, és :class:`MitigationResult`
objektumot ad vissza, amely a mitigált érték mellett a nyers pontokat és az
illesztési diagnosztikát is hordozza.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from vqebd.seeds import SeedSet

__all__ = ["MitigationResult", "MitigationStrategy"]


@dataclass(frozen=True, slots=True)
class MitigationResult:
    """Egy hibaenyhítési eljárás részletes eredménye.

    Attributes:
        mitigated_energy: Az extrapolált/mitigált elektronos energia (Hartree).
        raw_energy: A nyers (skálázatlan, λ=1) elektronos energia (Hartree).
        scale_factors: A használt zajszorzók (pl. (1.0, 3.0, 5.0)).
        scaled_energies: A skálázott áramkörökön mért energiák (Hartree).
        strategy_name: A stratégia azonosítója (pl. "zne_local", "zne_mitiq").
        extrapolator_name: Az alkalmazott extrapolációs modell (pl. "richardson").
        fit_residuals: Az illesztés négyzetes hibája vagy reziduuma (ha értelmezett).
        metadata: További diagnosztikai metaadatok (pl. kapuszámok skálázódása).
    """

    mitigated_energy: float
    raw_energy: float
    scale_factors: tuple[float, ...]
    scaled_energies: tuple[float, ...]
    strategy_name: str
    extrapolator_name: str
    fit_residuals: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def energy_improvement_ha(self) -> float:
        """A nyers és mitigált energia abszolút különbsége (Hartree)."""
        return abs(self.raw_energy - self.mitigated_energy)

    def to_dict(self) -> dict[str, Any]:
        """Szerializálható szótár a tárolási réteghez (Fázis 4)."""
        return {
            "mitigated_energy_ha": self.mitigated_energy,
            "raw_energy_ha": self.raw_energy,
            "scale_factors": list(self.scale_factors),
            "scaled_energies_ha": list(self.scaled_energies),
            "strategy_name": self.strategy_name,
            "extrapolator_name": self.extrapolator_name,
            "fit_residuals": self.fit_residuals,
            "metadata": dict(self.metadata),
        }


class MitigationStrategy(Protocol):
    """Közös protokoll az összes hibaenyhítési eljáráshoz."""

    @property
    def name(self) -> str:
        """A stratégia azonosítója az adatsémához és a CLI-hez."""
        ...

    def describe(self) -> dict[str, Any]:
        """A stratégia beállításainak leírása."""
        ...

    def execute(
        self,
        circuit: Any,
        observable: Any,
        evaluator: Any,
        parameters: Sequence[float],
        seeds: SeedSet,
    ) -> MitigationResult:
        """Hibaenyhített kiértékelés végrehajtása a megadott paramétervektornál."""
        ...
