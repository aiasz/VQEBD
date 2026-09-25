"""Fázis 3 validációs tesztek — Hibaenyhítés és ZNE (AC-3.2, AC-3.4, TP-F03).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("qiskit_aer", reason="a Fázis 3 Aer szimulátort igényli")
pytest.importorskip("qiskit_ibm_runtime", reason="a Fázis 3 FakeProvider-t igényli")

from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import AnsatzSpec, MitigationSpec, OptimizerSpec, VQEConfig
from vqebd.seeds import SeedSet
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation


# --- Közös előkészítés: H2 θ*-nál, egzakt zajos várható értékkel -------------
#
# A ZNE két hibakomponensét KÜLÖN mérjük (TR-F03, 1. javítási kör):
#   - torzítás: precision=0 — az Aer a zajmodell szerinti EGZAKT várható értéket
#     adja, így az extrapoláció rendszeres hibája determinisztikusan tesztelhető;
#   - szórás: a véges mintavétel (1/sqrt(8192) ≈ 11 mHa / kiértékelés) — ezt a
#     gen_report_figures.py seed-ensemble mérése dokumentálja, nem egységteszt.


@pytest.fixture(scope="module")
def h2_theta_star() -> dict[str, Any]:
    """H2 UCCSD ansatz, Hamilton-operátor és a zajmentes optimum (θ*)."""
    mol = h2(H2_REFERENCE_BOND_LENGTH)
    cfg = VQEConfig(
        molecule=mol, backend="qiskit_statevector", optimizer=OptimizerSpec(method="SLSQP")
    )
    res = run_vqe(cfg)
    seeds = SeedSet.derive(cfg.seed)
    structure = build_electronic_structure(mol)
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(kind="uccsd"), seeds)
    return {
        "theta": list(res.optimal_parameters),
        "reference": res.energy,
        "e_nuc": hamiltonian.nuclear_repulsion_energy,
        "circuit": ansatz.circuit,
        "observable": hamiltonian.operator,
        "seeds": seeds,
    }


def _zne(case: dict[str, Any], strategy: str, extrapolator: str) -> Any:
    from vqebd.backends.estimators import AerNoisyEnergyEvaluator
    from vqebd.mitigation import get_mitigation_strategy

    evaluator = AerNoisyEnergyEvaluator(
        case["circuit"], case["observable"], case["seeds"], precision=0.0
    )
    return get_mitigation_strategy(
        strategy, scale_factors=(1, 3, 5), extrapolator=extrapolator
    ).execute(case["circuit"], case["observable"], evaluator, case["theta"], case["seeds"])


def _error_ha(case: dict[str, Any], electronic: float) -> float:
    return float(electronic + case["e_nuc"] - case["reference"])


def test_tc_301b_isa_folding_scales_noise_exactly(h2_theta_star: dict[str, Any]) -> None:
    """A zajszorzó PONTOSAN a névleges λ: a kétqubites kapuk száma λ-szoros.

    Regressziós teszt a v0.7.0 hibájára: a logikai áramkör hajtogatása utáni
    ``optimization_level=3`` transzpilálás 4/10/16 CX-et adott (tényleges λ =
    1/2.5/4), így a Richardson-extrapoláció rossz abszcisszákkal dolgozott.
    """
    result = _zne(h2_theta_star, "zne_local", "richardson")
    meta = result.metadata
    assert meta["folding_level"] == "isa"
    counts = meta["two_qubit_gate_counts"]
    assert counts[0] > 0
    assert counts == [counts[0] * s for s in (1, 3, 5)]
    assert meta["effective_scale_factors"] == [1.0, 3.0, 5.0]


def test_tc_304_zne_bias_within_chemical_accuracy(h2_theta_star: dict[str, Any]) -> None:
    """A ZNE (Richardson, exp) RENDSZERES hibája kémiai pontosságon belül van.

    Egzakt zajos várható értékkel (precision=0) mérve: a nyers hiba nagy
    (FakeManilaV2: ~+27 mHa), a Richardson- és az exponenciális extrapoláció
    torzítása < 1.59 mHa. A lineáris modell a görbület miatt rosszabb — ez
    fizikai elvárás, és a teszt ezt is rögzíti.
    """
    from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA

    rich = _zne(h2_theta_star, "zne_local", "richardson")
    raw_err = _error_ha(h2_theta_star, rich.raw_energy)
    assert raw_err > 10 * CHEMICAL_ACCURACY_HA, f"a nyers zaj túl kicsi: {raw_err:.4e} Ha"

    rich_err = _error_ha(h2_theta_star, rich.mitigated_energy)
    exp_err = _error_ha(
        h2_theta_star, _zne(h2_theta_star, "zne_local", "exponential").mitigated_energy
    )
    lin_err = _error_ha(h2_theta_star, _zne(h2_theta_star, "zne_local", "linear").mitigated_energy)

    assert abs(rich_err) < CHEMICAL_ACCURACY_HA, f"Richardson torzítás: {rich_err:.4e} Ha"
    assert abs(exp_err) < CHEMICAL_ACCURACY_HA, f"exponenciális torzítás: {exp_err:.4e} Ha"
    assert abs(rich_err) < abs(lin_err) < abs(raw_err)


@pytest.mark.requires_mitiq
def test_tc_302_mitiq_cross_validation(h2_theta_star: dict[str, Any]) -> None:
    """Keresztvalidáció: a saját és a Mitiq-ZNE két független úton ugyanoda jut.

    A két út SZÁNDÉKOSAN eltér (ISA- vs. logikai szintű hajtogatás, ezért más
    fizikai qubitek és más nyers hiba), mégis: (1) a kétqubites kapuszámok
    egyeznek, (2) mindkét torzítás kémiai pontosságon belül van, (3) egymástól
    is kémiai pontosságon belül térnek el.
    """
    pytest.importorskip("mitiq", reason="a keresztvalidáció a mitiq csomagot igényli")
    from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA

    local = _zne(h2_theta_star, "zne_local", "richardson")
    mitiq_res = _zne(h2_theta_star, "zne_mitiq", "richardson")

    assert mitiq_res.metadata["two_qubit_gate_counts"] == local.metadata["two_qubit_gate_counts"]
    assert list(mitiq_res.scale_factors) == [1.0, 3.0, 5.0]
    # A skálázott energiák valódi mérések (a v0.7.0 a nyers értéket ismételte).
    assert len(set(mitiq_res.scaled_energies)) == 3

    local_err = _error_ha(h2_theta_star, local.mitigated_energy)
    mitiq_err = _error_ha(h2_theta_star, mitiq_res.mitigated_energy)
    assert abs(mitiq_err) < CHEMICAL_ACCURACY_HA
    assert abs(mitiq_err - local_err) < CHEMICAL_ACCURACY_HA


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
