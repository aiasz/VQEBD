"""A dashboard ábrarétege: tiszta függvények, amelyek Plotly-ábrát adnak (Fázis 7, ADR-0009).

Az ábrákat az UI-tól függetlenül, adatszinten teszteljük (``trace.x`` / ``trace.y`` / ``trace.z``):
az ``AppTest`` a JS-ben renderelt Plotly-t nem futtatja.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Final

import pandas as pd
import plotly.graph_objects as go

from vqebd.dashboard.data import CHEMICAL_ACCURACY_MHA, METHOD_ORDER

__all__ = [
    "METHOD_COLORS",
    "REFERENCE_LABEL",
    "dissociation_figure",
    "method_comparison_figure",
    "ordered_methods",
    "trace_points",
]

REFERENCE_LABEL: Final[str] = "referencia (Full CI)"
"""A sávdiagram referenciasávja: a Full CI hibája definíció szerint 0."""

METHOD_COLORS: Final[dict[str, str]] = {
    "egzakt": "#0072B2",
    "lövészaj": "#56B4E9",
    "zajos (nyers)": "#D55E00",
    "ZNE lineáris": "#E69F00",
    "ZNE Richardson": "#009E73",
    "ZNE exponenciális": "#CC79A7",
    "QPU (nyers)": "#999999",
    "QPU (TREX)": "#000000",
    "QPU (resilience 2)": "#F0E442",
}
"""Módszerenként állandó szín (Okabe–Ito, színtévesztés-biztos): ugyanaz a módszer minden
nézetben ugyanazt a színt kapja."""

_FALLBACK_COLOR: Final[str] = "#7F7F7F"
_SYMBOLS: Final[tuple[str, ...]] = (
    "circle",
    "square",
    "diamond",
    "triangle-up",
    "x",
    "cross",
    "star",
    "triangle-down",
    "hexagon",
)
_REFERENCE_FONT_COLOR: Final[str] = "#52514e"


def ordered_methods(methods: Iterable[str]) -> list[str]:
    """A módszerek megjelenítési sorrendje: a ``METHOD_ORDER`` szerint, a többi utánuk, ábécében."""
    unique = set(methods)
    known = [m for m in METHOD_ORDER if m in unique]
    return known + sorted(unique - set(known))


def _empty_figure(message: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16, "color": _REFERENCE_FONT_COLOR},
            }
        ],
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig


def dissociation_figure(
    frame: pd.DataFrame,
    molecule: str,
    *,
    active_space: str | None = None,
    methods: Iterable[str] | None = None,
) -> go.Figure:
    """Energia a kötéshossz függvényében: referenciagörbék és a futások pontjai.

    Args:
        frame: A ``vqebd.dashboard.data.load_results`` normalizált táblája.
        molecule: A megjelenítendő molekula (``molecule_name``).
        active_space: Szűrés aktív térre (pl. ``"(2e,5o)"``); ``None`` = mind.
        methods: Szűrés módszercímkékre; ``None`` = mind.

    Returns:
        Plotly-ábra. A trace-ek sorrendje: Full CI, Hartree–Fock (ha van), majd a módszerek a
        ``METHOD_ORDER`` szerint. A futások pontjai egyenként jelennek meg (átlátszó jelölőkkel),
        a súgószöveg a ``run_id``-t és a hibát mutatja. Adat nélkül üres ábra magyarázattal.
    """
    title = f"{molecule} — energia a kötéshossz függvényében"
    subset = frame[frame["molecule_name"] == molecule]
    if active_space is not None:
        subset = subset[subset["active_space"] == active_space]
    if methods is not None:
        subset = subset[subset["method"].isin(set(methods))]
    subset = subset.dropna(subset=["bond_length", "energy_ha"])
    if subset.empty:
        return _empty_figure("Nincs megjeleníthető adat a kijelölt szűrőkkel.", title)

    fig = go.Figure()
    for column, name, dash in (
        ("full_ci_ha", "Full CI", "dash"),
        ("hartree_fock_ha", "Hartree–Fock", "dot"),
    ):
        reference = (
            subset[["bond_length", column]]
            .dropna()
            .drop_duplicates()
            .groupby("bond_length", as_index=False)[column]
            .first()
            .sort_values("bond_length")
        )
        if reference.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=reference["bond_length"].tolist(),
                y=reference[column].tolist(),
                mode="lines",
                name=name,
                line={"color": "#52514e", "dash": dash, "width": 2},
                hovertemplate=f"{name}<br>R = %{{x}} Å<br>E = %{{y:.8f}} Ha<extra></extra>",
            )
        )

    for index, method in enumerate(ordered_methods(subset["method"])):
        points = subset[subset["method"] == method].sort_values(["bond_length", "run_id"])
        fig.add_trace(
            go.Scatter(
                x=points["bond_length"].tolist(),
                y=points["energy_ha"].tolist(),
                mode="markers",
                name=method,
                marker={
                    "color": METHOD_COLORS.get(method, _FALLBACK_COLOR),
                    "symbol": _SYMBOLS[index % len(_SYMBOLS)],
                    "size": 9,
                    "opacity": 0.65,
                },
                customdata=points[["run_id", "error_mha"]].to_numpy().tolist(),
                hovertemplate=(
                    "%{customdata[0]}<br>R = %{x} Å<br>E = %{y:.8f} Ha"
                    "<br>hiba = %{customdata[1]:+.3f} mHa<extra>" + method + "</extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Kötéshossz (Å)",
        yaxis_title="Energia (Ha)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        hovermode="closest",
        margin={"t": 90},
    )
    return fig


def method_comparison_figure(table: pd.DataFrame, title: str = "") -> go.Figure:
    """Sávdiagram: módszerenként az átlagos energiahiba a Full CI-hez (mHa), referenciasávval.

    Args:
        table: A ``vqebd.dashboard.data.method_comparison_table`` eredménye.
        title: Az ábra címe.

    Returns:
        Egyetlen sávsorozatot tartalmazó ábra. Az első sáv a **referencia** (Full CI, hiba
        definíció szerint 0), utána a módszerek a ``METHOD_ORDER`` szerint. A hibasáv a
        mintaszórás (több futásnál); a kémiai pontosság (±1.6 mHa) zöld sávként jelenik meg.
        Adat nélkül magyarázott üres ábra.
    """
    if table.empty:
        return _empty_figure("Nincs megjeleníthető adat a kijelölt ponthoz.", title)

    labels = [REFERENCE_LABEL, *table["method"].tolist()]
    values = [0.0, *table["mean_error_mha"].tolist()]
    spreads = [0.0, *table["sd_mha"].fillna(0.0).tolist()]
    counts = [None, *table["n"].tolist()]
    colors = ["#52514e", *[METHOD_COLORS.get(m, _FALLBACK_COLOR) for m in table["method"]]]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            error_y={"type": "data", "array": spreads, "visible": True},
            customdata=counts,
            hovertemplate=("%{x}<br>hiba = %{y:+.3f} mHa<br>futások: %{customdata}<extra></extra>"),
            name="hiba",
        )
    )
    fig.add_hrect(
        y0=-CHEMICAL_ACCURACY_MHA,
        y1=CHEMICAL_ACCURACY_MHA,
        fillcolor="#0ca30c",
        opacity=0.15,
        line_width=0,
        annotation_text="kémiai pontosság (±1.6 mHa)",
        annotation_position="top left",
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        yaxis_title="Hiba a Full CI-hez (mHa)",
        xaxis_title="Módszer",
        showlegend=False,
        margin={"t": 90},
    )
    return fig


def trace_points(fig: go.Figure, name: str) -> tuple[list[Any], list[Any]]:
    """Egy trace ``(x, y)`` értékei név szerint (tesztekhez és hibakereséshez).

    Raises:
        KeyError: Ha nincs ilyen nevű trace.
    """
    for trace in fig.data:
        if trace.name == name:
            return list(trace.x), list(trace.y)
    raise KeyError(f"nincs ilyen trace: {name!r}; van: {[t.name for t in fig.data]}")
