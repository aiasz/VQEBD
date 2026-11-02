"""Ütemező: a pipeline rendszeres indítása, átfedés elleni zárral (Fázis 6, ADR-0008).

Szándékosan nem cron-démon: a konténer nem-root felhasználóval fut, és egy Python-hurok
(injektálható ``sleep`` és óra) tesztelhető és platformfüggetlen.

**Hardverpolitika:** az ütemező ``allow_hardware=False``-szal hívja a pipeline-t, és a
``--allow-hardware`` kapcsolót az ismétlődő (``--every``) üzemmóddal együtt elutasítja.
Valódi QPU-t egyszeri, kézi futtatás indíthat (ADR-0008, 3. döntés).

A zár **kizárólag időalapú** elavulást ismer (nincs PID-ellenőrzés): Windowson az
``os.kill(pid, 0)`` a folyamatot megszüntetné, ezért nem használjuk.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Final

from vqebd.batch.spec import PRESETS
from vqebd.pipeline.retry import RetryPolicy
from vqebd.pipeline.runner import DEFAULT_LOG_DIR, EXIT_FATAL, run_pipeline
from vqebd.storage import DEFAULT_DB_PATH

__all__ = ["LockHeldError", "PipelineLock", "main", "parse_interval", "run_scheduler"]

DEFAULT_LOCK_PATH: Final[Path] = Path("data/scheduler.lock")
DEFAULT_STALE_AFTER_S: Final[float] = 12 * 3600.0
"""Az elavultnak tekintett zár kora. Nagyobb, mint a leghosszabb ismert pipeline
(``f5-deterministic`` ≈ 42 perc), de egy összeomlott folyamat zárja így sem marad örökre."""

_INTERVAL = re.compile(r"^(\d+(?:\.\d+)?)\s*([smhd])$")
_UNITS: Final[dict[str, float]] = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}


class LockHeldError(RuntimeError):
    """A zárat egy másik, még élő pipeline tartja."""


def parse_interval(text: str) -> float:
    """``"30s"``, ``"15m"``, ``"6h"``, ``"1d"`` → másodperc.

    Raises:
        ValueError: Ismeretlen formátum vagy nem pozitív érték.
    """
    match = _INTERVAL.match(text.strip().lower())
    if match is None:
        raise ValueError(f"érvénytelen intervallum: {text!r} (példa: 30s, 15m, 6h, 1d)")
    seconds = float(match.group(1)) * _UNITS[match.group(2)]
    if seconds <= 0:
        raise ValueError(f"az intervallum pozitív legyen: {text!r}")
    return seconds


class PipelineLock:
    """Átfedés elleni zárfájl (``O_CREAT | O_EXCL``, időalapú elavulással)."""

    def __init__(
        self,
        path: Path,
        *,
        stale_after_s: float = DEFAULT_STALE_AFTER_S,
        now: Callable[[], float] = time.time,
    ) -> None:
        self.path = path
        self.stale_after_s = stale_after_s
        self._now = now
        self._held = False

    def _age_s(self) -> float | None:
        """A meglévő zár kora, vagy ``None``, ha nincs. Sérült tartalom: elavult."""
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        try:
            started = float(json.loads(raw)["started"])
        except (ValueError, KeyError, TypeError):
            return float("inf")
        return self._now() - started

    def acquire(self) -> None:
        """A zár megszerzése.

        Raises:
            LockHeldError: Ha egy friss zár létezik.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        age = self._age_s()
        if age is not None:
            if age < self.stale_after_s:
                raise LockHeldError(f"a zár él ({age:.0f} s): {self.path}")
            self.path.unlink(missing_ok=True)  # elavult vagy sérült zár
        payload = json.dumps({"pid": os.getpid(), "started": self._now()})
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise LockHeldError(
                f"a zárat közben megszerezte egy másik folyamat: {self.path}"
            ) from None
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        self._held = True

    def release(self) -> None:
        """A zár elengedése (csak a sajátunkat)."""
        if self._held:
            self.path.unlink(missing_ok=True)
            self._held = False


def run_scheduler(
    job: Callable[[], int],
    *,
    every_s: float | None,
    lock: PipelineLock,
    sleep: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
    log: Callable[[str], None] = print,
) -> int:
    """A feladat egyszeri vagy ismétlődő futtatása, átfedés nélkül.

    Args:
        job: A pipeline-hívás; kilépési kódot ad.
        every_s: Az ismétlés periódusa másodpercben; ``None`` = egyszeri futás.
        lock: Az átfedés elleni zár.
        sleep: A várakozás (tesztben injektálható).
        max_iterations: Az iterációk korlátja (tesztekhez); ``None`` = végtelen.
        log: Naplózó.

    Returns:
        Egyszeri futásnál a feladat kilépési kódja (``0`` / ``1`` / ``2``), ha a zár
        foglalt: ``2``. Ismétlődő üzemmódban az utolsó iteráció kilépési kódja.
    """
    iteration = 0
    exit_code = 0
    while True:
        iteration += 1
        try:
            lock.acquire()
        except LockHeldError as exc:
            log(f"[ütemező] kihagyva: {exc}")
            exit_code = EXIT_FATAL if every_s is None else exit_code
        else:
            try:
                exit_code = job()
                log(f"[ütemező] iteráció {iteration}: kilépési kód {exit_code}")
            finally:
                lock.release()
        if every_s is None or (max_iterations is not None and iteration >= max_iterations):
            return exit_code
        sleep(every_s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VQEBD ütemező (Fázis 6)")
    parser.add_argument("--preset", required=True, choices=sorted(PRESETS))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--export", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument(
        "--every", default=None, help="ismétlési periódus (pl. 6h); nélküle egyszeri"
    )
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument(
        "--allow-hardware",
        action="store_true",
        help="valódi QPU engedélyezése; CSAK egyszeri futással (nem --every)",
    )
    args = parser.parse_args(argv)

    if args.allow_hardware and args.every is not None:
        parser.error(
            "--allow-hardware nem kombinálható --every-vel (ADR-0008: a hardver nem ütemezett)"
        )
    try:
        every_s = parse_interval(args.every) if args.every is not None else None
        policy = RetryPolicy(max_attempts=args.max_attempts)
    except ValueError as exc:
        parser.error(str(exc))

    def job() -> int:
        result = run_pipeline(
            args.preset,
            db_path=args.db,
            export_path=args.export,
            policy=policy,
            log_dir=args.log_dir,
            allow_hardware=args.allow_hardware,
        )
        print(f"[pipeline] {result.message} (napló: {result.log_path})")
        return result.exit_code

    return run_scheduler(job, every_s=every_s, lock=PipelineLock(args.lock))


if __name__ == "__main__":
    sys.exit(main())
