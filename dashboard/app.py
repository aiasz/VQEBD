"""A dashboard belépési pontja: ``streamlit run dashboard/app.py``.

Szándékosan vékony: a teljes logika a ``vqebd.dashboard`` csomagban él (ADR-0009, 1. döntés).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from vqebd.dashboard.app import main

main()
