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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fázis 11 — kalibráció-életkor (csak olvasás)")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    blocks = load_blocks(args.data_dir)
    if not blocks:
        print("Nincs megerősítő vagy kiegészítő blokk.", file=sys.stderr)
        return 1
    service = connect_service()
    backends: dict[str, Any] = {}
    records = []
    for block in blocks:
        name = block["backend"]
        if name not in backends:
            backends[name] = service.backend(name)
        backend = backends[name]
        properties = backend.properties(datetime=first_job_running(block))
        record = block_calibration_age(block, properties)
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
    out = args.data_dir / OUT_NAME
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Mentve: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
