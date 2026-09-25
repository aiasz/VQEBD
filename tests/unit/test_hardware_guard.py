"""Valódi QPU-használat védőkorlátai és a több PUB-os kiértékelés (Fázis 5.H).

Egyik teszt sem csatlakozik az IBM-hez: a kvótaválasz szótár, a Runtime mockolt.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from vqebd.credentials import IbmCredentials
from vqebd.hardware import (
    HardwareNotAllowedError,
    QuotaExhaustedError,
    assert_hardware_allowed,
    assert_quota_available,
    quota_summary,
)
from vqebd.seeds import SeedSet

pytestmark = pytest.mark.unit

# A 2026-09-25-én ténylegesen lekérdezett (azonosítóktól megtisztított) kvótaállás.
EXHAUSTED: dict[str, Any] = {
    "usage_consumed_seconds": 630,
    "usage_limit_seconds": 600,
    "usage_remaining_seconds": 0,
    "usage_limit_reached": True,
    "time_available_at": "2026-10-21T11:27:12.987Z",
    "plan_id": "nem-kerul-a-dokumentumba",
}


def test_exhausted_quota_is_refused_with_availability_date() -> None:
    with pytest.raises(QuotaExhaustedError, match="2026-10-21"):
        assert_quota_available(EXHAUSTED, 120.0)


@pytest.mark.parametrize(
    ("remaining", "required", "ok"),
    [(600, 120.0, True), (120, 120.0, True), (119, 120.0, False), (0, 1.0, False)],
)
def test_remaining_quota_threshold(remaining: int, required: float, ok: bool) -> None:
    usage = {"usage_limit_reached": False, "usage_remaining_seconds": remaining}
    if ok:
        assert_quota_available(usage, required)
    else:
        with pytest.raises(QuotaExhaustedError, match="kevesebb"):
            assert_quota_available(usage, required)


def test_unknown_quota_is_refused() -> None:
    """Ismeretlen kvótával nem küldünk be — a hiány nem engedély."""
    with pytest.raises(QuotaExhaustedError, match="nem ismert"):
        assert_quota_available({"usage_limit_reached": False}, 10.0)


def test_nonpositive_requirement_is_rejected() -> None:
    with pytest.raises(ValueError):
        assert_quota_available({"usage_remaining_seconds": 600}, 0.0)


def test_quota_summary_drops_identifiers() -> None:
    summary = quota_summary(EXHAUSTED)
    assert "plan_id" not in summary
    assert summary["usage_remaining_seconds"] == 0


@pytest.mark.parametrize("value", [None, "false", "1", "yes", ""])
def test_hardware_requires_explicit_true(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    else:
        monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", value)
    with pytest.raises(HardwareNotAllowedError):
        assert_hardware_allowed()


def test_hardware_allowed_when_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "TRUE")
    assert_hardware_allowed()


# --- több PUB egy jobban ---------------------------------------------------------


@patch("qiskit_ibm_runtime.QiskitRuntimeService")
@patch("qiskit_ibm_runtime.EstimatorV2")
def test_evaluate_observables_submits_one_job_with_all_pubs(
    mock_estimator_cls: MagicMock, mock_service_cls: MagicMock
) -> None:
    """Egy job, N PUB; PUB-onként szórás és metaadat; a layout minden observable-re."""
    from vqebd.backends.estimators import IBMQpuEnergyEvaluator

    backend = MagicMock()
    backend.name = "ibm_kingston"
    mock_service_cls.return_value.backend.return_value = backend

    pubs_out = []
    for i in range(3):
        pr = MagicMock()
        pr.data.evs = -1.0 - i
        pr.data.stds = 0.05 + i
        pr.data.ensemble_standard_error = 0.01 + i
        pr.metadata = {"shots": 8192, "index": i}
        pubs_out.append(pr)
    result = MagicMock()
    result.__iter__.return_value = iter(pubs_out)
    result.metadata = {"resilience": {"measure_mitigation": True}}
    job = MagicMock()
    job.job_id.return_value = "job-pes"
    job.result.return_value = result
    mock_estimator_cls.return_value.run.return_value = job

    qc = QuantumCircuit(2)
    ops = [SparsePauliOp(["ZZ", "XX"], coeffs=[c, 0.1]) for c in (0.1, 0.2, 0.3)]
    creds = IbmCredentials(token="123456789012345678901234", source="test")
    with (
        patch("vqebd.credentials.load_ibm_credentials", return_value=creds),
        patch("qiskit.transpile", return_value=qc),
    ):
        evaluator = IBMQpuEnergyEvaluator(qc, ops[0], SeedSet.derive(1), resilience_level=0)
        out = evaluator.evaluate_observables(ops, [[0.1], [0.2], [0.3]])

    assert mock_estimator_cls.return_value.run.call_count == 1
    submitted = mock_estimator_cls.return_value.run.call_args.args[0]
    assert len(submitted) == 3
    assert [pub[2] for pub in submitted] == [[0.1], [0.2], [0.3]]
    assert [r["evs"] for r in out] == [-1.0, -2.0, -3.0]
    assert [r["stds"] for r in out] == pytest.approx([0.05, 1.05, 2.05])
    assert [r["metadata"]["index"] for r in out] == [0, 1, 2]
    assert evaluator.last_job_id == "job-pes"
    assert mock_estimator_cls.call_args.kwargs["options"]["resilience_level"] == 0

    with pytest.raises(ValueError, match="száma"):
        evaluator.evaluate_observables(ops, [[0.1]])
    with pytest.raises(ValueError, match="qubit"):
        evaluator.evaluate_observables([SparsePauliOp("ZZZ")], [[0.1]])
