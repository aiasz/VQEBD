"""Molekula → elektronszerkezeti feladat (PySCF + Qiskit Nature).

Ez a modul a `Qiskit Nature`_ ``PySCFDriver``-ét burkolja be egy **típusos**
adatszerkezetbe. A burkolásnak két oka van:

1. A Qiskit Nature nem szállít típusannotációkat, így a kódbázis többi része
   ``Any``-vel dolgozna. Itt egyetlen ponton konvertálunk konkrét típusokra, és
   ettől kezdve a statikus ellenőrzés (``mypy --strict``) érdemi.
2. A meghajtó API-ja verziók között változik. Ha egyetlen helyen érintkezünk vele,
   a Qiskit 2.x-re való átállás (R4 kockázat) egyetlen fájl módosítása.

.. _Qiskit Nature: https://qiskit-community.github.io/qiskit-nature/

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from vqebd.config import MoleculeSpec

if TYPE_CHECKING:  # pragma: no cover — csak a típusellenőrzéshez
    pass

__all__ = ["ElectronicStructure", "build_electronic_structure"]


@dataclass(frozen=True, slots=True)
class ElectronicStructure:
    """Egy molekula második kvantált elektronszerkezeti feladata.

    A ``problem`` és a ``second_q_op`` mezők típusa szándékosan ``Any``: ezek
    Qiskit Nature objektumok, amelyeknek nincs típusannotációjuk. Minden
    **számértéket** viszont konkrét típusra konvertálva tárolunk, így a kódbázis
    többi része típusosan dolgozhat.

    Attributes:
        spec: A bemeneti molekula-leírás.
        problem: A Qiskit Nature ``ElectronicStructureProblem`` példánya.
        second_q_op: A második kvantált (fermionos) Hamilton-operátor.
        num_spatial_orbitals: A térbeli pályák száma. A spin-pályák száma ennek
            a kétszerese, és Jordan–Wigner leképezéssel ennyi qubit kell.
        num_particles: ``(alfa, béta)`` elektronszám.
        nuclear_repulsion_energy: A magtaszítási energia (Ha). Konstans eltolás:
            a kvantumszámítás csak az **elektronos** részt adja, ezt hozzá kell adni.
        hartree_fock_energy: A Hartree–Fock **teljes** energia (Ha), a PySCF SCF
            eredménye. Ez a legjobb egydetermináns-közelítés, és a VQE
            ``θ = 0`` kezdőpontjának várt értéke.
    """

    spec: MoleculeSpec
    problem: Any
    second_q_op: Any
    num_spatial_orbitals: int
    num_particles: tuple[int, int]
    nuclear_repulsion_energy: float
    hartree_fock_energy: float

    @property
    def num_spin_orbitals(self) -> int:
        """A spin-pályák száma — ennyi qubit kell Jordan–Wigner leképezéssel."""
        return 2 * self.num_spatial_orbitals

    @property
    def num_electrons(self) -> int:
        """Az elektronok teljes száma."""
        return sum(self.num_particles)

    def summary(self) -> str:
        """Egysoros, naplóba illő összefoglaló."""
        return (
            f"{self.spec.name} [{self.spec.basis}] "
            f"{self.num_spatial_orbitals} térbeli pálya, "
            f"{self.num_particles} részecske, "
            f"E_nuc={self.nuclear_repulsion_energy:.8f} Ha, "
            f"E_HF={self.hartree_fock_energy:.8f} Ha"
        )


def build_electronic_structure(spec: MoleculeSpec) -> ElectronicStructure:
    """Elektronszerkezeti feladat felépítése egy molekula-leírásból.

    A PySCF Hartree–Fock számítást futtat, majd a molekulaintegrálokból
    összeállítja a második kvantált Hamilton-operátort.

    Args:
        spec: A molekula leírása.

    Returns:
        A típusos :class:`ElectronicStructure`.

    Raises:
        RuntimeError: Ha a PySCF nem tudja felépíteni vagy megoldani a feladatot
            (pl. ismeretlen bázis, értelmetlen geometria, nem konvergáló SCF).
            Az eredeti kivétel a ``__cause__``-ban marad.
    """
    # Késleltetett import: a modul importálható legyen a nehéz függőségek nélkül is
    # (pl. a Fázis 0 image-ében futó strukturális teszteknél).
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.units import DistanceUnit

    try:
        driver = PySCFDriver(
            atom=spec.atom,
            basis=spec.basis,
            charge=spec.charge,
            spin=spec.spin,
            unit=DistanceUnit.ANGSTROM,
        )
        problem = driver.run()
    except Exception as exc:
        raise RuntimeError(
            f"a(z) '{spec.name}' molekula elektronszerkezeti feladata nem építhető fel "
            f"(bázis='{spec.basis}', geometria='{spec.atom}'): {type(exc).__name__}: {exc}"
        ) from exc

    # A Qiskit Nature több mezőt `| None` típusúnak deklarál (a meghajtó nem
    # minden feladatra tölti ki őket). Mindegyiket explicit ellenőrizzük: egy
    # hiányzó érték itt beszédes hibát adjon, ne később egy `NoneType` kivételt
    # a számítás közepén.
    raw_particles = problem.num_particles
    if raw_particles is None:
        raise RuntimeError(f"a(z) '{spec.name}' molekulára a meghajtó nem adott részecskeszámot")
    particles = tuple(int(n) for n in raw_particles)
    if len(particles) != 2:
        raise RuntimeError(f"váratlan részecskeszám-alak: {raw_particles!r} (2 elemet vártunk)")

    num_spatial_orbitals = problem.num_spatial_orbitals
    if num_spatial_orbitals is None:
        raise RuntimeError(
            f"a(z) '{spec.name}' molekulára a meghajtó nem adta meg a térbeli pályák számát"
        )

    nuclear_repulsion = problem.nuclear_repulsion_energy
    if nuclear_repulsion is None:
        raise RuntimeError(f"a(z) '{spec.name}' molekulára nem érhető el a magtaszítási energia")

    reference_energy = problem.reference_energy
    if reference_energy is None:
        raise RuntimeError(
            f"a(z) '{spec.name}' molekulára nem érhető el Hartree–Fock referenciaenergia; "
            "valószínűleg az SCF nem konvergált"
        )

    return ElectronicStructure(
        spec=spec,
        problem=problem,
        second_q_op=problem.hamiltonian.second_q_op(),
        num_spatial_orbitals=int(num_spatial_orbitals),
        num_particles=(particles[0], particles[1]),
        nuclear_repulsion_energy=float(nuclear_repulsion),
        hartree_fock_energy=float(reference_energy),
    )
