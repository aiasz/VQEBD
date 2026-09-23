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
    "DERIVATIVE_FREE_OPTIMIZERS",
    "GRADIENT_BASED_OPTIMIZERS",
    "PLATFORMS",
    "SCIPY_FINITE_DIFFERENCE_STEP",
    "PlatformInfo",
    "PlatformName",
    "Precision",
    "backend_tolerance_ha",
    "check_optimizer_compatibility",
    "platform_of",
]

PlatformName = Literal["qiskit", "cirq", "qsim"]
"""A támogatott kvantum-szoftverplatformok."""

Precision = Literal["complex128", "complex64"]
"""Az állapotvektor számábrázolása.

Ez **nem** minőségi ítélet: a ``complex64`` tudatos pontosság–sebesség
kompromisszum a qsim oldalán.
"""


SCIPY_FINITE_DIFFERENCE_STEP: Final[float] = 1.4901161193847656e-08
"""A SciPy alapértelmezett véges-differencia lépésköze: ``sqrt(eps_float64)``.

Ez a szám a projekt egyik legfontosabb mérőszáma. A gradiens-alapú optimalizálók
(``SLSQP``, ``L-BFGS-B``, ``BFGS``, ``CG``, ``TNC``) ezzel a lépéssel becsülnek
gradienst::

    g ≈ [f(x + h) − f(x)] / h

Ha a célfüggvény **zaja** (``noise_floor_ha``) összemérhető vagy nagyobb ennél a
lépésnél, a számláló tisztán zajt tartalmaz, és a becsült gradiens értelmetlen.

Mért példa (H2, az optimum közelében — TR-F01M):

===================  ==========================  ===================
Platform             ``f(x+h) − f(x)``           becsült gradiens
===================  ==========================  ===================
qiskit_statevector   +6.66 × 10⁻¹⁶               +4.47 × 10⁻⁸  ✅
cirq_simulator       +2.22 × 10⁻¹⁶               +1.49 × 10⁻⁸  ✅
**qsim**             **−1.13 × 10⁻⁷**            **−7.61**  ❌
===================  ==========================  ===================

A qsim becsült gradiense **nyolc nagyságrenddel** téves — nem hiba, hanem a
``complex64`` aritmetika elkerülhetetlen következménye.
"""

GRADIENT_BASED_OPTIMIZERS: Final[frozenset[str]] = frozenset(
    {"SLSQP", "L-BFGS-B", "BFGS", "CG", "TNC"}
)
"""SciPy-metódusok, amelyek véges differenciákkal becsülnek gradienst.

Ezek **alacsony pontosságú vagy zajos** célfüggvényen megbízhatatlanok.
"""

