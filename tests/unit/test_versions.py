"""A környezet-ujjlenyomat egységtesztjei.

Minden eredményrekord magával hordozza a futáskori csomagverziókat. Enélkül a
benchmark-adat később nem lenne értelmezhető: ugyanaz a kód más Qiskit-verzióval
más eredményt adhat.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

from vqebd.versions import (
    NOT_INSTALLED,
    TRACKED_PACKAGES,
    environment_fingerprint,
    package_versions,
    runtime_info,
)

pytestmark = pytest.mark.unit


def test_every_tracked_package_appears() -> None:
    """A hiányzó csomag is megjelenik — a hiány maga is információ."""
    versions = package_versions()
    assert set(versions) == set(TRACKED_PACKAGES)


def test_missing_packages_are_marked_not_installed() -> None:
    """Nem létező csomag esetén értelmes jelölés, nem kivétel."""
    versions = package_versions(("ez-a-csomag-biztosan-nem-letezik-12345",))
    assert versions["ez-a-csomag-biztosan-nem-letezik-12345"] == NOT_INSTALLED


def test_qiskit_algorithms_is_tracked_even_though_unused() -> None:
    """A ``qiskit-algorithms`` tranzitívan települ, és nem hívjuk (ADR-0002).

    A verzióját mégis rögzítjük: a jelenléte befolyásolhatja a környezetet, és a
    reprodukáláshoz tudni kell, mi volt telepítve.
    """
    assert "qiskit-algorithms" in TRACKED_PACKAGES


def test_optional_packages_are_tracked() -> None:
    """A Mitiq opcionális (GPL-3.0 elkülönítés, ADR-0003), de követjük."""
    assert "mitiq" in TRACKED_PACKAGES


def test_runtime_info_has_the_expected_keys() -> None:
    info = runtime_info()
    assert set(info) == {"python", "implementation", "system", "machine"}
    assert info["python"].startswith("3.")


def test_environment_fingerprint_is_a_sha256_hex_digest() -> None:
    fingerprint = environment_fingerprint()
    assert len(fingerprint) == 64
    assert all(ch in "0123456789abcdef" for ch in fingerprint)


def test_environment_fingerprint_is_stable_within_a_run() -> None:
    """Ugyanabban a környezetben kétszer hívva ugyanazt adja."""
    assert environment_fingerprint() == environment_fingerprint()


def test_own_version_is_tracked() -> None:
    """A kódverzió a rekord része (v0.7.1): mintavételi modell-váltás azonos függőségek mellett."""
    from vqebd import __version__

    assert package_versions()["vqebd"] == __version__
