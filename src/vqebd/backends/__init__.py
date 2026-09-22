"""Backend-absztrakció: hol és hogyan értékeljük ki az energiát.

A VQE klasszikus hurka egyetlen dolgot kér a kvantumos rétegtől:
``θ → ⟨ψ(θ)|H|ψ(θ)⟩``. Ez a réteg ezt a leképezést csomagolja hívható objektumba,
így a hurok kódja azonos marad egzakt állapotvektoron, véges lövésszámmal, zajos
szimulátoron és valódi QPU-n is.

Fázis 1M: három egzakt platform — ``qiskit_statevector``, ``cirq_simulator``
és ``qsim`` (ADR-0006). A zajos és hardveres backendek a Fázis 1b-ben és 2-ben
kerülnek ide, változatlan interfésszel.

A ``conversion`` modul a Qiskit → Cirq átalakítást végzi; a legkritikusabb
pontja a **qubit-sorrend** (endianness), amelyet mátrixszintű teszt őriz.
"""

from __future__ import annotations

from vqebd.backends.conversion import (
    CIRQ_BASIS_GATES,
    cirq_qubit_order,
    to_cirq_circuit,
    to_cirq_pauli_sum,
    transpile_for_cirq,
)
from vqebd.backends.estimators import (
    EnergyEvaluator,
    StatevectorEnergyEvaluator,
    make_energy_evaluator,
)

__all__ = [
    "CIRQ_BASIS_GATES",
    "EnergyEvaluator",
    "StatevectorEnergyEvaluator",
    "cirq_qubit_order",
    "make_energy_evaluator",
    "to_cirq_circuit",
    "to_cirq_pauli_sum",
    "transpile_for_cirq",
]
