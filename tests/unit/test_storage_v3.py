"""Fázis 6 — séma v3: ``run_failures`` tábla és v2 → v3 migráció (AC-6.1, AC-6.9).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from vqebd.chemistry.molecule import h2
from vqebd.config import OptimizerSpec, VQEConfig
from vqebd.storage import CURRENT_SCHEMA_VERSION, Database
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.unit


def _record(db: Database, run_id: str = "r1", **overrides: object) -> int:
    kwargs: dict[str, object] = {
        "batch_id": "b1",
        "error_type": "ValueError",
        "error_class": "permanent",
        "error_message": "ValueError: rossz",
        "wall_time_s": 0.5,
        "will_retry": False,
    }
    kwargs.update(overrides)
    return db.record_failure(run_id, **kwargs)  # type: ignore[arg-type]


def test_current_schema_version_is_3() -> None:
    assert CURRENT_SCHEMA_VERSION == 3


def test_attempts_are_numbered_per_run_from_one() -> None:
    with Database(":memory:") as db:
        assert [_record(db, "a"), _record(db, "a"), _record(db, "b"), _record(db, "a")] == [
            1,
            2,
            1,
            3,
        ]


def test_failure_rows_carry_all_fields() -> None:
    with Database(":memory:") as db:
        _record(db, will_retry=True, error_class="transient", error_type="ConnectionError")
        (row,) = db.failure_history("r1")
        assert row["run_id"] == "r1" and row["batch_id"] == "b1" and row["attempt"] == 1
        assert row["error_type"] == "ConnectionError" and row["error_class"] == "transient"
        assert row["will_retry"] == 1 and row["forgiven"] == 0 and row["wall_time_s"] == 0.5
        assert row["timestamp"].endswith("Z")


def test_invalid_error_class_is_rejected_by_the_schema() -> None:
    with Database(":memory:") as db, pytest.raises(sqlite3.IntegrityError):
        _record(db, error_class="ismeretlen")


def test_long_messages_are_truncated() -> None:
    with Database(":memory:") as db:
        _record(db, error_message="x" * 5000)
        assert len(db.failure_history("r1")[0]["error_message"]) == 2000


def test_failures_can_be_filtered_by_batch() -> None:
    with Database(":memory:") as db:
        _record(db, "a", batch_id="b1")
        _record(db, "b", batch_id="b2")
        assert [f["run_id"] for f in db.failures("b1")] == ["a"]
        assert [f["run_id"] for f in db.failures()] == ["a", "b"]


def test_forgive_requires_exactly_one_selector() -> None:
    with Database(":memory:") as db:
        with pytest.raises(ValueError, match="pontosan"):
            db.forgive_failures()
        with pytest.raises(ValueError, match="pontosan"):
            db.forgive_failures(batch_id="b1", run_id="r1")


def test_forgive_by_run_counts_only_active_rows() -> None:
    with Database(":memory:") as db:
        _record(db, "a")
        _record(db, "a")
        _record(db, "b")
        assert db.forgive_failures(run_id="a") == 2
        assert db.forgive_failures(run_id="a") == 0  # már megbocsátott
        assert db.effective_attempts("b") == 1


def test_read_only_database_can_query_failures(tmp_path: Path) -> None:
    path = tmp_path / "ro.sqlite"
    with Database(path) as db:
        _record(db)
    with Database(path, read_only=True) as ro:
        assert len(ro.failure_history("r1")) == 1


# --- migráció (AC-6.9) ---------------------------------------------------------------


def _downgrade_to_v2(path: Path) -> None:
    """Egy v3 adatbázis visszaállítása v2 állapotra (a v3 tábla nélkül)."""
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE run_failures")
    conn.execute("UPDATE meta SET value = '2' WHERE key = 'schema_version'")
    conn.commit()
    conn.close()


def _columns(path: Path, table: str) -> list[tuple[str, str]]:
    with Database(path) as db:
        return [(r["name"], r["type"]) for r in db._conn.execute(f"PRAGMA table_info({table})")]


def test_v2_database_migrates_to_v3_and_keeps_records_bitwise(tmp_path: Path) -> None:
    """AC-6.9: a v2 rekord bitre változatlan; a második megnyitás nem migrál újra."""
    path = tmp_path / "v2.sqlite"
    config = VQEConfig(molecule=h2(), optimizer=OptimizerSpec(method="SLSQP", maxiter=50))
    with Database(path) as db:
        db.insert_result(run_vqe(config), run_id="v2-rekord", batch_id="b", repeat_index=0)
        before = db.get_result("v2-rekord")
    _downgrade_to_v2(path)

    with Database(path) as db:
        meta = dict(db._conn.execute("SELECT key, value FROM meta").fetchall())
        assert meta["schema_version"] == "3"
        assert "migrated_v2_to_v3_at" in meta
        assert db.get_result("v2-rekord") == before
        assert db.failure_history("bárki") == []

    with Database(path) as db:
        meta2 = dict(db._conn.execute("SELECT key, value FROM meta").fetchall())
    assert meta2["migrated_v2_to_v3_at"] == meta["migrated_v2_to_v3_at"]


def test_fresh_and_migrated_v3_schemas_are_identical(tmp_path: Path) -> None:
    """AC-6.9: a friss és a migrált adatbázis szerkezete azonos (results és run_failures)."""
    fresh = tmp_path / "fresh.sqlite"
    Database(fresh).close()
    migrated = tmp_path / "migrated.sqlite"
    Database(migrated).close()
    _downgrade_to_v2(migrated)
    for table in ("results", "run_failures"):
        assert _columns(migrated, table) == _columns(fresh, table), table


def test_failures_survive_reopening(tmp_path: Path) -> None:
    path = tmp_path / "persist.sqlite"
    with Database(path) as db:
        _record(db)
    with Database(path) as db:
        assert db.effective_attempts("r1") == 1
