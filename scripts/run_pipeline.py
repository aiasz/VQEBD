#!/usr/bin/env python3
"""Fázis 6 — a teljes pipeline egyszeri futtatása (``docs/plan/phase_06.md``).

Lánc: előellenőrzés → batch (korlátos újrapróbálkozással, hibatárolással) → export →
összegzés. Minden lépés egy JSON-soros naplóbejegyzés (``data/logs/``).

Használat::

    python scripts/run_pipeline.py --preset f5-smoke --db data/db/pipeline.sqlite \\
        --export data/exports/f5_smoke.json

    # a feladott (abandoned) futások hibáinak megbocsátása, majd újrapróbálás:
    python scripts/run_pipeline.py --preset f5-smoke --db data/db/pipeline.sqlite --retry-abandoned

Kilépési kód: ``0`` minden rendben · ``1`` részleges hiba (tárolva) · ``2`` végzetes.

Valódi QPU-t csak ``--allow-hardware`` + ``VQEBD_ALLOW_HARDWARE=true`` mellett indít,
és hardveres futásra a próbálkozások száma alapértelmezésben 1 (ADR-0008).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vqebd.batch.spec import PRESETS
from vqebd.pipeline.retry import RetryPolicy
from vqebd.pipeline.runner import DEFAULT_LOG_DIR, run_pipeline
from vqebd.storage import DEFAULT_DB_PATH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VQEBD pipeline (Fázis 6)")
    parser.add_argument("--preset", required=True, choices=sorted(PRESETS))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--export", type=Path, default=None, help="JSON-export célfájl")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--max-runs", type=int, default=None, help="legfeljebb ennyi új futás")
    parser.add_argument("--max-attempts", type=int, default=3, help="próbálkozások futásonként")
    parser.add_argument("--base-delay", type=float, default=5.0, help="első visszalépés (s)")
    parser.add_argument("--retry-abandoned", action="store_true")
    parser.add_argument("--allow-hardware", action="store_true")
    args = parser.parse_args(argv)

    try:
        policy = RetryPolicy(
            max_attempts=args.max_attempts,
            base_delay_s=args.base_delay,
            max_delay_s=max(300.0, args.base_delay),
        )
    except ValueError as exc:
        parser.error(str(exc))

    result = run_pipeline(
        args.preset,
        db_path=args.db,
        export_path=args.export,
        policy=policy,
        log_dir=args.log_dir,
        allow_hardware=args.allow_hardware,
        max_runs=args.max_runs,
        retry_abandoned=args.retry_abandoned,
    )
    print(result.message)
    print(f"Napló: {result.log_path}")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
