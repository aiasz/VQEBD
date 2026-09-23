"""Fázis 2 egység- és mocktesztek — IBMQpuEnergyEvaluator (L5).

Ezek a tesztek **nem fogyasztanak kvótát**:
- Ellenőrzik a platform-metaadatokat és a konfigurációs ujjlenyomatot.
- Mockolják a Qiskit Runtime API-t a hívási lánc ellenőrzésére.
- Az éles hardveres tesztet `@pytest.mark.hardware` jelöléssel látják el, amit
  a CI kizár (``-m "not hardware"``).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from vqebd.backends.estimators import IBMQpuEnergyEvaluator
from vqebd.chemistry.molecule import h2
from vqebd.config import OptimizerSpec, VQEConfig
from vqebd.credentials import IbmCredentials
from vqebd.platforms import platform_of
from vqebd.seeds import SeedSet

pytestmark = pytest.mark.unit


def test_platform_info_ibm_qpu() -> None:
    """Az ibm_qpu platform-metaadatai helyesek és kvótavédettek."""
    info = platform_of("ibm_qpu")
    assert info.backend == "ibm_qpu"
    assert info.platform == "qiskit"
    assert info.requires_quota is True
    assert info.exact is False
    assert info.deterministic is False
    assert info.recommended_optimizer == "COBYLA"


def test_ibm_qpu_config_fingerprint() -> None:
    """A konfiguráció ujjlenyomata egyedi az ibm_qpu backendre."""
    cfg = VQEConfig(
        molecule=h2(),
        backend="ibm_qpu",
        optimizer=OptimizerSpec(method="COBYLA"),
    )
    fp = cfg.fingerprint()
    assert len(fp) == 64
    assert fp != VQEConfig(molecule=h2(), backend="qiskit_statevector").fingerprint()


def test_mismatched_qubit_count_raises_value_error() -> None:
    """Ha az áramkör és az observable qubitszáma eltér, ValueError keletkezik."""
    qc = QuantumCircuit(2)
    op = SparsePauliOp(["III"])
    seeds = SeedSet.derive(42)

    with pytest.raises(ValueError, match="eltér"):
        IBMQpuEnergyEvaluator(qc, op, seeds)


@patch("qiskit_ibm_runtime.QiskitRuntimeService")
@patch("qiskit_ibm_runtime.EstimatorV2")
def test_ibm_qpu_mock_evaluation(
    mock_estimator_cls: MagicMock, mock_service_cls: MagicMock
) -> None:
    """Mockolt futtatás igazolja az inicializációt és a kiértékelést."""
    mock_backend = MagicMock()
    mock_backend.name = "ibm_kingston"
    mock_backend.num_qubits = 156
    mock_backend.configuration().num_qubits = 156

    mock_service = MagicMock()
    mock_service.backend.return_value = mock_backend
    mock_service_cls.return_value = mock_service

    mock_job = MagicMock()
    mock_job.job_id.return_value = "job_test_123"
    mock_pub_result = MagicMock()
    mock_pub_result.data.evs = -1.821039
    mock_job.result.return_value = [mock_pub_result]

    mock_estimator = MagicMock()
    mock_estimator.run.return_value = mock_job
    mock_estimator_cls.return_value = mock_estimator

    qc = QuantumCircuit(2)
    op = SparsePauliOp(["II", "ZZ"])
    seeds = SeedSet.derive(42)
    dummy_creds = IbmCredentials(token="123456789012345678901234", source="test")

    with (
        patch("vqebd.credentials.load_ibm_credentials", return_value=dummy_creds),
        patch("qiskit.transpile", return_value=qc),
    ):
        evaluator = IBMQpuEnergyEvaluator(
            circuit=qc,
            observable=op,
            seeds=seeds,
            backend_name="ibm_kingston",
        )
        desc = evaluator.describe()
        assert desc["backend"] == "ibm_qpu"
        assert desc["ibm_backend"] == "ibm_kingston"
        assert desc["shots"] == 8192

        val = evaluator.evaluate([0.0])
        assert val == pytest.approx(-1.821039)
        assert evaluator.last_job_id == "job_test_123"


@pytest.mark.hardware
def test_live_ibm_qpu_connection() -> None:
    """Csak explicit '--run-hardware' vagy '-m hardware' esetén futó teszt."""
    from vqebd.credentials import load_ibm_credentials

    creds = load_ibm_credentials()
    assert creds.reveal()
