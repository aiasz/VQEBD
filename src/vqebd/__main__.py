"""``python -m vqebd`` belépési pont.

A tényleges megvalósítás a :mod:`vqebd.cli` modulban van; ez a fájl csak a
futtatható modul-protokollt (PEP 338) elégíti ki.
"""

from __future__ import annotations

from vqebd.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
