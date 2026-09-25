"""Fázis 5 — batch-specifikáció és kifejtés egységtesztjei (AC-5.4, TP-F05).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

from vqebd.batch import BatchCell, BatchSpec, expand, get_preset, run_batch
from vqebd.batch.spec import PRESETS
from vqebd.chemistry.molecule import h2
from vqebd.config import OptimizerSpec
from vqebd.storage import Database

pytestmark = pytest.mark.unit


def test_expand_is_deterministic() -> None:
    """AC-5.4: azonos spec → bitre azonos futáslista és azonosítók."""
    first = [(r.run_id, r.config.fingerprint()) for r in expand(get_preset("f5-statistical"))]
    second = [(r.run_id, r.config.fingerprint()) for r in expand(get_preset("f5-statistical"))]
    assert first == second
    assert len({rid for rid, _ in first}) == len(first)


def test_repeats_differ_only_in_seed() -> None:
    """Egy cella ismétlései csak a seedben térnek el (master_seed + ismétlés)."""
    runs = [r for r in expand(get_preset("f5-smoke")) if r.cell_index == 2]
    assert [r.repeat_index for r in runs] == [0, 1, 2]
    assert [r.config.seed for r in runs] == [20260922, 20260923, 20260924]
    base = runs[0].config
    for r in runs[1:]:
        assert r.config.molecule == base.molecule
        assert r.config.backend == base.backend
        assert r.config.reestimate == base.reestimate


@pytest.mark.parametrize(
    ("preset", "expected_runs"),
    [("f5-deterministic", 50), ("f5-statistical", 180), ("f5-smoke", 5)],
)
def test_preset_sizes_match_plan(preset: str, expected_runs: int) -> None:
    """A preset-ek mérete a phase_05.md 6. fejezetével egyezik."""
    spec = get_preset(preset)
    assert spec.total_runs == expected_runs
    assert len(expand(spec)) == expected_runs


def test_unknown_preset_lists_known_ones() -> None:
    with pytest.raises(ValueError, match="ismertek: " + ", ".join(sorted(PRESETS))):
        get_preset("nincs-ilyen")


def test_exact_backend_rejects_repeats() -> None:
    """Negatív: egzakt backenden az ismétlés bitre azonos eredményt adna."""
    with pytest.raises(ValueError, match="egzakt"):
        BatchCell(h2(), "qiskit_statevector", OptimizerSpec(), repeats=2)


def test_invalid_cell_and_spec_are_rejected() -> None:
    with pytest.raises(ValueError, match="ismétlésszám"):
        BatchCell(h2(), "qiskit_aer_shot", OptimizerSpec(method="COBYLA"), repeats=0)
    cell = BatchCell(h2(), "qiskit_statevector", OptimizerSpec())
    with pytest.raises(ValueError, match="batch_id"):
        BatchSpec(batch_id="a:b", description="", cells=(cell,))
    with pytest.raises(ValueError, match="cellát"):
        BatchSpec(batch_id="ures", description="", cells=())


def test_duplicate_cells_are_rejected() -> None:
    cell = BatchCell(h2(), "qiskit_statevector", OptimizerSpec())
    with pytest.raises(ValueError, match="duplikált"):
        expand(BatchSpec(batch_id="dup", description="", cells=(cell, cell)))


def test_hardware_batch_requires_explicit_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kvótavédelem: ibm_qpu cella csak VQEBD_ALLOW_HARDWARE=true mellett indul."""
    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    spec = BatchSpec(
        batch_id="hw",
        description="",
        cells=(BatchCell(h2(), "ibm_qpu", OptimizerSpec(method="COBYLA")),),
    )
    with Database(":memory:") as db, pytest.raises(PermissionError, match="VQEBD_ALLOW_HARDWARE"):
        run_batch(spec, db)
