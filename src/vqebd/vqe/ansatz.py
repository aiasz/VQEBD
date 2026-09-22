"""Variációs próbaállapot (ansatz) építése.

UCCSD — Unitary Coupled Cluster, Singles & Doubles
---------------------------------------------------
A próbaállapot alakja

.. code-block::

    |ψ(θ)⟩ = exp(T(θ) − T†(θ)) |HF⟩

ahol ``|HF⟩`` a Hartree–Fock determináns, ``T`` pedig az egyszeres és kétszeres
gerjesztési operátorok összege. Ez a klasszikus coupled cluster módszer unitáris
változata [romero2019].

Miért ez, és nem „hardware-efficient" ansatz?
---------------------------------------------
- **Kémiailag motivált**: a paraméterek gerjesztési amplitúdóknak felelnek meg,
  nem önkényes forgatási szögeknek. Ez a Hilbert-tér fizikailag releváns részére
  korlátoz, ami csökkenti a barren-plateau kockázatot (R7).
- **Részecskeszám-megőrző**: az állapot mindig a helyes elektronszám-szektorban
  marad, így a variációs minimum fizikailag értelmes.
- **H2-re egzakt**: paritás-leképezéssel, kétqubites redukcióval 3 paraméter,
  amely a 2 qubites tér teljes releváns alterét lefedi. Ezért a Fázis 1-ben
  ``L2 ≡ L1`` várható gépi pontossággal — ez teszi a validálást élessé.

Az ára a mélyebb áramkör; ez a Fázis 1b-től (zaj) válik lényegessé, és ott a
„hardware-efficient" alternatíva [kandala2017] külön benchmark-dimenzióként
vethető össze vele.

A kezdőpont
-----------
``θ = 0`` esetén ``exp(0) = I``, tehát ``|ψ(0)⟩ = |HF⟩``, és így
``E(0) = E_HF``. A kezdőpont ezért

- **determinisztikus** (nincs véletlen — ADR-0005),
- **fizikailag motivált** (a legjobb egydetermináns-közelítés),
- és **automatikusan ellenőrizhető**: az AC-1.8 teszt pontosan ezt méri.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vqebd.chemistry.mapping import QubitHamiltonian
from vqebd.chemistry.problem import ElectronicStructure
from vqebd.config import AnsatzSpec
from vqebd.seeds import SeedSet

__all__ = ["AnsatzBundle", "build_ansatz", "initial_point"]

RANDOM_INITIAL_POINT_SCALE: float = 0.1
"""A véletlen kezdőpont szórása.

Kicsi érték, hogy a Hartree–Fock állapot közelében maradjunk: a nagy amplitúdójú
véletlen kezdőpont barren plateau-ra vezethet (R7 kockázat).
"""


@dataclass(frozen=True, slots=True)
class AnsatzBundle:
    """A felépített ansatz és a hozzá tartozó kezdőpont.

    Attributes:
        circuit: A paraméterezett Qiskit ``QuantumCircuit``.
        num_qubits: Az áramkör qubit-száma. Egyeznie kell a Hamilton-operátoréval.
        num_parameters: A variációs paraméterek száma.
        initial_point: A kezdőparaméterek.
        kind: Az ansatz azonosítója (az adatsémához).
        initial_point_kind: A kezdőpont fajtája (az adatsémához).
    """

    circuit: Any
    num_qubits: int
    num_parameters: int
    initial_point: tuple[float, ...]
    kind: str
    initial_point_kind: str

    def summary(self) -> str:
        """Egysoros, naplóba illő összefoglaló."""
        return (
            f"{self.kind}: {self.num_qubits} qubit, {self.num_parameters} paraméter, "
            f"kezdőpont={self.initial_point_kind}"
        )


def initial_point(
    num_parameters: int,
    spec: AnsatzSpec,
    seeds: SeedSet,
) -> tuple[float, ...]:
    """A variációs paraméterek kezdőértéke.

    Args:
        num_parameters: A paraméterek száma.
        spec: Az ansatz-leírás (ebből jön a kezdőpont fajtája).
        seeds: A seed-készlet; véletlen kezdőpontnál az ``initial_point`` seed dönt.

    Returns:
        A kezdőparaméterek.
    """
    if spec.initial_point == "zeros":
        return (0.0,) * num_parameters

    import numpy as np

    rng = np.random.default_rng(seeds.initial_point)
    values = rng.normal(loc=0.0, scale=RANDOM_INITIAL_POINT_SCALE, size=num_parameters)
    return tuple(float(v) for v in values)


def build_ansatz(
    structure: ElectronicStructure,
    hamiltonian: QubitHamiltonian,
    spec: AnsatzSpec,
    seeds: SeedSet,
) -> AnsatzBundle:
    """UCCSD ansatz felépítése Hartree–Fock kezdőállapottal.

    Fontos: az ansatz **ugyanazt a mapper-objektumot** használja, mint a
    Hamilton-operátor. Enélkül az állapot és az operátor különböző qubit-térben
    élne, és az eredmény csendben értelmetlen lenne.

    Args:
        structure: Az elektronszerkezeti feladat.
        hamiltonian: A leképezett Hamilton-operátor (a mappert is hordozza).
        spec: Az ansatz-leírás.
        seeds: A seed-készlet.

    Returns:
        Az :class:`AnsatzBundle`.

    Raises:
        ValueError: Ismeretlen ansatz-fajta esetén, vagy ha az áramkör qubit-száma
            nem egyezik a Hamilton-operátoréval.
    """
    if spec.kind != "uccsd":
        raise ValueError(f"ismeretlen ansatz: {spec.kind!r}")

    from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock

    reference_state = HartreeFock(
        structure.num_spatial_orbitals,
        structure.num_particles,
        hamiltonian.mapper,
    )
    circuit = UCCSD(
        structure.num_spatial_orbitals,
        structure.num_particles,
        hamiltonian.mapper,
        initial_state=reference_state,
    )

    num_qubits = int(circuit.num_qubits)
    if num_qubits != hamiltonian.num_qubits:
        raise ValueError(
            f"az ansatz ({num_qubits} qubit) és a Hamilton-operátor "
            f"({hamiltonian.num_qubits} qubit) qubit-száma eltér — "
            "valószínűleg eltérő mapper-objektumot kaptak"
        )

    num_parameters = int(circuit.num_parameters)
    return AnsatzBundle(
        circuit=circuit,
        num_qubits=num_qubits,
        num_parameters=num_parameters,
        initial_point=initial_point(num_parameters, spec, seeds),
        kind=spec.kind,
        initial_point_kind=spec.initial_point,
    )
