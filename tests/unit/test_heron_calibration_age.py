"""Fázis 11 — a kalibráció-életkor definíciója (``phase_11.md``, 2026-11-19), hálózat nélkül.

A ``BackendProperties`` szerkezetét egyszerű objektumokkal utánozzuk; a számpéldák a C6 valós
időpontjait használják (a q1 T1 2026-11-12 19:33:48, az első job 2026-11-16 09:23:49 → ~85,8 h).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from vqebd.heron_calibration_age import (
    block_calibration_age,
    calibration_age_hours,
    first_job_running,
    pair_parameters,
)

pytestmark = pytest.mark.unit

UTC = dt.UTC


def _t(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text).replace(tzinfo=UTC)


def _item(name: str, value: float, unit: str, date: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, value=value, unit=unit, date=_t(date))


def _props(*, sx_date: str = "2026-11-05 10:00:00") -> SimpleNamespace:
    """A C6 idején érvényes kalibráció (az sx a legrégebbi, de az életkorba nem számít)."""
    q1 = [
        _item("T1", 341.0, "us", "2026-11-12 19:33:48"),
        _item("T2", 598.0, "us", "2026-11-12 19:34:10"),
        _item("readout_error", 0.0044, "", "2026-11-12 21:10:00"),
        _item("frequency", 4.9, "GHz", "2026-11-01 00:00:00"),
    ]
    q2 = [
        _item("T1", 308.0, "us", "2026-11-12 19:33:50"),
        _item("T2", 122.0, "us", "2026-11-12 19:34:12"),
        _item("readout_error", 0.0132, "", "2026-11-12 21:10:00"),
    ]
    gates = [
        SimpleNamespace(
            gate="sx", qubits=[1], parameters=[_item("gate_error", 0.00023, "", sx_date)]
        ),
        SimpleNamespace(
            gate="cz",
            qubits=[2, 1],
            parameters=[
                _item("gate_error", 0.00097, "", "2026-11-12 20:29:00"),
                _item("gate_length", 68.0, "ns", "2026-11-01 00:00:00"),
            ],
        ),
        SimpleNamespace(
            gate="cz",
            qubits=[2, 3],
            parameters=[_item("gate_error", 0.5, "", "2026-10-01 00:00:00")],
        ),
    ]
    return SimpleNamespace(
        qubits={1: q1, 2: q2}, gates=gates, last_update_date=_t("2026-11-13 14:57:10")
    )


def _block() -> dict[str, Any]:
    return {
        "block": "C6",
        "kind": "confirmatory",
        "physical_qubits": [1, 2],
        "calibration_before": {
            "qubits": {
                "1": {"t1_s": 341.0e-6, "t2_s": 598.0e-6, "readout_error": 0.0044},
                "2": {"t1_s": 308.0e-6, "t2_s": 122.0e-6, "readout_error": 0.0132},
            },
            "cz_errors": {"1-2": 0.00097, "2-1": 0.00097},
        },
        "runs": [
            {"timestamps": {"running": "2026-11-16T09:24:40.000Z"}},
            {"timestamps": {"running": "2026-11-16T09:23:49.146036Z"}},
        ],
    }


def test_only_t1_t2_readout_and_the_pair_cz_count() -> None:
    names = [p["name"] for p in pair_parameters(_props(), [1, 2])]
    assert names == [
        "q1 T1",
        "q1 T2",
        "q1 readout_error",
        "q2 T1",
        "q2 T2",
        "q2 readout_error",
        "cz gate_error",
    ]  # az sx, a frekvencia, a gate_length és a [2, 3] pár cz-je kimarad


def test_first_job_running_is_the_earliest_running_timestamp() -> None:
    assert first_job_running(_block()) == _t("2026-11-16 09:23:49.146036")
    with pytest.raises(ValueError, match="running"):
        first_job_running({"block": "X", "runs": [{"timestamps": {}}]})


def test_the_c6_age_is_about_85_8_hours_from_the_oldest_pair_parameter() -> None:
    record = block_calibration_age(_block(), _props())
    assert record["oldest_parameter"] == "q1 T1"
    assert record["oldest_parameter_date_utc"] == "2026-11-12T19:33:48+00:00"
    assert record["age_h"] == pytest.approx(85.83, abs=0.01)
    assert record["properties_last_update_utc"] == "2026-11-13T14:57:10+00:00"
    assert record["matches_snapshot"] is True
    json.dumps(record)  # JSON-szerializálható


def test_last_update_date_and_sx_do_not_change_the_age() -> None:
    fresh = _props(sx_date="2026-11-16 09:00:00")
    fresh.last_update_date = _t("2026-11-16 09:00:00")  # frissült, de a párt nem mérték újra
    assert block_calibration_age(_block(), fresh)["age_h"] == pytest.approx(85.83, abs=0.01)


def test_a_changed_value_is_flagged_against_the_saved_snapshot() -> None:
    block = _block()
    block["calibration_before"]["qubits"]["1"]["t2_s"] = 22.0e-6
    assert block_calibration_age(block, _props())["matches_snapshot"] is False
    del block["calibration_before"]
    assert block_calibration_age(block, _props())["matches_snapshot"] is None


def test_missing_parameters_or_a_measurement_after_the_job_are_refused() -> None:
    props = _props()
    props.qubits[2] = [p for p in props.qubits[2] if p.name != "T2"]
    with pytest.raises(ValueError, match="q2"):
        pair_parameters(props, [1, 2])
    props = _props()
    props.gates = [g for g in props.gates if g.qubits != [2, 1]]
    with pytest.raises(ValueError, match="cz"):
        pair_parameters(props, [1, 2])
    later = pair_parameters(_props(), [1, 2])
    with pytest.raises(ValueError, match="későbbi"):
        calibration_age_hours(_t("2026-11-12 21:00:00"), later)
    with pytest.raises(ValueError, match="nincs"):
        calibration_age_hours(_t("2026-11-16 09:00:00"), [])


def test_the_age_is_stored_without_rounding_for_the_48_hour_boundary() -> None:
    block = _block()
    block["runs"] = [{"timestamps": {"running": "2026-11-14T19:33:48Z"}}]  # +48 h 0 s
    assert block_calibration_age(block, _props())["age_h"] == 48.0
    block["runs"] = [{"timestamps": {"running": "2026-11-14T19:34:03Z"}}]  # +48 h 15 s
    age = block_calibration_age(block, _props())["age_h"]
    assert age > 48.0 and age == pytest.approx(48.0 + 15 / 3600)


def test_the_cz_value_is_compared_with_the_same_direction_of_the_snapshot() -> None:
    block = _block()
    block["calibration_before"]["cz_errors"] = {"1-2": 0.00111, "2-1": 0.00097}
    record = block_calibration_age(block, _props())  # a kalibráció [2, 1] iránya: 0,00097
    assert record["matches_snapshot"] is True
    assert record["parameters"][-1]["qubits"] == [2, 1]
    block["calibration_before"]["cz_errors"] = {"1-2": 0.00097, "2-1": 0.00111}
    assert block_calibration_age(block, _props())["matches_snapshot"] is False


# --- a rekonstrukciós szkript hamis szolgáltatással -----------------------------------------------


@pytest.fixture
def age_script(repo_root: Path) -> ModuleType:
    path = repo_root / "scripts" / "heron_calibration_age.py"
    if not path.is_file():
        pytest.skip("scripts/ nincs a szállított image-ben")
    spec = importlib.util.spec_from_file_location("heron_calibration_age_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_script_queries_the_calibration_at_the_first_job_and_survives_a_bad_block(
    age_script: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asked: list[dt.datetime] = []

    class Backend:
        def properties(self, datetime: dt.datetime) -> Any:
            asked.append(datetime)
            if datetime.day == 20:
                raise RuntimeError("nincs történeti adat")
            return _props()

    service = SimpleNamespace(backend=lambda name: Backend())
    monkeypatch.setattr(age_script, "connect_service", lambda: service)
    good = {**_block(), "backend": "ibm_test"}
    bad = {**_block(), "block": "C7", "backend": "ibm_test"}
    bad["runs"] = [{"timestamps": {"running": "2026-11-20T10:00:00Z"}}]
    pilot = {**_block(), "block": "B0", "kind": "pilot", "backend": "ibm_test"}
    for name, block in (("c6", good), ("c7", bad), ("b0", pilot)):
        (tmp_path / f"{name}.json").write_text(json.dumps(block), encoding="utf-8")

    assert age_script.main(["--data-dir", str(tmp_path)]) == 1  # egy blokk hibás
    payload = json.loads((tmp_path / "calibration_age.json").read_text(encoding="utf-8"))
    records = {r["block"]: r for r in payload["blocks"]}
    assert set(records) == {"C6", "C7"}  # a pilot kimarad
    assert records["C6"]["age_h"] == pytest.approx(85.83, abs=0.01)
    assert records["C7"]["age_h"] is None and "nincs történeti adat" in records["C7"]["error"]
    assert asked[0] == _t("2026-11-16 09:23:49.146036")  # az első job indulásakor


def test_a_run_without_a_running_timestamp_makes_the_age_unknown() -> None:
    block = _block()
    block["runs"][0]["timestamps"] = {}  # az egyik futás időbélyege hiányzik
    with pytest.raises(ValueError, match="running"):
        first_job_running(block)


def test_a_failed_query_keeps_the_previous_valid_record(
    age_script: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Backend:
        ok = True

        def properties(self, datetime: dt.datetime) -> Any:
            if not Backend.ok:
                raise RuntimeError("átmeneti hiba")
            return _props()

    service = SimpleNamespace(backend=lambda name: Backend())
    monkeypatch.setattr(age_script, "connect_service", lambda: service)
    (tmp_path / "c6.json").write_text(json.dumps({**_block(), "backend": "ibm_test"}), "utf-8")
    assert age_script.main(["--data-dir", str(tmp_path)]) == 0
    Backend.ok = False
    assert age_script.main(["--data-dir", str(tmp_path)]) == 1
    record = json.loads((tmp_path / "calibration_age.json").read_text("utf-8"))["blocks"][0]
    assert record["age_h"] == pytest.approx(85.83, abs=0.01)  # a jó érték megmaradt
    assert "átmeneti hiba" in record["reused_after_error"]
