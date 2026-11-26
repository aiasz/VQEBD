#!/usr/bin/env python3
"""Fázis 11 — a blokkok kalibráció-életkorának rekonstrukciója az IBM történeti kalibrációjából.

Minden megerősítő és kiegészítő blokkhoz (``c*.json``) lekérdezi a blokk első jobjának indulásakor
érvényes kalibrációt (``backend.properties(datetime=…)``), és a ``vqebd.heron_calibration_age``
definíciója szerint kiszámolja az életkort (a ``phase_11.md`` 2026-11-19-i rögzítése). **Csak
olvasás**: jobot nem küld be, QPU-időt nem használ. Az eredmény a C9 előre rögzített, 48 órás
érzékenységi vizsgálatának bemenete (``scripts/analyze_heron.py``).

Használat::

    python scripts/heron_calibration_age.py    # → docs/figures/data/f11/calibration_age.json

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

from vqebd.hardware import connect_service
from vqebd.heron_calibration_age import block_calibration_age, first_job_running

DATA_DIR = Path("docs/figures/data/f11")
OUT_NAME = "calibration_age.json"


def load_blocks(data_dir: Path) -> list[dict[str, Any]]:
    """A megerősítő és kiegészítő blokkfájlok (``c1.json`` …), blokkszám szerint rendezve."""
    files = sorted(data_dir.glob("c[0-9].json"), key=lambda f: int(f.stem[1:]))
    blocks = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    return [b for b in blocks if b.get("kind") in ("confirmatory", "supplementary")]


def load_previous(path: Path) -> dict[str, dict[str, Any]]:
    """A korábbi életkor-fájl rekordjai blokknév szerint (hiányában vagy hibásan üres)."""
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(r.get("block")): r for r in payload.get("blocks", []) if isinstance(r, dict)}


def still_valid(record: dict[str, Any], block: dict[str, Any]) -> bool:
    """Érvényes-e még a korábbi rekord: van életkora, és ugyanahhoz a blokkfuttatáshoz tartozik."""
    age, recorded = record.get("age_h"), record.get("first_job_running_utc")
    if isinstance(age, bool) or not isinstance(age, int | float) or not recorded:
        return False
    try:
        start = first_job_running(block)
        then = dt.datetime.fromisoformat(str(recorded).replace("Z", "+00:00"))
    except ValueError:
        return False
    return abs((start - then).total_seconds()) < 1.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fázis 11 — kalibráció-életkor (csak olvasás)")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    blocks = load_blocks(args.data_dir)
    if not blocks:
        print("Nincs megerősítő vagy kiegészítő blokk.", file=sys.stderr)
        return 1
    out = args.data_dir / OUT_NAME
    previous = load_previous(out)
    service = connect_service()
    backends: dict[str, Any] = {}
    records = []
    failed = []
    for block in blocks:
        try:
            name = block["backend"]
            if name not in backends:
                backends[name] = service.backend(name)
            properties = backends[name].properties(datetime=first_job_running(block))
            if properties is None:
                raise ValueError("a történeti kalibráció nem érhető el")
            record = block_calibration_age(block, properties)
        except Exception as exc:  # egy blokk hibája ne vesszen el a többi eredménye
            failed.append(block.get("block"))
            old = previous.get(str(block.get("block")))
            if old is not None and still_valid(old, block):
                records.append({**old, "reused_after_error": repr(exc)})
                print(
                    f"{block.get('block')}: HIBA — a korábbi rekord marad: {exc!r}", file=sys.stderr
                )
                continue
            records.append(
                {
                    "block": block.get("block"),
                    "kind": block.get("kind"),
                    "age_h": None,
                    "error": repr(exc),
                }
            )
            print(f"{block.get('block')}: HIBA — {exc!r}", file=sys.stderr)
            continue
        records.append(record)
        print(
            f"{record['block']}: {record['age_h']:.1f} h "
            f"(legrégebbi: {record['oldest_parameter']}, "
            f"{record['oldest_parameter_date_utc']}; egyezik a pillanatképpel: "
            f"{record['matches_snapshot']})"
        )
    payload = {
        "definition": (
            "az első job indulása − a qubitpár T1, T2, kiolvasási hiba és cz-hiba legrégebbi "
            "mérési időpontja (órában); az sx/x hiba kimarad (phase_11.md, 2026-11-19)"
        ),
        "source": "backend.properties(datetime=<az első job indulása>), csak olvasás",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "blocks": records,
    }
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Mentve: {out}")
    if failed:
        print(f"Ismeretlen életkorú blokkok (hiba): {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
