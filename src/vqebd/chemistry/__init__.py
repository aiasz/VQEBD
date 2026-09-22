"""Elektronszerkezeti réteg: molekula → fermionos → qubit-Hamilton-operátor.

A réteg a PySCF-re és a Qiskit Nature-re épül, de azokat **típusos burkolókba**
zárja, hogy a kódbázis többi része statikusan ellenőrizhető maradjon, és hogy a
Qiskit-verzióváltás egyetlen réteget érintsen.

Modulok
-------
:mod:`~vqebd.chemistry.molecule`
    Molekula-definíciók (H2, LiH, BeH2) és geometria-segédfüggvények.
:mod:`~vqebd.chemistry.problem`
    PySCF-meghajtó → típusos :class:`~vqebd.chemistry.problem.ElectronicStructure`.
:mod:`~vqebd.chemistry.mapping`
    Fermion → qubit leképezés (Jordan–Wigner, paritás, Bravyi–Kitaev).
:mod:`~vqebd.chemistry.reference`
    Klasszikus referenciaenergiák: L0 (Full CI) és L1 (egzakt diagonalizáció).
"""

from __future__ import annotations

from vqebd.chemistry.mapping import QubitHamiltonian, map_to_qubits
from vqebd.chemistry.molecule import beh2, h2, lih
from vqebd.chemistry.problem import ElectronicStructure, build_electronic_structure
from vqebd.chemistry.reference import (
    CHEMICAL_ACCURACY_HA,
    ReferenceEnergies,
    collect_references,
    exact_ground_state_energy,
    fci_energy,
)

__all__ = [
    "CHEMICAL_ACCURACY_HA",
    "ElectronicStructure",
    "QubitHamiltonian",
    "ReferenceEnergies",
    "beh2",
    "build_electronic_structure",
    "collect_references",
    "exact_ground_state_energy",
    "fci_energy",
    "h2",
    "lih",
    "map_to_qubits",
]
