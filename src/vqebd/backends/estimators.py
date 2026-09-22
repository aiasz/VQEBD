"""Energiakiértékelők — a VQE kvantumos oldala.

A VQE klasszikus optimalizáló-hurka egyetlen dolgot kér a kvantumos rétegtől:

.. code-block::

    θ  →  ⟨ψ(θ)| H |ψ(θ)⟩

Ez a modul ezt a leképezést csomagolja egy **hívható objektumba**. Az absztrakció
haszna, hogy a VQE-hurok kódja azonos marad, akárhol fut a kiértékelés:

=====================  =========================================  ==========
``BackendKind``        Kiértékelés                                Fázis
=====================  =========================================  ==========
``statevector``        Zajmentes állapotvektor (egzakt)           1
``aer_shot``           Véges lövésszám, zaj nélkül                1b
``aer_noisy``          Zajos szimuláció valós kalibrációval       1b
``ibm_qpu``            Valódi IBM kvantumprocesszor               2
=====================  =========================================  ==========

A Fázis 1 csak a ``statevector`` változatot valósítja meg; a többi a megfelelő
fázisban kerül ide, változatlan interfésszel.

Miért V2 primitív?
------------------
A Qiskit 2.0 eltávolította a V1 primitíveket. A V2 primitívek (``StatevectorEstimator``,
``BackendEstimatorV2``, ``EstimatorV2``) a Qiskit 1.4-ben és 2.x-ben egyaránt
léteznek, így az itt írt kód **előre-hordozható** (ADR-0002).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from vqebd.config import BackendKind
from vqebd.seeds import SeedSet

__all__ = ["EnergyEvaluator", "StatevectorEnergyEvaluator", "make_energy_evaluator"]


class EnergyEvaluator(ABC):
    """Egy paraméter-vektorhoz energiát rendelő, hívható objektum.

    A hívások számát magában tartja nyilván (``call_count``), mert a
    célfüggvény-kiértékelések száma a VQE egyik legfontosabb költségmutatója —
    valódi hardveren ez fordul le közvetlenül QPU-időre.
    """

    def __init__(self, num_qubits: int) -> None:
        self.num_qubits = num_qubits
        self.call_count = 0

    def __call__(self, parameters: Sequence[float]) -> float:
        """Az elektronos energia várható értéke a megadott paramétereknél (Ha).

        A magtaszítási energiát **nem** tartalmazza: azt a hívó adja hozzá.
        """
        self.call_count += 1
        return self.evaluate(parameters)

    @abstractmethod
    def evaluate(self, parameters: Sequence[float]) -> float:
        """A tényleges kiértékelés. Leszármazottak ezt írják felül."""

    @property
    @abstractmethod
    def kind(self) -> BackendKind:
        """A backend azonosítója az adatsémához."""

    def describe(self) -> dict[str, Any]:
        """A kiértékelő paraméterei az eredményrekordhoz."""
        return {"backend": self.kind, "num_qubits": self.num_qubits}


class StatevectorEnergyEvaluator(EnergyEvaluator):
    """Qiskit: zajmentes, egzakt kiértékelés állapotvektorral (``complex128``).

    Nincs sem lövészaj, sem hardverzaj: a várható érték a gépi pontosság határáig
    egzakt. Ez az **L2 referenciaszint** — az ansatz korlátait mutatja meg, minden
    más hibaforrás nélkül.
    """

    def __init__(self, circuit: Any, observable: Any) -> None:
        from qiskit.primitives import StatevectorEstimator

        super().__init__(num_qubits=int(circuit.num_qubits))
        if int(observable.num_qubits) != self.num_qubits:
            raise ValueError(
                f"az áramkör ({self.num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )
        self._circuit = circuit
        self._observable = observable
        self._estimator = StatevectorEstimator()

    @property
    def kind(self) -> BackendKind:
        return "qiskit_statevector"

    def evaluate(self, parameters: Sequence[float]) -> float:
        # A V2 primitív „PUB" formátuma: (áramkör, observable, paraméterek).
        job = self._estimator.run([(self._circuit, self._observable, list(parameters))])
        return float(job.result()[0].data.evs)


def make_energy_evaluator(
    kind: BackendKind,
    circuit: Any,
    observable: Any,
    seeds: SeedSet,
) -> EnergyEvaluator:
    """Energiakiértékelő létrehozása a kért platform-backendhez.

    A VQE-hurok szempontjából mindegy, melyiket kapja: az interfész azonos
    (ADR-0002). Ez teszi lehetővé, hogy ugyanaz a kód fusson mindhárom platformon.

    Args:
        kind: A platform-backend azonosítója.
        circuit: A paraméterezett ansatz-áramkör (Qiskit).
        observable: A qubit-Hamilton-operátor (Qiskit ``SparsePauliOp``).
        seeds: A seed-készlet. A ``qiskit_statevector`` kiértékelés egzakt és
            determinisztikus, ezért nem használ seedet; a Cirq-alapú backendek
            viszont **transzpilálnak**, és ahhoz kell a ``seed_transpiler``
            (ADR-0005: a SABRE-alapú lépések sztochasztikusak).

    Returns:
        A kiértékelő.

    Raises:
        ValueError: Ismeretlen backend esetén.
    """
    if kind == "qiskit_statevector":
        return StatevectorEnergyEvaluator(circuit, observable)

    # Késleltetett import: a Cirq-réteg csak akkor töltődik be, ha tényleg kell.
    if kind == "cirq_simulator":
        from vqebd.backends.cirq_estimators import CirqEnergyEvaluator

        return CirqEnergyEvaluator(circuit, observable, seed_transpiler=seeds.transpiler)

    if kind == "qsim":
        from vqebd.backends.cirq_estimators import QsimEnergyEvaluator

        return QsimEnergyEvaluator(circuit, observable, seed_transpiler=seeds.transpiler)

    # A típusellenőrző szerint ez elérhetetlen (a BackendKind kimerítő), de
    # futásidőben érkezhet érvénytelen string is — ezért maradjon a védelem.
    from vqebd.platforms import PLATFORMS

    raise ValueError(f"ismeretlen backend: {kind!r}. Ismert backendek: {sorted(PLATFORMS)}")
