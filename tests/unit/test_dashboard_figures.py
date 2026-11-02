"""Fázis 7 — a dashboard ábrarétege, adatszinten (AC-7.5 és később AC-7.6, AC-7.7).

A trace-ek ``x`` / ``y`` értékeit vizsgáljuk: a JS-ben renderelt képet a headless teszt nem látja.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

pytest.importorskip("plotly", reason="az ábraréteg-tesztek a plotly csomagot igénylik")

from vqebd.dashboard.data import (
    CHEMICAL_ACCURACY_MHA,
    COMPARISON_COLUMNS,
    METHOD_ORDER,
    default_bond_length,
    load_results,
    method_comparison_table,
)
from vqebd.dashboard.figures import (
    METHOD_COLORS,
    REFERENCE_LABEL,
    dissociation_figure,
    method_comparison_figure,
    ordered_methods,
    trace_points,
)
from vqebd.storage import Database

pytestmark = pytest.mark.unit

RecordFactory = Callable[..., dict[str, Any]]

# Ismert tesztadat: a Full CI és a HF értékei R-függők, így a görbék ellenőrizhetők.
FCI = {0.5: -1.0552, 0.735: -1.1373, 1.0: -1.1012}
HF = {0.5: -1.0430, 0.735: -1.1170, 1.0: -1.0661}


@pytest.fixture
def curve_frame(tmp_path: Path, record_factory: RecordFactory) -> pd.DataFrame:
    """H₂ három geometrián (egzakt), 0.735 és 1.0 Å-nél zajos és ZNE is; LiH két aktív térrel."""
    records: list[dict[str, Any]] = []
    for r in (0.5, 0.735, 1.0):
        records.append(
            record_factory(
                run_id=f"h2-exact-{r}",
                bond_length=r,
                energy_ha=FCI[r],
                full_ci_ha=FCI[r],
                hartree_fock_ha=HF[r],
            )
        )
    for r in (0.735, 1.0):
        records.append(
            record_factory(
                run_id=f"h2-noisy-{r}",
                bond_length=r,
                backend="qiskit_aer_noisy",
                energy_ha=FCI[r] + 0.030,
                full_ci_ha=FCI[r],
                hartree_fock_ha=HF[r],
            )
        )
    records.append(
        record_factory(
            run_id="h2-zne-0.735",
            bond_length=0.735,
            backend="qiskit_aer_noisy",
            mitigation_strategy="zne_local",
            mitigation_extrapolator="richardson",
            energy_ha=FCI[0.735] + 0.010,
            full_ci_ha=FCI[0.735],
            hartree_fock_ha=HF[0.735],
        )
    )
    # Egy második zajos futás ugyanarra a pontra: az egyes futások mind megjelennek.
    records.append(
        record_factory(
            run_id="h2-noisy-0.735-b",
            bond_length=0.735,
            backend="qiskit_aer_noisy",
            energy_ha=FCI[0.735] + 0.040,
            full_ci_ha=FCI[0.735],
            hartree_fock_ha=HF[0.735],
        )
    )
    for run_id, r, orbitals in (
        ("lih-3o-1.2", 1.2, 3),
        ("lih-3o-1.6", 1.6, 3),
        ("lih-5o-1.6", 1.6, 5),
    ):
        records.append(
            record_factory(
                run_id=run_id,
                molecule_name="LiH",
                bond_length=r,
                active_electrons=2,
                active_orbitals=orbitals,
                energy_ha=-7.80 - 0.01 * orbitals - r / 100,
                full_ci_ha=-7.9 - r / 100,
                hartree_fock_ha=-7.86 - r / 100,
                casci_ha=-7.80 - 0.01 * orbitals - r / 100,
            )
        )
    path = tmp_path / "curve.sqlite"
    with Database(path) as db:
        for record in records:
            db.insert_record(record)
    return load_results(path)


# --- sorrend és színek -----------------------------------------------------------------------


def test_ordered_methods_follow_the_display_order_then_alphabetical() -> None:
    methods = ["ZNE Richardson", "valami_uj", "egzakt", "zajos (nyers)", "abc"]
    assert ordered_methods(methods) == [
        "egzakt",
        "zajos (nyers)",
        "ZNE Richardson",
        "abc",
        "valami_uj",
    ]
    assert ordered_methods([]) == []


def test_every_known_method_has_a_color() -> None:
    assert set(METHOD_ORDER) <= set(METHOD_COLORS)
    assert len(set(METHOD_COLORS.values())) == len(METHOD_COLORS)  # nincs két azonos szín


# --- disszociációs görbe (AC-7.5) ---------------------------------------------------------------


def test_trace_order_is_references_then_methods(curve_frame: pd.DataFrame) -> None:
    fig = dissociation_figure(curve_frame, "H2")
    assert [t.name for t in fig.data] == [
        "Full CI",
        "Hartree–Fock",
        "egzakt",
        "zajos (nyers)",
        "ZNE Richardson",
    ]


def test_reference_curves_hold_the_known_values_sorted_by_bond_length(
    curve_frame: pd.DataFrame,
) -> None:
    fig = dissociation_figure(curve_frame, "H2")
    assert trace_points(fig, "Full CI") == ([0.5, 0.735, 1.0], [FCI[0.5], FCI[0.735], FCI[1.0]])
    assert trace_points(fig, "Hartree–Fock") == ([0.5, 0.735, 1.0], [HF[0.5], HF[0.735], HF[1.0]])


def test_each_run_appears_as_its_own_point(curve_frame: pd.DataFrame) -> None:
    """0.735 Å-nél két zajos futás van: mindkettő látszik, determinisztikus sorrendben."""
    fig = dissociation_figure(curve_frame, "H2")
    x, y = trace_points(fig, "zajos (nyers)")
    assert x == [0.735, 0.735, 1.0]
    assert y == pytest.approx([FCI[0.735] + 0.030, FCI[0.735] + 0.040, FCI[1.0] + 0.030])
    assert trace_points(fig, "egzakt")[0] == [0.5, 0.735, 1.0]
    assert trace_points(fig, "ZNE Richardson") == ([0.735], [pytest.approx(FCI[0.735] + 0.010)])


def test_switching_molecule_changes_every_trace(curve_frame: pd.DataFrame) -> None:
    """AC-7.5: a másik molekula ábrája kizárólag a saját pontjait tartalmazza."""
    h2 = dissociation_figure(curve_frame, "H2")
    lih = dissociation_figure(curve_frame, "LiH")
    assert trace_points(h2, "Full CI")[0] == [0.5, 0.735, 1.0]
    assert trace_points(lih, "Full CI")[0] == [1.2, 1.6]
    assert {t.name for t in lih.data} == {"Full CI", "Hartree–Fock", "egzakt"}
    lih_x, lih_y = trace_points(lih, "egzakt")
    assert lih_x == [1.2, 1.6, 1.6] and all(e < -7.0 for e in lih_y)
    h2_y = trace_points(h2, "egzakt")[1]
    assert all(e > -1.2 for e in h2_y)  # H₂ energiái nincsenek a LiH ábráján és fordítva
    assert "H2" in h2.layout.title.text and "LiH" in lih.layout.title.text


def test_active_space_filter_keeps_only_that_space(curve_frame: pd.DataFrame) -> None:
    fig = dissociation_figure(curve_frame, "LiH", active_space="(2e,5o)")
    assert trace_points(fig, "egzakt")[0] == [1.6]
    fig3 = dissociation_figure(curve_frame, "LiH", active_space="(2e,3o)")
    assert trace_points(fig3, "egzakt")[0] == [1.2, 1.6]


def test_method_filter_removes_the_other_traces(curve_frame: pd.DataFrame) -> None:
    fig = dissociation_figure(curve_frame, "H2", methods=["zajos (nyers)"])
    assert [t.name for t in fig.data] == ["Full CI", "Hartree–Fock", "zajos (nyers)"]


def test_marker_colors_are_stable_per_method(curve_frame: pd.DataFrame) -> None:
    fig = dissociation_figure(curve_frame, "H2")
    colors = {t.name: t.marker.color for t in fig.data if t.mode == "markers"}
    assert colors == {m: METHOD_COLORS[m] for m in ("egzakt", "zajos (nyers)", "ZNE Richardson")}


def test_hover_carries_run_id_and_error(curve_frame: pd.DataFrame) -> None:
    fig = dissociation_figure(curve_frame, "H2", methods=["ZNE Richardson"])
    (trace,) = [t for t in fig.data if t.name == "ZNE Richardson"]
    run_id, error_mha = trace.customdata[0]
    assert run_id == "h2-zne-0.735" and error_mha == pytest.approx(10.0, abs=1e-6)


def test_missing_hartree_fock_values_omit_that_trace(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    path = tmp_path / "nohf.sqlite"
    with Database(path) as db:
        db.insert_record(record_factory(run_id="a", hartree_fock_ha=-1.0))
    frame = load_results(path).assign(hartree_fock_ha=float("nan"))
    fig = dissociation_figure(frame, "H2")
    assert [t.name for t in fig.data] == ["Full CI", "egzakt"]


@pytest.mark.parametrize(
    ("kwargs", "molecule"),
    [
        ({}, "N2"),  # nincs ilyen molekula
        ({"active_space": "(9e,9o)"}, "LiH"),  # nincs ilyen aktív tér
        ({"methods": []}, "H2"),  # üres módszerlista
        ({"methods": ["QPU (TREX)"]}, "H2"),  # nincs ilyen módszer az adatban
    ],
)
def test_empty_selection_gives_an_explained_empty_figure(
    curve_frame: pd.DataFrame, kwargs: dict[str, Any], molecule: str
) -> None:
    fig = dissociation_figure(curve_frame, molecule, **kwargs)
    assert len(fig.data) == 0
    assert "Nincs megjeleníthető adat" in fig.layout.annotations[0].text


def test_empty_frame_gives_an_empty_figure(tmp_path: Path) -> None:
    path = tmp_path / "empty.sqlite"
    Database(path).close()
    fig = dissociation_figure(load_results(path), "H2")
    assert len(fig.data) == 0


def test_trace_points_reports_the_available_names() -> None:
    import plotly.graph_objects as go

    fig = go.Figure(go.Scatter(x=[1], y=[2], name="a"))
    with pytest.raises(KeyError, match="van: \\['a'\\]"):
        trace_points(fig, "b")


# =====================================================================================
# 7.3 — módszer-összehasonlítás (AC-7.6)
# =====================================================================================


def test_comparison_table_aggregates_per_method_with_known_numbers(
    curve_frame: pd.DataFrame,
) -> None:
    """H₂ 0.735 Å: egzakt (0), két zajos futás (+30, +40 mHa), ZNE (+10 mHa)."""
    table = method_comparison_table(curve_frame, "H2", 0.735)
    assert list(table.columns) == list(COMPARISON_COLUMNS)
    assert table["method"].tolist() == ["egzakt", "zajos (nyers)", "ZNE Richardson"]
    assert table["n"].tolist() == [1, 2, 1]
    assert table["mean_error_mha"].tolist() == pytest.approx([0.0, 35.0, 10.0], abs=1e-6)
    sd = table["sd_mha"].tolist()
    assert sd[1] == pytest.approx(7.0710678, abs=1e-6)  # mintaszórás (ddof = 1)
    assert pd.isna(sd[0]) and pd.isna(sd[2])  # egy futásból nincs szórás
    assert table["sem_mha"].tolist()[1] == pytest.approx(5.0, abs=1e-6)  # 7.0711 / gyök 2
    assert table["chemically_accurate"].tolist() == [True, False, False]


def test_comparison_table_uses_the_chemical_accuracy_threshold_on_the_mean(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    path = tmp_path / "edge.sqlite"
    with Database(path) as db:
        for run_id, backend, err in (
            ("in", "qiskit_aer_shot", CHEMICAL_ACCURACY_MHA - 0.01),
            ("out", "qiskit_aer_noisy", CHEMICAL_ACCURACY_MHA + 0.01),
        ):
            db.insert_record(
                record_factory(
                    run_id=run_id,
                    backend=backend,
                    energy_ha=-1.1373060358 + err * 1e-3,
                    full_ci_ha=-1.1373060358,
                )
            )
    table = method_comparison_table(load_results(path), "H2", 0.735).set_index("method")
    assert bool(table.loc["lövészaj", "chemically_accurate"]) is True
    assert bool(table.loc["zajos (nyers)", "chemically_accurate"]) is False


def test_comparison_table_matches_bond_length_with_float_tolerance(
    curve_frame: pd.DataFrame,
) -> None:
    assert len(method_comparison_table(curve_frame, "H2", 0.7350000000001)) == 3
    assert method_comparison_table(curve_frame, "H2", 0.74).empty


def test_comparison_table_respects_the_active_space(curve_frame: pd.DataFrame) -> None:
    both = method_comparison_table(curve_frame, "LiH", 1.6)
    assert both["n"].tolist() == [2]  # a két aktív tér együtt: 2 egzakt futás
    one = method_comparison_table(curve_frame, "LiH", 1.6, active_space="(2e,5o)")
    assert one["n"].tolist() == [1]


def test_comparison_table_for_missing_data_is_empty_with_all_columns(
    curve_frame: pd.DataFrame,
) -> None:
    table = method_comparison_table(curve_frame, "N2", 0.735)
    assert table.empty and list(table.columns) == list(COMPARISON_COLUMNS)


def test_default_bond_length_prefers_the_point_with_most_methods(
    curve_frame: pd.DataFrame,
) -> None:
    # H₂: 0.735 Å-nél 3 módszer, 1.0 Å-nél 2, 0.5 Å-nél 1
    assert default_bond_length(curve_frame, "H2") == 0.735
    # LiH: minden pontnál 1 módszer: döntetlennél a legkisebb
    assert default_bond_length(curve_frame, "LiH") == 1.2
    assert default_bond_length(curve_frame, "LiH", active_space="(2e,5o)") == 1.6
    assert default_bond_length(curve_frame, "N2") is None


def test_comparison_figure_has_reference_raw_and_mitigated_bars(
    curve_frame: pd.DataFrame,
) -> None:
    """AC-7.6: referencia (0), nyers (+35) és mitigált (+10) sáv a vártakkal."""
    table = method_comparison_table(curve_frame, "H2", 0.735)
    fig = method_comparison_figure(table, "teszt")
    (bar,) = fig.data
    assert list(bar.x) == [REFERENCE_LABEL, "egzakt", "zajos (nyers)", "ZNE Richardson"]
    assert list(bar.y) == pytest.approx([0.0, 0.0, 35.0, 10.0], abs=1e-6)
    assert list(bar.error_y.array) == pytest.approx([0.0, 0.0, 7.0710678, 0.0], abs=1e-6)
    assert list(bar.customdata) == [None, 1, 2, 1]
    assert fig.layout.title.text == "teszt"
    assert bar.marker.color[2] == METHOD_COLORS["zajos (nyers)"]


def test_comparison_figure_marks_the_chemical_accuracy_band(curve_frame: pd.DataFrame) -> None:
    fig = method_comparison_figure(method_comparison_table(curve_frame, "H2", 0.735))
    (band,) = fig.layout.shapes
    assert band.y0 == pytest.approx(-CHEMICAL_ACCURACY_MHA)
    assert band.y1 == pytest.approx(CHEMICAL_ACCURACY_MHA)


def test_comparison_figure_without_data_is_an_explained_empty_figure() -> None:
    empty = pd.DataFrame(columns=list(COMPARISON_COLUMNS))
    fig = method_comparison_figure(empty, "x")
    assert len(fig.data) == 0
    assert "Nincs megjeleníthető adat" in fig.layout.annotations[0].text
