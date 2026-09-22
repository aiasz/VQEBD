"""A ``vqebd`` csomag alapvető épségének ellenőrzése.

Ezek a tesztek a **kódot** vizsgálják, ezért a szállított image-ben is futnak —
nem igényelnek teljes repó-checkoutot.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

import vqebd

pytestmark = pytest.mark.unit

SUBPACKAGES: tuple[str, ...] = (
    "vqebd.backends",
    "vqebd.chemistry",
    "vqebd.mitigation",
    "vqebd.storage",
    "vqebd.vqe",
)


def test_version_is_a_semver_string() -> None:
    assert isinstance(vqebd.__version__, str)
    assert re.match(r"^\d+\.\d+\.\d+", vqebd.__version__), (
        f"a verzió nem MAJOR.MINOR.PATCH alakú: {vqebd.__version__!r}"
    )


def test_version_was_actually_resolved() -> None:
    """A tartalék érték azt jelentené, hogy sem a metaadat, sem a VERSION nem elérhető."""
    assert vqebd.__version__ != "0.0.0+unknown", (
        "a verzió feloldása nem sikerült: sem a csomag-metaadat, sem a VERSION fájl "
        "nem volt elérhető. Ellenőrizd a PYTHONPATH-t és a VERSION fájl helyét."
    )


def test_authors_are_declared() -> None:
    """A készítők feltüntetése a projekt követelménye, nem esztétika."""
    assert "Kormos Attila" in vqebd.AUTHORS
    assert any("Claude" in author for author in vqebd.AUTHORS)


def test_license_is_mit() -> None:
    assert vqebd.LICENSE == "MIT"


@pytest.mark.parametrize("module_name", SUBPACKAGES)
def test_subpackage_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module.__doc__, f"{module_name}: hiányzó modul-docstring"


@pytest.mark.parametrize("module_name", SUBPACKAGES)
def test_subpackage_declares_all(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "__all__"), f"{module_name}: hiányzó __all__"


def test_py_typed_marker_is_shipped() -> None:
    """PEP 561 — a típusinformáció csak ``py.typed`` jelölővel használható kívülről."""
    marker = Path(vqebd.__file__).parent / "py.typed"
    assert marker.is_file(), "hiányzik a src/vqebd/py.typed jelölő (PEP 561)"


def test_no_qiskit_algorithms_import_in_source() -> None:
    """ADR-0002 — a ``qiskit_algorithms`` telepítve lehet, de NEM hívhatjuk.

    A csomag a ``qiskit-nature`` tranzitív függősége. A saját VQE-hurkot V2
    primitívekkel írjuk, hogy a kód Qiskit 2.x-re átvihető maradjon. Ez a teszt
    kényszeríti ki a döntést, mielőtt az bárhol „bekúszna" a kódba.
    """
    package_dir = Path(vqebd.__file__).parent
    forbidden = re.compile(r"^\s*(?:import\s+qiskit_algorithms|from\s+qiskit_algorithms)")
    offenders: list[str] = []
    for path in package_dir.rglob("*.py"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if forbidden.match(line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert not offenders, (
        f"a qiskit_algorithms importálása tilos a src/vqebd alatt (ADR-0002): {offenders}"
    )
