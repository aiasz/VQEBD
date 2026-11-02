"""Fázis 7 — a dashboard végponttól végpontig, fej nélkül (``AppTest``).

Minden belső lépés (7.1 … 7.4) saját tesztblokkot kap; a következő lépés az előzőket
változatlanul átengedi (AC-7.8). Az ``AppTest`` a JS-ben renderelt Plotly-t nem futtatja,
ezért az ábrákat adatszinten ellenőrizzük (a trace-ek ``x``/``y``/``z`` értékei).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
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
