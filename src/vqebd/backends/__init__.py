"""Backend-absztrakció: hol és hogyan értékeljük ki az energiát.

A VQE klasszikus hurka egyetlen dolgot kér a kvantumos rétegtől:
``θ → ⟨ψ(θ)|H|ψ(θ)⟩``. Ez a réteg ezt a leképezést csomagolja hívható objektumba,
így a hurok kódja azonos marad egzakt állapotvektoron, véges lövésszámmal, zajos
szimulátoron és valódi QPU-n is.

Fázis 1: csak ``statevector``. A további backendek a Fázis 1b-ben és 2-ben
kerülnek ide, változatlan interfésszel.
"""

from __future__ import annotations

from vqebd.backends.estimators import (
    EnergyEvaluator,
    StatevectorEnergyEvaluator,
    make_energy_evaluator,
)

__all__ = [
    "EnergyEvaluator",
    "StatevectorEnergyEvaluator",
    "make_energy_evaluator",
]
