"""Platform-metaadatok — a platform mint önálló benchmark-dimenzió.

Egy benchmark, amelynek eredménye egyetlen könyvtár sajátossága lehet, nem
benchmark. A projekt ezért ugyanazt a feladatot **több, egymástól független
implementációval** is kiértékeli.

Ez a modul a platformok **objektív tulajdonságait** rögzíti: melyik milyen
aritmetikát használ, mekkora hibát szabad tőle elfogadni, és mire képes. Ezek az
adatok az eredményrekordba is bekerülnek, így egy mérés utólag is értelmezhető
marad.

Lásd: ``docs/adr/ADR-0006-tobbplatformos-architektura.md``.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from vqebd.config import BackendKind

__all__ = [
    "PLATFORMS",
    "PlatformInfo",
    "PlatformName",
    "Precision",
    "backend_tolerance_ha",
    "platform_of",
]

PlatformName = Literal["qiskit", "cirq", "qsim"]
"""A támogatott kvantum-szoftverplatformok."""

Precision = Literal["complex128", "complex64"]
"""Az állapotvektor számábrázolása.

Ez **nem** minőségi ítélet: a ``complex64`` tudatos pontosság–sebesség
kompromisszum a qsim oldalán.
"""


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    """Egy platform-backend objektív tulajdonságai.

    Attributes:
        backend: A konfigurációban használt azonosító.
        platform: A mögöttes szoftverplatform.
        precision: Az állapotvektor számábrázolása.
        machine_epsilon: Az aritmetika gépi epszilonja.
        tolerance_ha: Az elfogadható eltérés a referenciától, Hartree-ban.
            **Nem** „ami éppen átmegy", hanem a számábrázolásból levezetett érték
            (lásd ``docs/plan/phase_01m.md``, 5. fejezet).
        exact: Egzakt (állapotvektor-alapú) kiértékelés-e, vagy mintavételes.
        requires_quota: Fogyaszt-e külső, korlátozott erőforrást (QPU-idő).
        deterministic: Azonos seed mellett bitre azonos eredményt ad-e.
        description: Rövid, ember által olvasható leírás.
    """

    backend: BackendKind
    platform: PlatformName
    precision: Precision
    machine_epsilon: float
    tolerance_ha: float
    exact: bool
    requires_quota: bool
    deterministic: bool
    description: str

    @property
    def chemical_accuracy_margin(self) -> float:
        """Hányszorosan van a tolerancia a kémiai pontosság alatt.

        Ez a szám mondja meg, hogy a platform numerikus korlátja befolyásolja-e a
        kémiai következtetéseket. 1.0 alatti érték azt jelentené, hogy igen.
        """
        from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA

        return CHEMICAL_ACCURACY_HA / self.tolerance_ha


# A gépi epszilonok a IEEE 754 szabvány szerint:
#   binary64 (complex128 komponensei): 2^-52  = 2.220446e-16
#   binary32 (complex64  komponensei): 2^-23  = 1.192093e-07
_EPS_64: Final[float] = 2.220446049250313e-16
_EPS_32: Final[float] = 1.1920928955078125e-07

PLATFORMS: Final[dict[BackendKind, PlatformInfo]] = {
    "qiskit_statevector": PlatformInfo(
        backend="qiskit_statevector",
        platform="qiskit",
        precision="complex128",
        machine_epsilon=_EPS_64,
        tolerance_ha=1e-9,
        exact=True,
        requires_quota=False,
        deterministic=True,
        description="Qiskit StatevectorEstimator — egzakt, kétszeres pontosságú referencia.",
    ),
    "cirq_simulator": PlatformInfo(
        backend="cirq_simulator",
        platform="cirq",
        precision="complex128",
        machine_epsilon=_EPS_64,
        tolerance_ha=1e-9,
        exact=True,
        requires_quota=False,
        deterministic=True,
        description=(
            "Google Cirq beépített szimulátora — független implementáció, "
            "kétszeres pontosság. ~20 qubitig kényelmes."
        ),
    ),
    "qsim": PlatformInfo(
        backend="qsim",
        platform="qsim",
        precision="complex64",
        machine_epsilon=_EPS_32,
        tolerance_ha=1e-5,
        exact=True,
        requires_quota=False,
        deterministic=True,
        description=(
            "Google qsim — C++-ban optimalizált szimulátor. EGYSZERES pontosságú "
            "(complex64), cserébe 24 qubiten ~22x gyorsabb a cirq.Simulator-nál."
        ),
    ),
}
"""A platform-backendek nyilvántartása.

A Fázis 1b (``qiskit_aer_shot``, ``qiskit_aer_noisy``, ``qsim_noisy``) és a
Fázis 2 (``ibm_qpu``) újabb bejegyzésekkel bővíti.
"""


def platform_of(backend: BackendKind) -> PlatformInfo:
    """Egy backend platform-metaadatai.

    Args:
        backend: A backend azonosítója.

    Returns:
        A :class:`PlatformInfo`.

    Raises:
        KeyError: Ismeretlen backend esetén — a hibaüzenet felsorolja az ismerteket.
    """
    try:
        return PLATFORMS[backend]
    except KeyError:
        raise KeyError(
            f"ismeretlen backend: {backend!r}. Ismert backendek: {sorted(PLATFORMS)}"
        ) from None


def backend_tolerance_ha(backend: BackendKind) -> float:
    """Az adott backendtől elfogadható eltérés Hartree-ban."""
    return platform_of(backend).tolerance_ha
