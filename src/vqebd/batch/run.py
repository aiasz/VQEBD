"""Batch végrehajtás: folytatható, hibaizolált futtatás adatbázisba.

- **Folytathatóság:** a már tárolt ``run_id``-kat kihagyja (AC-5.5).
- **Hibaizoláció:** egy futás kivétele nem állítja le a batchet; a hiba a
  jelentésbe kerül (típus + üzenet), a többi futás folytatódik.
- **Hibatárolás (Fázis 6):** minden sikertelen próbálkozás a ``run_failures``
  táblába kerül (titoktalanítva). ``retry`` politikával a rendszer az átmeneti
  hibát korlátosan újrapróbálja, a feladott (``abandoned``) futásokat pedig
  kihagyja; politika nélkül a viselkedés a Fázis 5-tel azonos: egy hibás futást
  minden hívás újra megpróbál.
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

from vqebd.batch.expand import PlannedRun, expand
from vqebd.batch.spec import BatchSpec
from vqebd.config import VQEConfig
from vqebd.pipeline.errors import known_secrets
from vqebd.pipeline.retry import RetryPolicy, run_with_retry
from vqebd.storage import Database
from vqebd.vqe.result import VQEResult
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
        failed: Sikertelen futások: ``(run_id, "Kivételtípus: üzenet")`` (titoktalanítva).
        abandoned: Korábban feladott futások (``retry`` politikával), amelyeket most
            kihagytunk; a ``--retry-abandoned`` állítja vissza őket.
        wall_time_s: A hívás teljes ideje.
    """

    batch_id: str
    planned: int
    completed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    abandoned: list[str] = field(default_factory=list)
    wall_time_s: float = 0.0

    @property
    def remaining(self) -> int:
        """A még le nem futott futások száma (hibás, feladott, ``max_runs`` miatt kimaradt)."""
        return self.planned - len(self.completed) - len(self.skipped)


def run_batch(
    spec: BatchSpec,
    db: Database,
    *,
    max_runs: int | None = None,
    progress: Callable[[str], None] | None = None,
    retry: RetryPolicy | None = None,
    hardware_max_attempts: int = 1,
    sleep: Callable[[float], None] = time.sleep,
) -> BatchReport:
    """A batch végrehajtása (vagy folytatása) a megadott adatbázisba.

    Args:
        spec: A batch.
        db: A céladatbázis (megnyitva).
        max_runs: Legfeljebb ennyi **új** futás ebben a hívásban (``None`` = mind).
            Részleges futtatáshoz és a folytathatóság teszteléséhez.
        progress: Opcionális naplózó (pl. ``print``).
        retry: Újrapróbálkozási politika. ``None``: nincs újrapróbálás és nincs
            feladás (a hibák tárolódnak, de a futás a következő híváskor újra próbál).
        hardware_max_attempts: ``ibm_qpu`` futásra a próbálkozások felső korlátja
            (alapértelmezés 1: egy újrapróbálás kvótát fogyasztana, ADR-0008).
        sleep: A visszalépés várakozása (tesztben injektálható).

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
    secrets = known_secrets()
    runs = expand(spec)
    report = BatchReport(batch_id=spec.batch_id, planned=len(runs))
    started = time.perf_counter()
    new_runs = 0

    for i, planned in enumerate(runs, start=1):
        if db.get_result(planned.run_id) is not None:
            report.skipped.append(planned.run_id)
            continue
        if retry is not None and db.is_abandoned(planned.run_id):
            report.abandoned.append(planned.run_id)
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

        def operation(planned: PlannedRun = planned, cfg: VQEConfig = cfg) -> VQEResult:
            result = run_vqe(cfg)
            db.insert_result(
                result,
                run_id=planned.run_id,
                batch_id=spec.batch_id,
                repeat_index=planned.repeat_index,
            )
            return result

        def log_failure(message: str, label: str = label) -> None:
            log(f"{label} HIBA: {message}")

        policy = retry if retry is not None else RetryPolicy(max_attempts=1)
        if cfg.backend == "ibm_qpu":
            policy = policy.limited_to(hardware_max_attempts)
        outcome = run_with_retry(
            operation,
            db=db,
            run_id=planned.run_id,
            batch_id=spec.batch_id,
            policy=policy,
            secrets=secrets,
            sleep=sleep,
            on_failure=log_failure,
        )
        if not outcome.succeeded:  # hibaizoláció: a batch folytatódik
            report.failed.append((planned.run_id, outcome.error or "ismeretlen hiba"))
            continue
        assert outcome.value is not None
        new_runs += 1
        report.completed.append(planned.run_id)
        log(f"{label} E={outcome.value.energy:+.10f} ({time.perf_counter() - t0:.1f} s)")

    report.wall_time_s = time.perf_counter() - started
    return report
