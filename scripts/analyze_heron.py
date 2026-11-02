#!/usr/bin/env python3
"""Fázis 11 — a H1–H4 kiértékelése a mentett blokkfájlokból (``docs/figures/data/f11/``).

Az elemzés logikája a ``vqebd.heron_analysis`` modulban van (a mérések előtt megírva és
szintetikus adaton tesztelve); ez a szkript csak beolvassa a blokkokat és kiírja az eredményt.

Használat::

    python scripts/analyze_heron.py                # a nyers eredmény JSON-ként a stdout-ra
    python scripts/analyze_heron.py --out docs/figures/data/f11/analysis.json

Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vqebd.heron_analysis import AnalysisError, analyze
from vqebd.heron_model import PROTOCOL, protocol_fingerprint


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
        result = analyze(
            blocks,
            delta=PROTOCOL["delta_mha"],
            equivalence_confidence=PROTOCOL["equivalence_confidence"],
        )
    except AnalysisError as exc:
        print(f"Az elemzés nem végezhető el: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
