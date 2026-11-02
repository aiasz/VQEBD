"""Automatizálás: hibaosztályozás, újrapróbálkozás, pipeline (Fázis 6, ``docs/plan/phase_06.md``).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations

from vqebd.pipeline.errors import ErrorClass, classify, known_secrets, scrub_secrets
from vqebd.pipeline.retry import AttemptResult, RetryPolicy, run_with_retry

__all__ = [
    "AttemptResult",
    "ErrorClass",
    "RetryPolicy",
    "classify",
    "known_secrets",
    "run_with_retry",
    "scrub_secrets",
]
