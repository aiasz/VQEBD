"""AC-0.2 / AC-0.4 / AC-0.5 — a futtatási környezet ellenőrzése.

Ezek a tesztek a **szállított image**-et validálják. A gazdagépen futtatva a
konténer-specifikus állítások (nem-root futás, ``PYTHONHASHSEED``) kihagyásra
kerülnek, mert ott nem értelmezhetők.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import os
import sys

import pytest

pytestmark = pytest.mark.unit

# A projekt által támogatott Python-verziók. Alsó határ: a projekt célja.
# Felső határ: a mitiq `requires_python = ">=3.10,<3.13"` korlátja (ADR-0001).
SUPPORTED_MINORS: tuple[int, ...] = (11, 12)
CONTAINER_MINOR = 11  # a docker/Dockerfile python:3.11-slim alapra épül


def test_python_major_is_3() -> None:
    assert sys.version_info.major == 3


def test_python_minor_is_supported() -> None:
    assert sys.version_info.minor in SUPPORTED_MINORS, (
        f"Python 3.{sys.version_info.minor} nem támogatott; "
        f"engedélyezett: {SUPPORTED_MINORS} (ADR-0001)"
    )


def test_container_runs_python_311(in_container: bool) -> None:
    """AC-0.2 — a konténerben pontosan a Dockerfile-ban rögzített minor fusson."""
    if not in_container:
        pytest.skip("nem konténerben futunk; az AC-0.2 az image-re vonatkozik")
    assert sys.version_info.minor == CONTAINER_MINOR, (
        f"a konténer Python 3.{sys.version_info.minor}-et futtat, "
        f"de a Dockerfile 3.{CONTAINER_MINOR}-re épül"
    )


def test_container_is_not_root(in_container: bool) -> None:
    """AC-0.4 — a konténer nem root felhasználóként fut (R0.3 kockázat)."""
    if not in_container:
        pytest.skip("nem konténerben futunk; az AC-0.4 az image-re vonatkozik")
    getuid = getattr(os, "getuid", None)
    assert getuid is not None, "POSIX rendszer várt a konténerben"
    assert getuid() != 0, "a konténer root-ként fut; a Dockerfile-ban USER vqebd kell"


def test_pythonhashseed_is_deterministic(in_container: bool) -> None:
    """AC-0.5 — ``PYTHONHASHSEED=0`` a determinizmushoz (ADR-0005, 5. véletlenforrás)."""
    if not in_container:
        pytest.skip("nem konténerben futunk; az AC-0.5 az image-re vonatkozik")
    assert os.environ.get("PYTHONHASHSEED") == "0", (
        f"PYTHONHASHSEED={os.environ.get('PYTHONHASHSEED')!r}, de 0 kell (docker/Dockerfile ENV)"
    )


def test_hashing_is_actually_stable(in_container: bool) -> None:
    """A ``PYTHONHASHSEED`` deklaráción túl a tényleges hash-érték is rögzített.

    Ez erősebb állítás a környezeti változó meglétnél: azt igazolja, hogy a
    beállítás *hatályba is lépett* az értelmező indulásakor.
    """
    if not in_container:
        pytest.skip("nem konténerben futunk; az AC-0.5 az image-re vonatkozik")
    # PYTHONHASHSEED=0 mellett a str-hash determinisztikus az értelmező indulásaitól
    # függetlenül; a konkrét értéket nem rögzítjük (CPython-belső), csak azt, hogy
    # a randomizáció ki van kapcsolva.
    assert sys.flags.hash_randomization == 0, (
        "a hash-randomizáció aktív, tehát a PYTHONHASHSEED=0 nem lépett hatályba"
    )
