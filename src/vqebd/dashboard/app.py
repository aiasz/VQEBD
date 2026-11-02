"""A dashboard Streamlit-felülete — vékony réteg az adat- és ábrarétegek fölött.

Indítás: ``streamlit run dashboard/app.py``. A felület csak olvas: az adatbázist
``read_only=True``-val nyitja, hálózatot és QPU-t nem ér el (ADR-0009, 4. döntés).

Környezeti változók:

``VQEBD_DASHBOARD_SOURCE``
    Az alapértelmezett adatforrás útvonala (felülírja az automatikus felderítést).
``VQEBD_DASHBOARD_ROOT``
    A felderítés gyökere (alapértelmezés: az aktuális könyvtár).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import pandas as pd
import streamlit as st

from vqebd.dashboard.data import (
    DataLoadError,
    load_failures,
    load_results,
)

__all__ = ["DISPLAY_COLUMNS", "discover_sources", "main"]

DISPLAY_COLUMNS: Final[tuple[str, ...]] = (
    "run_id",
    "molecule_name",
    "bond_length",
    "active_space",
    "n_qubits",
    "backend",
    "method",
    "energy_ha",
    "error_mha",
    "chemically_accurate",
    "repeat_index",
    "batch_id",
)
"""A táblázatban megjelenő oszlopok (a teljes, levezetett tábla ennél több mezőt tart)."""

_DISCOVERY_GLOBS: Final[tuple[str, ...]] = (
    "data/db/*.sqlite",
    "data/db/*.db",
    "docs/figures/data/f5_*.json",
    "docs/figures/data/results_v*.json",
)


def discover_sources(root: Path) -> list[Path]:
    """A ``root`` alatt található adatforrások (SQLite és ismert JSON-exportok), rendezve."""
    found: list[Path] = []
    for pattern in _DISCOVERY_GLOBS:
        found.extend(sorted(root.glob(pattern)))
    return found


@st.cache_data(show_spinner=False)
def _load(path: str, mtime: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Betöltés gyorsítótárral; a ``mtime`` a kulcs része, így a változott fájl újratöltődik."""
    del mtime
    return load_results(path), load_failures(path)


def _choose_source() -> Path | None:
    """Az oldalsáv: felderített források + egyéni útvonal. ``None``, ha nincs mit megnyitni."""
    root = Path(os.environ.get("VQEBD_DASHBOARD_ROOT", "."))
    preset = os.environ.get("VQEBD_DASHBOARD_SOURCE")
    options = [str(p) for p in discover_sources(root)]
    if preset and preset not in options:
        options.insert(0, preset)

    st.sidebar.header("Adatforrás")
    chosen = st.sidebar.selectbox("Felderített források", options, index=0 if options else None)
    custom = st.sidebar.text_input("Egyéni útvonal (felülírja a fentit)", value="")
    path = custom.strip() or chosen
    return Path(path) if path else None


def main() -> None:
    """A dashboard belépési pontja."""
    st.set_page_config(page_title="VQEBD", layout="wide")
    st.title("VQEBD — eredmények")

    source = _choose_source()
    if source is None:
        st.info(
            "Nincs megnyitható adatforrás. Futtass egy batch-et "
            "(`scripts/run_batch.py`), vagy adj meg egyéni útvonalat az oldalsávban."
        )
        return

    try:
        results, failures = _load(str(source), source.stat().st_mtime if source.is_file() else 0.0)
    except DataLoadError as exc:
        st.error(str(exc))
        return

    st.caption(f"Forrás: `{source}`")
    columns = st.columns(3)
    columns[0].metric("Futások", len(results))
    columns[1].metric("Kémiailag pontos", int(results["chemically_accurate"].sum()))
    columns[2].metric("Hibás próbálkozások", len(failures))

    tab_results, tab_failures = st.tabs(["Eredmények", "Hibák"])
    with tab_results:
        if results.empty:
            st.info("A forrás nem tartalmaz eredményt.")
        else:
            st.dataframe(results[list(DISPLAY_COLUMNS)], hide_index=True)
    with tab_failures:
        if failures.empty:
            st.info("Nincs tárolt hiba (a hibatábla csak SQLite-forrásban van).")
        else:
            st.dataframe(failures, hide_index=True)
