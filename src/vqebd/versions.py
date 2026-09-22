"""Környezet-ujjlenyomat: a futásidejű csomagverziók összegyűjtése.

A kvantum-szoftverstack gyorsan változik: ugyanaz a kód más Qiskit- vagy
PySCF-verzióval eltérő eredményt adhat. Egy benchmark-eredmény ezért csak akkor
értelmezhető, ha **magával hordozza a környezetét**.

Ez a modul ezt a környezet-ujjlenyomatot állítja elő. A Fázis 4 adatsémájában
minden eredményrekord tárolja.

Lásd: ``docs/plan/00_master_plan.md`` 4.4, ``docs/adr/ADR-0004-adattarolas.md``.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import hashlib
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Final

__all__ = ["TRACKED_PACKAGES", "environment_fingerprint", "package_versions", "runtime_info"]

TRACKED_PACKAGES: Final[tuple[str, ...]] = (
    "qiskit",
    "qiskit-aer",
    "qiskit-nature",
    "qiskit-algorithms",
    "qiskit-ibm-runtime",
    "pyscf",
    "numpy",
    "scipy",
    "mitiq",
    "cirq-core",
    "qsimcirq",
)
"""A nyomon követett csomagok.

A ``qiskit-algorithms`` azért szerepel, mert tranzitívan települ, és a jelenléte
befolyásolhatja a viselkedést — noha nem hívjuk (ADR-0002). A ``mitiq`` és a
``cirq-core`` opcionális: hiányuk ``"nincs telepítve"`` értékként jelenik meg,
nem hiba.
"""

NOT_INSTALLED: Final[str] = "nincs telepítve"


def package_versions(packages: tuple[str, ...] = TRACKED_PACKAGES) -> dict[str, str]:
    """A megadott csomagok telepített verziói.

    A nem telepített csomagokhoz :data:`NOT_INSTALLED` érték tartozik — a hiány
    maga is információ, ezért nem hagyjuk ki a szótárból.
    """
    result: dict[str, str] = {}
    for name in packages:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = NOT_INSTALLED
    return result


def runtime_info() -> dict[str, str]:
    """A Python-értelmező és a platform azonosítói.

    A lebegőpontos eredmények az utolsó bitekben függhetnek a processzor-
    architektúrától és a BLAS-implementációtól, ezért ezt is rögzítjük.
    """
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "machine": platform.machine(),
    }


def environment_fingerprint() -> str:
    """A teljes környezet stabil SHA-256 ujjlenyomata (64 hexa karakter).

    Két eredmény akkor és csak akkor hasonlítható össze fenntartás nélkül, ha
    ez az ujjlenyomat megegyezik.
    """
    parts = {**package_versions(), **runtime_info()}
    canonical = ";".join(f"{key}={parts[key]}" for key in sorted(parts))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
