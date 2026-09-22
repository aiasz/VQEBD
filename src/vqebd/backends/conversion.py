"""Qiskit → Cirq konverzió: Hamilton-operátor és áramkör.

A többplatformos validáció (ADR-0006) alapelve, hogy a fizikai feladat
**egyetlen helyen** születik (PySCF + Qiskit Nature), és onnan konvertálódik a
másik platformra. Így a platformok közti eltérés kizárólag a **szimulátorból**
származhat, nem a bemenetből.

A két kritikus pont
-------------------

**1. Qubit-sorrend (endianness).**
A Qiskit little-endian: a Pauli-címke *jobb szélső* karaktere a 0. qubit, és a
``to_matrix()`` a 0. qubitet tekinti a legkisebb helyiértéknek. A Cirq viszont a
``qubit_order`` lista *elején* álló qubitet tekinti a legnagyobb helyiértékűnek.

A mátrixegyezéshez tehát a Cirq oldalán **megfordított** qubit-sorrend kell.
Mért bizonyíték (H2, 2 qubit, 5 Pauli-tag):

===============================  ==========================
``PauliSum.matrix()`` sorrendje  ``max|M_cirq − M_qiskit|``
===============================  ==========================
``[q0, q1]`` (egyenes)           1.59
``[q1, q0]`` (**fordított**)     **0.00**
===============================  ==========================

Ez a projekt egyik legveszélyesebb rejtett hibaforrása: szimmetrikus
Hamilton-operátoron a rossz sorrend **véletlenül helyes energiát is adhat**.
Ezért a konverziót **mátrixszinten** validáljuk, nem energiaszinten.

**2. Szélességmegőrzés.**
A Mitiq QASM-alapú konverziója eldobja azokat a qubiteket, amelyeken nincs
művelet (TR-000, M3). Ezt a hibát itt nem ismételjük meg: minden qubitre
``cirq.I`` kerül, így az áramkör szélessége megmarad.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final

__all__ = [
    "CIRQ_BASIS_GATES",
    "cirq_qubit_order",
    "to_cirq_circuit",
    "to_cirq_pauli_sum",
    "transpile_for_cirq",
]

CIRQ_BASIS_GATES: Final[tuple[str, ...]] = ("rz", "ry", "rx", "h", "x", "sx", "cx", "cz")
"""A konverter által ismert kapukészlet.

