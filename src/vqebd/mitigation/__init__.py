"""Pluginalapú hibaenyhítési stratégiák (ADR-0003).

A VQEBD hibaenyhítési rétege több független módszert biztosít a zajcsökkentésre:
- ``none``: Nyers, mitigálatlan referencia (:class:`NoMitigation`).
- ``zne_local``: Saját, ISA- és layout-biztos ZNE (:class:`ZneLocalMitigation`).
- ``zne_mitiq``: Opcionális Mitiq ZNE referencia (:class:`MitiqZneMitigation`).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from typing import Final

from vqebd.mitigation.base import MitigationResult, MitigationStrategy
from vqebd.mitigation.extrapolation import (
    exponential_extrapolate,
    extrapolate,
    linear_extrapolate,
    polynomial_extrapolate,
    richardson_extrapolate,
)
from vqebd.mitigation.folding import count_two_qubit_gates, fold_global_unitary
from vqebd.mitigation.mitiq_zne import MitiqZneMitigation
from vqebd.mitigation.none import NoMitigation
from vqebd.mitigation.zne import ZneLocalMitigation

__all__ = [
    "AVAILABLE_STRATEGIES",
    "MitigationResult",
    "MitigationStrategy",
    "MitiqZneMitigation",
    "NoMitigation",
    "ZneLocalMitigation",
    "count_two_qubit_gates",
    "exponential_extrapolate",
    "extrapolate",
    "fold_global_unitary",
    "get_mitigation_strategy",
    "linear_extrapolate",
    "polynomial_extrapolate",
    "richardson_extrapolate",
]

AVAILABLE_STRATEGIES: Final[tuple[str, ...]] = ("none", "zne_local", "zne_mitiq")


def get_mitigation_strategy(
    name: str = "none",
    *,
    scale_factors: tuple[int, ...] = (1, 3, 5),
    extrapolator: str = "richardson",
) -> MitigationStrategy:
    """Gyárfüggvény hibaenyhítési stratégia példányosításához.

    Args:
        name: A stratégia neve ("none", "zne_local", "zne_mitiq").
        scale_factors: A zajszorzók (λ) ZNE esetén.
        extrapolator: Az extrapolációs modell neve ("richardson", "linear", stb.).

    Returns:
        A :class:`MitigationStrategy` implementáció.

    Raises:
        ValueError: Ismeretlen stratégia neve esetén.
    """
    n = name.lower()
    if n == "none":
        return NoMitigation()
    if n == "zne_local":
        return ZneLocalMitigation(scale_factors=scale_factors, extrapolator=extrapolator)
    if n == "zne_mitiq":
        return MitiqZneMitigation(scale_factors=scale_factors, extrapolator=extrapolator)

    raise ValueError(
        f"ismeretlen hibaenyhítési stratégia: {name!r}. "
        f"Ismert stratégiák: {sorted(AVAILABLE_STRATEGIES)}"
    )