DERIVATIVE_FREE_OPTIMIZERS: Final[frozenset[str]] = frozenset({"COBYLA", "Powell", "Nelder-Mead"})
"""SciPy-metódusok, amelyek **nem** becsülnek gradienst.

Zajos célfüggvényen ezek a helyes választás. Áruk a több
célfüggvény-kiértékelés — ami valódi hardveren QPU-időre fordul.
"""


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    """Egy platform-backend objektív tulajdonságai.

    Attributes:
        backend: A konfigurációban használt azonosító.
        platform: A mögöttes szoftverplatform.
        precision: Az állapotvektor számábrázolása.
        machine_epsilon: Az aritmetika gépi epszilonja.
        noise_floor_ha: A célfüggvény **mért** kiértékelési zaja Hartree-ban.
            Ez dönti el, használható-e véges differenciás gradiens.
        tolerance_ha: Az elfogadható eltérés a referenciától, Hartree-ban.
            **Nem** „ami éppen átmegy", hanem a számábrázolásból levezetett érték
            (lásd ``docs/plan/phase_01m.md``, 5. fejezet).
        exact: Egzakt (állapotvektor-alapú) kiértékelés-e, vagy mintavételes.
        requires_quota: Fogyaszt-e külső, korlátozott erőforrást (QPU-idő).
        deterministic: Azonos seed mellett bitre azonos eredményt ad-e.
        recommended_optimizer: A platformhoz **mérésekkel** igazolt alapértelmezés.
        description: Rövid, ember által olvasható leírás.
    """

    backend: BackendKind
    platform: PlatformName
    precision: Precision
    machine_epsilon: float
    noise_floor_ha: float
    tolerance_ha: float
    exact: bool
    requires_quota: bool
    deterministic: bool
    recommended_optimizer: str
    description: str

    @property
    def gradient_safe(self) -> bool:
        """Használható-e rajta véges differenciás gradiens-becslés.

        Feltétel: a zajszintnek **nagyságrendekkel** a véges-differencia lépésköz
        alatt kell lennie, különben a becsült gradiens zajból származik.
        Konzervatív küszöb: a lépésköz századrésze.
        """
        return self.noise_floor_ha < SCIPY_FINITE_DIFFERENCE_STEP * 1e-2

    @property
    def gradient_error_factor(self) -> float:
        """A véges differenciás gradiens-becslés nagyságrendi hibaszorzója.

        ``noise_floor / h`` — ennyivel téveszthet a becsült gradiens. 1.0 alatti
        érték megbízható becslést jelent.
        """
        return self.noise_floor_ha / SCIPY_FINITE_DIFFERENCE_STEP

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
        # Mért: f(x+h) − f(x) = 6.66e−16 az optimum közelében (TR-F01M).
        noise_floor_ha=1e-15,
        tolerance_ha=1e-9,
        exact=True,
        requires_quota=False,
        deterministic=True,
        recommended_optimizer="SLSQP",
        description="Qiskit StatevectorEstimator — egzakt, kétszeres pontosságú referencia.",
    ),
    "cirq_simulator": PlatformInfo(
        backend="cirq_simulator",
        platform="cirq",
        precision="complex128",
        machine_epsilon=_EPS_64,
        # Mért: f(x+h) − f(x) = 2.22e−16 az optimum közelében (TR-F01M).
        noise_floor_ha=1e-15,
        tolerance_ha=1e-9,
        exact=True,
        requires_quota=False,
        deterministic=True,
        recommended_optimizer="SLSQP",
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
        # Mért: f(x+h) − f(x) = 1.13e−07 az optimum közelében (TR-F01M).
        # Ez NAGYOBB a véges-differencia lépésköznél (1.49e−08), ezért a
        # gradiens-alapú optimalizálók itt nem használhatók.
        noise_floor_ha=1.2e-7,
        tolerance_ha=1e-5,
        exact=True,
        requires_quota=False,
        deterministic=True,
        # Mért: Powell 2.90e−08, Nelder-Mead 9.87e−09, COBYLA 4.14e−07 hibát ad,
        # míg az SLSQP 1.46e−02-t (TR-F01M, 2. szakasz).
        recommended_optimizer="Powell",
        description=(
            "Google qsim — C++-ban optimalizált szimulátor. EGYSZERES pontosságú "
            "(complex64), cserébe 4-9x gyorsabb a cirq.Simulator-nál (mért, 12-24 qubit). "
            "DERIVÁLTMENTES optimalizálót igényel."
        ),
    ),
    "qiskit_aer_shot": PlatformInfo(
        backend="qiskit_aer_shot",
        platform="qiskit",
        precision="complex128",
        machine_epsilon=_EPS_64,
        # Mért: 8192 lövésnél a szórás ~1e-2 Ha nagyságrendű.
        noise_floor_ha=1e-2,
        tolerance_ha=5e-2,
        exact=False,
        requires_quota=False,
        deterministic=True,
        recommended_optimizer="COBYLA",
        description="Qiskit Aer — véges lövésszám (8192), zajmodell nélkül (L3a).",
    ),
    "qiskit_aer_noisy": PlatformInfo(
        backend="qiskit_aer_noisy",
        platform="qiskit",
        precision="complex128",
        machine_epsilon=_EPS_64,
        # Mért: FakeManilaV2 zajjal a hiba ~1.5e-2 Ha.
        noise_floor_ha=2e-2,
        tolerance_ha=5e-2,
        exact=False,
        requires_quota=False,
        deterministic=True,
        recommended_optimizer="COBYLA",
        description="Qiskit Aer — FakeManilaV2 kalibrációs zajmodellel (L3b).",
    ),
    "ibm_qpu": PlatformInfo(
        backend="ibm_qpu",
        platform="qiskit",
        precision="complex128",
        machine_epsilon=_EPS_64,
        # Heron QPU tipikus mérési hiba ~1-3e-2 Ha.
        noise_floor_ha=2e-2,
        tolerance_ha=1e-1,
        exact=False,
        requires_quota=True,
        deterministic=False,
        recommended_optimizer="COBYLA",
        description="IBM Quantum — valódi szupravezető QPU (Heron processzor, L5).",
    ),
}
"""A platform-backendek nyilvántartása.

A Fázis 3 (hibaenyhített backendek) újabb bejegyzésekkel bővíti.
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


def check_optimizer_compatibility(backend: BackendKind, method: str) -> str | None:
    """Figyelmeztető szöveg, ha az optimalizáló nem illik a platformhoz.

    A gradiens-alapú optimalizálók **csendben rossz eredményt** adnak alacsony
    pontosságú vagy zajos platformon: nem hibával állnak el, hanem konvergáltnak
    jelentett, de téves minimumot találnak. Ez a projekt egyik legveszélyesebb
    hibamódja, ezért explicit figyelmeztetést adunk.

    Args:
        backend: A platform-backend azonosítója.
        method: A SciPy optimalizáló-metódus neve.

    Returns:
        A figyelmeztetés szövege, vagy ``None``, ha a kombináció rendben van.
    """
    info = platform_of(backend)
    if method not in GRADIENT_BASED_OPTIMIZERS or info.gradient_safe:
        return None
    return (
        f"a(z) {method!r} gradiens-alapú optimalizáló a(z) {backend!r} platformon "
        f"MEGBÍZHATATLAN: a célfüggvény zajszintje ({info.noise_floor_ha:.1e} Ha) "
        f"{info.gradient_error_factor:.0f}-szerese a SciPy véges-differencia "
        f"lépésközének ({SCIPY_FINITE_DIFFERENCE_STEP:.2e}), ezért a becsült "
        f"gradiens zajból származik. Az optimalizáló CSENDBEN téves minimumot "
        f"találhat. Ajánlott helyette: {info.recommended_optimizer!r} vagy más "
        f"deriváltmentes módszer ({', '.join(sorted(DERIVATIVE_FREE_OPTIMIZERS))})."
    )
