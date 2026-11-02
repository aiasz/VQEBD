"""A batch JSON-exportja (a ``scripts/run_batch.py`` és a pipeline közös kódja).

A formátum a Fázis 5 óta változatlan: a ``docs/figures/data/f5_*.json`` fájlokat ez
állítja elő. Itt él, hogy a CLI és a pipeline bitre azonos exportot adjon.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from vqebd import __version__
from vqebd.batch.aggregate import GroupStatistics
from vqebd.batch.spec import BatchSpec

__all__ = ["EXPORT_FIELDS", "build_export_payload", "write_export"]

EXPORT_FIELDS: Final[tuple[str, ...]] = (
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
"""A JSON-exportba kerülő rekordmezők (a teljes rekord az adatbázisban marad)."""


def build_export_payload(
    spec: BatchSpec,
    rows: Sequence[dict[str, Any]],
    groups: Sequence[GroupStatistics],
    failed: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    """Az export szótára: metaadat, hibák, csoportstatisztikák és rekordok."""
    return {
        "batch_id": spec.batch_id,
        "description": spec.description,
        "vqebd_version": __version__,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "planned_runs": spec.total_runs,
        "stored_runs": len(rows),
        "failed": [{"run_id": r, "error": m} for r, m in failed],
        "groups": [g.to_dict() for g in groups],
        "rows": [{k: row.get(k) for k in EXPORT_FIELDS} for row in rows],
    }


def write_export(
    path: Path,
    spec: BatchSpec,
    rows: Sequence[dict[str, Any]],
    groups: Sequence[GroupStatistics],
    failed: Sequence[tuple[str, str]],
) -> None:
    """Az export írása (UTF-8, LF sorvég, a célmappa létrehozásával)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_export_payload(spec, rows, groups, failed)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
