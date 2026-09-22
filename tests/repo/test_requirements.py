"""AC-1.11 — a függőségrögzítés épsége.

A projekt terméke a **reprodukálhatóság**, ezért a függőségkezelés maga is
tesztelt felület:

``requirements.txt``
    A **közvetlen** függőségek, mindegyik `==` pinnel és írásos indoklással.
``requirements.lock``
    A **teljes, tranzitív** fa a megépült image-ből (`pip freeze --all`).

Ha a kettő elcsúszik egymástól, az eredmények utólag nem reprodukálhatók — ezt
kapják el az alábbi tesztek.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# A Fázis 1 stackjének kötelező elemei (docs/adr/ADR-0001-technologiai-stack.md).
REQUIRED_PINS: dict[str, str] = {
    "numpy": "1.26.4",
    "scipy": "1.13.1",
    "qiskit": "1.4.6",
    "qiskit-aer": "0.17.2",
    "qiskit-nature": "0.7.2",
    "qiskit-ibm-runtime": "0.41.1",
    "pyscf": "2.14.0",
    "ply": "3.11",
    # Fázis 1M — a második platform (ADR-0006)
    "cirq-core": "1.4.1",
    "qsimcirq": "0.22.1",
    "matplotlib": "3.11.2",
}

# A mitiq GPL-3.0 licencű; opcionális, futásidőben betöltött komponens (ADR-0003).
FORBIDDEN_IN_REQUIREMENTS: frozenset[str] = frozenset({"mitiq"})

_PIN_RE = re.compile(r"^([A-Za-z0-9._-]+)==([^\s;#]+)")


def _parse_pins(path: Path) -> dict[str, str]:
    """Csomagnév → verzió leképezés egy requirements-fájlból.

    A neveket a PEP 503 szerint normalizáljuk (kisbetű, ``_``/``.`` → ``-``),
    mert a ``pip freeze`` és a kézzel írt fájl eltérő írásmódot használhat.
    """
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _PIN_RE.match(stripped)
        if match:
            name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
            pins[name] = match.group(2)
    return pins


@pytest.fixture(scope="module")
def direct_pins(repo_root: Path) -> dict[str, str]:
    return _parse_pins(repo_root / "requirements.txt")


@pytest.fixture(scope="module")
def locked_pins(repo_root: Path) -> dict[str, str]:
    return _parse_pins(repo_root / "requirements.lock")


# --- Létezés -----------------------------------------------------------------


def test_lock_file_exists(repo_root: Path) -> None:
    """A tranzitív függőségek rögzítve vannak."""
    lock = repo_root / "requirements.lock"
    assert lock.is_file(), (
        "hiányzik a requirements.lock. Generálás: "
        "docker run --rm vqebd:<verzió> python -m pip freeze --all > requirements.lock"
    )


def test_lock_file_is_substantial(locked_pins: dict[str, str]) -> None:
    """A lock-fájl a teljes fát tartalmazza, nem csak a közvetlen függőségeket."""
    assert len(locked_pins) >= 30, (
        f"a requirements.lock csak {len(locked_pins)} csomagot tartalmaz; "
        "ez kevés a teljes tranzitív fához"
    )


# --- Konzisztencia -----------------------------------------------------------


@pytest.mark.parametrize(("package", "version"), sorted(REQUIRED_PINS.items()))
def test_required_package_is_pinned(
    direct_pins: dict[str, str], package: str, version: str
) -> None:
    """Minden kötelező csomag pontos verzióval szerepel a requirements.txt-ben."""
    assert package in direct_pins, f"a requirements.txt-ből hiányzik: {package}"
    assert direct_pins[package] == version, (
        f"{package}: a requirements.txt {direct_pins[package]}-t ír elő, "
        f"az ADR-0001 viszont {version}-t"
    )


@pytest.mark.parametrize(("package", "version"), sorted(REQUIRED_PINS.items()))
def test_lock_matches_direct_pin(locked_pins: dict[str, str], package: str, version: str) -> None:
    """A lock-fájl ugyanazt a verziót rögzíti, mint a requirements.txt.

    Elcsúszás esetén a dokumentált és a ténylegesen telepített stack eltérne —
    és az eredmények nem lennének reprodukálhatók.
    """
    assert package in locked_pins, f"a requirements.lock-ból hiányzik: {package}"
    assert locked_pins[package] == version, (
        f"{package}: a lock {locked_pins[package]}-t rögzít, a pin {version}"
    )


def test_every_direct_pin_appears_in_the_lock(
    direct_pins: dict[str, str], locked_pins: dict[str, str]
) -> None:
    """Minden közvetlen függőség megjelenik a lock-fájlban is."""
    missing = sorted(set(direct_pins) - set(locked_pins))
    assert not missing, f"a requirements.lock-ból hiányzó közvetlen függőségek: {missing}"


def test_direct_and_lock_versions_never_conflict(
    direct_pins: dict[str, str], locked_pins: dict[str, str]
) -> None:
    """Egyetlen közvetlen függőség verziója sem tér el a lock-ban rögzítettől."""
    conflicts = {
        name: (direct_pins[name], locked_pins[name])
        for name in direct_pins
        if name in locked_pins and direct_pins[name] != locked_pins[name]
    }
    assert not conflicts, f"verzióütközés (requirements.txt vs lock): {conflicts}"


# --- Licencelkülönítés -------------------------------------------------------


@pytest.mark.parametrize("package", sorted(FORBIDDEN_IN_REQUIREMENTS))
def test_gpl_package_is_not_a_direct_dependency(direct_pins: dict[str, str], package: str) -> None:
    """A GPL-3.0 licencű Mitiq nem lehet kötelező függőség (ADR-0003).

    A VQEBD MIT licencű. A Mitiq opcionális, futásidőben betöltött komponens,
    és a nélküle is teljes funkcionalitást automatikus teszt őrzi.
    """
    assert package not in direct_pins, (
        f"a(z) '{package}' csomag GPL-3.0 licencű, ezért nem lehet a "
        "requirements.txt-ben. Helye: requirements-mitiq.txt (ADR-0003)."
    )


# --- Nyomon követés ----------------------------------------------------------


def test_tracked_packages_cover_the_direct_dependencies(
    direct_pins: dict[str, str],
) -> None:
    """Minden közvetlen függőség verziója bekerül az eredményrekordba.

    A ``ply`` kivétel: nincs hozzá ``importlib.metadata`` szerinti érdemi
    információ a benchmark szempontjából, és csak a Mitiq-interfész igényli.
    """
    from vqebd.versions import TRACKED_PACKAGES

    tracked = {re.sub(r"[-_.]+", "-", name).lower() for name in TRACKED_PACKAGES}
    untracked = sorted(set(direct_pins) - tracked - {"ply", "matplotlib"})
    assert not untracked, (
        f"nem követett közvetlen függőségek: {untracked}. "
        "Vedd fel őket a vqebd.versions.TRACKED_PACKAGES listába."
    )
