"""A VQE-futtatás konfigurációja — fagyasztott, hash-elhető adatszerkezetek.

Minden konfigurációs objektum ``frozen=True``, és kizárólag hash-elhető mezőket
tartalmaz (skalárok és ``tuple``-ök, sosem ``list`` vagy ``dict``). Ennek két oka van:

1. **Véletlen módosítás kizárása.** Egy futtatás konfigurációja a futás közben nem
   változhat meg; különben az eredményrekord nem írná le hűen, mi történt.
2. **Stabil ujjlenyomat.** A :meth:`VQEConfig.fingerprint` a kanonikus JSON-alakból
   képzett SHA-256 hash. Ez lesz a Fázis 4 adatsémájában a ``config_hash`` mező,
   amellyel egy futás azonosítható és újrajátszható.

Az ujjlenyomat szándékosan **nem** a beépített ``hash()``-en alapul: az csak a
folyamaton belül stabil, és a Python-verzióval is változhat.

Lásd: ``docs/plan/phase_01.md`` 3.3, ``docs/adr/ADR-0005-determinizmus.md``.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = [
    "AnsatzSpec",
    "BackendKind",
    "InitialPointKind",
    "MapperKind",
    "MoleculeSpec",
    "OptimizerSpec",
    "VQEConfig",
]

MapperKind = Literal["jordan_wigner", "parity", "bravyi_kitaev"]
"""A támogatott fermion → qubit leképezések.

- ``jordan_wigner`` — [jordan1928]; a legegyszerűbb, de a legtöbb qubitet igényli.
- ``parity`` — paritás-leképezés; ``two_qubit_reduction`` mellett 2 qubitet spórol.
- ``bravyi_kitaev`` — [bravyi2002], [seeley2012]; logaritmikus Pauli-súly.
"""

BackendKind = Literal["statevector"]
"""A Fázis 1-ben egyetlen backend: zajmentes állapotvektor.

A Fázis 1b-ben ``aer_shot`` és ``aer_noisy``, a Fázis 2-ben ``ibm_qpu`` bővíti.
"""

InitialPointKind = Literal["zeros", "random"]
"""A variációs paraméterek kezdőértéke.

``zeros`` esetén az UCCSD ansatz **pontosan a Hartree–Fock állapotot** adja
(``exp(0) = I``), ami determinisztikus és fizikailag motivált kiindulás.
"""


@dataclass(frozen=True, slots=True)
class MoleculeSpec:
    """Egy molekula elektronszerkezeti feladatának teljes leírása.

    Attributes:
        name: Rövid azonosító (pl. ``"H2"``), az adatsémába és a naplókba kerül.
        atom: Geometria PySCF-formátumban, ångströmben,
            pl. ``"H 0 0 0; H 0 0 0.735"``.
        basis: Bázis neve (alapértelmezés: ``"sto3g"``, lásd [hehre1969]).
        charge: Teljes töltés.
        spin: ``2S`` (a párosítatlan elektronok száma), **nem** ``2S+1``.
        bond_length: Kötéshossz ångströmben, kétatomos molekuláknál.
            Csak dokumentációs és ábrázolási célra; a geometriát az ``atom`` adja.
    """

    name: str
    atom: str
    basis: str = "sto3g"
    charge: int = 0
    spin: int = 0
    bond_length: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a molekula neve nem lehet üres")
        if not self.atom.strip():
            raise ValueError("a geometria (atom) nem lehet üres")
        if self.spin < 0:
            raise ValueError(f"a spin (2S) nem lehet negatív: {self.spin}")
        if self.bond_length is not None and self.bond_length <= 0:
            raise ValueError(f"a kötéshossznak pozitívnak kell lennie: {self.bond_length}")


@dataclass(frozen=True, slots=True)
class AnsatzSpec:
    """A variációs próbaállapot (ansatz) leírása.

    Attributes:
        kind: Jelenleg csak ``"uccsd"`` — unitary coupled cluster, egyszeres és
            kétszeres gerjesztésekkel ([romero2019]).
        initial_point: A paraméterek kezdőértéke; lásd :data:`InitialPointKind`.
    """

    kind: Literal["uccsd"] = "uccsd"
    initial_point: InitialPointKind = "zeros"


@dataclass(frozen=True, slots=True)
class OptimizerSpec:
    """A klasszikus optimalizáló beállításai.

    A ``method`` közvetlenül a ``scipy.optimize.minimize`` metódusneve.

    Attributes:
        method: ``"SLSQP"`` [kraft1988], ``"COBYLA"`` [powell1994],
            ``"Nelder-Mead"`` [nelder1965], ``"L-BFGS-B"`` vagy ``"Powell"``.
        maxiter: Iterációs felső korlát.
        tol: Konvergencia-tűrés; ``None`` esetén a SciPy alapértelmezése.
    """

    method: str = "SLSQP"
    maxiter: int = 300
    tol: float | None = 1e-10

    def __post_init__(self) -> None:
        if self.maxiter < 1:
            raise ValueError(f"a maxiter legyen legalább 1: {self.maxiter}")
        if self.tol is not None and self.tol <= 0:
            raise ValueError(f"a tol legyen pozitív: {self.tol}")


@dataclass(frozen=True, slots=True)
class VQEConfig:
    """Egyetlen VQE-futtatás teljes, önmagában elegendő leírása.

    „Önmagában elegendő" azt jelenti: ebből az objektumból — a rögzített
    csomagverziók mellett — a futás bitre újrajátszható (ADR-0005).

    Attributes:
        molecule: A fizikai feladat.
        mapper: A fermion → qubit leképezés.
        two_qubit_reduction: Paritás-leképezésnél a részecskeszám- és
            spin-megmaradáson alapuló kétqubites redukció. Más leképezéssel
            nem értelmezett, és figyelmen kívül marad.
        ansatz: A próbaállapot.
        optimizer: A klasszikus optimalizáló.
        backend: A kiértékelés módja.
        seed: A **mester**-seed; ebből származik az összes többi (:mod:`vqebd.seeds`).
    """

    molecule: MoleculeSpec
    mapper: MapperKind = "parity"
    two_qubit_reduction: bool = True
    ansatz: AnsatzSpec = field(default_factory=AnsatzSpec)
    optimizer: OptimizerSpec = field(default_factory=OptimizerSpec)
    backend: BackendKind = "statevector"
    seed: int = 20260922

    def to_dict(self) -> dict[str, Any]:
        """Beágyazott szótár-alak — naplózáshoz és az adatsémához."""
        return dataclasses.asdict(self)

    def canonical_json(self) -> str:
        """Kanonikus JSON-alak: rendezett kulcsok, fix elválasztók.

        Ez az ujjlenyomat bemenete. A determinizmus feltétele, hogy a szerializálás
        ne függjön a szótárak bejárási sorrendjétől.
        """
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def fingerprint(self) -> str:
        """A konfiguráció stabil SHA-256 ujjlenyomata (64 hexa karakter).

        Folyamatok, Python-verziók és platformok között is azonos. A Fázis 4
        adatsémájában ez a ``config_hash`` mező.
        """
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def short_fingerprint(self) -> str:
        """Az ujjlenyomat első 12 karaktere — naplókhoz és fájlnevekhez."""
        return self.fingerprint()[:12]
