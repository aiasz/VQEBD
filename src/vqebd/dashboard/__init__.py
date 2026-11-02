"""A VQEBD dashboardja (Fázis 7, ``docs/plan/phase_07.md``, ADR-0009).

Rétegek: ``data`` (pandas, tiszta), ``figures`` (Plotly, tiszta), ``app`` (Streamlit, vékony).
A csomag ``__init__``-je szándékosan nem importál semmit: az adat- és ábrarétegek a
Streamlit nélkül is használhatók és tesztelhetők.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations
