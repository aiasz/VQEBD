"""Batch végrehajtás: folytatható, hibaizolált futtatás adatbázisba.

- **Folytathatóság:** a már tárolt ``run_id``-kat kihagyja (AC-5.5).
- **Hibaizoláció:** egy futás kivétele nem állítja le a batchet; a hiba a
  jelentésbe kerül (típus + üzenet), a többi futás folytatódik. Újrapróbálkozás
  és ütemezés a Fázis 6 feladata.
- **Nincs kvótafogyasztás:** ``ibm_qpu`` backendet tartalmazó batchet csak
  ``VQEBD_ALLOW_HARDWARE=true`` mellett indít (``phase_05.md`` 6.4).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from vqebd.batch.expand import expand
from vqebd.batch.spec import BatchSpec
from vqebd.storage import Database
from vqebd.vqe.runner import run_vqe

__all__ = ["BatchReport", "run_batch"]


@dataclass(slots=True)
class BatchReport:
    """Egy batch-végrehajtás összegzése.

    Attributes:
        batch_id: A batch azonosítója.
        planned: A tervezett futások száma.
        completed: Ebben a hívásban lefutott és tárolt futások.
        skipped: Már tárolt, ezért kihagyott futások (folytatás).
        failed: Sikertelen futások: ``(run_id, "Kivételtípus: üzenet")``.
        wall_time_s: A hívás teljes ideje.
    """

    batch_id: str
    planned: int
    completed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    wall_time_s: float = 0.0

    @property
    def remaining(self) -> int:
        """A még le nem futott futások száma (hibásak + a ``max_runs`` miatt kimaradtak)."""
        return self.planned - len(self.completed) - len(self.skipped)


def run_batch(
    spec: BatchSpec,
    db: Database,
    *,
    max_runs: int | None = None,
    progress: Callable[[str], None] | None = None,
) -> BatchReport:
    """A batch végrehajtása (vagy folytatása) a megadott adatbázisba.

    Args:
        spec: A batch.
        db: A céladatbázis (megnyitva).
        max_runs: Legfeljebb ennyi **új** futás ebben a hívásban (``None`` = mind).
            Részleges futtatáshoz és a folytathatóság teszteléséhez.
        progress: Opcionális naplózó (pl. ``print``).

    Raises:
        PermissionError: ``ibm_qpu`` cella esetén, ha a hardverhasználat nincs
            kifejezetten engedélyezve.
    """
    if any(cell.backend == "ibm_qpu" for cell in spec.cells) and (
        os.environ.get("VQEBD_ALLOW_HARDWARE", "false").lower() != "true"
    ):
        raise PermissionError(
            "a batch valódi QPU-t használna; kvótavédelem miatt csak "
            "VQEBD_ALLOW_HARDWARE=true mellett indul"
        )

    log = progress or (lambda _msg: None)
    runs = expand(spec)
    report = BatchReport(batch_id=spec.batch_id, planned=len(runs))
    started = time.perf_counter()
    new_runs = 0

    for i, planned in enumerate(runs, start=1):
        if db.get_result(planned.run_id) is not None:
            report.skipped.append(planned.run_id)
            continue
        if max_runs is not None and new_runs >= max_runs:
            break
        cfg = planned.config
        mitigation = (
            "none"
            if cfg.mitigation.strategy == "none"
            else f"{cfg.mitigation.strategy}/{cfg.mitigation.extrapolator}"
        )
        label = (
            f"[{i}/{len(runs)}] {cfg.molecule.name} R={cfg.molecule.bond_length} "
            f"{cfg.active_space.label if cfg.active_space else 'teljes'} {cfg.backend} "
            f"{mitigation} r{planned.repeat_index}"
        )
        t0 = time.perf_counter()
        try:
            result = run_vqe(cfg)
            db.insert_result(
                result,
                run_id=planned.run_id,
                batch_id=spec.batch_id,
                repeat_index=planned.repeat_index,
            )
        except Exception as exc:  # hibaizoláció: a batch folytatódik
            report.failed.append((planned.run_id, f"{type(exc).__name__}: {exc}"))
            log(f"{label} HIBA: {type(exc).__name__}: {exc}")
            continue
        new_runs += 1
        report.completed.append(planned.run_id)
        log(f"{label} E={result.energy:+.10f} ({time.perf_counter() - t0:.1f} s)")

    report.wall_time_s = time.perf_counter() - started
    return report
