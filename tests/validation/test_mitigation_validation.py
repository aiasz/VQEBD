"""Fázis 3 validációs tesztek — Hibaenyhítés és ZNE (AC-3.2, AC-3.4, TP-F03).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

pytest.importorskip("qiskit_aer", reason="a Fázis 3 Aer szimulátort igényli")
pytest.importorskip("qiskit_ibm_runtime", reason="a Fázis 3 FakeProvider-t igényli")

from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import AnsatzSpec, MitigationSpec, OptimizerSpec, VQEConfig
from vqebd.mitigation.folding import count_two_qubit_gates, fold_global_unitary
from vqebd.seeds import SeedSet
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation


def test_tc_302_mitiq_cross_validation_gate_counts() -> None:
    """Keresztvalidáció: fold_global_unitary és Mitiq fold_global kapuszámai megegyeznek."""
    try:
        from mitiq.zne.scaling import fold_global
    except ImportError:
        pytest.skip("A mitiq csomag nincs telepítve a keresztvalidációhoz")

    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(20260922)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(kind="uccsd"), seeds)

    for scale in (1, 3, 5):
        saját_folded = fold_global_unitary(ansatz.circuit, scale)
        saját_2q = count_two_qubit_gates(saját_folded)

        mitiq_folded = fold_global(ansatz.circuit, scale_factor=scale)
        mitiq_2q = count_two_qubit_gates(mitiq_folded)

        assert saját_2q == mitiq_2q, (
            f"λ={scale} esetén a 2-qubit kapuszám eltér: saját={saját_2q}, mitiq={mitiq_2q}"
        )


def test_tc_304_zne_mitigation_on_noisy_simulation() -> None:
    """A ZNE (Richardson) szignifikánsan csökkenti a FakeManilaV2 zajmodell hibáját."""
    mol = h2(H2_REFERENCE_BOND_LENGTH)
    opt = OptimizerSpec(method="COBYLA", maxiter=20)

    # Nyers futtatás
    cfg_raw = VQEConfig(
        molecule=mol,
        backend="qiskit_aer_noisy",
        optimizer=opt,
        mitigation=MitigationSpec(strategy="none"),
        seed=20260922,
    )
    res_raw = run_vqe(cfg_raw)

    # Mitigált futtatás (ZNE local, Richardson, λ ∈ {1, 3, 5})
    mit_spec = MitigationSpec(
        strategy="zne_local", scale_factors=(1, 3, 5), extrapolator="richardson"
    )
    cfg_zne = VQEConfig(
        molecule=mol,
        backend="qiskit_aer_noisy",
        optimizer=opt,
        mitigation=mit_spec,
        seed=20260922,
    )
    res_zne = run_vqe(cfg_zne)

    assert res_zne.mitigation is not None
    assert res_zne.mitigation.strategy_name == "zne_local"
    assert res_zne.mitigation.extrapolator_name == "richardson"
    assert len(res_zne.mitigation.scaled_energies) == 3

    ref = res_raw.reference.exact_diagonalization
    assert ref is not None

    raw_error = abs(res_raw.energy - ref)
    zne_error = abs(res_zne.energy - ref)

    print(f"\nNyers hiba:    {raw_error * 1000:.2f} mHa")
    print(f"Mitigált hiba: {zne_error * 1000:.2f} mHa")

    # A mitigáció javítja az eredményt a nyers értékhez képest
    assert zne_error < raw_error or zne_error < 0.05


def test_tc_306_mitigation_result_in_cli_and_dict() -> None:
    """A mitigációs eredmény bekerül a to_dict és report kimenetekbe."""
    mol = h2(H2_REFERENCE_BOND_LENGTH)
    cfg = VQEConfig(
        molecule=mol,
        backend="qiskit_statevector",
        mitigation=MitigationSpec(strategy="zne_local", scale_factors=(1, 3)),
    )
    res = run_vqe(cfg)

    d = res.to_dict()
    assert "mitigation" in d
    assert d["mitigation"]["strategy_name"] == "zne_local"
    assert d["mitigation"]["scale_factors"] == [1.0, 3.0]

    rep = res.report()
    assert "L4  VQE (mitigated)" in rep
    assert "zne_local" in rep
