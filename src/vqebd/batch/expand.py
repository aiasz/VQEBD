"""A batch-mátrix kifejtése futáslistává, determinisztikus azonosítókkal.

A ``run_id`` alakja: ``"{batch_id}:{ujjlenyomat[:16]}:r{ismétlés:02d}"``. Az
ujjlenyomat a teljes konfigurációé (a seedet is beleértve), így:

- azonos spec → **bitre azonos** futáslista és azonosítók (AC-5.4);
- egy megszakadt batch újraindítva a már tárolt ``run_id``-kat kihagyja, és a
  végeredmény azonos egy megszakítás nélküli futáséval (AC-5.5).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import dataclass

from vqebd.batch.spec import BatchCell, BatchSpec
from vqebd.config import VQEConfig

__all__ = ["PlannedRun", "expand"]


@dataclass(frozen=True, slots=True)
class PlannedRun:
    """Egy tervezett futás.

    Attributes:
        run_id: Determinisztikus, egyedi azonosító.
        config: A teljes futáskonfiguráció.
        repeat_index: Az ismétlés sorszáma a cellán belül (0-tól).
        cell_index: A cella sorszáma a specben.
    """

    run_id: str
    config: VQEConfig
    repeat_index: int
    cell_index: int


def _config(cell: BatchCell, seed: int) -> VQEConfig:
    return VQEConfig(
        molecule=cell.molecule,
        backend=cell.backend,
        optimizer=cell.optimizer,
        mitigation=cell.mitigation,
        active_space=cell.active_space,
        reestimate=cell.reestimate,
        seed=seed,
    )


def expand(spec: BatchSpec) -> list[PlannedRun]:
    """A spec kifejtése futáslistává (cellasorrendben, azon belül ismétlésenként).

    Raises:
        ValueError: Ha két futás azonosítója egybeesne (duplikált cella).
    """
    runs: list[PlannedRun] = []
    seen: set[str] = set()
    for cell_index, cell in enumerate(spec.cells):
        for repeat in range(cell.repeats):
            config = _config(cell, spec.master_seed + repeat)
            run_id = f"{spec.batch_id}:{config.fingerprint()[:16]}:r{repeat:02d}"
            if run_id in seen:
                raise ValueError(f"duplikált futás a batchben (azonos cella kétszer?): {run_id}")
            seen.add(run_id)
            runs.append(PlannedRun(run_id, config, repeat, cell_index))
    return runs
