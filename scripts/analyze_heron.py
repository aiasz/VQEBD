#!/usr/bin/env python3
"""Fázis 11 — a H1–H4 kiértékelése a mentett blokkfájlokból (``docs/figures/data/f11/``).

Az elemzés logikája a ``vqebd.heron_analysis`` modulban van (a mérések előtt megírva és
szintetikus adaton tesztelve); ez a szkript csak beolvassa a blokkokat és kiírja az eredményt.

Kimenet:

- ``primary`` — az előre rögzített H1–H4 (``analyze``): **csak a megerősítő blokkok** (C1–C8);
  a pilot csak a H4 referenciája, a kiegészítő C9 nem számít bele;
- ``confirmatory_complete`` — a megerősítő blokkok száma eléri-e a ``PROTOCOL`` szerinti 8-at
  (ha nem, az eredmény nem a végleges elsődleges elemzés);
- ``sensitivity`` — a 2026-11-18-án rögzített, csak leíró érzékenységi vizsgálatok (döntés
  nélkül): (a) C1–C9, (b) a legfeljebb 48 órás kalibrációjú blokkok. A (b) a
  ``calibration_age.json`` fájlt használja (``scripts/heron_calibration_age.py``); ha hiányzik,
  minden blokk „ismeretlen életkorú”.

Használat::

    python scripts/analyze_heron.py                # a nyers eredmény JSON-ként a stdout-ra
    python scripts/analyze_heron.py --out docs/figures/data/f11/analysis.json

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vqebd.heron_analysis import AnalysisError, analyze, sensitivity_analyses
from vqebd.heron_model import PROTOCOL, protocol_fingerprint

SENSITIVITY_MAX_AGE_H = 48.0
"""A (b) érzékenységi vizsgálat határa órában (``phase_11.md``, 2026-11-18; nem ``PROTOCOL``)."""


def load_ages(data_dir: Path) -> dict[str, float]:
    """Blokkonkénti kalibráció-életkor (óra) a ``calibration_age.json``-ból; hiányában üres."""
    path = data_dir / "calibration_age.json"
    if not path.is_file():
        return {}
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return {str(r["block"]): float(r["age_h"]) for r in payload.get("blocks", [])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fázis 11 elemzés")
    parser.add_argument("--data-dir", type=Path, default=Path("docs/figures/data/f11"))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    files = sorted(args.data_dir.glob("[bc][0-9].json"))
    blocks = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    stale = [b["block"] for b in blocks if b.get("protocol_fingerprint") != protocol_fingerprint()]
    if stale:
        print(
            f"FIGYELEM: a(z) {stale} blokk más protokollal készült — nem elemezhető együtt",
            file=sys.stderr,
        )
        return 2
    try:
        primary = analyze(
            blocks,
            delta=PROTOCOL["delta_mha"],
            equivalence_confidence=PROTOCOL["equivalence_confidence"],
        )
        sensitivity = sensitivity_analyses(
            blocks,
            load_ages(args.data_dir),
            max_age_h=SENSITIVITY_MAX_AGE_H,
            confidence=PROTOCOL["equivalence_confidence"],
        )
    except AnalysisError as exc:
        print(f"Az elemzés nem végezhető el: {exc}", file=sys.stderr)
        return 1
    expected = int(PROTOCOL["confirmatory_blocks"])
    complete = primary["n_confirmatory_blocks"] == expected
    if not complete:
        print(
            f"FIGYELEM: {primary['n_confirmatory_blocks']} megerősítő blokk a tervezett {expected} "
            "helyett — ez nem a végleges elsődleges elemzés",
            file=sys.stderr,
        )
    result = {
        "protocol_fingerprint": protocol_fingerprint(),
        "confirmatory_blocks_expected": expected,
        "confirmatory_complete": complete,
        "primary": primary,
        "sensitivity": sensitivity,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
