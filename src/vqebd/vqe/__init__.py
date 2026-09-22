"""VQE-réteg: ansatz-építés és a saját optimalizáló-hurok.

A hurok **nem** a ``qiskit-algorithms`` csomagra épül, hanem V2 primitívekre és a
SciPy-ra. Indoklás: a V2 primitívek a Qiskit 2.x-ben is léteznek, így a kód
előre-hordozható marad. Lásd: ``docs/adr/ADR-0002-sajat-vqe-hurok.md``.

Modulok
-------
:mod:`~vqebd.vqe.ansatz`
    UCCSD próbaállapot Hartree–Fock kezdőállapottal.
:mod:`~vqebd.vqe.optimizer`
    SciPy-burkolat konvergencia-naplóval.
:mod:`~vqebd.vqe.result`
    A strukturált :class:`~vqebd.vqe.result.VQEResult`.
:mod:`~vqebd.vqe.runner`
    A ``run_vqe()`` belépési pont és a parancssori felület.
"""

from __future__ import annotations

from vqebd.vqe.ansatz import AnsatzBundle, build_ansatz
from vqebd.vqe.optimizer import OptimizationOutcome, minimize_energy
from vqebd.vqe.result import VQEResult
from vqebd.vqe.runner import run_vqe

__all__ = [
    "AnsatzBundle",
    "OptimizationOutcome",
    "VQEResult",
    "build_ansatz",
    "minimize_energy",
    "run_vqe",
]
