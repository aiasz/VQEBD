"""Sémaverziózott, append-only eredménytárolás (SQLite) és export (ADR-0004).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vqebd.storage.db import DEFAULT_DB_PATH, Database
from vqebd.storage.export import export_to_csv, export_to_json
from vqebd.storage.schema import CURRENT_SCHEMA_VERSION
from vqebd.vqe.result import VQEResult

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "DEFAULT_DB_PATH",
    "Database",
    "export_to_csv",
    "export_to_json",
    "load_results",
    "save_result",
]


def save_result(
    result: VQEResult,
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    run_id: str | None = None,
) -> str:
    """Eredmény rekord közvetlen mentése az SQLite adatbázisba."""
    with Database(db_path) as db:
        return db.insert_result(result, run_id=run_id)


def load_results(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    molecule: str | None = None,
    backend: str | None = None,
    mitigation: str | None = None,
    within_chemical_accuracy: bool | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Eredmények lekérdezése az SQLite adatbázisból szűrőkkel."""
    with Database(db_path, read_only=True) as db:
        return db.query_results(
            molecule=molecule,
            backend=backend,
            mitigation=mitigation,
            within_chemical_accuracy=within_chemical_accuracy,
            limit=limit,
        )

