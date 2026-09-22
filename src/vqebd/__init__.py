"""VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard.

Konténerizált, reprodukálható rendszer kis molekulák (H2, LiH, BeH2) alapállapoti
energiájának VQE-alapú számítására, hibaenyhítési stratégiák összehasonlítására
szimulátoron és valódi IBM-hardveren.

A csomag rétegei
----------------
``vqebd.chemistry``
    Molekula → fermionos Hamilton-operátor → qubit-Hamilton-operátor (PySCF, Qiskit Nature).
``vqebd.vqe``
    Ansatz-építés és a saját VQE optimalizáló-hurok (V2 primitívek + SciPy).
``vqebd.mitigation``
    Pluginalapú hibaenyhítési stratégiák (``none``, ``zne_local``, ``zne_mitiq``, ``zne_runtime``).
``vqebd.backends``
    Backend-absztrakció: egzakt állapotvektor, Aer (zajmentes/zajos), IBM QPU.
``vqebd.storage``
    Sémaverziózott, append-only eredménytárolás (SQLite) és export.

Dokumentáció
------------
- Mesterterv: ``docs/plan/00_master_plan.md``
- Architektúra-döntések: ``docs/adr/``
- Hivatkozásjegyzék: ``docs/references.md``

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["AUTHORS", "LICENSE", "__version__"]

AUTHORS: tuple[str, ...] = ("Kormos Attila", "Claude AI (Anthropic, Claude Opus 5)")
LICENSE: str = "MIT"

_UNKNOWN_VERSION = "0.0.0+unknown"


def _read_version() -> str:
    """A verzió beolvasása a repó gyökerében lévő ``VERSION`` fájlból.

    A ``VERSION`` fájl az egyetlen igazságforrás (lásd ``docs/plan/00_master_plan.md``
    8.1). Telepített csomag esetén először a disztribúció metaadatát próbáljuk,
    mert wheelből a repó ``VERSION`` fájlja nem elérhető.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("vqebd")
        except PackageNotFoundError:
            pass
    except ImportError:  # pragma: no cover — csak nagyon régi Pythonon fordulhat elő
        pass

    # Fejlesztői (src-layout, PYTHONPATH-alapú) futtatás: src/vqebd/ -> src/ -> repó gyökér
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return _UNKNOWN_VERSION


__version__: str = _read_version()
