"""Fázis 11 — a kalibráció-életkor definíciója (``phase_11.md``, 2026-11-19), hálózat nélkül.

A ``BackendProperties`` szerkezetét egyszerű objektumokkal utánozzuk; a számpéldák a C6 valós
időpontjait használják (a q1 T1 2026-11-12 19:33:48, az első job 2026-11-16 09:23:49 → ~85,8 h).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import datetime as dt
import json
from types import SimpleNamespace
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
