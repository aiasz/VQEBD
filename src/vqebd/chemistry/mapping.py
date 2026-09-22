"""Fermion → qubit leképezés.

A második kvantált Hamilton-operátor fermionos keltő/eltüntető operátorokból áll,
amelyek **antikommutálnak**. A qubitek viszont Pauli-operátorokkal írhatók le,
amelyek különböző qubiteken **kommutálnak**. A leképezés feladata ennek az
eltérésnek az áthidalása.

Támogatott leképezések
----------------------
``jordan_wigner``
    A klasszikus leképezés [jordan1928]. Minden spin-pálya egy qubit. Az
    antikommutáció egy Pauli-Z „sztringgel" valósul meg, amelynek hossza a
    pályaindexszel nő — ez mély áramköröket eredményez nagy rendszereknél.

``parity``
    A részecskeszám paritását tárolja a qubitekben. Önmagában ugyanannyi qubitet
    igényel, mint a Jordan–Wigner, **de** a részecskeszám- és spin-megmaradás
    kihasználásával két qubit eltávolítható (``two_qubit_reduction``). H2-re ez
    4 qubit helyett 2-t jelent — a Fázis 1 alapértelmezése.

``bravyi_kitaev``
    Kompromisszum a pálya-foglaltság és a paritás tárolása között [bravyi2002],
    [seeley2012]: a Pauli-súly logaritmikusan nő a pályaszámmal.

**A három leképezésnek ugyanazt a spektrumot kell adnia.** Ez a Fázis 1 egyik
keresztvalidációs tesztje (AC-1.7).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vqebd.chemistry.problem import ElectronicStructure
from vqebd.config import MapperKind

__all__ = ["QubitHamiltonian", "build_mapper", "map_to_qubits"]


@dataclass(frozen=True, slots=True)
class QubitHamiltonian:
    """A qubit-térre leképezett Hamilton-operátor és a leképezés kontextusa.

    Attributes:
        operator: A Qiskit ``SparsePauliOp`` — az **elektronos** Hamilton-operátor.
            A magtaszítási energiát nem tartalmazza; azt konstansként kell hozzáadni.
        mapper: A Qiskit Nature mapper-objektum. Az ansatz-építéshez is kell, ezért
            megőrizzük — a ``HartreeFock`` és az ``UCCSD`` ugyanezt a leképezést
            kell hogy használja, különben az állapot és az operátor nem illeszkedik.
        kind: A leképezés azonosítója.
        two_qubit_reduction: Alkalmaztunk-e kétqubites redukciót.
        num_qubits: Az operátor qubit-száma.
        num_terms: A Pauli-tagok száma. A mérési költség ezzel arányos, ezért
            a benchmark szempontjából lényeges mennyiség.
        nuclear_repulsion_energy: A konstans magtaszítás (Ha), kényelmi másolat.
    """

    operator: Any
    mapper: Any
    kind: MapperKind
    two_qubit_reduction: bool
    num_qubits: int
    num_terms: int
    nuclear_repulsion_energy: float

    def summary(self) -> str:
        """Egysoros, naplóba illő összefoglaló."""
        suffix = " (2-qubit redukcióval)" if self.two_qubit_reduction else ""
        return f"{self.kind}{suffix}: {self.num_qubits} qubit, {self.num_terms} Pauli-tag"


def build_mapper(
    kind: MapperKind,
    num_particles: tuple[int, int],
    *,
    two_qubit_reduction: bool = True,
) -> Any:
    """A Qiskit Nature mapper-objektum létrehozása.

    Args:
        kind: A leképezés fajtája.
        num_particles: ``(alfa, béta)`` elektronszám. A paritás-leképezés
            kétqubites redukciójához szükséges.
        two_qubit_reduction: Csak ``parity`` esetén értelmezett. Más leképezésnél
            figyelmen kívül marad — ezt a hívó felelőssége dokumentálni.

    Returns:
        A mapper-objektum.

    Raises:
        ValueError: Ismeretlen leképezés esetén.
    """
    from qiskit_nature.second_q.mappers import (
        BravyiKitaevMapper,
        JordanWignerMapper,
        ParityMapper,
    )

    if kind == "jordan_wigner":
        return JordanWignerMapper()
    if kind == "bravyi_kitaev":
        return BravyiKitaevMapper()
    if kind == "parity":
        # A `num_particles` megadása kapcsolja be a kétqubites redukciót:
        # a mapper ekkor a megmaradó mennyiségek szektorába vetít.
        return ParityMapper(num_particles=num_particles) if two_qubit_reduction else ParityMapper()
    raise ValueError(f"ismeretlen leképezés: {kind!r}")


def map_to_qubits(
    structure: ElectronicStructure,
    kind: MapperKind = "parity",
    *,
    two_qubit_reduction: bool = True,
) -> QubitHamiltonian:
    """A fermionos Hamilton-operátor leképezése qubit-térre.

    Args:
        structure: Az elektronszerkezeti feladat.
        kind: A leképezés fajtája.
        two_qubit_reduction: Kétqubites redukció (csak ``parity`` esetén hat).

    Returns:
        A :class:`QubitHamiltonian`.
    """
    # A redukció csak paritás-leképezésnél értelmezett; ezt az eredményben is
    # őszintén tükrözzük, hogy a rekord ne állítson valótlant.
    effective_reduction = two_qubit_reduction and kind == "parity"

    mapper = build_mapper(kind, structure.num_particles, two_qubit_reduction=effective_reduction)
    operator = mapper.map(structure.second_q_op)

    return QubitHamiltonian(
        operator=operator,
        mapper=mapper,
        kind=kind,
        two_qubit_reduction=effective_reduction,
        num_qubits=int(operator.num_qubits),
        num_terms=len(operator),
        nuclear_repulsion_energy=structure.nuclear_repulsion_energy,
    )
