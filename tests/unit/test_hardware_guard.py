"""Valódi QPU-használat védőkorlátai és a több PUB-os kiértékelés (Fázis 5.H).

Egyik teszt sem csatlakozik az IBM-hez: a kvótaválasz szótár, a Runtime mockolt.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from vqebd.credentials import IbmCredentials
from vqebd.hardware import (
    QPU_SECONDS_PER_EVALUATION,
    EvaluationBudgetExceededError,
    HardwareNotAllowedError,
    QuotaExhaustedError,
    assert_hardware_allowed,
    assert_quota_available,
    guard_hardware_vqe,
    hardware_evaluation_budget,
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


# --- hardveres VQE-útvonal: kvótavédelem és kiértékelési keret (K7) --------------


def _service_with(usage: dict[str, Any]) -> MagicMock:
    service = MagicMock()
    service.usage.return_value = usage
    return service


def test_guard_vqe_requires_permission_before_any_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Engedély nélkül a kvótát sem kérdezzük le: nincs hálózati hívás."""
    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    service = _service_with({"usage_remaining_seconds": 600, "usage_limit_reached": False})
    with pytest.raises(HardwareNotAllowedError):
        guard_hardware_vqe(10, service=service)
    service.usage.assert_not_called()


def test_guard_vqe_refuses_when_worst_case_exceeds_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 2026-09-23-i eset: 300 kiértékelés × 15 s ≫ 600 s — beküldés előtt megáll."""
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    service = _service_with({"usage_remaining_seconds": 600, "usage_limit_reached": False})
    with pytest.raises(QuotaExhaustedError, match="--maxiter"):
        guard_hardware_vqe(300, service=service)


def test_guard_vqe_passes_and_returns_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    service = _service_with({"usage_remaining_seconds": 600, "usage_limit_reached": False})
    assert guard_hardware_vqe(20, service=service) == 20 * QPU_SECONDS_PER_EVALUATION


def test_guard_vqe_rejects_nonpositive_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    with pytest.raises(ValueError, match="legalább 1"):
        guard_hardware_vqe(0, service=_service_with({}))


class _CountingEvaluator:
    """Az EnergyEvaluator ``__call__``-keretét tesztelő, hálózatmentes kiértékelő."""

    @staticmethod
    def build() -> Any:
        from vqebd.backends.estimators import EnergyEvaluator

        class Dummy(EnergyEvaluator):
            def __init__(self) -> None:
                super().__init__(num_qubits=1)
                self.evaluated = 0

            def evaluate(self, parameters: Any) -> float:
                self.evaluated += 1
                return 0.0

            @property
            def kind(self) -> Any:
                return "qiskit_statevector"

        return Dummy()


def test_evaluator_budget_stops_before_the_extra_evaluation() -> None:
    """A keret elfogyása után a kiértékelés NEM indul el (QPU-n ez job lenne)."""
    evaluator = _CountingEvaluator.build()
    evaluator.max_calls = 3
    for _ in range(3):
        evaluator([0.0])
    with pytest.raises(EvaluationBudgetExceededError, match="keret"):
        evaluator([0.0])
    assert evaluator.evaluated == 3
    assert evaluator.call_count == 3


def test_evaluator_without_budget_is_unlimited() -> None:
    evaluator = _CountingEvaluator.build()
    assert evaluator.max_calls is None
    for _ in range(50):
        evaluator([0.0])
    assert evaluator.call_count == 50


def test_run_vqe_on_qpu_is_guarded_before_any_computation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``run_vqe`` hardveres útja engedély nélkül azonnal megáll (K7)."""
    from vqebd.chemistry.molecule import h2
    from vqebd.config import OptimizerSpec, VQEConfig
    from vqebd.vqe.runner import run_vqe

    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    config = VQEConfig(
        molecule=h2(), backend="ibm_qpu", optimizer=OptimizerSpec(method="COBYLA", maxiter=5)
    )
    with (
        patch("vqebd.backends.estimators.IBMQpuEnergyEvaluator") as evaluator_cls,
        pytest.raises(HardwareNotAllowedError),
    ):
        run_vqe(config, compute_fci=False)
    evaluator_cls.assert_not_called()


def test_run_vqe_on_qpu_budget_includes_reestimate_and_mitigation() -> None:
    """A legrosszabb eset: maxiter + K × zajszorzók száma (ZNE esetén)."""
    from vqebd.chemistry.molecule import h2
    from vqebd.config import MitigationSpec, OptimizerSpec, VQEConfig
    from vqebd.vqe.runner import run_vqe

    config = VQEConfig(
        molecule=h2(),
        backend="ibm_qpu",
        optimizer=OptimizerSpec(method="COBYLA", maxiter=10),
        mitigation=MitigationSpec(strategy="zne_local", scale_factors=(1, 3, 5)),
        reestimate=4,
    )
    with (
        patch("vqebd.vqe.runner.guard_hardware_vqe", side_effect=RuntimeError("stop")) as guard,
        pytest.raises(RuntimeError, match="stop"),
    ):
        run_vqe(config, compute_fci=False)
    guard.assert_called_once_with(10 + 4 * 3)


def test_reserve_scales_the_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    service = _service_with({"usage_remaining_seconds": 600, "usage_limit_reached": False})
    assert guard_hardware_vqe(10, service=service, reserve=1.2) == pytest.approx(
        10 * QPU_SECONDS_PER_EVALUATION * 1.2
    )
    # 600 / 15 = 40 kiértékelés fér a keretbe; tartalékkal már 34 sem
    with pytest.raises(QuotaExhaustedError):
        guard_hardware_vqe(34, service=service, reserve=1.2)
    guard_hardware_vqe(33, service=service, reserve=1.2)


def test_hardware_evaluation_budget_counts_reestimates_and_zne_factors() -> None:
    from vqebd.chemistry.molecule import h2
    from vqebd.config import MitigationSpec, OptimizerSpec, VQEConfig

    base = VQEConfig(molecule=h2(), backend="ibm_qpu", optimizer=OptimizerSpec(maxiter=10))
    assert hardware_evaluation_budget(base) == 10 + 1  # újramintavétel nélkül 1 végső becslés
    resampled = VQEConfig(
        molecule=h2(), backend="ibm_qpu", optimizer=OptimizerSpec(maxiter=10), reestimate=4
    )
    assert hardware_evaluation_budget(resampled) == 10 + 4
    zne = VQEConfig(
        molecule=h2(),
        backend="ibm_qpu",
        optimizer=OptimizerSpec(maxiter=10),
        mitigation=MitigationSpec(strategy="zne_local", scale_factors=(1, 3, 5)),
        reestimate=4,
    )
    assert hardware_evaluation_budget(zne) == 10 + 4 * 3
