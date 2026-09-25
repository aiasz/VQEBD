"""Batch-futtatás konfigurációs mátrixon (Fázis 5, ``docs/plan/phase_05.md``).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from vqebd.batch.aggregate import GroupStatistics, aggregate_rows
from vqebd.batch.expand import PlannedRun, expand
from vqebd.batch.run import BatchReport, run_batch
from vqebd.batch.spec import PRESETS, BatchCell, BatchSpec, get_preset

__all__ = [
    "PRESETS",
    "BatchCell",
    "BatchReport",
    "BatchSpec",
    "GroupStatistics",
    "PlannedRun",
    "aggregate_rows",
    "expand",
    "get_preset",
    "run_batch",
]
