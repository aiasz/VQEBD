"""Determinisztikus seed-származtatás (ADR-0005).

A VQE-ben legalább hat független véletlenforrás van, és közül három rejtett
(transzpiláció, sztochasztikus optimalizálók, Python hash-randomizáció). A projekt
alapelve:

    Minden véletlenforrás explicit seedet kap, és minden seed bekerül az
    eredményrekordba.

A felhasználó **egyetlen** mester-seedet ad meg; ebből a :class:`SeedSet`
származtatja a komponensenkénti seedeket úgy, hogy azok ne ütközzenek, és ne is
legyenek korreláltak.

Miért nem a beépített ``hash()``?
---------------------------------
A ``hash()`` stringekre randomizált (``PYTHONHASHSEED``), és a Python-verzióval is
változhat. A konténerben ugyan ``PYTHONHASHSEED=0``, de egy seed-származtatás nem
támaszkodhat környezeti változóra: a BLAKE2b kriptográfiai hash minden platformon,
minden Python-verzióban ugyanazt adja.

Lásd: ``docs/adr/ADR-0005-determinizmus.md``.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Final

__all__ = ["MAX_SEED", "SeedSet", "derive_seed"]

MAX_SEED: Final[int] = 2**31 - 1
"""A származtatott seedek felső korlátja.

A NumPy, a Qiskit és a SciPy egyaránt elfogad 32 bites előjeles egészet; ez a
legszűkebb közös tartomány.
"""

_DIGEST_BYTES: Final[int] = 8


def derive_seed(master: int, label: str) -> int:
    """Egy komponens-seed származtatása a mester-seedből.

    A származtatás **tiszta függvény**: ugyanaz a ``(master, label)`` pár minden
    platformon, minden futásban ugyanazt az értéket adja.

    Args:
        master: A mester-seed.
        label: A komponens azonosítója (pl. ``"simulator"``).

    Returns:
        Seed a ``[0, MAX_SEED)`` tartományban.
    """
    digest = hashlib.blake2b(f"{master}:{label}".encode(), digest_size=_DIGEST_BYTES).digest()
    return int.from_bytes(digest, "big") % MAX_SEED


@dataclass(frozen=True, slots=True)
class SeedSet:
    """A futtatás összes véletlenforrásának seedje.

    Egyetlen objektumként utazik a hívási láncon, hogy ne kelljen öt külön
    paramétert átvezetni minden függvényen, és hogy az eredményrekordba is
    egyben bekerülhessen.

    Attributes:
        master: A felhasználó által megadott mester-seed.
        simulator: Az Aer szimulátor lövés-mintavételezése (``seed_simulator``).
        transpiler: A Qiskit transzpiler SABRE layout/routing lépése
            (``seed_transpiler``). **Ez a leggyakrabban elfeledett seed:** nélküle
            ugyanaz a kód más fizikai áramkört, és így más zajt adhat.
        optimizer: Sztochasztikus optimalizálók (pl. SPSA) perturbációi.
        mitigation: Véletlent használó hibaenyhítési lépések (pl. véletlen folding).
        initial_point: A variációs paraméterek véletlen kezdőpontja, ha
            ``initial_point="random"``.
    """

    master: int
    simulator: int
    transpiler: int
    optimizer: int
    mitigation: int
    initial_point: int

    @classmethod
    def derive(cls, master: int) -> SeedSet:
        """A teljes seed-készlet előállítása egyetlen mester-seedből."""
        if master < 0:
            raise ValueError(f"a mester-seed nem lehet negatív: {master}")
        return cls(
            master=master,
            simulator=derive_seed(master, "simulator"),
            transpiler=derive_seed(master, "transpiler"),
            optimizer=derive_seed(master, "optimizer"),
            mitigation=derive_seed(master, "mitigation"),
            initial_point=derive_seed(master, "initial_point"),
        )

    def to_dict(self) -> dict[str, int]:
        """Szótár-alak az eredményrekordhoz."""
        return asdict(self)
