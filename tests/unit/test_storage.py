"""Adattárolási réteg egység- és integrációs tesztjei (AC-4.1 - AC-4.6, ADR-0004).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.config import MitigationSpec, OptimizerSpec, VQEConfig
from vqebd.storage import (
    CURRENT_SCHEMA_VERSION,
    Database,
    export_to_csv,
    export_to_json,
    load_results,
    save_result,
)
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.unit


def test_tc_401_database_init_in_memory() -> None:
    """Az in-memory adatbázis sémainicializálása és metaadatai helyesek."""
    with Database(":memory:") as db:
        cur = db._conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key = 'schema_version'")
        assert int(cur.fetchone()["value"]) == CURRENT_SCHEMA_VERSION
        assert db.count() == 0


def test_tc_401_database_file_init_and_wal(tmp_path: Path) -> None:
    """Fájlalapú adatbázis WAL módban inicializál."""
    db_file = tmp_path / "test.sqlite"
    with Database(db_file) as db:
        cur = db._conn.cursor()
        cur.execute("PRAGMA journal_mode")
        mode = cur.fetchone()[0]
        assert mode.lower() == "wal"


def test_tc_402_insert_and_get_result_roundtrip(tmp_path: Path) -> None:
    """VQEResult beszúrása és visszakeresése bitpontos lebegőpontos értékekkel."""
    db_file = tmp_path / "test.sqlite"
    cfg = VQEConfig(
        molecule=h2(H2_REFERENCE_BOND_LENGTH),
        backend="qiskit_statevector",
        optimizer=OptimizerSpec(method="SLSQP", maxiter=20),
    )
    result = run_vqe(cfg)

    with Database(db_file) as db:
        run_id = db.insert_result(result, run_id="run-h2-test-01")
        assert run_id == "run-h2-test-01"
        assert db.count() == 1

        record = db.get_result("run-h2-test-01")
        assert record is not None
        assert record["molecule_name"] == "H2"
        assert record["bond_length"] == pytest.approx(0.735)
        assert record["energy_ha"] == pytest.approx(result.energy)
        assert record["electronic_energy_ha"] == pytest.approx(result.electronic_energy)
        assert record["nuclear_repulsion_ha"] == pytest.approx(result.nuclear_repulsion_energy)
        assert record["within_chemical_accuracy"] == (1 if result.within_chemical_accuracy else 0)
        assert record["config_hash"] == cfg.fingerprint()
        assert record["backend"] == "qiskit_statevector"


def test_tc_402_insert_result_with_mitigation(tmp_path: Path) -> None:
    """Hibaenyhített VQEResult mentése és a ZNE metaadatok megőrzése."""
    db_file = tmp_path / "test.sqlite"
    cfg = VQEConfig(
        molecule=h2(H2_REFERENCE_BOND_LENGTH),
        backend="qiskit_statevector",
        mitigation=MitigationSpec(
            strategy="zne_local", scale_factors=(1, 3, 5), extrapolator="richardson"
        ),
    )
    result = run_vqe(cfg)

    with Database(db_file) as db:
        run_id = db.insert_result(result)
        record = db.get_result(run_id)
        assert record is not None
        assert record["mitigation_strategy"] == "zne_local"
        assert record["mitigation_extrapolator"] == "richardson"
        assert json.loads(record["scale_factors_json"]) == [1.0, 3.0, 5.0]
        assert len(json.loads(record["scaled_energies_json"])) == 3


def test_tc_403_query_results_filters(tmp_path: Path) -> None:
    """Szűrés molekula, backend, mitigáció és kémiai pontosság szerint."""
    db_file = tmp_path / "test.sqlite"
    cfg_exact = VQEConfig(molecule=h2(0.735), backend="qiskit_statevector")
    res_exact = run_vqe(cfg_exact)

    cfg_noisy = VQEConfig(
        molecule=h2(0.735),
        backend="qiskit_aer_noisy",
        optimizer=OptimizerSpec(method="COBYLA", maxiter=5),
    )
    res_noisy = run_vqe(cfg_noisy)

    save_result(res_exact, db_file)
    save_result(res_noisy, db_file)

    # Szűrés backendre
    exact_list = load_results(db_file, backend="qiskit_statevector")
    assert len(exact_list) == 1
    assert exact_list[0]["backend"] == "qiskit_statevector"

    noisy_list = load_results(db_file, backend="qiskit_aer_noisy")
    assert len(noisy_list) == 1
    assert noisy_list[0]["backend"] == "qiskit_aer_noisy"

    # Szűrés kémiai pontosságra
    chem_acc_list = load_results(db_file, within_chemical_accuracy=True)
    assert len(chem_acc_list) == 1
    assert chem_acc_list[0]["backend"] == "qiskit_statevector"


def test_tc_404_deterministic_csv_and_json_export(tmp_path: Path) -> None:
    """A CSV és JSON export determinisztikus kimenetet ad."""
    db_file = tmp_path / "test.sqlite"
    cfg = VQEConfig(molecule=h2(0.735), backend="qiskit_statevector")
    res = run_vqe(cfg)
    save_result(res, db_file, run_id="run-001")

    records = load_results(db_file)
    csv_file1 = tmp_path / "export1.csv"
    csv_file2 = tmp_path / "export2.csv"
    export_to_csv(records, csv_file1)
    export_to_csv(records, csv_file2)

    assert csv_file1.read_bytes() == csv_file2.read_bytes()
    assert "energy_ha" in csv_file1.read_text(encoding="utf-8")

    json_file = tmp_path / "export.json"
    export_to_json(records, json_file)
    loaded = json.loads(json_file.read_text(encoding="utf-8"))
    assert len(loaded) == 1
    assert loaded[0]["run_id"] == "run-001"


def test_tc_406_duplicate_run_id_raises_integrity_error(tmp_path: Path) -> None:
    """Duplikált run_id beszúrása IntegrityError kivételt vált ki."""
    db_file = tmp_path / "test.sqlite"
    cfg = VQEConfig(molecule=h2(0.735))
    res = run_vqe(cfg)

    with Database(db_file) as db:
        db.insert_result(res, run_id="dup-id")
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_result(res, run_id="dup-id")


def test_tc_406_schema_version_mismatch(tmp_path: Path) -> None:
    """Eltérő sémaverzió esetén az inicializáció hibát jelez."""
    db_file = tmp_path / "test.sqlite"
    with Database(db_file) as db:
        db._conn.execute("UPDATE meta SET value = '999' WHERE key = 'schema_version'")
        db._conn.commit()

    with pytest.raises(ValueError, match="sémaverzió eltérés"):
        Database(db_file)
