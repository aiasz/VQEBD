"""Batch-specifikáció: a konfigurációs mátrix leírása és az előre definiált mátrixok.

Egy :class:`BatchSpec` **cellákból** áll. Egy cella egy konfiguráció (molekula,
geometria, aktív tér, backend, optimalizáló, hibaenyhítés) és az ismétlésszám.
A cella minden ismétlése ugyanaz a konfiguráció, más mester-seeddel
(``master_seed + ismétlés``); a statisztikai aggregálás (``vqebd.stats``) ezeket
a független ismétléseket kezeli egy eloszlásként.

A mátrix-választás mért indoklása: ``docs/plan/phase_05.md`` 2. és 6. fejezet.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from vqebd.chemistry.molecule import beh2, h2, lih
from vqebd.config import (
    ActiveSpaceSpec,
    BackendKind,
    MitigationSpec,
    MoleculeSpec,
    OptimizerSpec,
)
from vqebd.platforms import platform_of

__all__ = ["PRESETS", "BatchCell", "BatchSpec", "get_preset"]


@dataclass(frozen=True, slots=True)
class BatchCell:
    """A mátrix egy cellája: egy konfiguráció és az ismétlésszám.

    Attributes:
        molecule: A molekula (geometriával).
        backend: A kiértékelő platform-backend.
        optimizer: Az optimalizáló.
        active_space: Aktív tér; ``None`` = teljes tér.
        mitigation: Hibaenyhítés.
        repeats: Független ismétlések száma (különböző seed). Zajmentes backenden 1.
        reestimate: A végső energia friss kiértékeléseinek száma (K, G4); 0 = ki.
    """

    molecule: MoleculeSpec
    backend: BackendKind
    optimizer: OptimizerSpec
    active_space: ActiveSpaceSpec | None = None
    mitigation: MitigationSpec = field(default_factory=MitigationSpec)
    repeats: int = 1
    reestimate: int = 0

    def __post_init__(self) -> None:
        if self.repeats < 1:
            raise ValueError(f"az ismétlésszám legalább 1: {self.repeats}")
        if platform_of(self.backend).exact and self.repeats > 1:
            raise ValueError(
                f"a(z) '{self.backend}' egzakt (zajmentes) backend: az ismétlés "
                f"({self.repeats}) bitre azonos eredményt adna, csak időt pazarolna"
            )


@dataclass(frozen=True, slots=True)
class BatchSpec:
    """Egy teljes batch: azonosító, mester-seed és cellák.

    Attributes:
        batch_id: Rövid, stabil azonosító (a ``run_id`` előtagja).
        description: Emberi leírás (a jegyzőkönyvbe).
        master_seed: Az ismétlések seedjeinek alapja.
        cells: A cellák.
    """

    batch_id: str
    description: str
    cells: tuple[BatchCell, ...]
    master_seed: int = 20260922

    def __post_init__(self) -> None:
        if not self.batch_id or ":" in self.batch_id:
            raise ValueError(
                f"érvénytelen batch_id (üres vagy ':'-ot tartalmaz): {self.batch_id!r}"
            )
        if not self.cells:
            raise ValueError("a batch legalább egy cellát tartalmazzon")

    @property
    def total_runs(self) -> int:
        """Az összes futás (ismétlésekkel együtt)."""
        return sum(cell.repeats for cell in self.cells)


# ============================================================ preset-ek

_EXACT = {
    "qiskit_statevector": OptimizerSpec(method="SLSQP", maxiter=300),
    "cirq_simulator": OptimizerSpec(method="SLSQP", maxiter=300),
    # qsim: complex64 → deriváltmentes optimalizáló kell (ADR-0006, M13).
    "qsim": OptimizerSpec(method="Powell", maxiter=2000),
}
_ALL_EXACT: tuple[BackendKind, ...] = ("qiskit_statevector", "cirq_simulator", "qsim")
_NO_QSIM: tuple[BackendKind, ...] = ("qiskit_statevector", "cirq_simulator")
_COBYLA = OptimizerSpec(method="COBYLA", maxiter=300)

LIH_MINIMAL = ActiveSpaceSpec(2, 3)
LIH_FROZEN_CORE = ActiveSpaceSpec(2, 5)
BEH2_MINIMAL = ActiveSpaceSpec(2, 3)
BEH2_FROZEN_CORE = ActiveSpaceSpec(4, 6)


def _exact_cells(
    molecules: tuple[MoleculeSpec, ...],
    active_space: ActiveSpaceSpec | None,
    backends: tuple[BackendKind, ...],
) -> tuple[BatchCell, ...]:
    return tuple(
        BatchCell(molecule=m, backend=b, optimizer=_EXACT[b], active_space=active_space)
        for m in molecules
        for b in backends
    )


def _f5_deterministic() -> BatchSpec:
    """L2, platformdimenzió (``phase_05.md`` 6.1).

    A qsim + Powell költsége a paraméterszámmal meredeken nő (mérve: LiH (2e,5o),
    24 paraméter: 7178 kiértékelés, 486 s), ezért a qsim a frozen-core LiH-n csak
    az egyensúlyi geometriában, a 92 paraméteres BeH₂ (4e,6o)-n pedig nem fut.
    """
    cells = (
        _exact_cells(tuple(h2(r) for r in (0.5, 0.735, 1.0, 1.5, 2.0, 2.5)), None, _ALL_EXACT)
        + _exact_cells(tuple(lih(r) for r in (1.2, 1.595, 2.2, 3.0)), LIH_MINIMAL, _ALL_EXACT)
        + _exact_cells(tuple(lih(r) for r in (1.2, 1.595, 2.2, 3.0)), LIH_FROZEN_CORE, _NO_QSIM)
        + _exact_cells((lih(1.595),), LIH_FROZEN_CORE, ("qsim",))
        + _exact_cells(tuple(beh2(r) for r in (1.0, 1.33, 1.8)), BEH2_MINIMAL, _ALL_EXACT)
        + _exact_cells((beh2(1.33),), BEH2_FROZEN_CORE, _NO_QSIM)
    )
    return BatchSpec(
        batch_id="f5-deterministic",
        description="L2 platformdimenzió: H2, LiH és BeH2 (minimális és frozen-core aktív tér)",
        cells=cells,
    )


def _f5_statistical() -> BatchSpec:
    """L3a/L3b/L4, ismétlésdimenzió (``phase_05.md`` 6.2)."""
    mitigations = (
        MitigationSpec(),
        MitigationSpec(strategy="zne_local", extrapolator="linear"),
        MitigationSpec(strategy="zne_local", extrapolator="richardson"),
    )
    cells: list[BatchCell] = []
    for r in (0.735, 1.5):
        cells.append(BatchCell(h2(r), "qiskit_aer_shot", _COBYLA, repeats=20, reestimate=16))
        for mit in mitigations:
            cells.append(
                BatchCell(
                    h2(r), "qiskit_aer_noisy", _COBYLA, mitigation=mit, repeats=20, reestimate=16
                )
            )
    noisy_backends: tuple[BackendKind, ...] = ("qiskit_aer_shot", "qiskit_aer_noisy")
    for backend in noisy_backends:
        cells.append(
            BatchCell(
                lih(1.595),
                backend,
                _COBYLA,
                active_space=LIH_MINIMAL,
                repeats=10,
                reestimate=16,
            )
        )
    return BatchSpec(
        batch_id="f5-statistical",
        description="Zajos szintek ismétléssel: H2 (egyensúlyi és nyújtott), LiH (2e,3o)",
        cells=tuple(cells),
    )


def _f5_smoke() -> BatchSpec:
    """Kicsi, gyors batch a tesztekhez (nem mérési eredmény)."""
    return BatchSpec(
        batch_id="f5-smoke",
        description="Füstteszt: H2 két geometrián, egzakt és lövészajos backenden",
        cells=(
            BatchCell(h2(0.735), "qiskit_statevector", _EXACT["qiskit_statevector"]),
            BatchCell(h2(1.5), "qiskit_statevector", _EXACT["qiskit_statevector"]),
            BatchCell(
                h2(0.735),
                "qiskit_aer_shot",
                OptimizerSpec(method="COBYLA", maxiter=40),
                repeats=3,
                reestimate=4,
            ),
        ),
    )


PRESETS: dict[str, Callable[[], BatchSpec]] = {
    "f5-deterministic": _f5_deterministic,
    "f5-statistical": _f5_statistical,
    "f5-smoke": _f5_smoke,
}
"""Az előre definiált mátrixok, név szerint."""


def get_preset(name: str) -> BatchSpec:
    """Előre definiált batch név szerint.

    Raises:
        ValueError: Ismeretlen név esetén (a hibaüzenet felsorolja az ismerteket).
    """
    try:
        factory = PRESETS[name]
    except KeyError:
        raise ValueError(
            f"ismeretlen batch-preset: {name!r}; ismertek: {', '.join(sorted(PRESETS))}"
        ) from None
    return factory()
