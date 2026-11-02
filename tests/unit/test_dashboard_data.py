"""Fázis 7 — a dashboard adatrétege (AC-7.4, AC-7.7 qubitszám, AC-7.9, AC-7.10, AC-7.11).

Tiszta pandas-tesztek: Streamlit nélkül futnak.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from vqebd.dashboard.data import (
    CHEMICAL_ACCURACY_MHA,
    FAILURE_COLUMNS,
    METHOD_ORDER,
    DataLoadError,
    derive_n_qubits,
    load_failures,
    load_results,
    method_label,
)
from vqebd.storage import Database

pytestmark = pytest.mark.unit

RecordFactory = Callable[..., dict[str, Any]]


def _make_db(path: Path, records: list[dict[str, Any]]) -> Path:
    with Database(path) as db:
        for record in records:
            db.insert_record(record)
    return path


# --- konstans és címkék ----------------------------------------------------------------


def test_chemical_accuracy_matches_the_canonical_constant() -> None:
    """A dashboard saját konstansa egyezik a kémiai modul értékével (mHa-ban)."""
    from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA

    assert pytest.approx(CHEMICAL_ACCURACY_HA * 1e3) == CHEMICAL_ACCURACY_MHA


@pytest.mark.parametrize(
    ("backend", "strategy", "extrapolator", "expected"),
    [
        ("qiskit_statevector", "none", None, "egzakt"),
        ("cirq_simulator", "none", None, "egzakt"),
        ("qsim", "none", None, "egzakt"),
        ("qiskit_aer_shot", "none", None, "lövészaj"),
        ("qiskit_aer_noisy", "none", None, "zajos (nyers)"),
        ("qiskit_aer_noisy", "zne_local", "linear", "ZNE lineáris"),
        ("qiskit_aer_noisy", "zne_local", "richardson", "ZNE Richardson"),
        ("qiskit_aer_noisy", "zne_mitiq", "exponential", "ZNE exponenciális"),
        ("ibm_qpu", "none", None, "QPU (nyers)"),
        ("ibm_qpu", "ibm_resilience_0", None, "QPU (nyers)"),
        ("ibm_qpu", "ibm_resilience_1", None, "QPU (TREX)"),
        ("ibm_qpu", "ibm_resilience_2", None, "QPU (resilience 2)"),
        ("valami_uj", "none", None, "valami_uj"),
        (None, None, None, "ismeretlen"),
    ],
)
def test_method_label(
    backend: str | None, strategy: str | None, extrapolator: str | None, expected: str
) -> None:
    assert method_label(backend, strategy, extrapolator) == expected


def test_every_known_label_is_in_the_display_order() -> None:
    labels = {
        method_label(b, s, e)
        for b, s, e in [
            ("qiskit_statevector", "none", None),
            ("qiskit_aer_shot", "none", None),
            ("qiskit_aer_noisy", "none", None),
            ("qiskit_aer_noisy", "zne_local", "linear"),
            ("qiskit_aer_noisy", "zne_local", "richardson"),
            ("qiskit_aer_noisy", "zne_local", "exponential"),
            ("ibm_qpu", "none", None),
            ("ibm_qpu", "ibm_resilience_1", None),
            ("ibm_qpu", "ibm_resilience_2", None),
        ]
    }
    assert labels <= set(METHOD_ORDER)


# --- qubitszám (AC-7.7, M8) --------------------------------------------------------------


@pytest.mark.parametrize(
    ("molecule", "orbitals", "expected"),
    [
        ("H2", float("nan"), 2),  # teljes tér, STO-3G
        ("LiH", 3.0, 4),  # (2e,3o)
        ("LiH", 5.0, 8),  # (2e,5o) frozen core
        ("BeH2", 3.0, 4),  # (2e,3o)
        ("BeH2", 6.0, 10),  # (4e,6o) frozen core
    ],
)
def test_qubit_count_matches_the_five_measured_systems(
    molecule: str, orbitals: float, expected: int
) -> None:
    """Mért építés (phase_07.md M8): parity + kétqubites redukció."""
    assert derive_n_qubits(molecule, "sto3g", orbitals, "parity", True) == expected


def test_qubit_count_without_reduction_or_with_other_mapper() -> None:
    assert derive_n_qubits("LiH", "sto3g", 5.0, "parity", False) == 10
    assert derive_n_qubits("LiH", "sto3g", 5.0, "jordan_wigner", True) == 10
    assert (
        derive_n_qubits("LiH", "sto3g", 5.0, None, None) == 8
    )  # alapértelmezés: parity + redukció


@pytest.mark.parametrize(("molecule", "basis"), [("H2", "6-31g"), ("N2", "sto3g"), (None, None)])
def test_unknown_basis_gives_nan_instead_of_guessing(
    molecule: str | None, basis: str | None
) -> None:
    assert math.isnan(derive_n_qubits(molecule, basis, float("nan"), "parity", True))


# --- betöltés SQLite-ból -----------------------------------------------------------------


def test_sqlite_results_are_normalized_with_derived_columns(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    exact = record_factory(run_id="exact")
    noisy = record_factory(
        run_id="noisy",
        backend="qiskit_aer_noisy",
        platform="qiskit",
        energy_ha=-1.1373060358 + 0.0381,  # +38.1 mHa
    )
    zne = record_factory(
        run_id="zne",
        backend="qiskit_aer_noisy",
        mitigation_strategy="zne_local",
        mitigation_extrapolator="richardson",
        energy_ha=-1.1373060358 + 0.0010,  # +1.0 mHa: kémiailag pontos
    )
    frame = load_results(_make_db(tmp_path / "t.sqlite", [exact, noisy, zne])).set_index("run_id")

    assert len(frame) == 3
    assert frame.loc["exact", "error_mha"] == pytest.approx(0.0, abs=1e-9)
    assert frame.loc["noisy", "error_mha"] == pytest.approx(38.1, abs=1e-6)
    assert frame.loc["zne", "error_mha"] == pytest.approx(1.0, abs=1e-6)
    assert list(frame["chemically_accurate"][["exact", "noisy", "zne"]]) == [True, False, True]
    assert frame.loc["noisy", "method"] == "zajos (nyers)"
    assert frame.loc["zne", "method"] == "ZNE Richardson"
    assert (frame["n_qubits"] == 2).all() and not frame["size_assumed"].any()
    assert (frame["active_space"] == "teljes").all()
    assert (frame["source"] == "t.sqlite").all()


def test_active_space_label_and_casci_error(tmp_path: Path, record_factory: RecordFactory) -> None:
    lih = record_factory(
        run_id="lih",
        molecule_name="LiH",
        active_electrons=2,
        active_orbitals=5,
        energy_ha=-7.8821745058,
        full_ci_ha=-7.8823,
        casci_ha=-7.8821745058,
    )
    row = load_results(_make_db(tmp_path / "t.sqlite", [lih])).iloc[0]
    assert row["active_space"] == "(2e,5o)" and row["n_qubits"] == 8
    assert row["casci_error_mha"] == pytest.approx(0.0, abs=1e-9)
    assert row["error_mha"] == pytest.approx(0.1254942, abs=1e-6)


def test_empty_database_is_not_an_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.sqlite"
    Database(path).close()
    frame = load_results(path)
    assert frame.empty
    for column in ("error_mha", "method", "n_qubits", "chemically_accurate", "active_space"):
        assert column in frame.columns


# --- betöltés JSON-ból és keresztvalidáció (AC-7.4) ----------------------------------------


def test_three_sources_give_identical_derived_columns(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    """AC-7.4: ugyanaz a rekord SQLite-ból, teljes listából és batch-exportból ugyanazt adja."""
    records = [
        record_factory(run_id="a"),
        record_factory(
            run_id="b",
            backend="qiskit_aer_noisy",
            mitigation_strategy="zne_local",
            mitigation_extrapolator="linear",
            energy_ha=-1.1220,
        ),
    ]
    sqlite = load_results(_make_db(tmp_path / "t.sqlite", records))
    full_list = tmp_path / "list.json"
    full_list.write_text(json.dumps(records), encoding="utf-8")
    export_keys = (
        "run_id",
        "molecule_name",
        "bond_length",
        "backend",
        "platform",
        "mitigation_strategy",
        "mitigation_extrapolator",
        "energy_ha",
        "full_ci_ha",
        "repeat_index",
    )
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps(
            {
                "batch_id": "bx",
                "rows": [{k: r.get(k) for k in export_keys} for r in records],
            }
        ),
        encoding="utf-8",
    )
    frames = {
        "sqlite": sqlite.sort_values("run_id").reset_index(drop=True),
        "lista": load_results(full_list).sort_values("run_id").reset_index(drop=True),
        "export": load_results(export).sort_values("run_id").reset_index(drop=True),
    }
    compared = ["run_id", "error_mha", "chemically_accurate", "method", "n_qubits", "active_space"]
    reference = frames["sqlite"][compared]
    for name in ("lista", "export"):
        pd.testing.assert_frame_equal(frames[name][compared], reference, check_dtype=False)
    # Az export nem hordozza a mapper/basis mezőt: a feltevést a size_assumed jelzi.
    assert not frames["sqlite"]["size_assumed"].any()
    assert not frames["lista"]["size_assumed"].any()
    assert frames["export"]["size_assumed"].all()
    assert (frames["export"]["batch_id"] == "bx").all()


def test_batch_export_keeps_row_level_batch_id(tmp_path: Path) -> None:
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps(
            {
                "batch_id": "outer",
                "rows": [
                    {"run_id": "x", "batch_id": "inner", "energy_ha": -1.0, "full_ci_ha": -1.1}
                ],
            }
        ),
        encoding="utf-8",
    )
    assert load_results(export)["batch_id"].iloc[0] == "inner"


# --- hibás és hiányzó adat (AC-7.10) ---------------------------------------------------------


def test_missing_file_gives_a_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(DataLoadError, match="nem található"):
        load_results(tmp_path / "nincs.sqlite")
    with pytest.raises(DataLoadError, match="nem található"):
        load_failures(tmp_path / "nincs.sqlite")


def test_unknown_suffix_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "adat.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DataLoadError, match="Ismeretlen adatforrás-típus"):
        load_results(path)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("nem json", "hibás"),
        ('{"valami": 1}', "Ismeretlen JSON-szerkezet"),
        ('"csak szöveg"', "Ismeretlen JSON-szerkezet"),
        ('{"rows": "nem lista"}', "Ismeretlen JSON-szerkezet"),
        ("[1, 2, 3]", "nem szótárak"),
    ],
)
def test_malformed_json_gives_a_friendly_error(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "rossz.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError, match=message):
        load_results(path)


def test_non_database_file_with_sqlite_suffix_is_a_friendly_error(tmp_path: Path) -> None:
    path = tmp_path / "hamis.sqlite"
    path.write_text("ez nem sqlite", encoding="utf-8")
    with pytest.raises(DataLoadError, match="nem olvasható"):
        load_results(path)


def test_empty_json_list_is_an_empty_table_not_an_error(tmp_path: Path) -> None:
    path = tmp_path / "ures.json"
    path.write_text("[]", encoding="utf-8")
    frame = load_results(path)
    assert frame.empty and "error_mha" in frame.columns


# --- hibatábla -------------------------------------------------------------------------------


def test_failures_are_loaded_from_sqlite(tmp_path: Path, record_factory: RecordFactory) -> None:
    path = _make_db(tmp_path / "t.sqlite", [record_factory(run_id="ok")])
    with Database(path) as db:
        db.record_failure(
            "bad",
            batch_id="b1",
            error_type="ValueError",
            error_class="permanent",
            error_message="ValueError: rossz",
            wall_time_s=0.2,
            will_retry=False,
        )
    failures = load_failures(path)
    assert list(failures.columns) == list(FAILURE_COLUMNS)
    assert len(failures) == 1 and failures.iloc[0]["error_class"] == "permanent"


def test_failures_are_empty_for_json_sources(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text("[]", encoding="utf-8")
    frame = load_failures(path)
    assert frame.empty and list(frame.columns) == list(FAILURE_COLUMNS)


def test_failures_table_missing_in_an_old_database_is_not_an_error(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    """Egy v1/v2 adatbázisban nincs ``run_failures``: ez üres hibatörténet, nem hiba."""
    import sqlite3

    path = _make_db(tmp_path / "old.sqlite", [record_factory()])
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE run_failures")
    conn.commit()
    conn.close()
    assert load_failures(path).empty


# --- csak olvasás (AC-7.9) -----------------------------------------------------------------


def test_loading_never_modifies_the_database(tmp_path: Path, record_factory: RecordFactory) -> None:
    """AC-7.9: a betöltés után az adatbázisfájl bitre változatlan."""
    path = _make_db(tmp_path / "t.sqlite", [record_factory(), record_factory()])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    load_results(path)
    load_failures(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_read_only_database_rejects_writes_through_the_loader_path(
    tmp_path: Path, record_factory: RecordFactory
) -> None:
    """A betöltő által használt nyitási mód valóban csak olvasható."""
    import sqlite3

    path = _make_db(tmp_path / "t.sqlite", [record_factory()])
    with Database(path, read_only=True) as db, pytest.raises(sqlite3.OperationalError):
        db.record_failure(
            "x",
            batch_id=None,
            error_type="E",
            error_class="permanent",
            error_message="m",
            wall_time_s=None,
            will_retry=False,
        )