Szándékosan szűk és explicit. A Qiskit-áramkört előbb erre a bázisra
transzpiláljuk; ismeretlen kapu esetén a konverter **azonnal hibát dob**, nem
hagyja ki némán.
"""

# Fizikai hatás nélküli utasítások a zajmentes szimulációban.
_IGNORED_INSTRUCTIONS: Final[frozenset[str]] = frozenset({"barrier", "id", "delay"})


def cirq_qubit_order(qubits: Sequence[Any]) -> list[Any]:
    """A Qiskit little-endian konvenciójának megfelelő Cirq qubit-sorrend.

    Minden olyan Cirq-hívásnál ezt kell átadni ``qubit_order`` (vagy ``qubits``)
    paraméterként, amely mátrixot vagy állapotvektort állít elő — különben a
    helyiértékek felcserélődnek.

    Args:
        qubits: A qubitek a 0. indextől növekvő sorrendben.

    Returns:
        A megfordított lista.
    """
    return list(reversed(list(qubits)))


def to_cirq_pauli_sum(operator: Any, qubits: Sequence[Any]) -> Any:
    """Qiskit ``SparsePauliOp`` → ``cirq.PauliSum``.

    Args:
        operator: A Qiskit ``SparsePauliOp``.
        qubits: Cirq qubitek, a 0. indextől növekvő sorrendben. Hosszának meg kell
            egyeznie az operátor qubit-számával.

    Returns:
        A ``cirq.PauliSum``.

    Raises:
        ValueError: Ha a qubitek száma nem egyezik, vagy a Pauli-címke ismeretlen
            karaktert tartalmaz.
    """
    import cirq

    n = int(operator.num_qubits)
    if len(qubits) != n:
        raise ValueError(
            f"a megadott qubitek száma ({len(qubits)}) nem egyezik az operátoréval ({n})"
        )

    table = {"X": cirq.X, "Y": cirq.Y, "Z": cirq.Z}
    total = cirq.PauliSum()
    for pauli, coefficient in zip(operator.paulis, operator.coeffs, strict=True):
        label = pauli.to_label()
        factors: dict[Any, Any] = {}
        # A Qiskit-címke little-endian: a JOBB szélső karakter a 0. qubit.
        # A `reversed` ezért a karakterindexet közvetlenül qubit-indexszé teszi.
        for index, character in enumerate(reversed(label)):
            if character == "I":
                continue
            gate = table.get(character)
            if gate is None:
                raise ValueError(
                    f"ismeretlen Pauli-karakter a(z) {label!r} címkében: {character!r}"
                )
            factors[qubits[index]] = gate
        total += cirq.PauliString(factors, coefficient=complex(coefficient))
    return total


def transpile_for_cirq(circuit: Any, *, seed_transpiler: int, optimization_level: int = 1) -> Any:
    """Qiskit-áramkör transzpilálása a :data:`CIRQ_BASIS_GATES` készletre.

    A konverzió előfeltétele: a konverter csak ezt a szűk kapukészletet ismeri.

    Args:
        circuit: A Qiskit-áramkör (paraméterek már behelyettesítve).
        seed_transpiler: A transzpiler seedje (ADR-0005 — a SABRE-alapú lépések
            sztochasztikusak, seed nélkül más áramkör születne futásonként).
        optimization_level: A Qiskit transzpiler optimalizálási szintje.

    Returns:
        A transzpilált áramkör.
    """
    from qiskit import transpile

    return transpile(
        circuit,
        basis_gates=list(CIRQ_BASIS_GATES),
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )


def to_cirq_circuit(circuit: Any, qubits: Sequence[Any]) -> Any:
    """Qiskit ``QuantumCircuit`` → ``cirq.Circuit``, szélességmegőrzéssel.

    A bemeneti áramkörnek a :data:`CIRQ_BASIS_GATES` kapukészletben kell lennie
    (lásd :func:`transpile_for_cirq`).

    A globális fázist **nem** visszük át: az energia (``⟨ψ|H|ψ⟩``) fázisinvariáns.
    Az állapotvektorokat ezért abszolút átfedéssel kell összehasonlítani.

    Args:
        circuit: A transzpilált Qiskit-áramkör.
        qubits: Cirq qubitek, a 0. indextől növekvő sorrendben.

    Returns:
        A ``cirq.Circuit``.

    Raises:
        ValueError: Ha a qubitek száma nem egyezik, vagy ismeretlen kapu fordul elő.
    """
    import cirq

    if len(qubits) != circuit.num_qubits:
        raise ValueError(
            f"a megadott qubitek száma ({len(qubits)}) nem egyezik az áramköréval "
            f"({circuit.num_qubits})"
        )

    converted = cirq.Circuit()
    # Minden qubitre azonosságot teszünk, hogy az inaktív qubitek se vesszenek el
    # (a Mitiq QASM-alapú konverziója pont ezt rontja el — TR-000, M3).
    converted.append(cirq.I.on_each(*qubits), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    index = {bit: position for position, bit in enumerate(circuit.qubits)}
    for instruction in circuit.data:
        name = instruction.operation.name
        if name in _IGNORED_INSTRUCTIONS:
            continue
        targets = [qubits[index[bit]] for bit in instruction.qubits]
        params = [float(value) for value in instruction.operation.params]

        if name == "rz":
            converted.append(cirq.rz(params[0]).on(targets[0]))
        elif name == "ry":
            converted.append(cirq.ry(params[0]).on(targets[0]))
        elif name == "rx":
            converted.append(cirq.rx(params[0]).on(targets[0]))
        elif name == "h":
            converted.append(cirq.H.on(targets[0]))
        elif name == "x":
            converted.append(cirq.X.on(targets[0]))
        elif name == "sx":
            # sqrt(X) — a Qiskit `sx` kapuja a cirq XPowGate(exponent=0.5)
            converted.append(cirq.XPowGate(exponent=0.5).on(targets[0]))
        elif name == "cx":
            converted.append(cirq.CNOT.on(targets[0], targets[1]))
        elif name == "cz":
            converted.append(cirq.CZ.on(targets[0], targets[1]))
        else:
            raise ValueError(
                f"a konverter nem ismeri a(z) {name!r} kaput. "
                f"Ismert kapuk: {sorted(CIRQ_BASIS_GATES)} (+ figyelmen kívül hagyott: "
                f"{sorted(_IGNORED_INSTRUCTIONS)}). "
                "Transzpiláld az áramkört a CIRQ_BASIS_GATES készletre, vagy bővítsd "
                "a leképezést — néma kihagyás NEM megengedett."
            )
    return converted
