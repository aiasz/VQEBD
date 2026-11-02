"""Fázis 7 — a dashboard végponttól végpontig, fej nélkül (``AppTest``).

Minden belső lépés (7.1 … 7.4) saját tesztblokkot kap; a következő lépés az előzőket
változatlanul átengedi (AC-7.8). Az ``AppTest`` a JS-ben renderelt Plotly-t nem futtatja,
ezért az ábrákat adatszinten ellenőrizzük (a trace-ek ``x``/``y``/``z`` értékei).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("streamlit", reason="a dashboard-tesztek a streamlit csomagot igénylik")

from streamlit.testing.v1 import AppTest

from vqebd.dashboard.app import DISPLAY_COLUMNS, discover_sources
from vqebd.storage import Database

pytestmark = pytest.mark.integration

RecordFactory = Callable[..., dict[str, Any]]


def _app() -> None:
    from vqebd.dashboard.app import main

    main()


def _run(monkeypatch: pytest.MonkeyPatch, source: Path | None, root: Path | None = None) -> AppTest:
    """Az app futtatása a megadott forrással (környezeti változón át, mint éles indításnál)."""
    if source is None:
        monkeypatch.delenv("VQEBD_DASHBOARD_SOURCE", raising=False)
    else:
        monkeypatch.setenv("VQEBD_DASHBOARD_SOURCE", str(source))
    if root is not None:
        monkeypatch.setenv("VQEBD_DASHBOARD_ROOT", str(root))
    return AppTest.from_function(_app, default_timeout=60).run()


@pytest.fixture
def fixture_db(tmp_path: Path, record_factory: RecordFactory) -> Path:
    """Három ismert rekord (egzakt, zajos, ZNE) és egy tárolt hiba."""
    path = tmp_path / "dash.sqlite"
    with Database(path) as db:
        db.insert_record(record_factory(run_id="r-exact"))
        db.insert_record(
            record_factory(run_id="r-noisy", backend="qiskit_aer_noisy", energy_ha=-1.0992060358)
        )
        db.insert_record(
            record_factory(
                run_id="r-zne",
                backend="qiskit_aer_noisy",
                mitigation_strategy="zne_local",
                mitigation_extrapolator="richardson",
                energy_ha=-1.1363060358,
            )
        )
        db.record_failure(
            "r-bad",
            batch_id="b1",
            error_type="ValueError",
            error_class="permanent",
            error_message="ValueError: rossz aktív tér",
            wall_time_s=0.1,
            will_retry=False,
        )
    return path


# =====================================================================================
# 7.1 — statikus táblázat (AC-7.3)
# =====================================================================================


def test_app_starts_without_exception(monkeypatch: pytest.MonkeyPatch, fixture_db: Path) -> None:
    at = _run(monkeypatch, fixture_db)
    assert not at.exception
    assert at.title[0].value == "VQEBD — eredmények"


def test_table_shows_exactly_the_fixture_records(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    """AC-7.3: a táblázat pontosan a három fixture-rekordot mutatja, a megadott oszlopokkal."""
    at = _run(monkeypatch, fixture_db)
    table = at.dataframe[0].value
    assert list(table.columns) == list(DISPLAY_COLUMNS)
    assert sorted(table["run_id"]) == ["r-exact", "r-noisy", "r-zne"]
    by_id = table.set_index("run_id")
    assert by_id.loc["r-exact", "method"] == "egzakt"
    assert by_id.loc["r-noisy", "method"] == "zajos (nyers)"
    assert by_id.loc["r-zne", "method"] == "ZNE Richardson"
    assert by_id.loc["r-noisy", "error_mha"] == pytest.approx(38.1, abs=1e-6)
    assert by_id.loc["r-zne", "error_mha"] == pytest.approx(1.0, abs=1e-6)
    assert bool(by_id.loc["r-zne", "chemically_accurate"]) is True
    assert bool(by_id.loc["r-noisy", "chemically_accurate"]) is False


def test_metrics_summarize_the_source(monkeypatch: pytest.MonkeyPatch, fixture_db: Path) -> None:
    at = _run(monkeypatch, fixture_db)
    values = {m.label: m.value for m in at.metric}
    assert values == {"Futások": "3", "Kémiailag pontos": "2", "Hibás próbálkozások": "1"}


def test_failures_tab_shows_the_stored_failure(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    at = _run(monkeypatch, fixture_db)
    failures = at.dataframe[1].value
    assert len(failures) == 1
    assert failures.iloc[0]["run_id"] == "r-bad"
    assert "aktív tér" in failures.iloc[0]["error_message"]
    assert [t.label for t in at.tabs] == ["Eredmények", "Hibák"]


def test_custom_path_in_the_sidebar_overrides_the_discovered_source(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path, tmp_path: Path, record_factory: RecordFactory
) -> None:
    other = tmp_path / "other.sqlite"
    with Database(other) as db:
        db.insert_record(record_factory(run_id="only-one"))
    at = _run(monkeypatch, fixture_db)
    at.sidebar.text_input[0].set_value(str(other)).run()
    assert not at.exception
    assert list(at.dataframe[0].value["run_id"]) == ["only-one"]


def test_json_export_is_shown_and_has_no_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    export = tmp_path / "f5_x.json"
    export.write_text(
        json.dumps(
            {
                "batch_id": "bx",
                "rows": [
                    {
                        "run_id": "e1",
                        "molecule_name": "H2",
                        "bond_length": 0.735,
                        "backend": "qiskit_statevector",
                        "energy_ha": -1.1373,
                        "full_ci_ha": -1.1373,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    at = _run(monkeypatch, export)
    assert not at.exception
    assert list(at.dataframe[0].value["run_id"]) == ["e1"]
    assert at.info and "csak SQLite" in at.info[-1].value


def test_discovery_finds_sqlite_and_known_exports(tmp_path: Path) -> None:
    (tmp_path / "data" / "db").mkdir(parents=True)
    (tmp_path / "docs" / "figures" / "data").mkdir(parents=True)
    wanted = [
        tmp_path / "data" / "db" / "a.sqlite",
        tmp_path / "docs" / "figures" / "data" / "f5_deterministic.json",
        tmp_path / "docs" / "figures" / "data" / "results_v1.json",
    ]
    ignored = [
        tmp_path / "data" / "db" / ".gitkeep",
        tmp_path / "docs" / "figures" / "data" / "hibalanc.json",
    ]
    for path in [*wanted, *ignored]:
        path.write_text("x", encoding="utf-8")
    assert discover_sources(tmp_path) == wanted


# =====================================================================================
# 7.2 — disszociációs görbe molekulaválasztóval (AC-7.5)
# =====================================================================================

CURVE_VIEW = "Disszociációs görbe"


def _chart_traces(at: AppTest) -> dict[str, tuple[list[float], list[float]]]:
    """A kirajzolt Plotly-ábra trace-ei (név → (x, y)), a Streamlit-protóból kiolvasva."""
    charts = at.get("plotly_chart")
    assert len(charts) == 1, f"pontosan egy ábra várt, van: {len(charts)}"
    spec = json.loads(charts[0].proto.spec)
    return {t["name"]: (list(t["x"]), list(t["y"])) for t in spec["data"]}


@pytest.fixture
def curve_db(tmp_path: Path, record_factory: RecordFactory) -> Path:
    """H₂ három geometrián (egzakt + zajos), LiH két aktív térrel."""
    path = tmp_path / "curve.sqlite"
    full_ci = {0.5: -1.0552, 0.735: -1.1373, 1.0: -1.1012}
    with Database(path) as db:
        for r, fci in full_ci.items():
            db.insert_record(
                record_factory(run_id=f"h2-e-{r}", bond_length=r, energy_ha=fci, full_ci_ha=fci)
            )
            db.insert_record(
                record_factory(
                    run_id=f"h2-n-{r}",
                    bond_length=r,
                    backend="qiskit_aer_noisy",
                    energy_ha=fci + 0.03,
                    full_ci_ha=fci,
                )
            )
        for run_id, r, orbitals in (("lih-a", 1.2, 3), ("lih-b", 1.6, 3), ("lih-c", 1.6, 5)):
            db.insert_record(
                record_factory(
                    run_id=run_id,
                    molecule_name="LiH",
                    bond_length=r,
                    active_electrons=2,
                    active_orbitals=orbitals,
                    energy_ha=-7.80 - r / 100,
                    full_ci_ha=-7.90 - r / 100,
                )
            )
    return path


def test_default_view_is_still_the_table(monkeypatch: pytest.MonkeyPatch, curve_db: Path) -> None:
    """AC-7.8: a 7.2 lépés után az alapnézet a 7.1 táblázata."""
    at = _run(monkeypatch, curve_db)
    assert at.sidebar.radio(key="view").value == "Táblázat"
    assert len(at.dataframe) >= 1 and not at.get("plotly_chart")


def test_curve_view_renders_the_first_molecule(
    monkeypatch: pytest.MonkeyPatch, curve_db: Path
) -> None:
    at = _run(monkeypatch, curve_db)
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    assert not at.exception
    assert at.selectbox(key="molecule").options == ["H2", "LiH"]
    traces = _chart_traces(at)
    assert list(traces) == ["Full CI", "Hartree–Fock", "egzakt", "zajos (nyers)"]
    assert traces["Full CI"][0] == [0.5, 0.735, 1.0]


def test_switching_molecule_updates_the_chart(
    monkeypatch: pytest.MonkeyPatch, curve_db: Path
) -> None:
    """AC-7.5: molekulát váltva az ábra pontjai a másik molekuláéra változnak."""
    at = _run(monkeypatch, curve_db)
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    h2 = _chart_traces(at)

    at.selectbox(key="molecule").select("LiH").run()
    assert not at.exception
    lih = _chart_traces(at)

    assert h2["Full CI"][0] == [0.5, 0.735, 1.0]
    assert lih["Full CI"][0] == [1.2, 1.6]
    assert "zajos (nyers)" in h2 and "zajos (nyers)" not in lih
    assert lih["egzakt"][0] == [1.2, 1.6, 1.6]
    assert all(e < -7.0 for e in lih["egzakt"][1])
    assert "LiH" in at.get("plotly_chart")[0].proto.spec  # a cím is frissült


def test_active_space_selector_filters_the_chart(
    monkeypatch: pytest.MonkeyPatch, curve_db: Path
) -> None:
    at = _run(monkeypatch, curve_db)
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    at.selectbox(key="molecule").select("LiH").run()
    assert at.selectbox(key="space").options == ["összes", "(2e,3o)", "(2e,5o)"]
    at.selectbox(key="space").select("(2e,5o)").run()
    assert not at.exception
    assert _chart_traces(at)["egzakt"][0] == [1.6]
    assert "1 futás" in at.caption[-1].value


def test_method_multiselect_removes_a_trace_and_resets_on_molecule_change(
    monkeypatch: pytest.MonkeyPatch, curve_db: Path
) -> None:
    at = _run(monkeypatch, curve_db)
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    selector = at.multiselect(key="methods-H2-összes")
    assert selector.value == ["egzakt", "zajos (nyers)"]
    selector.unselect("zajos (nyers)").run()
    assert "zajos (nyers)" not in _chart_traces(at)

    # Molekulaváltás: az új molekula módszerlistája alapértelmezésben teljes.
    at.selectbox(key="molecule").select("LiH").run()
    assert at.multiselect(key="methods-LiH-összes").value == ["egzakt"]
    # Visszaváltva a választás NEM marad meg (a Streamlit a nem kirajzolt widget állapotát
    # eldobja): a H₂ módszerlistája újra alapértelmezett, azaz teljes.
    at.selectbox(key="molecule").select("H2").run()
    assert at.multiselect(key="methods-H2-összes").value == ["egzakt", "zajos (nyers)"]
    assert "zajos (nyers)" in _chart_traces(at)


def test_curve_view_with_real_batch_data_switches_molecules(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """Valódi adat: a verziózott batch-export három molekulája között váltva az ábra változik."""
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_deterministic.json")
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    assert not at.exception
    assert at.selectbox(key="molecule").options == ["BeH2", "H2", "LiH"]
    seen: dict[str, list[float]] = {}
    for molecule in ("BeH2", "H2", "LiH"):
        at.selectbox(key="molecule").select(molecule).run()
        assert not at.exception
        seen[molecule] = _chart_traces(at)["Full CI"][0]
    assert seen["H2"] == [0.5, 0.735, 1.0, 1.5, 2.0, 2.5]
    assert seen["LiH"] == [1.2, 1.595, 2.2, 3.0]
    assert seen["BeH2"] == [1.0, 1.33, 1.8]


def test_curve_view_with_no_molecules_shows_an_info_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "ures.sqlite"
    Database(empty).close()
    at = _run(monkeypatch, empty)
    at.sidebar.radio(key="view").set_value(CURVE_VIEW).run()
    assert not at.exception
    assert any("nem tartalmaz molekulát" in i.value for i in at.info)


# =====================================================================================
# 7.3 — módszer-összehasonlítás (AC-7.6)
# =====================================================================================

COMPARE_VIEW = "Módszer-összehasonlítás"


def _chart_bars(at: AppTest) -> tuple[list[str], list[float], dict[str, Any]]:
    """A sávdiagram (x, y) értékei és a teljes spec a Streamlit-protóból."""
    charts = at.get("plotly_chart")
    assert len(charts) == 1, f"pontosan egy ábra várt, van: {len(charts)}"
    spec = json.loads(charts[0].proto.spec)
    (bar,) = spec["data"]
    return list(bar["x"]), list(bar["y"]), spec


def test_comparison_view_shows_reference_raw_and_mitigated_bars(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    """AC-7.6: a három sáv (referencia, nyers, mitigált) értéke egy ismert rekordra helyes."""
    at = _run(monkeypatch, fixture_db)
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    assert not at.exception
    x, y, spec = _chart_bars(at)
    assert x == ["referencia (Full CI)", "egzakt", "zajos (nyers)", "ZNE Richardson"]
    assert y == pytest.approx([0.0, 0.0, 38.1, 1.0], abs=1e-6)
    # a kémiai pontosság sávja ±1.5936 mHa
    (band,) = spec["layout"]["shapes"]
    assert band["y0"] == pytest.approx(-1.5936) and band["y1"] == pytest.approx(1.5936)


def test_comparison_view_also_lists_the_numbers_in_a_table(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    at = _run(monkeypatch, fixture_db)
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    table = at.dataframe[-1].value
    assert table["method"].tolist() == ["egzakt", "zajos (nyers)", "ZNE Richardson"]
    assert table["n"].tolist() == [1, 1, 1]
    assert table["mean_error_mha"].tolist() == pytest.approx([0.0, 38.1, 1.0], abs=1e-6)


def test_comparison_changes_with_the_bond_length_selector(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record_factory: RecordFactory
) -> None:
    path = tmp_path / "bonds.sqlite"
    with Database(path) as db:
        for r, err in ((0.5, 0.030), (1.0, 0.010)):
            db.insert_record(
                record_factory(run_id=f"e-{r}", bond_length=r, energy_ha=-1.1, full_ci_ha=-1.1)
            )
            db.insert_record(
                record_factory(
                    run_id=f"n-{r}",
                    bond_length=r,
                    backend="qiskit_aer_noisy",
                    energy_ha=-1.1 + err,
                    full_ci_ha=-1.1,
                )
            )
    at = _run(monkeypatch, path)
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    assert at.selectbox(key="cmp-bond-H2-összes").options == ["0.5", "1.0"]
    assert _chart_bars(at)[1] == pytest.approx([0.0, 0.0, 30.0], abs=1e-6)  # 0.5 Å (az első)
    at.selectbox(key="cmp-bond-H2-összes").select(1.0).run()
    assert not at.exception
    assert _chart_bars(at)[1] == pytest.approx([0.0, 0.0, 10.0], abs=1e-6)


def test_comparison_defaults_to_the_bond_length_with_most_methods(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record_factory: RecordFactory
) -> None:
    path = tmp_path / "many.sqlite"
    with Database(path) as db:
        db.insert_record(record_factory(run_id="a", bond_length=0.5, energy_ha=-1.0))
        db.insert_record(record_factory(run_id="b", bond_length=1.0, energy_ha=-1.1))
        db.insert_record(
            record_factory(run_id="c", bond_length=1.0, backend="qiskit_aer_shot", energy_ha=-1.0)
        )
    at = _run(monkeypatch, path)
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    assert at.selectbox(key="cmp-bond-H2-összes").value == 1.0  # 2 módszer vs 1


def test_comparison_matches_the_published_tr_f05_statistics(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """Keresztvalidáció: a dashboard átlaghibái egyeznek a TR-F05 4. pontjának táblázatával.

    H₂ 0.735 Å, N = 20 seed: lövészaj +11.59, zajos +38.15, ZNE lineáris +15.52, ZNE Richardson
    +11.54 mHa (átlag a Full CI-hez).
    """
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_statistical.json")
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    assert not at.exception
    assert at.selectbox(key="cmp-molecule").value == "H2"
    assert at.selectbox(key="cmp-bond-H2-összes").value == 0.735
    x, y, _ = _chart_bars(at)
    got = dict(zip(x, y, strict=True))
    assert got["lövészaj"] == pytest.approx(11.59, abs=0.01)
    assert got["zajos (nyers)"] == pytest.approx(38.15, abs=0.01)
    assert got["ZNE lineáris"] == pytest.approx(15.52, abs=0.01)
    assert got["ZNE Richardson"] == pytest.approx(11.54, abs=0.01)
    table = at.dataframe[-1].value.set_index("method")
    assert (table["n"] == 20).all()


def test_comparison_lih_depth_wall_from_the_published_statistics(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """LiH (2e,3o) zajosan +465.65 mHa: az UCCSD mélységi fala (TR-F05 4. pont)."""
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_statistical.json")
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    at.selectbox(key="cmp-molecule").select("LiH").run()
    assert not at.exception
    x, y, _ = _chart_bars(at)
    got = dict(zip(x, y, strict=True))
    assert got["zajos (nyers)"] == pytest.approx(465.65, abs=0.01)
    assert got["lövészaj"] == pytest.approx(28.04, abs=0.01)


def test_comparison_view_with_no_molecules_shows_an_info_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "ures.sqlite"
    Database(empty).close()
    at = _run(monkeypatch, empty)
    at.sidebar.radio(key="view").set_value(COMPARE_VIEW).run()
    assert not at.exception
    assert any("nem tartalmaz molekulát" in i.value for i in at.info)


# =====================================================================================
# 7.4 — körméret × módszer hőtérkép (AC-7.7)
# =====================================================================================

HEAT_VIEW = "Hőtérkép"


def _heat(at: AppTest) -> tuple[list[str], list[str], list[list[float | None]]]:
    """A hőtérkép (x, y, z) értékei a Streamlit-protóból."""
    charts = at.get("plotly_chart")
    assert len(charts) == 1, f"pontosan egy ábra várt, van: {len(charts)}"
    (heat,) = json.loads(charts[0].proto.spec)["data"]
    return list(heat["x"]), list(heat["y"]), [list(row) for row in heat["z"]]


def test_heatmap_view_colors_a_known_fixture(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    """AC-7.7: egy molekula (H₂, 2 qubit) ismert rekordjaira a cellaértékek helyesek."""
    at = _run(monkeypatch, fixture_db)
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert not at.exception
    x, y, z = _heat(at)
    assert x == ["2"]
    assert y == ["egzakt", "zajos (nyers)", "ZNE Richardson"]
    # egzakt: hiba 0 -> pontos; zajos +38.1 mHa -> nem; ZNE +1.0 mHa -> pontos (az egyetlen futás)
    assert z == [[1.0], [0.0], [1.0]]


def test_heatmap_metric_radio_switches_to_the_median_error(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    at = _run(monkeypatch, fixture_db)
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert at.radio(key="heat-metric").value == "success_rate"
    at.radio(key="heat-metric").set_value("median_abs_error_mha").run()
    assert not at.exception
    z = _heat(at)[2]
    assert z[0][0] == pytest.approx(0.0, abs=1e-6)
    assert z[1][0] == pytest.approx(38.1, abs=1e-6)
    assert z[2][0] == pytest.approx(1.0, abs=1e-6)


def test_heatmap_molecule_filter_changes_the_columns(
    monkeypatch: pytest.MonkeyPatch, curve_db: Path
) -> None:
    at = _run(monkeypatch, curve_db)
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert _heat(at)[0] == ["2", "4", "8"]  # H₂, LiH (2e,3o), LiH (2e,5o)
    at.multiselect(key="heat-molecules").unselect("LiH").run()
    assert not at.exception
    assert _heat(at)[0] == ["2"]


def test_heatmap_with_the_real_deterministic_batch(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """Valódi adat, kereszt-validáció a TR-F05 / fig09 számaival.

    Az egzakt futások Full CI-hez mért hibája a **csonkolás**: a minimális (2e,3o) terek
    (4 qubit) 15–72 mHa-t veszítenek, így 0%-ban pontosak; a frozen-core terek (8 és 10 qubit)
    0.23–0.71 mHa-val kémiai pontosságon belül vannak (100%); H₂ (2 qubit) teljes tér, 100%.
    """
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_deterministic.json")
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert not at.exception
    x, y, z = _heat(at)
    assert x == ["2", "4", "8", "10"] and y == ["egzakt"]
    assert z == [[1.0, 0.0, 1.0, 1.0]]


def test_heatmap_with_the_real_statistical_batch_shows_the_noise_floor(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    """Zajos szimulációban sehol nincs 50% feletti sikeresség; a LiH-fal (4 qubit) látszik."""
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_statistical.json")
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert not at.exception
    x, y, z = _heat(at)
    assert x == ["2", "4"]
    assert "zajos (nyers)" in y
    noisy = z[y.index("zajos (nyers)")]
    assert noisy[0] == 0.0 and noisy[1] == 0.0  # sem H₂ (2), sem LiH (4) zajos futás nem pontos
    assert all(v is None or v <= 0.5 for row in z for v in row)
    at.radio(key="heat-metric").set_value("median_abs_error_mha").run()
    row = _heat(at)[2][y.index("zajos (nyers)")]
    h2_error, lih_error = row
    assert h2_error is not None and lih_error is not None
    # LiH 4 qubiten a zajos medián hiba nagyságrenddel nagyobb, mint H₂-n (466 vs ~38 mHa)
    assert lih_error > 10 * h2_error


def test_heatmap_with_no_molecules_shows_an_info_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "ures.sqlite"
    Database(empty).close()
    at = _run(monkeypatch, empty)
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert not at.exception
    assert any("nem tartalmaz molekulát" in i.value for i in at.info)


def test_heatmap_notes_assumed_sizes_for_exports_without_a_mapper(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / "f5_deterministic.json")
    at.sidebar.radio(key="view").set_value(HEAT_VIEW).run()
    assert any("alapértelmezése" in c.value for c in at.caption)


# --- hiányzó, üres és sérült adat (AC-7.10) -----------------------------------------------


def test_missing_source_shows_a_friendly_error_not_a_traceback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    at = _run(monkeypatch, tmp_path / "nincs.sqlite")
    assert not at.exception
    assert at.error and "nem található" in at.error[0].value


def test_malformed_json_shows_a_friendly_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad = tmp_path / "rossz.json"
    bad.write_text("nem json", encoding="utf-8")
    at = _run(monkeypatch, bad)
    assert not at.exception
    assert at.error and "hibás" in at.error[0].value


def test_empty_database_shows_an_info_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "ures.sqlite"
    Database(empty).close()
    at = _run(monkeypatch, empty)
    assert not at.exception
    assert any("nem tartalmaz eredményt" in i.value for i in at.info)
    assert {m.label: m.value for m in at.metric}["Futások"] == "0"


def test_no_sources_at_all_shows_guidance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    at = _run(monkeypatch, None, root=tmp_path)
    assert not at.exception
    assert at.info and "Nincs megnyitható adatforrás" in at.info[0].value


# --- csak olvasás (AC-7.9) ----------------------------------------------------------------


def test_running_the_app_leaves_the_database_bitwise_unchanged(
    monkeypatch: pytest.MonkeyPatch, fixture_db: Path
) -> None:
    import hashlib

    before = hashlib.sha256(fixture_db.read_bytes()).hexdigest()
    at = _run(monkeypatch, fixture_db)
    assert not at.exception
    assert hashlib.sha256(fixture_db.read_bytes()).hexdigest() == before


# --- valódi adat (AC-7.11) ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "rows"),
    [("f5_deterministic.json", 50), ("f5_statistical.json", 180), ("results_v1.json", 8)],
)
def test_the_versioned_exports_load_with_the_expected_row_count(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path, name: str, rows: int
) -> None:
    """AC-7.11: a verziózott exportok kivétel nélkül betöltődnek, a sorszám egyezik."""
    at = _run(monkeypatch, repo_root / "docs" / "figures" / "data" / name)
    assert not at.exception
    assert {m.label: m.value for m in at.metric}["Futások"] == str(rows)
    assert len(at.dataframe[0].value) == rows
