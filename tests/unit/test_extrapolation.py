"""Extrapolációs modellek egységtesztjei (AC-3.3, ADR-0003).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import numpy as np
import pytest

from vqebd.mitigation.extrapolation import (
    exponential_extrapolate,
    extrapolate,
    linear_extrapolate,
    polynomial_extrapolate,
    richardson_extrapolate,
)

pytestmark = pytest.mark.unit


def test_linear_extrapolate_exact_on_linear_data() -> None:
    """Lineáris adatokon (E(λ) = 2.0 * λ - 1.137) az extrapoláció egzakt."""
    scales = [1.0, 3.0, 5.0]
    vals = [2.0 * s - 1.137 for s in scales]
    extrapolated, _ = linear_extrapolate(scales, vals)
    assert extrapolated == pytest.approx(-1.137, abs=1e-12)


def test_richardson_extrapolate_exact_on_quadratic_data() -> None:
    """Másodfokú adatokon (E(λ) = 0.5 * λ² + 1.2 * λ - 1.137) a 3-pontos Richardson egzakt."""
    scales = [1.0, 3.0, 5.0]
    vals = [0.5 * s**2 + 1.2 * s - 1.137 for s in scales]
    extrapolated, _ = richardson_extrapolate(scales, vals)
    assert extrapolated == pytest.approx(-1.137, abs=1e-12)


def test_polynomial_extrapolate_quadratic() -> None:
    """Másodfokú illesztés egzakt másodfokú görbén."""
    scales = [1.0, 3.0, 5.0, 7.0]
    vals = [0.2 * s**2 - 0.5 * s - 1.137 for s in scales]
    extrapolated, _ = polynomial_extrapolate(scales, vals, deg=2)
    assert extrapolated == pytest.approx(-1.137, abs=1e-12)


def test_exponential_extrapolate() -> None:
    """Exponenciális adatokon (E(λ) = 1.0 - 2.137 * exp(-0.1 * λ)) jól becsül."""
    scales = [1.0, 3.0, 5.0, 7.0]
    vals = [1.0 - 2.137 * np.exp(-0.1 * s) for s in scales]
    extrapolated, _ = exponential_extrapolate(scales, vals)
    # E(0) = 1.0 - 2.137 = -1.137
    assert extrapolated == pytest.approx(-1.137, abs=1e-3)


def test_extrapolate_dispatcher() -> None:
    """A diszpécser helyesen hívja a kiválasztott modellt."""
    scales = [1.0, 3.0, 5.0]
    vals = [1.0 * s - 1.0 for s in scales]
    val_r, _ = extrapolate("richardson", scales, vals)
    val_l, _ = extrapolate("linear", scales, vals)
    assert val_r == pytest.approx(-1.0)
    assert val_l == pytest.approx(-1.0)


def test_extrapolate_rejects_unknown_method() -> None:
    with pytest.raises(ValueError, match="ismeretlen extrapolációs modell"):
        extrapolate("nincs_ilyen", [1.0, 3.0], [1.0, 2.0])


@pytest.mark.parametrize(
    ("scales", "vals", "match"),
    [
        ([1.0], [2.0], "legalább 2"),
        ([1.0, 2.0, 3.0], [1.0, 2.0], "nem egyezik meg"),
        ([1.0, 1.0], [1.0, 2.0], "duplikáció"),
        ([-1.0, 2.0], [1.0, 2.0], "pozitívnak"),
    ],
)
def test_validate_inputs(scales: list[float], vals: list[float], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        richardson_extrapolate(scales, vals)
