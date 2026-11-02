"""Fázis 6 — hibaosztályozás és titoktalanítás (AC-6.2, AC-6.8).

Az IBM-hibák osztályait **nem** valódi IBM-hívás adja: a megfigyelt hibák
(``RequestsApiError`` 403, ``InvalidAccountError``) és a feltételezett átmeneti hibák
(hálózat, 429/5xx) szimulált megfelelői tesztelik a szabálytáblát.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vqebd.hardware import (
    EvaluationBudgetExceededError,
    HardwareNotAllowedError,
    QuotaExhaustedError,
)
from vqebd.pipeline.errors import classify, known_secrets, scrub_secrets

pytestmark = pytest.mark.unit


class _ApiError(Exception):
    """A ``RequestsApiError`` szimulált megfelelője: HTTP-státuszt hordoz."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class InvalidAccountError(Exception):
    """Az IBM Runtime hasonló nevű (megfigyelt) kivételének szimulált megfelelője."""


class Timeout(Exception):  # noqa: N818 - a requests.Timeout nevét szimulálja
    """A ``requests.Timeout`` szimulált megfelelője (név szerint osztályozzuk)."""


class _ReadTimeout(Timeout):
    """Leszármazott: az MRO-ban megtalálható a ``Timeout`` név."""


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (QuotaExhaustedError("elfogyott"), "quota"),
        (EvaluationBudgetExceededError("keret"), "quota"),
        (ConnectionError("hálózat"), "transient"),
        (ConnectionResetError("reset"), "transient"),
        (TimeoutError("idő"), "transient"),
        (Timeout("idő"), "transient"),
        (_ReadTimeout("idő"), "transient"),
        (_ApiError(429), "transient"),
        (_ApiError(500), "transient"),
        (_ApiError(503), "transient"),
        # megfigyelt, tartós IBM-hibák
        (_ApiError(403), "permanent"),
        (_ApiError(401), "permanent"),
        (_ApiError(404), "permanent"),
        (InvalidAccountError("Unable to retrieve instances."), "permanent"),
        # belső hibák
        (ValueError("rossz"), "permanent"),
        (KeyError("rossz"), "permanent"),
        (PermissionError("nincs engedély"), "permanent"),
        (HardwareNotAllowedError("tiltva"), "permanent"),
        (RuntimeError("váratlan"), "permanent"),
    ],
)
def test_classification_table(exc: Exception, expected: str) -> None:
    assert classify(exc) == expected


def test_unknown_exception_is_permanent() -> None:
    """Konzervatív alapértelmezés: ismeretlen = tartós (hardveren az újrapróbálás kvóta)."""

    class UnknownError(Exception):
        pass

    assert classify(UnknownError("?")) == "permanent"


def test_status_code_takes_precedence_over_name() -> None:
    """Egy 403-at hordozó, de ``ConnectionError``-ból származó kivétel tartós: a kód dönt."""

    class MixedError(ConnectionError):
        status_code = 403

    assert classify(MixedError("x")) == "permanent"


# --- titoktalanítás ----------------------------------------------------------------

TOKEN = "Zk3-" + "a" * 40  # 44 karakter, API-kulcs alakú
CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef:11111111-2222::"


def test_scrub_removes_explicit_secret() -> None:
    text = scrub_secrets(f"hitelesítés sikertelen: {TOKEN}!", [TOKEN])
    assert TOKEN not in text
    assert "***" in text


def test_scrub_removes_crn_pattern_without_being_told() -> None:
    text = scrub_secrets(f"instance {CRN} nem érhető el")
    assert "crn:v1" not in text
    assert "0123456789abcdef" not in text


def test_scrub_masks_api_key_shaped_strings_without_being_told() -> None:
    assert TOKEN not in scrub_secrets(f"kulcs={TOKEN}")


def test_scrub_leaves_ordinary_text_alone() -> None:
    text = "ValueError: a(z) (2e,50o) aktív tér a(z) 'LiH' molekulára nem értelmezhető"
    assert scrub_secrets(text) == text


def test_scrub_ignores_too_short_secrets() -> None:
    """Egy rövid érték szó szerinti cseréje ártalmas lenne (pl. ``ab`` minden szóban)."""
    assert scrub_secrets("abcabc", ["ab"]) == "abcabc"


def test_known_secrets_never_raises_without_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Hitelesítő adat nélkül (nincs env, nincs fájl) üres tuple, nem kivétel."""
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    assert known_secrets() == ()


def test_known_secrets_returns_loaded_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", TOKEN)
    assert TOKEN in known_secrets()
