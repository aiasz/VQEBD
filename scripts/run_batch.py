#!/usr/bin/env python3
"""Fázis 5 — batch futtatás konfigurációs mátrixon (``docs/plan/phase_05.md``).

Futtat vagy folytat egy előre definiált batchet az SQLite adatbázisba, majd a
batch rekordjait csoportosítja és összegzi (``vqebd.batch.aggregate``). Az
összegzés és a nyers rekordok JSON-ba kerülnek (``--export``) — ez a verziózott
proveniencia, mert maga az adatbázis nem kerül a repóba.

Használat::

    python scripts/run_batch.py --preset f5-deterministic --db data/db/f5.sqlite \\
        --export docs/figures/data/f5_deterministic.json

A futás folytatható: újraindítva a már tárolt futásokat kihagyja. A sikertelen
futások a ``run_failures`` táblába kerülnek (Fázis 6); újrapróbálkozáshoz és
ütemezéshez a ``scripts/run_pipeline.py`` való.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vqebd.batch import aggregate_rows, get_preset, run_batch
from vqebd.batch.export import write_export
from vqebd.batch.spec import PRESETS
from vqebd.storage import DEFAULT_DB_PATH, Database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VQEBD batch futtatás (Fázis 5)")
    parser.add_argument("--preset", required=True, choices=sorted(PRESETS))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--max-runs", type=int, default=None, help="legfeljebb ennyi új futás")
    parser.add_argument("--export", type=Path, default=None, help="JSON-export célfájl")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    spec = get_preset(args.preset)
    print(f"Batch: {spec.batch_id} — {spec.description}")
    print(f"Cellák: {len(spec.cells)}, futások: {spec.total_runs}, adatbázis: {args.db}")

    with Database(args.db) as db:
        report = run_batch(spec, db, max_runs=args.max_runs, progress=None if args.quiet else print)
        print(
            f"\nKész: {len(report.completed)} új, {len(report.skipped)} kihagyva (már tárolt), "
            f"{len(report.failed)} hibás, {report.remaining} hátra — {report.wall_time_s:.1f} s"
        )
        for run_id, message in report.failed:
            print(f"  HIBA {run_id}: {message}")

        rows = db.batch_results(spec.batch_id)

    groups = aggregate_rows(rows)
    print(f"\nCsoportok: {len(groups)}")
    for g in groups:
        err = g.error_vs_fci
        err_txt = f"{1e3 * err.mean:+9.4f} ± {1e3 * err.sd:7.4f} mHa" if err is not None else "—"
        print(
            f"  {g.molecule:5s} R={g.bond_length:<6g} {g.active_space_label:8s} "
            f"{g.backend:18s} {g.mitigation_label:22s} n={g.n:2d}  hiba(FCI) {err_txt}  "
            f"[{g.accuracy}]"
        )

    if args.export is not None:
        write_export(args.export, spec, rows, groups, report.failed)
        print(f"\nExport: {args.export}")

    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
