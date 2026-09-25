"""Fázis 1b validációs tesztek — véges lövésszámú és zajos szimuláció (L3a / L3b).

Ez a modul a Fázis 1b elfogadási kritériumait ellenőrzi (TP-F01B / phase_01b.md).
A tesztek célja:
1. L3a (Qiskit Aer, 8192 lövés, zajmentes) működése és determinizmusa.
2. L3b (Qiskit Aer + FakeManilaV2 kalibrációs zajmodell) működése és determinizmusa.
3. Transzpiláció és ISA layout alkalmazása az observable-re.
4. Gradiens-alapú vs. deriváltmentes optimalizálók viselkedése és figyelmeztetései.
5. Konfiguráció-ujjlenyomatok (content_hash) egyedisége.
6. Offline futtathatóság (IBM Quantum token vagy hálózat nélkül).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("qiskit_aer", reason="a Fázis 1b Aer szimulátort igényli")
pytest.importorskip("qiskit_ibm_runtime", reason="a Fázis 1b FakeProvider-t igényli")

from vqebd.backends.estimators import (
    AerNoisyEnergyEvaluator,
    AerShotEnergyEvaluator,
    make_energy_evaluator,
)
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import BackendKind, OptimizerSpec, VQEConfig
from vqebd.platforms import (
    DERIVATIVE_FREE_OPTIMIZERS,
    GRADIENT_BASED_OPTIMIZERS,
    check_optimizer_compatibility,
    platform_of,
)
from vqebd.seeds import SeedSet
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation


def _noisy_config(backend: BackendKind, **kwargs: Any) -> VQEConfig:
    """Segédfüggvény gyors tesztkonfigurációk készítéséhez."""
    optimizer = kwargs.pop("optimizer", OptimizerSpec(method="COBYLA", maxiter=100))
    return VQEConfig(
        molecule=h2(H2_REFERENCE_BOND_LENGTH),
        backend=backend,
        optimizer=optimizer,
        **kwargs,
    )


# --- TC-1B01 / AC-1B.1: Aer Shot Evaluator (L3a) -----------------------------


def test_tc_1b01_aer_shot_evaluator() -> None:
    """Aer shot evaluator L3a energiát ad és megfelelően konfigurált."""
    config = _noisy_config("qiskit_aer_shot")
    result = run_vqe(config)

    assert result.energy < -1.0
    # A lövésszám miatti ingadozás ellenére az energia reális tartományban van
    assert abs(result.energy - result.reference.exact_diagonalization) < 0.05  # type: ignore[operator]
    assert result.platform == "qiskit"
    assert result.config.backend == "qiskit_aer_shot"

    structure = build_electronic_structure(config.molecule)
    hamiltonian = map_to_qubits(
        structure, config.mapper, two_qubit_reduction=config.two_qubit_reduction
    )
    seeds = SeedSet.derive(config.seed)
    ansatz = build_ansatz(structure, hamiltonian, config.ansatz, seeds)
    evaluator = make_energy_evaluator(
        "qiskit_aer_shot", ansatz.circuit, hamiltonian.operator, seeds
    )

    assert isinstance(evaluator, AerShotEnergyEvaluator)
    desc = evaluator.describe()
    assert desc["shots"] == 8192
    assert desc["backend"] == "qiskit_aer_shot"
    assert desc["optimization_level"] == 1


# --- TC-1B02 / AC-1B.2: Aer Noisy Evaluator (L3b) ----------------------------


def test_tc_1b02_aer_noisy_evaluator() -> None:
    """Aer noisy evaluator FakeManilaV2 kalibrációval fut és L3b energiát ad."""
    config = _noisy_config("qiskit_aer_noisy")
    result = run_vqe(config)

    assert result.energy < -1.0
    # Zaj miatt az energia eltér a zajmentes állapottól
    assert result.platform == "qiskit"
    assert result.config.backend == "qiskit_aer_noisy"

    structure = build_electronic_structure(config.molecule)
    hamiltonian = map_to_qubits(
        structure, config.mapper, two_qubit_reduction=config.two_qubit_reduction
    )
    seeds = SeedSet.derive(config.seed)
    ansatz = build_ansatz(structure, hamiltonian, config.ansatz, seeds)
    evaluator = make_energy_evaluator(
        "qiskit_aer_noisy", ansatz.circuit, hamiltonian.operator, seeds
    )

    assert isinstance(evaluator, AerNoisyEnergyEvaluator)
    desc = evaluator.describe()
    assert desc["shots"] == 8192
    assert desc["backend"] == "qiskit_aer_noisy"
    assert desc["fake_backend"] == "FakeManilaV2"
    assert desc["optimization_level"] == 3


# --- TC-1B03 / AC-1B.3: ISA Transzpiláció és Layout --------------------------


def test_tc_1b03_isa_transpilation_and_layout() -> None:
    """A transzpilált áramkör és az observable azonos qubit-számú és kompatibilis."""
    from vqebd.config import AnsatzSpec

    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(20260922)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(kind="uccsd"), seeds)

    evaluator = AerNoisyEnergyEvaluator(ansatz.circuit, hamiltonian.operator, seeds)
    # A FakeManilaV2 5-qubites eszköz
    assert evaluator._isa_circuit.num_qubits == 5
    assert evaluator._isa_observable.num_qubits == 5
    # Kiértékelés tetszőleges pontban hibamentesen fut
    val = evaluator.evaluate([0.0] * ansatz.num_parameters)
    assert isinstance(val, float)


# --- TC-1B04 & TC-1B05 / AC-1B.4: Determinizmus ------------------------------


def test_tc_1b04_determinism_aer_shot() -> None:
    """Két azonos seedű L3a futás bitre azonos eredményt ad."""
    opt = OptimizerSpec(method="COBYLA", maxiter=20)
    config = _noisy_config("qiskit_aer_shot", seed=42, optimizer=opt)
    res1 = run_vqe(config)
    res2 = run_vqe(config)
    assert res1.energy == res2.energy
    assert res1.optimal_parameters == res2.optimal_parameters


def test_tc_1b05_determinism_aer_noisy() -> None:
    """Két azonos seedű L3b futás bitre azonos eredményt ad."""
    opt = OptimizerSpec(method="COBYLA", maxiter=20)
    config = _noisy_config("qiskit_aer_noisy", seed=42, optimizer=opt)
    res1 = run_vqe(config)
    res2 = run_vqe(config)
    assert res1.energy == res2.energy
    assert res1.optimal_parameters == res2.optimal_parameters


def test_different_seeds_yield_different_noisy_results() -> None:
    """Különböző seedek eltérő mintavételi trajektóriát eredményeznek."""
    opt = OptimizerSpec(method="COBYLA", maxiter=20)
    cfg1 = _noisy_config("qiskit_aer_shot", seed=100, optimizer=opt)
    cfg2 = _noisy_config("qiskit_aer_shot", seed=200, optimizer=opt)
    res1 = run_vqe(cfg1)
    res2 = run_vqe(cfg2)
    assert res1.energy != res2.energy


# --- TC-1B06 / AC-1B.5: Konfiguráció-hash egyedisége -------------------------


def test_tc_1b06_content_hash_uniqueness() -> None:
    """A backend megváltozása megváltoztatja a konfiguráció-ujjlenyomatot."""
    c_state = _noisy_config("qiskit_statevector")
    c_shot = _noisy_config("qiskit_aer_shot")
    c_noisy = _noisy_config("qiskit_aer_noisy")

    assert c_state.fingerprint() != c_shot.fingerprint()
    assert c_shot.fingerprint() != c_noisy.fingerprint()
    assert c_state.fingerprint() != c_noisy.fingerprint()


# --- TC-1B07 / AC-1B.6: Optimalizáló-kompatibilitás --------------------------


@pytest.mark.parametrize("backend", ["qiskit_aer_shot", "qiskit_aer_noisy"])
def test_tc_1b07_gradient_optimizers_warn_on_noisy_platforms(backend: BackendKind) -> None:
    """Zajos és lövéses platformon gradiens-alapú optimalizáló figyelmeztetést kap."""
    info = platform_of(backend)
    assert not info.gradient_safe
    assert info.recommended_optimizer in DERIVATIVE_FREE_OPTIMIZERS

    for method in sorted(GRADIENT_BASED_OPTIMIZERS):
        warning = check_optimizer_compatibility(backend, method)
        assert warning is not None
        assert "MEGBÍZHATATLAN" in warning
        assert info.recommended_optimizer in warning


@pytest.mark.parametrize("backend", ["qiskit_aer_shot", "qiskit_aer_noisy"])
@pytest.mark.parametrize("method", sorted(DERIVATIVE_FREE_OPTIMIZERS))
def test_tc_1b07_derivative_free_optimizers_accepted_on_noisy_platforms(
    backend: BackendKind, method: str
) -> None:
    """Deriváltmentes módszerek nem kapnak figyelmeztetést zajos platformon."""
    assert check_optimizer_compatibility(backend, method) is None


# --- TC-1B08 / AC-1B.7: CLI és riport formázás -------------------------------


def test_tc_1b08_cli_report_labels() -> None:
    """A VQEResult szöveges formázása L3a / L3b címkét tartalmaz."""
    cfg_shot = _noisy_config("qiskit_aer_shot", optimizer=OptimizerSpec(method="COBYLA", maxiter=5))
    res_shot = run_vqe(cfg_shot)
    text_shot = res_shot.report()
    assert "L3a VQE (shot)" in text_shot
    assert "ansatz+zaj (L3−L1)" in text_shot

    cfg_noisy = _noisy_config(
        "qiskit_aer_noisy", optimizer=OptimizerSpec(method="COBYLA", maxiter=5)
    )
    res_noisy = run_vqe(cfg_noisy)
    text_noisy = res_noisy.report()
    assert "L3b VQE (noisy)" in text_noisy
    assert "ansatz+zaj (L3−L1)" in text_noisy


# --- TC-1B09 / AC-1B.8: Offline működés és kvótamentesség --------------------


@pytest.mark.parametrize("backend", ["qiskit_aer_shot", "qiskit_aer_noisy"])
def test_tc_1b09_no_quota_required(backend: BackendKind) -> None:
    """A szimulált zajos platformok offline futnak és nem igényelnek kvótát."""
    info = platform_of(backend)
    assert not info.requires_quota
    assert info.deterministic


# --- Negatív tesztek ---------------------------------------------------------


def test_mismatched_qubit_count_raises_value_error() -> None:
    """Ha az áramkör és az observable qubit-száma eltér, ValueError keletkezik."""
    from qiskit.circuit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp

    qc = QuantumCircuit(2)
    op = SparsePauliOp(["III"])  # 3 qubit
    seeds = SeedSet.derive(42)

    with pytest.raises(ValueError, match="eltér"):
        AerShotEnergyEvaluator(qc, op, seeds)

    with pytest.raises(ValueError, match="eltér"):
        AerNoisyEnergyEvaluator(qc, op, seeds)


# --- TC-1B10: a mintavételi zaj FÜGGETLEN kiértékelésenként (v0.7.1) ------------
#
# Regressziós tesztek a v0.7.0 hibájára: az Aer EstimatorV2 minden run()-nál
# ugyanabból a seedből húzott, így minden kiértékelés ugyanazt a z·σ eltolást
# kapta (a „lövészaj" valójában állandó torzítás volt). Lásd TR-F03, 1. javítási kör.


def _h2_ansatz() -> tuple[Any, Any, SeedSet]:
    seeds = SeedSet.derive(20260922)
    structure = build_electronic_structure(h2(H2_REFERENCE_BOND_LENGTH))
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    from vqebd.config import AnsatzSpec

    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(kind="uccsd"), seeds)
    return ansatz.circuit, hamiltonian.operator, seeds


@pytest.mark.parametrize("cls", [AerShotEnergyEvaluator, AerNoisyEnergyEvaluator])
def test_tc_1b10_sampling_noise_is_independent_per_evaluation(cls: Any) -> None:
    """Azonos θ-nál az egymást követő kiértékelések zaja független és σ szórású."""
    import numpy as np

    circuit, observable, seeds = _h2_ansatz()
    theta = [0.0] * circuit.num_parameters
    evaluator = cls(circuit, observable, seeds)
    samples = np.array([evaluator.evaluate(theta) for _ in range(300)])
    exact = cls(circuit, observable, seeds, precision=0.0).evaluate(theta)

    assert len(set(samples.tolist())) == len(samples), "ismétlődő zajhúzás"
    sigma = 1.0 / np.sqrt(8192)
    # 300 minta: a szórás becslésének relatív hibája ~ 1/sqrt(2·299) ≈ 4%.
    assert samples.std(ddof=1) == pytest.approx(sigma, rel=0.15)
    # Az átlag torzítatlan: |átlag − egzakt| < 4 standard hiba.
    assert abs(samples.mean() - exact) < 4 * sigma / np.sqrt(len(samples))


@pytest.mark.parametrize("cls", [AerShotEnergyEvaluator, AerNoisyEnergyEvaluator])
def test_tc_1b10_sampling_sequence_is_reproducible(cls: Any) -> None:
    """Azonos seed → bitre azonos zajsorozat (ADR-0005 determinizmus)."""
    circuit, observable, seeds = _h2_ansatz()
    theta = [0.0] * circuit.num_parameters
    a = cls(circuit, observable, seeds)
    b = cls(circuit, observable, seeds)
    assert [a.evaluate(theta) for _ in range(5)] == [b.evaluate(theta) for _ in range(5)]


@pytest.mark.parametrize("cls", [AerShotEnergyEvaluator, AerNoisyEnergyEvaluator])
def test_tc_1b10_zero_precision_is_exact_and_negative_rejected(cls: Any) -> None:
    """precision=0 → determinisztikus egzakt érték; negatív precision → ValueError."""
    circuit, observable, seeds = _h2_ansatz()
    theta = [0.0] * circuit.num_parameters
    exact = cls(circuit, observable, seeds, precision=0.0)
    assert exact.evaluate(theta) == exact.evaluate(theta)
    with pytest.raises(ValueError, match="precision"):
        cls(circuit, observable, seeds, precision=-1e-3)
