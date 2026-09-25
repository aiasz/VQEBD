"""Valódi QPU-használat védőkorlátai: engedély és kvóta-előellenőrzés.

Az IBM Open Plan keretét (600 QPU-s / 28 nap) a projekt más futásai is
fogyasztják. Egy beküldött job a keret kimerülése után elutasításra kerül,
vagy a keretet túllépve a következő időszakot terheli. Ezért minden hardveres
szkript beküldés **előtt**:

1. ellenőrzi az explicit engedélyt (``VQEBD_ALLOW_HARDWARE=true``);
2. lekérdezi a kvótaállást (``QiskitRuntimeService.usage()``, csak olvasás), és
   megtagadja a beküldést, ha a becsült igény nem fér bele.

Mért eset (2026-09-25): 630 / 600 s felhasználva, ``usage_limit_reached = true``,
újra elérhető 2026-10-21 — a Fázis 5 hardveres kiegészítése ezért elhalasztva.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

__all__ = [
    "HardwareNotAllowedError",
    "QuotaExhaustedError",
    "assert_hardware_allowed",
    "assert_quota_available",
    "connect_service",
    "quota_summary",
]


class HardwareNotAllowedError(PermissionError):
    """A valódi QPU használata nincs kifejezetten engedélyezve."""


class QuotaExhaustedError(RuntimeError):
    """A hátralévő QPU-kvóta nem elég a tervezett futáshoz."""


def assert_hardware_allowed() -> None:
    """Hibát ad, ha a ``VQEBD_ALLOW_HARDWARE`` nem ``true`` (alapértelmezés: tiltva)."""
    if os.environ.get("VQEBD_ALLOW_HARDWARE", "false").strip().lower() != "true":
        raise HardwareNotAllowedError(
            "valódi QPU-futtatás csak VQEBD_ALLOW_HARDWARE=true mellett engedélyezett"
        )


def quota_summary(usage: Mapping[str, Any]) -> dict[str, Any]:
    """A ``service.usage()`` válaszának a dokumentálható, nem azonosító része."""
    keys = (
        "usage_consumed_seconds",
        "usage_limit_seconds",
        "usage_remaining_seconds",
        "usage_limit_reached",
        "usage_period",
        "time_available_at",
    )
    return {k: usage.get(k) for k in keys}


def assert_quota_available(usage: Mapping[str, Any], required_seconds: float) -> None:
    """Megtagadja a beküldést, ha a kvóta nem elég.

    Args:
        usage: A ``QiskitRuntimeService.usage()`` válasza.
        required_seconds: A futás becsült QPU-igénye (másodperc), tartalékkal.

    Raises:
        QuotaExhaustedError: Ha a keret elérve, vagy a hátralévő idő kevesebb a
            becsült igénynél. Ha a válasz nem tartalmaz hátralévő időt, szintén
            megtagadjuk — ismeretlen kvótával nem küldünk be.
    """
    if required_seconds <= 0:
        raise ValueError(f"a becsült igény pozitív legyen: {required_seconds}")
    available_at = usage.get("time_available_at")
    if usage.get("usage_limit_reached"):
        raise QuotaExhaustedError(
            f"a QPU-kvóta elfogyott ({usage.get('usage_consumed_seconds')} / "
            f"{usage.get('usage_limit_seconds')} s); újra elérhető: {available_at}"
        )
    remaining = usage.get("usage_remaining_seconds")
    if remaining is None:
        raise QuotaExhaustedError("a kvótaállás nem ismert — beküldés megtagadva")
    if float(remaining) < required_seconds:
        raise QuotaExhaustedError(
            f"a hátralévő kvóta ({remaining} s) kevesebb a becsült igénynél "
            f"({required_seconds:.0f} s)"
        )


def connect_service() -> Any:
    """``QiskitRuntimeService`` a projekt hitelesítő adataival (a tokent nem írja ki)."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    from vqebd.credentials import load_ibm_credentials

    creds = load_ibm_credentials()
    kwargs: dict[str, Any] = {"channel": creds.channel, "token": creds.reveal()}
    if creds.instance:
        kwargs["instance"] = creds.instance
    return QiskitRuntimeService(**kwargs)
