"""Referenciaenergiák — a validálás alapja (L0 és L1 szint).

A benchmark értelmezhetősége azon áll, hogy **minden mérésnek van nála
megbízhatóbb referenciája**. Ez a modul a két klasszikus, kvantumszámítástól
független referenciát állítja elő:

**L0 — Full CI (PySCF).**
    Az adott bázisban vett *egzakt* megoldás: a teljes determináns-tér
    diagonalizálása. Független implementáció, független elmélet — ez a
    „fizikai igazság" viszonyítási pontja.

**L1 — a qubit-Hamilton-operátor egzakt legkisebb sajátértéke.**
    Ugyanannak a feladatnak a megoldása, de már a **leképezés után**, sűrű
    mátrix-diagonalizációval.

Az ``L0 ≡ L1`` egyezés igazolja, hogy a fermion → qubit leképezés **helyes**. Ha
eltérnek, a hiba a leképezésben van, nem a VQE-ben — és ezt a két szint
szétválasztása nélkül nem lehetne megállapítani.

Skálázási korlát
----------------
Az L1 sűrű mátrixot épít: a memóriaigény ``4^n`` komplex szám ``n`` qubitre.
14 qubit fölött ez gyakorlatilag kezelhetetlen, ezért a
:data:`MAX_EXACT_DIAGONALIZATION_QUBITS` korlát fölött a függvény hibát dob,
nem pedig lefagyasztja a gépet.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

from vqebd.chemistry.mapping import QubitHamiltonian
from vqebd.chemistry.problem import ElectronicStructure
from vqebd.config import MoleculeSpec

__all__ = [
    "CHEMICAL_ACCURACY_HA",
    "MAX_EXACT_DIAGONALIZATION_QUBITS",
    "ReferenceEnergies",
    "collect_references",
    "exact_ground_state_energy",
    "fci_energy",
    "hartree_fock_energy",
]

CHEMICAL_ACCURACY_HA: Final[float] = 1.5936e-3
"""A kémiai pontosság Hartree-ban: 1 kcal/mol.

A kvantumkémiában ez a bevett hibahatár — az a pontosság, amely alatt egy
számítás kémiai következtetések levonására alkalmas [helgaker2000].

Átváltás: 1 kcal/mol = 4.184 kJ/mol, és 1 Ha = 2625.4996 kJ/mol, azaz
1 kcal/mol = 4.184 / 2625.4996 Ha = 1.5936 × 10⁻³ Ha.
"""

MAX_EXACT_DIAGONALIZATION_QUBITS: Final[int] = 14
"""A sűrű diagonalizáció qubit-korlátja.

