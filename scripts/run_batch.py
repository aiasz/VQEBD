#!/usr/bin/env python3
"""Fázis 5 — batch futtatás konfigurációs mátrixon (``docs/plan/phase_05.md``).

Futtat vagy folytat egy előre definiált batchet az SQLite adatbázisba, majd a
batch rekordjait csoportosítja és összegzi (``vqebd.batch.aggregate``). Az
összegzés és a nyers rekordok JSON-ba kerülnek (``--export``) — ez a verziózott
proveniencia, mert maga az adatbázis nem kerül a repóba.

Használat::

    python scripts/run_batch.py --preset f5-deterministic --db data/db/f5.sqlite \\
        --export docs/figures/data/f5_deterministic.json

A futás folytatható: újraindítva a már tárolt futásokat kihagyja.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from vqebd import __version__
from vqebd.batch import aggregate_rows, get_preset, run_batch
from vqebd.batch.spec import PRESETS
from vqebd.storage import DEFAULT_DB_PATH, Database

# A JSON-exportba kerülő rekordmezők (a teljes rekord a DB-ben marad).
EXPORT_FIELDS = (
    "run_id",
    "molecule_name",
    "bond_length",
    "active_electrons",
    "active_orbitals",
    "backend",
    "platform",
    "precision",
    "optimizer_method",
    "mitigation_strategy",
    "mitigation_extrapolator",
    "repeat_index",
    "master_seed",
    "energy_ha",
    "optimizer_final_ha",
    "optimizer_history_min_ha",
    "optimal_parameters_json",
    "reestimate_mean_ha",
    "reestimate_sem_ha",
    "reestimate_n",
    "hartree_fock_ha",
    "full_ci_ha",
    "casci_ha",
    "exact_diag_ha",
    "energy_offset_ha",
    "n_function_evaluations",
    "converged",
    "wall_time_s",
    "config_hash",
)


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
        args.export.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "batch_id": spec.batch_id,
            "description": spec.description,
            "vqebd_version": __version__,
            "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "planned_runs": spec.total_runs,
            "stored_runs": len(rows),
            "failed": [{"run_id": r, "error": m} for r, m in report.failed],
            "groups": [g.to_dict() for g in groups],
            "rows": [{k: row.get(k) for k in EXPORT_FIELDS} for row in rows],
        }
        args.export.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"\nExport: {args.export}")

    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
