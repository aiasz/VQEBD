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

from vqebd.dashboard.data import METHOD_ORDER

__all__ = ["METHOD_COLORS", "dissociation_figure", "ordered_methods", "trace_points"]

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


def trace_points(fig: go.Figure, name: str) -> tuple[list[Any], list[Any]]:
    """Egy trace ``(x, y)`` értékei név szerint (tesztekhez és hibakereséshez).

    Raises:
        KeyError: Ha nincs ilyen nevű trace.
    """
    for trace in fig.data:
        if trace.name == name:
            return list(trace.x), list(trace.y)
    raise KeyError(f"nincs ilyen trace: {name!r}; van: {[t.name for t in fig.data]}")
