"""Fázis 5 — a statisztikai modul egységtesztjei (AC-5.6, AC-5.7, TP-F05).

A függvényeket **ismert eloszláson** ellenőrizzük: ahol a helyes válasz
analitikusan ismert (CI-lefedettség, σ/√N skálázás), a teszt azt méri.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA
from vqebd.stats import (
    block_mean_spread,
    classify_chemical_accuracy,
    error_budget,
    loglog_slope,
    rmse,
    summarize,
)

pytestmark = pytest.mark.unit


# --- summarize ----------------------------------------------------------------


def test_summarize_known_values() -> None:
    """Kézzel ellenőrizhető minta: átlag, szórás (ddof=1), SEM, t-alapú CI."""
    s = summarize([1.0, 2.0, 3.0, 4.0])
    assert s.n == 4
    assert s.mean == pytest.approx(2.5)
    assert s.sd == pytest.approx(math.sqrt(5.0 / 3.0))
    assert s.sem == pytest.approx(math.sqrt(5.0 / 3.0) / 2.0)
    # t₀.₉₇₅(3) = 3.182446305284263
    half = 3.182446305284263 * s.sem
    assert (s.ci_low, s.ci_high) == pytest.approx((2.5 - half, 2.5 + half))
    assert s.median == pytest.approx(2.5)


def test_summarize_single_value_has_degenerate_ci() -> None:
    s = summarize([0.7])
    assert (s.n, s.sd, s.sem, s.ci_low, s.ci_high) == (1, 0.0, 0.0, 0.7, 0.7)


@pytest.mark.parametrize("bad", [[], [float("nan")], [1.0, float("inf")]])
def test_summarize_rejects_invalid_input(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        summarize(bad)


def test_summarize_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="konfidenciaszint"):
        summarize([1.0, 2.0], ci_level=1.0)


def test_t_interval_coverage_is_nominal() -> None:
    """AC-5.7: a 95%-os t-CI kis mintán (N=5) ténylegesen ~95%-ban fedi a várható értéket.

    A normális (z) alapú CI N=5-nél csak ~88%-ot fedne — ezért kell a t-eloszlás.
    4000 kísérlet: a lefedettség becslésének szórása ~0.0034, a tűrés ±0.015 (>4σ).
    """
    rng = np.random.default_rng(20260925)
    trials, n, mu = 4000, 5, 0.3
    hits = 0
    for _ in range(trials):
        s = summarize(rng.normal(mu, 1.0, n).tolist())
        hits += s.ci_low <= mu <= s.ci_high
    assert hits / trials == pytest.approx(0.95, abs=0.015)


# --- besorolás ------------------------------------------------------------------


def _summary_with_ci(lo: float, hi: float, n: int = 10) -> object:
    from vqebd.stats import SampleSummary

    mid = (lo + hi) / 2
    return SampleSummary(n, mid, 1.0, 0.1, mid, lo, hi, 0.95)


@pytest.mark.parametrize(
    ("lo", "hi", "expected"),
    [
        (-1.0e-3, 1.0e-3, "confirmed"),
        (-1.0e-3, 2.0e-3, "consistent"),
        (1.0e-3, 3.0e-3, "consistent"),
        (2.0e-3, 5.0e-3, "excluded"),
        (-5.0e-3, -2.0e-3, "excluded"),
        (-3.0e-3, 3.0e-3, "consistent"),
    ],
)
def test_classification_boundaries(lo: float, hi: float, expected: str) -> None:
    """AC-5.7: a háromállapotú besorolás a CI és a ±1.6 mHa sáv viszonyából."""
    assert classify_chemical_accuracy(_summary_with_ci(lo, hi)) == expected  # type: ignore[arg-type]


def test_single_noisy_sample_is_undetermined_but_exact_is_not() -> None:
    """Egy zajos minta nem minősíthető; egy egzakt érték igen (a CI pontra fajul)."""
    inside = summarize([0.5e-3])
    outside = summarize([5.0e-3])
    assert classify_chemical_accuracy(inside) == "undetermined"
    assert classify_chemical_accuracy(inside, exact=True) == "confirmed"
    assert classify_chemical_accuracy(outside, exact=True) == "excluded"


def test_classification_rejects_nonpositive_threshold() -> None:
    with pytest.raises(ValueError, match="küszöb"):
        classify_chemical_accuracy(summarize([0.0, 1.0]), threshold=0.0)


def test_chemical_accuracy_constant_is_one_kcal_per_mol() -> None:
    expected = 4.184 / 2625.4996  # 1 kcal/mol Hartree-ban
    assert abs(CHEMICAL_ACCURACY_HA - expected) / expected < 1e-4


# --- RMSE, blokkátlag, meredekség -------------------------------------------------


def test_rmse_combines_bias_and_spread() -> None:
    """RMSE² = torzítás² + szórás² (populációs szórással)."""
    errors = [1.0, 3.0]
    assert rmse(errors) == pytest.approx(math.sqrt(5.0))
    assert rmse(errors) ** 2 == pytest.approx(2.0**2 + 1.0**2)
    with pytest.raises(ValueError):
        rmse([])


def test_block_means_of_independent_noise_scale_as_inverse_sqrt_n() -> None:
    """AC-5.6 (szintetikus): független zajnál a blokkátlagok szórása ∝ N^−½."""
    rng = np.random.default_rng(7)
    values = rng.normal(0.0, 1.0, 4096).tolist()
    sizes = [1, 2, 4, 8, 16, 32]
    spread = block_mean_spread(values, sizes)
    slope = loglog_slope(sizes, [spread[n] for n in sizes])
    assert slope == pytest.approx(-0.5, abs=0.1)


def test_block_means_of_common_offset_do_not_shrink() -> None:
    """A v0.7.0-s hibamód: közös eltolás (korrelált zaj) mellett az ismétlés NEM segít.

    Minden „minta” = közös eltolás + kicsi független zaj → a blokkátlagok
    szórása N-től alig függ, a meredekség jóval −½ fölött van. Ez az a helyzet,
    amelyet a v0.7.1 megszüntetett, és amelyre a szimuláció korábban épült.
    """
    rng = np.random.default_rng(11)
    offsets = np.repeat(rng.normal(0.0, 1.0, 128), 32)  # 32-es csoportokban azonos eltolás
    values = (offsets + rng.normal(0.0, 0.05, offsets.size)).tolist()
    sizes = [1, 2, 4, 8, 16, 32]
    spread = block_mean_spread(values, sizes)
    slope = loglog_slope(sizes, [spread[n] for n in sizes])
    assert slope > -0.1


def test_block_mean_spread_needs_two_blocks() -> None:
    with pytest.raises(ValueError, match="blokk"):
        block_mean_spread([1.0, 2.0, 3.0], [2])
    with pytest.raises(ValueError, match="blokkméret"):
        block_mean_spread([1.0, 2.0], [0])


def test_loglog_slope_validates_input() -> None:
    assert loglog_slope([1.0, 10.0], [1.0, 100.0]) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        loglog_slope([1.0], [1.0])
    with pytest.raises(ValueError):
        loglog_slope([0.0, 1.0], [1.0, 1.0])


# --- hibaköltségvetés ---------------------------------------------------------------


def test_error_budget_is_telescoping() -> None:
    """G5: a tagok összege pontosan a teljes hiba (a SEM nem additív tag)."""
    noisy = summarize([-7.84, -7.86, -7.85])
    budget = error_budget(
        full_ci=-7.8824,
        casci=-7.8631,
        exact_diagonalization=-7.8631 + 1e-15,
        statevector=-7.8631 + 4e-13,
        noisy=noisy,
    )
    parts = [budget.truncation, budget.mapping, budget.ansatz, budget.noise_bias]
    assert all(p is not None for p in parts)
    assert sum(p for p in parts if p is not None) == pytest.approx(budget.total)
    assert budget.truncation == pytest.approx(-7.8631 + 7.8824)
    assert budget.statistical == pytest.approx(noisy.sem)


def test_error_budget_full_space_has_no_truncation() -> None:
    budget = error_budget(
        full_ci=-1.137, casci=None, exact_diagonalization=-1.137, statevector=-1.137
    )
    assert budget.truncation is None
    assert budget.noise_bias is None
    assert budget.total == pytest.approx(0.0)
