"""Cirq- és qsim-alapú energiakiértékelők.

Ugyanaz az interfész, mint a Qiskit-oldalon
(:class:`~vqebd.backends.estimators.EnergyEvaluator`), így a VQE optimalizáló-hurok
kódja **változatlan** marad — a platform cseréje pusztán más kiértékelő-objektumot
jelent (ADR-0002, ADR-0006).

Fontos különbség a két Cirq-alapú kiértékelő között
---------------------------------------------------
A ``cirq.Simulator`` ``complex128``, a ``qsimcirq.QSimSimulator`` viszont
**``complex64``** állapotvektorral dolgozik. Ez nem hiba, hanem tudatos
pontosság–sebesség kompromisszum a qsim oldalán: 24 qubiten ~22-szeres
gyorsulást ad, ~10⁻⁷ Ha hiba árán — ami négy nagyságrenddel a kémiai pontosság
alatt van.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from vqebd.backends.conversion import cirq_qubit_order
from vqebd.backends.estimators import EnergyEvaluator
from vqebd.config import BackendKind

__all__ = ["CirqEnergyEvaluator", "QsimEnergyEvaluator"]


class _CirqLikeEnergyEvaluator(EnergyEvaluator):
    """Közös alap a Cirq-kompatibilis szimulátorokhoz.

    A leszármazottak csak a szimulátor-objektumot és a backend-azonosítót adják meg.

    Args:
        circuit: Paraméterezett Qiskit-áramkör. A kiértékeléskor behelyettesítjük
            a paramétereket, majd transzpiláljuk és konvertáljuk.
        observable: A Qiskit ``SparsePauliOp`` Hamilton-operátor.
        seed_transpiler: A transzpiler seedje (ADR-0005).
    """

    def __init__(self, circuit: Any, observable: Any, *, seed_transpiler: int) -> None:
        import cirq

        from vqebd.backends.conversion import to_cirq_pauli_sum

        num_qubits = int(circuit.num_qubits)
        super().__init__(num_qubits=num_qubits)
        if int(observable.num_qubits) != num_qubits:
            raise ValueError(
                f"az áramkör ({num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )

        self._circuit = circuit
        self._seed_transpiler = seed_transpiler
        self._qubits = cirq.LineQubit.range(num_qubits)
        self._pauli_sum = to_cirq_pauli_sum(observable, self._qubits)
        # A Qiskit little-endian konvenciójához megfordított sorrend kell.
        self._qubit_order = cirq_qubit_order(self._qubits)
        self._simulator = self._make_simulator()

    def _make_simulator(self) -> Any:
        raise NotImplementedError

    def evaluate(self, parameters: Sequence[float]) -> float:
        import numpy as np

        from vqebd.backends.conversion import to_cirq_circuit, transpile_for_cirq

        bound = self._circuit.assign_parameters(list(parameters))
        transpiled = transpile_for_cirq(bound, seed_transpiler=self._seed_transpiler)
        converted = to_cirq_circuit(transpiled, self._qubits)
        values = self._simulator.simulate_expectation_values(
            converted, observables=[self._pauli_sum], qubit_order=self._qubit_order
        )
        return float(np.real(values[0]))

    def describe(self) -> dict[str, Any]:
        from vqebd.platforms import platform_of

        info = platform_of(self.kind)
        return {
            **super().describe(),
            "platform": info.platform,
            "precision": info.precision,
            "seed_transpiler": self._seed_transpiler,
        }


class CirqEnergyEvaluator(_CirqLikeEnergyEvaluator):
    """Google Cirq beépített szimulátora — egzakt, ``complex128``.

    Ez a Qiskit ``StatevectorEstimator`` **független implementációs párja**: azonos
    bemenetből azonos energiát kell adnia, ~10⁻¹⁵ Ha pontossággal.
    """

    @property
    def kind(self) -> BackendKind:
        return "cirq_simulator"

    def _make_simulator(self) -> Any:
        import cirq
        import numpy as np

        # A dtype explicit megadása fontos: enélkül a Cirq verziónként eltérő
        # alapértelmezést használhatna, ami a platformok összevetését rontaná el.
        return cirq.Simulator(dtype=np.complex128)


class QsimEnergyEvaluator(_CirqLikeEnergyEvaluator):
    """Google qsim — C++-ban optimalizált, **egyszeres pontosságú** szimulátor.

    A ``QSimOptions`` **nem** kínál pontosság-kapcsolót: a ``complex64`` beépített.
    Az ebből fakadó ~10⁻⁷ Ha hibát a :mod:`vqebd.platforms` tolerancia-táblája
    ismeri és elfogadja.

    A ``cpu_threads`` szándékosan 1: több szálon a lebegőpontos összegzés sorrendje
    futásonként változhatna, ami sértené az ADR-0005 bitre azonossági
    követelményét. **A determinizmus elsőbbséget élvez a sebességgel szemben.**
    """

    def __init__(
        self, circuit: Any, observable: Any, *, seed_transpiler: int, cpu_threads: int = 1
    ) -> None:
        self._cpu_threads = cpu_threads
        super().__init__(circuit, observable, seed_transpiler=seed_transpiler)

    @property
    def kind(self) -> BackendKind:
        return "qsim"

    def _make_simulator(self) -> Any:
        import qsimcirq

        return qsimcirq.QSimSimulator(
            qsim_options=qsimcirq.QSimOptions(cpu_threads=self._cpu_threads)
        )

    def describe(self) -> dict[str, Any]:
        return {**super().describe(), "cpu_threads": self._cpu_threads}
