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

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations

import itertools
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

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


@pytest.fixture
def record_factory() -> Callable[..., dict[str, Any]]:
    """Teljes, érvényes ``results``-rekordot gyártó függvény (a dashboard- és tárolótesztekhez).

    Az alapértelmezett rekord egy egzakt H₂-futás 0.735 Å-nél; a ``run_id`` automatikusan
    egyedi, az ``overrides`` bármely mezőt felülír. Az időbélyegek növekvők, így a
    ``query_results`` (timestamp szerint csökkenő) sorrendje determinisztikus.
    """
    counter = itertools.count(1)

    def make(**overrides: Any) -> dict[str, Any]:
        n = next(counter)
        record: dict[str, Any] = {
            "run_id": f"rec-{n:03d}",
            "timestamp": f"2026-11-02T10:{n:02d}:00Z",
            "schema_version": 3,
            "molecule_name": "H2",
            "geometry": "H 0 0 0; H 0 0 0.735",
            "bond_length": 0.735,
            "basis": "sto3g",
            "mapper": "parity",
            "two_qubit_reduction": 1,
            "ansatz_kind": "uccsd",
            "initial_point": "zeros",
            "optimizer_method": "SLSQP",
            "optimizer_maxiter": 300,
            "n_iterations": 5,
            "n_function_evaluations": 20,
            "converged": 1,
            "optimizer_message": "ok",
            "backend": "qiskit_statevector",
            "platform": "qiskit",
            "precision": "complex128",
            "mitigation_strategy": "none",
            "energy_ha": -1.1373060358,
            "electronic_energy_ha": -1.8572750302,
            "nuclear_repulsion_ha": 0.7199689944,
            "hartree_fock_ha": -1.1169989968,
            "full_ci_ha": -1.1373060358,
            "within_chemical_accuracy": 1,
            "satisfies_variational_principle": 1,
            "master_seed": 20260922,
            "seeds_json": "{}",
            "config_hash": "0" * 64,
            "environment_fingerprint": "0" * 64,
            "versions_json": "{}",
            "wall_time_s": 0.5,
            "optimal_parameters_json": "[0.0, 0.0, -0.1117]",
        }
        record.update(overrides)
        return record

    return make
