"""Hibaosztályozás és titoktalanítás (Fázis 6, ADR-0008).

Az osztályozás **konzervatív**: ami nincs a szabálytáblában, ``permanent``. Egy
rosszul osztályozott átmeneti hiba egy elmaradt újrapróbálás (pótolható), egy
rosszul osztályozott tartós hiba viszont hardveren fogyasztott kvóta.

A ``transient`` szabályok **feltevések**, amíg valódi IBM-hibákkal nem erősítik meg
(``docs/plan/phase_06.md`` 2. fejezet); a megfigyelt IBM-hibák (403 lejárt token,
``InvalidAccountError``) mindkettő tartós volt.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)
Licenc: MIT
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Final, Literal

from vqebd.hardware import EvaluationBudgetExceededError, QuotaExhaustedError

__all__ = ["ErrorClass", "classify", "known_secrets", "scrub_secrets"]

ErrorClass = Literal["transient", "permanent", "quota"]

_TRANSIENT_NAMES: Final[frozenset[str]] = frozenset(
    {"ConnectionError", "Timeout", "ConnectTimeout", "ReadTimeout", "TimeoutError"}
)
"""A kivétel-osztályhierarchiában (MRO) keresett nevek. Név szerint, hogy a ``requests``
és az IBM Runtime hibái importálás nélkül osztályozhatók legyenek."""

_RETRYABLE_HTTP: Final[frozenset[int]] = frozenset({408, 425, 429, 500, 502, 503, 504})


def classify(exc: BaseException) -> ErrorClass:
    """A kivétel osztálya: ``quota`` / ``transient`` / ``permanent``.

    Sorrend: (1) kvótahibák; (2) HTTP-státuszt hordozó kivétel (``status_code``):
    átmeneti, ha a kód újrapróbálható, különben tartós; (3) átmeneti kivételnevek az
    osztályhierarchiában; (4) minden más tartós.
    """
    if isinstance(exc, QuotaExhaustedError | EvaluationBudgetExceededError):
        return "quota"
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return "transient" if status in _RETRYABLE_HTTP else "permanent"
    if any(cls.__name__ in _TRANSIENT_NAMES for cls in type(exc).__mro__):
        return "transient"
    return "permanent"


_CRN_PATTERN: Final[re.Pattern[str]] = re.compile(r"crn:v1:[^\s'\"<>,;)]+")
_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b[A-Za-z0-9_-]{40,}\b")
_MIN_SECRET_LENGTH: Final[int] = 8
_MASK: Final[str] = "***"


def scrub_secrets(text: str, secrets: Iterable[str] = ()) -> str:
    """Titoktalanítás tárolás és naplózás előtt.

    Három réteg: (1) a kapott titkok (pl. a betöltött token és CRN) szó szerint;
    (2) IBM CRN-minta (``crn:v1:…``); (3) minden 40+ karakteres, betű-számjegy-kötőjel-
    aláhúzás karaktersorozat (API-kulcs alakú). A (3) szándékosan agresszív: egy hosszú
    azonosító (pl. egy job-azonosító) is maszkolódik, ami elfogadható ár a titokszivárgás
    ellen.
    """
    for secret in secrets:
        if secret and len(secret) >= _MIN_SECRET_LENGTH:
            text = text.replace(secret, _MASK)
    text = _CRN_PATTERN.sub(_MASK, text)
    return _KEY_PATTERN.sub(_MASK, text)


def known_secrets() -> tuple[str, ...]:
    """A betöltött IBM-hitelesítő adatok titkos értékei (token, CRN), ha vannak.

    Soha nem dob kivételt: ha nincs hitelesítő adat, üres a visszatérési érték. A
    visszaadott értékeket csak :func:`scrub_secrets`-nek szabad átadni.
    """
    from vqebd.credentials import CredentialsNotFoundError, load_ibm_credentials

    try:
        creds = load_ibm_credentials()
    except (CredentialsNotFoundError, ValueError, OSError):
        return ()
    return tuple(v for v in (creds.reveal(), creds.instance) if v)
