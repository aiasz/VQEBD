"""Determinisztikus CSV és JSON exportálás a FAIR-alapelvekhez (ADR-0004).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

__all__ = ["export_to_csv", "export_to_json"]


def export_to_csv(results: Sequence[dict[str, Any]], out_path: Path | str) -> Path:
    """Eredmények determinisztikus exportálása CSV fájlba.

    A rendezett sorrend és oszlopok biztosítják a Git diffek és archiválások
    stabilitását (reprodukálhatóság).
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        path.write_text("", encoding="utf-8", newline="\n")
        return path

    # Rögzített oszloprend az első rekordból
    fieldnames = list(results[0].keys())

    # Determinisztikus sorrend: timestamp, majd run_id szerint
    sorted_rows = sorted(
        results, key=lambda r: (str(r.get("timestamp", "")), str(r.get("run_id", "")))
    )

    with path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in sorted_rows:
            writer.writerow(row)

    return path


def export_to_json(results: Sequence[dict[str, Any]], out_path: Path | str) -> Path:
    """Eredmények determinisztikus exportálása JSON fájlba."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    sorted_rows = sorted(
        results, key=lambda r: (str(r.get("timestamp", "")), str(r.get("run_id", "")))
    )

    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(sorted_rows, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    return path
