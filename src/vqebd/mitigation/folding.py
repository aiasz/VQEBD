"""Unitáris áramkör-hajtogatás (Unitary Folding) a ZNE zajskálázásához (ADR-0003).

A ZNE zajskálázása a Giurgica-Tiron et al. [giurgicatiron2020] szerinti globális
unitáris hajtogatáson alapul:
    U → U (U† U)^n,  ahol  λ = 2n + 1 (páratlan pozitív egész).

Ez az implementáció **ISA- és layout-biztos**:
1. Megőrzi a fizikai qubit-számot, regiszterneveket és a ``layout`` attribútumot
   (elkerülve a Mitiq M3-as hibáját).
2. A kétqubites kapuk száma szigorúan λ-szorosára növekszik.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit

__all__ = ["count_two_qubit_gates", "fold_global_unitary"]

# Tipikus kétqubites kapuk a standard és hardveres bázisokban
_TWO_QUBIT_GATES: frozenset[str] = frozenset(
    {"cx", "ecr", "cz", "swap", "iswap", "rzz", "ryy", "rxx", "rzx", "crx", "cry", "crz"}
)


def count_two_qubit_gates(circuit: QuantumCircuit) -> int:
    """Megszámolja a kétqubites kapukat az áramkörben."""
    count = 0
    for instruction in circuit.data:
        op = instruction.operation
        if op.name in _TWO_QUBIT_GATES or len(instruction.qubits) == 2:
            count += 1
    return count


def fold_global_unitary(circuit: QuantumCircuit, scale_factor: int) -> QuantumCircuit:
    """Globális unitáris hajtogatás végrehajtása az áramkörön.

    Args:
        circuit: A hajtogatandó Qiskit áramkör (lehet logikai vagy ISA).
        scale_factor: A zajszorzó (\\lambda), amelynek pozitív páratlan egésznek
            kell lennie (1, 3, 5, ...).

    Returns:
        A meghajtogatott :class:`QuantumCircuit`, amely megőrzi az eredeti
        regisztereket és a layout-információt.

    Raises:
        ValueError: Ha a skálafaktor nem pozitív páratlan egész.
    """
    if scale_factor < 1:
        raise ValueError(f"a skálafaktornak legalább 1-nek kell lennie, kapott: {scale_factor}")
    if scale_factor % 2 != 1:
        raise ValueError(
            f"a unitáris hajtogatás páratlan egész skálafaktort igényel (1, 3, 5, ...), "
            f"kapott: {scale_factor}"
        )

    if scale_factor == 1:
        # λ=1 esetén a másolat elegendő
        return circuit.copy()

    n = (scale_factor - 1) // 2
    inv_circuit = circuit.inverse()

    # Új áramkör létrehozása azonos regiszterekkel és névvel
    name = f"{circuit.name}_folded_{scale_factor}"
    folded = QuantumCircuit(*circuit.qregs, *circuit.cregs, name=name)

    # 1. Alapáramkör: U
    folded.compose(circuit, inplace=True)

    # 2. n-szer hozzáfűzzük a (U† U) blokkot
    for _ in range(n):
        folded.compose(inv_circuit, inplace=True)
        folded.compose(circuit, inplace=True)

    # Layout és metaadatok megőrzése az ISA kompatibilitáshoz
    if hasattr(circuit, "layout") and circuit.layout is not None:
        folded._layout = circuit.layout

    return folded
