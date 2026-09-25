"""Unitáris áramkör-hajtogatás egységtesztjei (AC-3.1, ADR-0003).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest
from qiskit.circuit import QuantumCircuit

from vqebd.mitigation.folding import count_two_qubit_gates, fold_global_unitary

pytestmark = pytest.mark.unit


def _sample_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.rz(0.5, 1)
    qc.cx(0, 1)
    return qc


def test_fold_global_unitary_lambda_1() -> None:
    """λ=1 esetén az áramkör műveleteinek száma változatlan."""
    qc = _sample_circuit()
    folded = fold_global_unitary(qc, 1)
    assert len(folded.data) == len(qc.data)
    assert count_two_qubit_gates(folded) == count_two_qubit_gates(qc)


@pytest.mark.parametrize("scale", [3, 5, 7])
def test_fold_global_unitary_scales_two_qubit_gates(scale: int) -> None:
    """A kétqubites kapuk száma pontosan λ-szorosára növekszik."""
    qc = _sample_circuit()
    base_2q = count_two_qubit_gates(qc)
    assert base_2q == 2

    folded = fold_global_unitary(qc, scale)
    assert count_two_qubit_gates(folded) == scale * base_2q


def test_fold_global_preserves_layout() -> None:
    """A layout attribútum megmarad a hajtogatás után."""
    qc = _sample_circuit()
    qc._layout = "dummy_layout"
    folded = fold_global_unitary(qc, 3)
    assert folded.layout == "dummy_layout"


@pytest.mark.parametrize("invalid_scale", [0, -1, -3, 2, 4, 6])
def test_fold_global_rejects_invalid_scale(invalid_scale: int) -> None:
    """Nem pozitív vagy páros skálafaktor esetén ValueError keletkezik."""
    qc = _sample_circuit()
    with pytest.raises(ValueError, match="skálafaktor"):
        fold_global_unitary(qc, invalid_scale)
