"""Közös pytest-konfiguráció és fixture-ök a VQEBD tesztjeihez.

A tesztek két hatókörben futnak:

``tests/unit``, ``tests/integration``, ``tests/validation``
    A **kódot** tesztelik. Bárhol futnak: a gazdagépen, a fejlesztői
    bind-mountolt konténerben és a szállított image-ben is.

``tests/repo``
    A **repó-checkoutot** tesztelik (szerkezet, verzióegyezés, titokhigiénia).
    Ezekhez teljes repó kell; a szállított image-ben — amelybe szándékosan nem
    kerül bele a ``docs/``, a ``LICENSE`` és a ``.gitignore`` — automatikusan
    kihagyásra kerülnek, egyértelmű indoklással.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Egy könyvtár akkor tekinthető a repó gyökerének, ha MINDEGYIK jelölő megvan.
# A ``docs`` és a ``LICENSE`` szándékosan van benne: ezek nem kerülnek a futtatási
# image-be, így a szállított artefaktumban a repó-hatókörű tesztek kihagyódnak
# ahelyett, hogy félrevezetően elbuknának.
_REPO_MARKERS: tuple[str, ...] = ("pyproject.toml", "VERSION", "LICENSE", "docs", "src")


def find_repo_root() -> Path | None:
    """A repó gyökerének feloldása, vagy ``None``, ha nem érhető el.

    Sorrend:

    1. A ``VQEBD_REPO_ROOT`` környezeti változó (a konténeres tesztfuttatás ezt állítja).
    2. Felfelé haladás ettől a fájltól, amíg minden jelölő meg nem található.
    """
    env = os.environ.get("VQEBD_REPO_ROOT")
    if env:
        candidate = Path(env).resolve()
        if all((candidate / marker).exists() for marker in _REPO_MARKERS):
            return candidate
        return None

    for parent in Path(__file__).resolve().parents:
        if all((parent / marker).exists() for marker in _REPO_MARKERS):
            return parent
    return None


REPO_ROOT: Path | None = find_repo_root()

_SKIP_REASON = (
    "Nem érhető el teljes repó-checkout (hiányzik a jelölők egyike: "
    f"{', '.join(_REPO_MARKERS)}). Ez a szállított image-ben normális — a repó-hatókörű "
    "teszteket a gazdagépen futtasd, vagy bind-mountold a repót és állítsd be a "
    "VQEBD_REPO_ROOT változót."
)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """A repó gyökere.

    Ha nem érhető el teljes checkout, az ezt a fixture-t kérő tesztek — közvetlenül
    vagy közvetve — automatikusan kihagyásra kerülnek, egyértelmű indoklással.
    Ez megbízhatóbb, mint egy modulszintű ``skipif`` mark, mert nem igényel
    ``tests`` csomag-importot (a pytest ``--import-mode=importlib`` mellett az
    törékeny lenne).
    """
    if REPO_ROOT is None:
        pytest.skip(_SKIP_REASON)
    return REPO_ROOT


# A kvantum-stacket igénylő tesztmodulok a szabványos `pytest.importorskip`-et
# használják modulszinten, pl.:
#
#     pytest.importorskip("qiskit_nature", reason="a Fázis 1 kvantum-stackjét igényli")
#
# Ez nem igényel kereszt-modul importot a tests csomagból (ami az
# `--import-mode=importlib` mellett törékeny lenne), és a kihagyás indoklása
# megjelenik a `pytest -ra` kimenetben.


@pytest.fixture(scope="session")
def in_container() -> bool:
    """Igaz, ha a teszt konténerben fut.

    Felismerés: a ``/.dockerenv`` fájl jelenléte (a Docker hozza létre), vagy a
    ``VQEBD_IN_CONTAINER`` változó explicit beállítása.
    """
    return Path("/.dockerenv").exists() or os.environ.get("VQEBD_IN_CONTAINER") == "1"
