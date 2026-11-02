"""A pipeline: előellenőrzés → batch (újrapróbálkozással) → export → összegzés.

Minden lépés egy-egy JSON-soros naplóbejegyzést ír (``data/logs/pipeline-ÉÉÉÉHHNN.jsonl``);
a naplóba és a hibatáblába csak titoktalanított szöveg kerül (ADR-0008).

Kilépési kódok: ``0`` minden futás rendben · ``1`` részleges hiba (a hibák tárolva) ·
``2`` végzetes (konfiguráció, adatbázis, engedély).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vqebd.batch.aggregate import aggregate_rows
from vqebd.batch.expand import expand
from vqebd.batch.export import write_export
from vqebd.batch.run import BatchReport, run_batch
from vqebd.batch.spec import BatchSpec, get_preset
from vqebd.hardware import guard_hardware_vqe, hardware_evaluation_budget
from vqebd.pipeline.errors import known_secrets, scrub_secrets
from vqebd.pipeline.retry import RetryPolicy
from vqebd.storage import Database

__all__ = ["EXIT_FATAL", "EXIT_OK", "EXIT_PARTIAL", "PipelineResult", "run_pipeline"]

EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_FATAL = 2

DEFAULT_LOG_DIR = Path("data/logs")
HARDWARE_QUOTA_RESERVE = 1.2
"""A batch szintű kvótakapu tartaléka: a hátralévő időnek a becslés 120%-át kell fednie."""


@dataclass(slots=True)
class PipelineResult:
    """A pipeline eredménye.

    Attributes:
        exit_code: ``EXIT_OK`` / ``EXIT_PARTIAL`` / ``EXIT_FATAL``.
        batch_id: A batch azonosítója (végzetes hibánál lehet üres).
        report: A batch jelentése (``None``, ha a batch el sem indult).
        log_path: A JSON-soros napló útvonala.
        message: Egysoros összegzés.
    """

    exit_code: int
    batch_id: str
    report: BatchReport | None
    log_path: Path
    message: str


class _JsonlLog:
    """Titoktalanító, soronként flush-oló JSON-soros napló."""

    def __init__(self, path: Path, clock: Callable[[], time.struct_time]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._clock = clock
        self._secrets = known_secrets()

    def event(self, step: str, status: str, **fields: Any) -> None:
        entry: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", self._clock()),
            "step": step,
            "status": status,
        }
        for key, value in fields.items():
            entry[key] = scrub_secrets(value, self._secrets) if isinstance(value, str) else value
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_pipeline(
    preset: str | None = None,
    *,
    spec: BatchSpec | None = None,
    db_path: Path | str,
    export_path: Path | None = None,
    policy: RetryPolicy | None = None,
    log_dir: Path = DEFAULT_LOG_DIR,
    allow_hardware: bool = False,
    max_runs: int | None = None,
    retry_abandoned: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], time.struct_time] = time.gmtime,
) -> PipelineResult:
    """A teljes lánc végrehajtása; soha nem dob kivételt a hívó felé.

    Args:
        preset: Batch-preset neve (vagy ``spec``).
        spec: Közvetlenül megadott batch (tesztekhez, hibainjektáláshoz).
        db_path: Az SQLite adatbázis.
        export_path: JSON-export célfájl (``None`` = nincs export).
        policy: Újrapróbálkozási politika (alapértelmezés: 3 próbálkozás).
        log_dir: A JSON-soros napló mappája.
        allow_hardware: Engedi-e ``ibm_qpu`` cellát tartalmazó batch indítását. Az
            ütemező ezt sosem állítja be (ADR-0008, 3. döntés).
        max_runs: Legfeljebb ennyi új futás.
        retry_abandoned: A feladott futások hibáinak megbocsátása indítás előtt.
        sleep: A visszalépés várakozása (tesztben injektálható).
        clock: Az időbélyeg forrása (tesztben injektálható).
    """
    log = _JsonlLog(log_dir / f"pipeline-{time.strftime('%Y%m%d', clock())}.jsonl", clock)
    policy = policy or RetryPolicy()

    # 1. Előellenőrzés
    try:
        if spec is None:
            if preset is None:
                raise ValueError("preset vagy spec megadása kötelező")
            spec = get_preset(preset)
        if any(cell.backend == "ibm_qpu" for cell in spec.cells) and not allow_hardware:
            raise PermissionError(
                "a batch valódi QPU-t használna; az automatizált pipeline ezt csak "
                "--allow-hardware mellett indítja (ADR-0008)"
            )
        if allow_hardware:
            # Batch szintű kvótakapu: engedély + a teljes batch legrosszabb esetére (+20%).
            # A futásonkénti védelem (run_vqe) ettől függetlenül minden futásnál lefut.
            planned = [p.config for p in expand(spec) if p.config.backend == "ibm_qpu"]
            if planned:
                guard_hardware_vqe(
                    sum(hardware_evaluation_budget(c) for c in planned),
                    reserve=HARDWARE_QUOTA_RESERVE,
                )
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        log.event("preflight", "fatal", error=message)
        return PipelineResult(EXIT_FATAL, "", None, log.path, message)
    log.event(
        "preflight",
        "ok",
        batch_id=spec.batch_id,
        planned_runs=spec.total_runs,
        max_attempts=policy.max_attempts,
    )

    # 2–3. Adatbázis, batch
    try:
        with Database(db_path) as db:
            if retry_abandoned:
                forgiven = db.forgive_failures(batch_id=spec.batch_id)
                log.event("retry_abandoned", "ok", forgiven_rows=forgiven)
            report = run_batch(
                spec,
                db,
                max_runs=max_runs,
                retry=policy,
                sleep=sleep,
                progress=lambda line: log.event("batch", "progress", message=line),
            )
            rows = db.batch_results(spec.batch_id)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        log.event("batch", "fatal", error=message)
        return PipelineResult(EXIT_FATAL, spec.batch_id, None, log.path, message)
    log.event(
        "batch",
        "done",
        completed=len(report.completed),
        skipped=len(report.skipped),
        failed=len(report.failed),
        abandoned=len(report.abandoned),
        wall_time_s=round(report.wall_time_s, 3),
    )

    # 4. Export
    if export_path is not None:
        try:
            write_export(export_path, spec, rows, aggregate_rows(rows), report.failed)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            log.event("export", "fatal", error=message)
            return PipelineResult(EXIT_FATAL, spec.batch_id, report, log.path, message)
        log.event("export", "ok", path=str(export_path), stored_runs=len(rows))

    # 5. Összegzés
    partial = bool(report.failed or report.abandoned)
    exit_code = EXIT_PARTIAL if partial else EXIT_OK
    message = (
        f"{spec.batch_id}: {len(report.completed)} új, {len(report.skipped)} kihagyva, "
        f"{len(report.failed)} hibás, {len(report.abandoned)} feladott"
    )
    log.event("summary", "partial" if partial else "ok", exit_code=exit_code, message=message)
    return PipelineResult(exit_code, spec.batch_id, report, log.path, message)
