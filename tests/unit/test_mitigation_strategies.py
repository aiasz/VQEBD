"""Hibaenyhítési stratégiák egységtesztjei (AC-3.5, AC-3.6, ADR-0003).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from vqebd.backends.estimators import StatevectorEnergyEvaluator
from vqebd.mitigation import (
    NoMitigation,
    ZneLocalMitigation,
    get_mitigation_strategy,
)
from vqebd.seeds import SeedSet

pytestmark = pytest.mark.unit


def test_get_mitigation_strategy_factory() -> None:
    """A gyárfüggvény a kért stratégiát példányosítja."""
    assert isinstance(get_mitigation_strategy("none"), NoMitigation)
    assert isinstance(get_mitigation_strategy("zne_local"), ZneLocalMitigation)
    with pytest.raises(ValueError, match="ismeretlen"):
        get_mitigation_strategy("nincs_ilyen")


def test_no_mitigation_strategy() -> None:
    """A NoMitigation a nyers értéket adja vissza."""
    strat = NoMitigation()
    assert strat.name == "none"

    evaluator = MagicMock()
    evaluator.evaluate.return_value = -1.137
    res = strat.execute(None, None, evaluator, [0.0], SeedSet.derive(42))

    assert res.mitigated_energy == -1.137
    assert res.raw_energy == -1.137
    assert res.scale_factors == (1.0,)
    assert res.scaled_energies == (-1.137,)
    assert res.strategy_name == "none"


def test_zne_local_mitigation_on_statevector() -> None:
    """Zajmentes állapotvektoron a ZNE minden skálán azonos egzakt értéket ad."""
    qc = QuantumCircuit(2)
    qc.x(1)
    op = SparsePauliOp(["ZI"])
    seeds = SeedSet.derive(42)

    evaluator = StatevectorEnergyEvaluator(qc, op)
    strat = ZneLocalMitigation(scale_factors=(1, 3, 5), extrapolator="richardson")

    res = strat.execute(qc, op, evaluator, [], seeds)
    assert res.strategy_name == "zne_local"
    assert res.extrapolator_name == "richardson"
    assert len(res.scale_factors) == 3
    assert len(res.scaled_energies) == 3
    # Mivel állapotvektor, nincs zaj: E(1)=E(3)=E(5)=-1.0
    for val in res.scaled_energies:
        assert val == pytest.approx(-1.0)
    assert res.mitigated_energy == pytest.approx(-1.0)


def test_mitiq_optional_isolation() -> None:
    """A mitiq hiánya nem töri el a zne_local stratégiát."""
    strat = get_mitigation_strategy("zne_local")
    assert strat.name == "zne_local"

    # Ha a mitiq nincs telepítve, a zne_mitiq ImportError-t dob
    with patch.dict("sys.modules", {"mitiq": None}):
        mitiq_strat = get_mitigation_strategy("zne_mitiq")
        evaluator = MagicMock()
        with pytest.raises(ImportError, match="mitiq"):
            mitiq_strat.execute(None, None, evaluator, [], SeedSet.derive(42))
