"""Fázis 5 — batch és statisztikai módszertan validáció (AC-5.5, AC-5.6, AC-5.8).

Ez a modul a phase_05.md 3. fejezetének („hozzájárul-e a több teszt a
pontossághoz?”) **mért** válaszát rögzíti tesztként:

- az ismétlés a statisztikus hibát N^−½ szerint csökkenti (AC-5.6);
- a torzítást az ismétlés nem csökkenti (AC-5.6);
- a független újramintavételezés torzítatlan végső energiát ad (AC-5.8).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("qiskit_aer", reason="a Fázis 5 statisztika Aer szimulátort igényel")

from vqebd.backends.estimators import AerNoisyEnergyEvaluator, AerShotEnergyEvaluator
from vqebd.batch import aggregate_rows, get_preset, run_batch
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import AnsatzSpec, OptimizerSpec, VQEConfig
from vqebd.seeds import SeedSet
from vqebd.stats import block_mean_spread, loglog_slope, summarize
from vqebd.storage import Database
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation

_COMPARED = ("run_id", "energy_ha", "reestimate_mean_ha", "optimal_parameters_json")


def _snapshot(db: Database, batch_id: str) -> list[tuple[Any, ...]]:
    return [tuple(row[k] for k in _COMPARED) for row in db.batch_results(batch_id)]


def test_ac_5_5_resumed_batch_equals_uninterrupted(tmp_path: Path) -> None:
    """AC-5.5: megszakított, majd folytatott batch = megszakítás nélküli futás (bitre)."""
    spec = get_preset("f5-smoke")
    with Database(tmp_path / "resumed.sqlite") as db:
        partial = run_batch(spec, db, max_runs=2)
        assert len(partial.completed) == 2 and partial.remaining == spec.total_runs - 2
        rest = run_batch(spec, db)
        assert len(rest.skipped) == 2
        assert len(rest.completed) == spec.total_runs - 2
        assert not rest.failed
        resumed = _snapshot(db, spec.batch_id)
    with Database(tmp_path / "straight.sqlite") as db:
        run_batch(spec, db)
        straight = _snapshot(db, spec.batch_id)
    assert resumed == straight
    assert len(straight) == spec.total_runs


def test_aggregation_of_smoke_batch(tmp_path: Path) -> None:
    """A csoportosítás: egzakt csoport 'confirmed', a zajos csoport N=3 ismétlése egy csoport."""
    spec = get_preset("f5-smoke")
    with Database(tmp_path / "a.sqlite") as db:
        run_batch(spec, db)
        groups = aggregate_rows(db.batch_results(spec.batch_id))
    by_backend = {(g.backend, g.bond_length): g for g in groups}
    exact = by_backend[("qiskit_statevector", 0.735)]
    assert exact.n == 1 and exact.accuracy == "confirmed"
    noisy = by_backend[("qiskit_aer_shot", 0.735)]
    assert noisy.n == 3
    assert noisy.selection_bias is not None
    assert noisy.budget is not None and noisy.budget.noise_bias is not None
    # A költségvetés teleszkópikus: a tagok összege a teljes hiba.
    b = noisy.budget
    parts = [b.mapping, b.ansatz, b.noise_bias]
    assert all(p is not None for p in parts)
    assert b.total == pytest.approx(sum(p for p in parts if p is not None), abs=1e-12)


@pytest.fixture(scope="module")
def h2_optimum() -> dict[str, Any]:
    result = run_vqe(VQEConfig(molecule=h2()))
    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(20260925)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(), seeds)
    return {
        "theta": list(result.optimal_parameters),
        "l2": result.energy,
        "offset": hamiltonian.energy_offset,
        "circuit": ansatz.circuit,
        "observable": hamiltonian.operator,
        "seeds": seeds,
    }


def test_ac_5_6_repetition_reduces_statistical_error_as_inverse_sqrt_n(
    h2_optimum: dict[str, Any],
) -> None:
    """AC-5.6: valódi Aer-mintákon a blokkátlagok szórása ∝ N^−½ (meredekség −0.5 ± 0.15)."""
    case = h2_optimum
    evaluator = AerShotEnergyEvaluator(case["circuit"], case["observable"], case["seeds"])
    samples = [evaluator.evaluate(case["theta"]) for _ in range(512)]
    sizes = [1, 2, 4, 8, 16, 32]
    spread = block_mean_spread(samples, sizes)
    slope = loglog_slope(sizes, [spread[n] for n in sizes])
    assert slope == pytest.approx(-0.5, abs=0.15)


def test_ac_5_6_repetition_does_not_remove_bias(h2_optimum: dict[str, Any]) -> None:
    """AC-5.6: a zaj okozta torzítás N-től független — ismétléssel nem tűnik el.

    FakeManilaV2 zajmodell mellett a θ*-beli várható érték ~27 mHa-val az L2
    fölött van. Az átlag N = 16 és N = 256 mintára is ugyanezt a torzítást
    becsli (4 SEM-en belül), miközben a torzítás a SEM sokszorosa.
    """
    case = h2_optimum
    evaluator = AerNoisyEnergyEvaluator(case["circuit"], case["observable"], case["seeds"])
    samples = [evaluator.evaluate(case["theta"]) + case["offset"] - case["l2"] for _ in range(256)]
    small, large = summarize(samples[:16]), summarize(samples)
    assert large.mean > 10 * large.sem  # a torzítás messze a statisztikus hiba fölött
    assert abs(small.mean - large.mean) < 4 * small.sem
    assert large.mean > 0.015  # > 15 mHa: nem tűnt el


@pytest.mark.parametrize("backend", ["qiskit_aer_shot", "qiskit_aer_noisy"])
def test_ac_5_8_reestimated_energy_is_unbiased(backend: str) -> None:
    """AC-5.8: az újramintavételezett végső energia torzítatlan becslése a θ_opt-beli értéknek.

    Referencia: ugyanabban a θ_opt pontban a zajmodell szerinti EGZAKT várható
    érték (``precision=0``). Az újramintavételezett átlag ettől < 4 SEM-re van.
    """
    config = VQEConfig(
        molecule=h2(),
        backend=backend,  # type: ignore[arg-type]
        optimizer=OptimizerSpec(method="COBYLA", maxiter=60),
        reestimate=32,
    )
    result = run_vqe(config)
    assert result.reestimate is not None and result.reestimate.n == 32
    assert result.energy == pytest.approx(result.reestimate.mean_ha)

    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(config.seed)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(), seeds)
    cls = AerShotEnergyEvaluator if backend == "qiskit_aer_shot" else AerNoisyEnergyEvaluator
    exact = cls(ansatz.circuit, hamiltonian.operator, seeds, precision=0.0).evaluate(
        list(result.optimal_parameters)
    )
    exact_total = exact + hamiltonian.energy_offset
    assert abs(result.reestimate.mean_ha - exact_total) < 4 * result.reestimate.sem_ha


def test_reestimate_config_validation() -> None:
    with pytest.raises(ValueError, match="legalább 2"):
        VQEConfig(molecule=h2(), reestimate=1)
    with pytest.raises(ValueError, match="negatív"):
        VQEConfig(molecule=h2(), reestimate=-1)
