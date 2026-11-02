"""Valódi QPU-használat védőkorlátai: engedély és kvóta-előellenőrzés.

Az IBM Open Plan keretét (600 QPU-s / 28 nap) a projekt más futásai is
fogyasztják. Egy beküldött job a keret kimerülése után elutasításra kerül,
vagy a keretet túllépve a következő időszakot terheli. Ezért minden hardveres
szkript beküldés **előtt**:

1. ellenőrzi az explicit engedélyt (``VQEBD_ALLOW_HARDWARE=true``);
2. lekérdezi a kvótaállást (``QiskitRuntimeService.usage()``, csak olvasás), és
   megtagadja a beküldést, ha a becsült igény nem fér bele.

A VQE-útvonalra (``run_vqe``, ``python -m vqebd --backend ibm_qpu``) ugyanez
érvényes, kiegészítve **kiértékelési kerettel**: az optimalizáló nem küldhet be
több jobot, mint amennyit a kvóta-előellenőrzés fedezett. Mért eset (2026-09-23):
a védelem nélküli útvonal 42 jobot küldött be, 15 QPU-s jobonként, és ezzel
elfogyasztotta a teljes keretet.

Mért eset (2026-09-25): 630 / 600 s felhasználva, ``usage_limit_reached = true``,
újra elérhető 2026-10-21 — a Fázis 5 hardveres kiegészítése ezért elhalasztva.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vqebd.config import VQEConfig

__all__ = [
    "QPU_SECONDS_PER_EVALUATION",
    "EvaluationBudgetExceededError",
    "HardwareNotAllowedError",
    "QuotaExhaustedError",
    "assert_block_within_budget",
    "assert_hardware_allowed",
    "assert_quota_available",
    "connect_service",
    "guard_hardware_vqe",
    "hardware_evaluation_budget",
    "quota_summary",
]

QPU_SECONDS_PER_EVALUATION = 15.0
"""Egy kiértékelés (egy job) számlázott QPU-ideje, mp. Mérve: a 2026-09-23-i 41
lefutott VQE-job mindegyike pontosan 15 s volt (``ibm_kingston``, H₂, 8192 lövés).
Nagyobb áramkörnél ez alsó becslés; a kemény kiértékelési keret ezt nem függeti."""


class HardwareNotAllowedError(PermissionError):
    """A valódi QPU használata nincs kifejezetten engedélyezve."""


class QuotaExhaustedError(RuntimeError):
    """A hátralévő QPU-kvóta nem elég a tervezett futáshoz."""


class EvaluationBudgetExceededError(RuntimeError):
    """Az optimalizáló több kiértékelést kért, mint a kvóta-előellenőrzés fedezett."""


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


def assert_block_within_budget(
    usage: Mapping[str, Any],
    required_seconds: float,
    *,
    max_used_fraction: float = 0.80,
) -> None:
    """Megtagadja a blokkot, ha a használat a kerethányad fölé menne (Fázis 11, 4. fejezet).

    A ``assert_quota_available`` csak azt nézi, hogy a hátralévő kvóta fedezi-e az igényt. A
    Fázis 11 blokkjainál ennél szigorúbb szabály él: a már használt + a tervezett idő sem
    haladhatja meg a keret ``max_used_fraction`` részét (alapértelmezés 80% = 480 s), hogy
    mindig maradjon tartalék.

    Raises:
        QuotaExhaustedError: Ha a keret vagy a használat ismeretlen, vagy a határ átlépődne.
    """
    consumed = usage.get("usage_consumed_seconds")
    limit = usage.get("usage_limit_seconds")
    if consumed is None or limit is None:
        raise QuotaExhaustedError("a kvótaállás nem ismert — beküldés megtagadva")
    if not 0.0 < max_used_fraction <= 1.0:
        raise ValueError(f"max_used_fraction (0, 1] közé essen, kapott: {max_used_fraction}")
    ceiling = float(limit) * max_used_fraction
    projected = float(consumed) + required_seconds
    if projected > ceiling:
        raise QuotaExhaustedError(
            f"a blokk után {projected:.1f} s volna használva, a {max_used_fraction:.0%}-os határ "
            f"{ceiling:.1f} s (használt: {float(consumed):.1f} s, a blokk igénye: "
            f"{required_seconds:.1f} s) — beküldés megtagadva"
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


def hardware_evaluation_budget(config: VQEConfig) -> int:
    """Egy hardveres VQE-futás kiértékeléseinek felső korlátja.

    Az optimalizáló ``maxiter`` kiértékelése, plusz a végső (újra)becslések: ``K``
    (``reestimate``, legalább 1), ZNE-nél a zajszorzók számával szorozva.
    """
    final_estimates = max(config.reestimate, 1)
    if config.mitigation.strategy != "none":
        final_estimates *= len(config.mitigation.scale_factors)
    return config.optimizer.maxiter + final_estimates


def guard_hardware_vqe(
    max_evaluations: int, *, service: Any | None = None, reserve: float = 1.0
) -> float:
    """Beküldés előtti védelem egy hardveres VQE-futásra.

    Sorrend: (1) engedély — hálózati hívás nélkül; (2) kvóta lekérdezése; (3) a
    legrosszabb eset (``max_evaluations`` × :data:`QPU_SECONDS_PER_EVALUATION`) a
    hátralévő kerethez mérve.

    Args:
        max_evaluations: A futás kiértékeléseinek felső korlátja (optimalizáló +
            újramintavételezés, ZNE-nél a zajszorzókkal szorozva).
        service: Opcionális, már csatlakozott szolgáltatás (tesztekhez).
        reserve: A becsült igény szorzója tartalékként (pl. ``1.2`` = +20%).

    Returns:
        A kvótához mért becsült QPU-igény (mp).

    Raises:
        HardwareNotAllowedError: Ha a ``VQEBD_ALLOW_HARDWARE`` nem ``true``.
        QuotaExhaustedError: Ha a kvóta nem fedezi a legrosszabb esetet.
        ValueError: Ha ``max_evaluations`` nem pozitív.
    """
    if max_evaluations < 1:
        raise ValueError(f"a kiértékelési keret legalább 1: {max_evaluations}")
    assert_hardware_allowed()
    required = max_evaluations * QPU_SECONDS_PER_EVALUATION * reserve
    usage = quota_summary((service or connect_service()).usage())
    try:
        assert_quota_available(usage, required)
    except QuotaExhaustedError as exc:
        raise QuotaExhaustedError(
            f"{exc} — a futás legfeljebb {max_evaluations} kiértékelést kérhet; "
            "csökkentsd az optimalizáló iterációkorlátját (--maxiter)"
        ) from exc
    return required
