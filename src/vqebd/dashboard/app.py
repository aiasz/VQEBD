"""A dashboard Streamlit-felülete — vékony réteg az adat- és ábrarétegek fölött.

Indítás: ``streamlit run dashboard/app.py``. A felület csak olvas: az adatbázist
``read_only=True``-val nyitja, hálózatot és QPU-t nem ér el (ADR-0009, 4. döntés).

Környezeti változók:

``VQEBD_DASHBOARD_SOURCE``
    Az alapértelmezett adatforrás útvonala (felülírja az automatikus felderítést).
``VQEBD_DASHBOARD_ROOT``
    A felderítés gyökere (alapértelmezés: az aktuális könyvtár).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
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
    default_bond_length,
    load_failures,
    load_results,
    method_comparison_table,
    size_success_table,
)
from vqebd.dashboard.figures import (
    HEATMAP_METRICS,
    dissociation_figure,
    heatmap_figure,
    method_comparison_figure,
    ordered_methods,
)

__all__ = ["DISPLAY_COLUMNS", "VIEWS", "discover_sources", "main"]

VIEWS: Final[tuple[str, ...]] = (
    "Táblázat",
    "Disszociációs görbe",
    "Módszer-összehasonlítás",
    "Hőtérkép",
)
"""A nézetek (az oldalsáv „Nézet" kapcsolója). Az alapnézet az első; minden belső lépés egy
újabb nézetet ad hozzá, a korábbiak változatlanok (AC-7.8)."""

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

    view = st.sidebar.radio("Nézet", VIEWS, key="view")
    if view == "Táblázat":
        _render_table(results, failures)
    elif view == "Disszociációs görbe":
        _render_dissociation(results)
    elif view == "Módszer-összehasonlítás":
        _render_comparison(results)
    elif view == "Hőtérkép":
        _render_heatmap(results)


def _render_table(results: pd.DataFrame, failures: pd.DataFrame) -> None:
    """7.1: az eredménytábla és a hibák."""
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


def _render_dissociation(results: pd.DataFrame) -> None:
    """7.2: disszociációs görbe molekula-, aktívtér- és módszerválasztóval."""
    molecules = sorted(results["molecule_name"].dropna().unique())
    if not molecules:
        st.info("A forrás nem tartalmaz molekulát tartalmazó eredményt.")
        return
    molecule = st.selectbox("Molekula", molecules, key="molecule")
    of_molecule = results[results["molecule_name"] == molecule]
    spaces = ["összes", *sorted(of_molecule["active_space"].dropna().unique())]
    space = st.selectbox("Aktív tér", spaces, key="space")
    if space != "összes":
        of_molecule = of_molecule[of_molecule["active_space"] == space]
    available = ordered_methods(of_molecule["method"].dropna())
    # A kulcs a molekulától és az aktív tértől függ: váltáskor az alapértelmezett (mind) érvényesül.
    methods = st.multiselect(
        "Módszerek", available, default=available, key=f"methods-{molecule}-{space}"
    )
    st.plotly_chart(
        dissociation_figure(
            results,
            str(molecule),
            active_space=None if space == "összes" else str(space),
            methods=methods,
        ),
        key="dissociation",
    )
    st.caption(f"{len(of_molecule)} futás a kijelölt molekulára és aktív térre.")


def _render_comparison(results: pd.DataFrame) -> None:
    """7.3: módszer-összehasonlító sávdiagram (nyers vs. mitigált vs. referencia)."""
    molecules = sorted(results["molecule_name"].dropna().unique())
    if not molecules:
        st.info("A forrás nem tartalmaz molekulát tartalmazó eredményt.")
        return
    molecule = str(st.selectbox("Molekula", molecules, key="cmp-molecule"))
    of_molecule = results[results["molecule_name"] == molecule]
    spaces = ["összes", *sorted(of_molecule["active_space"].dropna().unique())]
    space = str(st.selectbox("Aktív tér", spaces, key="cmp-space"))
    active_space = None if space == "összes" else space
    if active_space is not None:
        of_molecule = of_molecule[of_molecule["active_space"] == active_space]
    lengths = sorted(of_molecule["bond_length"].dropna().unique())
    if not lengths:
        st.info("Nincs kötéshosszal rendelkező eredmény a kijelölésben.")
        return
    preferred = default_bond_length(results, molecule, active_space=active_space)
    index = lengths.index(preferred) if preferred in lengths else 0
    bond_length = float(
        st.selectbox("Kötéshossz (Å)", lengths, index=index, key=f"cmp-bond-{molecule}-{space}")
    )
    table = method_comparison_table(results, molecule, bond_length, active_space=active_space)
    title = f"{molecule} {bond_length:g} Å — módszerek összehasonlítása"
    st.plotly_chart(method_comparison_figure(table, title), key="comparison")
    if not table.empty:
        st.dataframe(table, hide_index=True)


def _render_heatmap(results: pd.DataFrame) -> None:
    """7.4: körméret × módszer hőtérkép (sikeresség vagy medián hiba)."""
    molecules = sorted(results["molecule_name"].dropna().unique())
    if not molecules:
        st.info("A forrás nem tartalmaz molekulát tartalmazó eredményt.")
        return
    chosen = st.multiselect("Molekulák", molecules, default=molecules, key="heat-molecules")
    metric = st.radio(
        "Mérőszám",
        list(HEATMAP_METRICS),
        format_func=lambda key: HEATMAP_METRICS[key][0],
        key="heat-metric",
    )
    table = size_success_table(results, chosen)
    st.plotly_chart(
        heatmap_figure(table, metric, "Körméret és sikeresség"),
        key="heatmap",
    )
    unknown = int(results[results["molecule_name"].isin(chosen)]["n_qubits"].isna().sum())
    if unknown:
        st.caption(f"{unknown} futás kimaradt: a körméret nem levezethető (ismeretlen bázis).")
    if results[results["molecule_name"].isin(chosen)]["size_assumed"].any():
        st.caption(
            "A körméret egy részénél a leképezés/bázis hiányzott az adatból: a VQEBD "
            "alapértelmezése (parity, kétqubites redukció, STO-3G) érvényes."
        )
    if not table.empty:
        st.dataframe(table, hide_index=True)
