"""Molekula-definíciók és geometria-segédfüggvények.

A projekt három molekulát céloz (alapterv): H2, LiH és BeH2. A Fázis 1 kizárólag
a H2-t validálja; a többi definíció itt készen áll a Fázis 5-höz.

Egységek
--------
Minden hosszúság **ångströmben** (Å) értendő, mert a PySCF és a Qiskit Nature
alapértelmezett bemeneti egysége ez. Az energiák **Hartree-ban** (Ha).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from typing import Final

from vqebd.config import MoleculeSpec

__all__ = [
    "BEH2_BE_H_DISTANCE",
    "H2_EQUILIBRIUM_BOND_LENGTH",
    "H2_REFERENCE_BOND_LENGTH",
    "LIH_EQUILIBRIUM_BOND_LENGTH",
    "beh2",
    "diatomic",
    "h2",
    "lih",
    "linear_triatomic",
]

H2_REFERENCE_BOND_LENGTH: Final[float] = 0.735
"""A projekt referencia-kötéshossza H2-re, ångströmben.

Ezt az értéket az alapterv írja elő, és a kvantumkémiai VQE-irodalomban is ez a
leggyakrabban használt H2-geometria. **Nem azonos** a kísérleti egyensúlyi
kötéshosszal (:data:`H2_EQUILIBRIUM_BOND_LENGTH`), de az eltérés (≈0.006 Å)
a benchmark szempontjából lényegtelen: minden eredményt az **ugyanezen a
geometrián** számolt egzakt megoldáshoz mérünk.
"""

H2_EQUILIBRIUM_BOND_LENGTH: Final[float] = 0.741
"""A H2 kísérleti egyensúlyi kötéshossza (r_e), ångströmben.

Csak dokumentációs célra; a számításokhoz a :data:`H2_REFERENCE_BOND_LENGTH`
használatos.
"""

LIH_EQUILIBRIUM_BOND_LENGTH: Final[float] = 1.595
"""A LiH egyensúlyi kötéshossza, ångströmben (Fázis 5)."""

BEH2_BE_H_DISTANCE: Final[float] = 1.330
"""A lineáris BeH2 Be–H távolsága, ångströmben.

Ez a VQE-irodalomban bevett érték; többek között [kandala2017] is ezt használja.
"""


def diatomic(
    name: str,
    first: str,
    second: str,
    distance: float,
    *,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
) -> MoleculeSpec:
    """Kétatomos molekula a z tengely mentén.

    Args:
        name: Rövid azonosító (pl. ``"H2"``).
        first: Az origóba helyezett atom vegyjele.
        second: A ``distance`` távolságra helyezett atom vegyjele.
        distance: Kötéshossz ångströmben.
        basis: Bázis neve.
        charge: Teljes töltés.
        spin: ``2S``.

    Returns:
        A molekulát leíró :class:`~vqebd.config.MoleculeSpec`.

    Raises:
        ValueError: Ha a távolság nem pozitív.
    """
    if distance <= 0:
        raise ValueError(f"a kötéshossznak pozitívnak kell lennie: {distance}")
    atom = f"{first} 0 0 0; {second} 0 0 {distance:.6f}"
    return MoleculeSpec(
        name=name, atom=atom, basis=basis, charge=charge, spin=spin, bond_length=distance
    )


def linear_triatomic(
    name: str,
    center: str,
    ligand: str,
    distance: float,
    *,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
) -> MoleculeSpec:
    """Szimmetrikus, lineáris háromatomos molekula (pl. BeH2).

    A központi atom az origóban, a két ligandum a z tengelyen ``±distance``
    távolságra. Ez a geometria D∞h szimmetriájú.
    """
    if distance <= 0:
        raise ValueError(f"a távolságnak pozitívnak kell lennie: {distance}")
    atom = f"{center} 0 0 0; {ligand} 0 0 {distance:.6f}; {ligand} 0 0 {-distance:.6f}"
    return MoleculeSpec(
        name=name, atom=atom, basis=basis, charge=charge, spin=spin, bond_length=distance
    )


def h2(bond_length: float = H2_REFERENCE_BOND_LENGTH, *, basis: str = "sto3g") -> MoleculeSpec:
    """A H2 molekula.

    STO-3G bázisban 2 térbeli pálya → 4 spin-pálya → 4 qubit Jordan–Wigner
    leképezéssel, illetve **2 qubit** paritás-leképezéssel, kétqubites redukcióval.
    """
    return diatomic("H2", "H", "H", bond_length, basis=basis)


def lih(bond_length: float = LIH_EQUILIBRIUM_BOND_LENGTH, *, basis: str = "sto3g") -> MoleculeSpec:
    """A LiH molekula (Fázis 5).

    STO-3G bázisban 6 térbeli pálya → 12 qubit (Jordan–Wigner). Aktív tér
    redukció nélkül ez már nehéz; lásd a TR-000 4. körének méréseit.
    """
    return diatomic("LiH", "Li", "H", bond_length, basis=basis)


def beh2(bond_length: float = BEH2_BE_H_DISTANCE, *, basis: str = "sto3g") -> MoleculeSpec:
    """A lineáris BeH2 molekula (Fázis 5).

    STO-3G bázisban 7 térbeli pálya → 14 qubit (Jordan–Wigner), 666 Hamilton-taggal
    és 204 UCCSD-paraméterrel. Aktív tér redukció **kötelező** a gyakorlatban.
    """
    return linear_triatomic("BeH2", "Be", "H", bond_length, basis=basis)