14 qubit → 2¹⁴ × 2¹⁴ komplex mátrix ≈ 4.3 GB (complex128). Efölött a művelet
nem fér a memóriába, ezért inkább hibát dobunk, mint hogy a folyamat elhaljon.
"""


@dataclass(frozen=True, slots=True)
class ReferenceEnergies:
    """A klasszikus referenciaszintek egy adott feladatra.

    Attributes:
        hartree_fock: A Hartree–Fock teljes energia (Ha). A legjobb
            egydetermináns-közelítés; a korrelációs energiát nem tartalmazza.
        full_ci: L0 — a Full CI teljes energia (Ha), vagy ``None``, ha a feladat
            túl nagy a klasszikus egzakt megoldáshoz.
        exact_diagonalization: L1 — a qubit-Hamilton-operátor legkisebb
            sajátértéke + magtaszítás (Ha), vagy ``None``, ha túl nagy.
        nuclear_repulsion: A magtaszítási energia (Ha).
    """

    hartree_fock: float
    full_ci: float | None
    exact_diagonalization: float | None
    nuclear_repulsion: float

    @property
    def correlation_energy(self) -> float | None:
        """A korrelációs energia: ``E_FCI − E_HF`` (Ha).

        Mindig negatív (vagy nulla): a Hartree–Fock felső korlát. Ez az a
        mennyiség, amelynek visszanyerése a VQE tényleges feladata.
        """
        if self.full_ci is None:
            return None
        return self.full_ci - self.hartree_fock

    @property
    def mapping_error(self) -> float | None:
        """``L1 − L0`` (Ha) — a fermion → qubit leképezés hibája.

        Helyes leképezésnél ez gépi pontossággal nulla. Bármi ennél nagyobb
        implementációs hibát jelez.
        """
        if self.full_ci is None or self.exact_diagonalization is None:
            return None
        return self.exact_diagonalization - self.full_ci

    @property
    def best(self) -> float:
        """A legmegbízhatóbb elérhető referencia (Ha).

        Sorrend: Full CI → egzakt diagonalizáció → Hartree–Fock.
        """
        if self.full_ci is not None:
            return self.full_ci
        if self.exact_diagonalization is not None:
            return self.exact_diagonalization
        return self.hartree_fock

    def to_dict(self) -> dict[str, float | None]:
        """Szótár-alak az eredményrekordhoz."""
        data: dict[str, float | None] = dict(asdict(self))
        data["correlation_energy"] = self.correlation_energy
        data["mapping_error"] = self.mapping_error
        return data


def hartree_fock_energy(structure: ElectronicStructure) -> float:
    """A Hartree–Fock teljes energia (Ha).

    Kényelmi elérés: a PySCF SCF már lefutott az :func:`build_electronic_structure`
    hívásakor, ez csak az eredményt adja vissza.
    """
    return structure.hartree_fock_energy


def fci_energy(spec: MoleculeSpec) -> float:
    """L0 — Full CI energia PySCF-fel (Ha).

    A Full CI a teljes determináns-térben diagonalizál, tehát az adott bázisban
    **egzakt**. Szándékosan a PySCF-et hívjuk közvetlenül, nem a Qiskit Nature-ön
    keresztül: így a referencia a kvantumszámítási lánctól **teljesen független**
    implementáció, ami a keresztvalidációt érdemivé teszi.

    Args:
        spec: A molekula leírása.

    Returns:
        A Full CI teljes energia Hartree-ban (a magtaszítást is tartalmazza).

    Raises:
        RuntimeError: Ha a PySCF nem tudja megoldani a feladatot.
    """
    from pyscf import fci, gto, scf

    try:
        mol = gto.M(
            atom=spec.atom,
            basis=spec.basis,
            charge=spec.charge,
            spin=spec.spin,
            unit="Angstrom",
            verbose=0,
        )
        mean_field = scf.RHF(mol) if spec.spin == 0 else scf.ROHF(mol)
        mean_field.run()
        if not mean_field.converged:
            raise RuntimeError("a Hartree–Fock SCF nem konvergált")
        energy, _ = fci.FCI(mean_field).kernel()
    except Exception as exc:
        raise RuntimeError(
            f"a(z) '{spec.name}' molekula Full CI energiája nem számolható: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    return float(energy)


def exact_ground_state_energy(hamiltonian: QubitHamiltonian) -> float:
    """L1 — a qubit-Hamilton-operátor legkisebb sajátértéke + magtaszítás (Ha).

    Sűrű mátrixot épít és ``numpy.linalg.eigvalsh``-t hív. Mivel a Hamilton-operátor
    hermitikus, az ``eigvalsh`` (nem ``eigvals``) a helyes választás: gyorsabb, és
    garantáltan valós sajátértékeket ad.

    Args:
        hamiltonian: A leképezett Hamilton-operátor.

    Returns:
        A teljes alapállapoti energia Hartree-ban.

    Raises:
        ValueError: Ha a qubit-szám meghaladja a
            :data:`MAX_EXACT_DIAGONALIZATION_QUBITS` korlátot.
    """
    if hamiltonian.num_qubits > MAX_EXACT_DIAGONALIZATION_QUBITS:
        raise ValueError(
            f"a sűrű diagonalizáció {hamiltonian.num_qubits} qubitre nem végezhető el "
            f"(korlát: {MAX_EXACT_DIAGONALIZATION_QUBITS}, memóriaigény ~4^n). "
            "Nagyobb rendszerhez aktív tér redukció vagy ritka sajátérték-megoldó kell."
        )

    import numpy as np

    matrix = hamiltonian.operator.to_matrix()
    electronic = float(np.linalg.eigvalsh(matrix)[0])
    return electronic + hamiltonian.nuclear_repulsion_energy


def collect_references(
    structure: ElectronicStructure,
    hamiltonian: QubitHamiltonian,
    *,
    compute_fci: bool = True,
) -> ReferenceEnergies:
    """Az összes elérhető klasszikus referencia összegyűjtése.

    Args:
        structure: Az elektronszerkezeti feladat.
        hamiltonian: A leképezett Hamilton-operátor.
        compute_fci: Ha ``False``, a Full CI kihagyható (nagy rendszereknél drága).

    Returns:
        A :class:`ReferenceEnergies`.
    """
    full_ci: float | None = fci_energy(structure.spec) if compute_fci else None

    exact: float | None
    try:
        exact = exact_ground_state_energy(hamiltonian)
    except ValueError:
        # Túl nagy a sűrű diagonalizációhoz — ez nem hiba, csak korlát.
        exact = None

    return ReferenceEnergies(
        hartree_fock=structure.hartree_fock_energy,
        full_ci=full_ci,
        exact_diagonalization=exact,
        nuclear_repulsion=structure.nuclear_repulsion_energy,
    )
