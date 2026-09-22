"""Az IBM-hitelesítő adatok kezelésének egységtesztjei.

A legfontosabb állítás nem az, hogy a betöltés működik — hanem hogy a **token
nem szivárog**: sem naplóba, sem kivételüzenetbe, sem ``repr()``-be.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vqebd.credentials import (
    DEFAULT_CHANNEL,
    CredentialsNotFoundError,
    IbmCredentials,
    load_ibm_credentials,
    mask_secret,
)

pytestmark = pytest.mark.unit

# Nem valódi token: az IBM Cloud API-kulcsok 44 karakteresek, ezt utánozzuk.
FAKE_TOKEN = "T3stT0k3n" + "x" * 32 + "End"


# --- Maszkolás ---------------------------------------------------------------


def test_mask_secret_hides_the_middle() -> None:
    masked = mask_secret(FAKE_TOKEN)
    assert FAKE_TOKEN not in masked
    assert masked.startswith("T3s")
    assert f"{len(FAKE_TOKEN)} karakter" in masked


def test_mask_secret_hides_short_values_completely() -> None:
    """Rövid értéknél semmi nem maradhat látható."""
    assert "abc" not in mask_secret("abcdef")


def test_mask_secret_handles_empty_input() -> None:
    assert mask_secret("") == "<üres>"


# --- Szivárgás elleni védelem ------------------------------------------------


def test_repr_never_contains_the_token() -> None:
    """A ``repr()`` az, ami naplóba és hibaüzenetbe kerül — ott nem lehet titok."""
    credentials = IbmCredentials(token=FAKE_TOKEN, source="teszt")
    assert FAKE_TOKEN not in repr(credentials)
    assert FAKE_TOKEN not in str(credentials)


def test_token_is_not_in_the_dataclass_repr_fields() -> None:
    """A ``token`` mező ``repr=False`` — ezt a dataclass-metaadat is rögzíti."""
    import dataclasses

    fields = {f.name: f for f in dataclasses.fields(IbmCredentials)}
    assert fields["token"].repr is False


def test_reveal_returns_the_raw_token() -> None:
    """A kiolvasás explicit hívás — a kódban látható, hol kerül elő a titok."""
    assert IbmCredentials(token=FAKE_TOKEN).reveal() == FAKE_TOKEN


def test_masked_helper_matches_mask_secret() -> None:
    credentials = IbmCredentials(token=FAKE_TOKEN)
    assert credentials.masked() == mask_secret(FAKE_TOKEN)


# --- Validálás ---------------------------------------------------------------


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_token_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="nem lehet üres"):
        IbmCredentials(token=value)


def test_suspiciously_short_token_is_rejected() -> None:
    """A csonkolt vagy elgépelt token azonnal bukjon el, ne az IBM-nél."""
    with pytest.raises(ValueError, match="gyanúsan rövid"):
        IbmCredentials(token="rovid-token")


def test_short_token_error_does_not_leak_the_value() -> None:
    secret = "titkos-de-rovid"
    with pytest.raises(ValueError) as excinfo:
        IbmCredentials(token=secret)
    assert secret not in str(excinfo.value)


# --- Betöltési források ------------------------------------------------------


def test_loads_from_environment_variable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", FAKE_TOKEN)
    credentials = load_ibm_credentials(tmp_path)
    assert credentials.reveal() == FAKE_TOKEN
    assert "környezeti változó" in credentials.source
    assert credentials.channel == DEFAULT_CHANNEL


def test_loads_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    (tmp_path / ".env").write_text(
        f"# megjegyzés\nIBM_QUANTUM_TOKEN={FAKE_TOKEN}\nIBM_QUANTUM_CHANNEL=ibm_cloud\n",
        encoding="utf-8",
    )
    credentials = load_ibm_credentials(tmp_path)
    assert credentials.reveal() == FAKE_TOKEN
    assert credentials.channel == "ibm_cloud"
    assert ".env" in credentials.source


def test_loads_from_ibm_token_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Az IBM Cloud konzol által letöltött JSON-formátum."""
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    (tmp_path / "IBM.token").write_text(
        json.dumps(
            {
                "name": "vqebd",
                "description": "IBM Quantum API key",
                "createdAt": "2026-09-22T12:00+0000",
                "apikey": FAKE_TOKEN,
            }
        ),
        encoding="utf-8",
    )
    credentials = load_ibm_credentials(tmp_path)
    assert credentials.reveal() == FAKE_TOKEN
    assert "IBM.token" in credentials.source


def test_loads_from_raw_token_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nyers, egysoros token is elfogadható."""
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    (tmp_path / "IBM.token").write_text(FAKE_TOKEN + "\n", encoding="utf-8")
    assert load_ibm_credentials(tmp_path).reveal() == FAKE_TOKEN


def test_environment_takes_priority_over_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dokumentált prioritási sorrend betartása."""
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", FAKE_TOKEN)
    (tmp_path / "IBM.token").write_text(json.dumps({"apikey": "M" * 44}), encoding="utf-8")
    assert load_ibm_credentials(tmp_path).reveal() == FAKE_TOKEN


def test_env_file_takes_priority_over_token_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    (tmp_path / ".env").write_text(f"IBM_QUANTUM_TOKEN={FAKE_TOKEN}\n", encoding="utf-8")
    (tmp_path / "IBM.token").write_text(json.dumps({"apikey": "M" * 44}), encoding="utf-8")
    assert load_ibm_credentials(tmp_path).reveal() == FAKE_TOKEN


# --- Hibakezelés -------------------------------------------------------------


def test_missing_credentials_raise_with_all_sources_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    with pytest.raises(CredentialsNotFoundError) as excinfo:
        load_ibm_credentials(tmp_path)
    message = str(excinfo.value)
    assert "IBM_QUANTUM_TOKEN" in message
    assert ".env" in message
    assert "IBM.token" in message


def test_json_without_a_key_field_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    (tmp_path / "IBM.token").write_text(json.dumps({"name": "x", "note": "y"}), encoding="utf-8")
    with pytest.raises(CredentialsNotFoundError, match="apikey"):
        load_ibm_credentials(tmp_path)


def test_empty_env_value_falls_through_to_the_next_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Üres környezeti változó nem „nyeli el" a következő forrást."""
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", "")
    (tmp_path / "IBM.token").write_text(json.dumps({"apikey": FAKE_TOKEN}), encoding="utf-8")
    assert load_ibm_credentials(tmp_path).reveal() == FAKE_TOKEN
