"""Fázis 11 — az előre kimondott elemzés szintetikus adaton (AC-11.3).

Pozitív és negatív kontroll: ismert eltolást ki kell mutatni, eltolás nélkül egyenértékűséget kell
adni. Az elemzést a mérések előtt teszteltük, hogy a döntési szabály ne az adat szerint alakuljon.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from vqebd.heron_analysis import (
    AnalysisError,
    TostResult,
    analyze,
    decide_h1,
    paired_improvement,
    tost_equivalence,
)

pytestmark = pytest.mark.unit

GEOMS = ("0.735", "1.5", "2.0")
HW_TRUE = {"0.735": 22.0, "1.5": 12.0, "2.0": 12.0}


def _blocks(
    *, shift: float, n: int = 8, noise: float = 1.0, seed: int = 7, no_readout_bias: float = -12.0
) -> list[dict[str, Any]]:
    """Szintetikus megerősítő blokkok: a hardver = igazság + zaj, a modell = igazság + ``shift``."""
    rng = np.random.default_rng(seed)
    out: list[dict[str, Any]] = []
    for i in range(n):
        hw = {g: HW_TRUE[g] + float(rng.normal(0, noise)) for g in GEOMS}
        trex = {g: HW_TRUE[g] - 6.0 + float(rng.normal(0, noise)) for g in GEOMS}
        ro = {g: HW_TRUE[g] + shift + float(rng.normal(0, 0.3)) for g in GEOMS}
        no = {g: HW_TRUE[g] + no_readout_bias + float(rng.normal(0, 0.3)) for g in GEOMS}
        out.append(
            {
                "block": f"C{i + 1}",
                "kind": "confirmatory",
                "hardware_mha": {"raw": hw, "trex": trex},
                "model_mha": {"readout": ro, "no_readout": no},
            }
        )
    return out


def test_tost_declares_a_zero_difference_equivalent() -> None:
    rng = np.random.default_rng(1)
    result = tost_equivalence(list(rng.normal(0.0, 1.0, 8)), delta=3.0)
    assert result.equivalent
    assert -3.0 < result.ci_low < result.ci_high < 3.0
    assert result.n == 8


def test_tost_detects_a_known_five_mha_offset() -> None:
    """Negatív kontroll: 5 mHa eltolás δ = 3 mHa mellett nem lehet egyenértékű."""
    rng = np.random.default_rng(2)
    result = tost_equivalence(list(5.0 + rng.normal(0.0, 1.0, 8)), delta=3.0)
    assert not result.equivalent
    assert result.ci_low > 3.0


def test_tost_is_not_equivalent_when_the_spread_is_too_large() -> None:
    """Nulla várható eltérés, de nagy szórás: a CI kilóg a sávból (nincs egyenértékűség)."""
    result = tost_equivalence([-8.0, 7.0, -6.0, 9.0, -7.0, 6.0, -9.0, 8.0], delta=3.0)
    assert not result.equivalent


def test_tost_needs_two_blocks_and_a_positive_delta() -> None:
    with pytest.raises(AnalysisError):
        tost_equivalence([1.0], delta=3.0)
    with pytest.raises(ValueError, match="delta"):
        tost_equivalence([1.0, 2.0], delta=0.0)


def _r(equivalent: bool) -> TostResult:
    return TostResult(8, 0.0, 1.0, -1.0, 1.0, 3.0, equivalent)


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ((True, True, True), "equivalent"),
        ((True, True, False), "partial"),
        ((True, False, False), "rejected"),
        ((False, False, False), "rejected"),
    ],
)
def test_h1_decision_rule(flags: tuple[bool, ...], expected: str) -> None:
    assert decide_h1({g: _r(f) for g, f in zip(GEOMS, flags, strict=True)}) == expected


def test_analyze_an_accurate_model_is_equivalent_and_readout_helps() -> None:
    result = analyze(_blocks(shift=0.0), delta=3.0)
    assert result["H1"]["decision"] == "equivalent"
    assert result["H2"]["supported"] is True
    assert result["n_confirmatory_blocks"] == 8


def test_analyze_a_five_mha_biased_model_is_rejected() -> None:
    result = analyze(_blocks(shift=5.0), delta=3.0)
    assert result["H1"]["decision"] == "rejected"


def test_analyze_h2_is_not_supported_when_readout_adds_nothing() -> None:
    blocks = _blocks(shift=0.0, no_readout_bias=0.0)
    assert analyze(blocks, delta=3.0)["H2"]["supported"] is False


def test_analyze_h4_uses_the_pilot_model_as_the_fixed_calibration() -> None:
    blocks = _blocks(shift=0.0)
    pilot = {
        "block": "B0",
        "kind": "pilot",
        "hardware_mha": {"raw": HW_TRUE, "trex": HW_TRUE},
        "model_mha": {
            "readout": {g: HW_TRUE[g] + 4.0 for g in GEOMS},
            "no_readout": HW_TRUE,
        },
    }
    result = analyze([pilot, *blocks], delta=3.0)
    assert result["H4"] is not None and result["H4"]["supported"] is True
    # a pilot nem számít bele a megerősítő végpontokba
    assert result["n_confirmatory_blocks"] == 8
    assert analyze(blocks, delta=3.0)["H4"] is None


def test_analyze_rejects_too_few_or_inconsistent_blocks() -> None:
    with pytest.raises(AnalysisError, match="legalább 2"):
        analyze(_blocks(shift=0.0, n=1), delta=3.0)
    blocks = _blocks(shift=0.0, n=3)
    del blocks[1]["hardware_mha"]["raw"]["2.0"]
    with pytest.raises(AnalysisError, match="geometriái eltérnek"):
        analyze(blocks, delta=3.0)
    broken = _blocks(shift=0.0, n=3)
    del broken[2]["model_mha"]
    with pytest.raises(AnalysisError, match="hiányzik"):
        analyze(broken, delta=3.0)


def test_paired_improvement_sign_and_shape() -> None:
    result = paired_improvement([10.0, 12.0, 11.0, 13.0], [1.0, 2.0, 1.5, 2.5])
    assert result["supported"] is True and result["mean_difference"] > 0
    with pytest.raises(AnalysisError):
        paired_improvement([1.0, 2.0], [1.0])
