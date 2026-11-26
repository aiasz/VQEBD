"""Fázis 11 — az előre kimondott elemzés szintetikus adaton (AC-11.3).

Pozitív és negatív kontroll: ismert eltolást ki kell mutatni, eltolás nélkül egyenértékűséget kell
adni. Az elemzést a mérések előtt teszteltük, hogy a döntési szabály ne az adat szerint alakuljon.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

from vqebd.heron_analysis import (
    AnalysisError,
    TostResult,
    analyze,
    decide_h1,
    describe_differences,
    paired_improvement,
    sensitivity_analyses,
    tost_equivalence,
)
from vqebd.heron_model import PROTOCOL, protocol_fingerprint

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


# --- a kiegészítő C9 és az előre rögzített leíró érzékenységi vizsgálatok (2026-11-18) ----------


def _supplementary(offset: float) -> dict[str, Any]:
    """Egy kiegészítő blokk, amelynek nyers eltérése ``offset`` mHa minden geometrián."""
    return {
        "block": "C9",
        "kind": "supplementary",
        "hardware_mha": {"raw": {g: HW_TRUE[g] + offset for g in GEOMS}, "trex": HW_TRUE},
        "model_mha": {"readout": HW_TRUE, "no_readout": HW_TRUE},
    }


def test_a_supplementary_block_never_changes_the_primary_analysis() -> None:
    """A C9 az elsődleges elemzésbe nem számít bele — szélsőséges értékkel sem."""
    blocks = _blocks(shift=0.0)
    alone = analyze(blocks, delta=3.0)
    with_c9 = analyze([*blocks, _supplementary(500.0)], delta=3.0)
    assert with_c9 == alone
    assert with_c9["n_confirmatory_blocks"] == 8


def test_describe_differences_matches_the_paired_differences() -> None:
    blocks = _blocks(shift=2.0, n=4)
    out = describe_differences(blocks)
    raw = out["raw_vs_readout_model"]["0.735"]
    expected = [
        b["hardware_mha"]["raw"]["0.735"] - b["model_mha"]["readout"]["0.735"] for b in blocks
    ]
    assert raw["n"] == 4 and raw["blocks"] == ["C1", "C2", "C3", "C4"]
    assert raw["mean"] == pytest.approx(float(np.mean(expected)))
    assert raw["sd"] == pytest.approx(float(np.std(expected, ddof=1)))
    tost = tost_equivalence(expected, delta=3.0)  # ugyanaz a 90%-os intervallum, döntés nélkül
    assert raw["ci_low"] == pytest.approx(tost.ci_low) and raw["ci_high"] == pytest.approx(
        tost.ci_high
    )
    assert "equivalent" not in raw and "decision" not in raw
    assert set(out["trex_vs_no_readout_model"]) == set(GEOMS)


def test_describe_differences_handles_one_or_no_block() -> None:
    one = describe_differences(_blocks(shift=1.0, n=1))
    cell = one["raw_vs_readout_model"]["1.5"]
    assert cell["n"] == 1 and cell["mean"] is not None and cell["sd"] is None
    assert cell["ci_low"] is None and cell["ci_high"] is None
    empty = describe_differences([])
    assert empty == {"blocks": [], "raw_vs_readout_model": {}, "trex_vs_no_readout_model": {}}


def test_sensitivity_a_uses_c1_to_c9_and_b_filters_by_calibration_age() -> None:
    blocks = _blocks(shift=0.0)
    pilot = {**blocks[0], "block": "B0", "kind": "pilot"}
    every = [pilot, *blocks, _supplementary(1.0)]
    ages = {"C1": 9.2, "C2": 48.0, "C3": 48.01, "C6": 85.8, "C7": 37.3, "C8": 10.7, "C9": 20.0}
    out = sensitivity_analyses(every, ages, max_age_h=48.0)
    assert out["decision_rule"] is None
    assert out["all_blocks"]["blocks"] == [f"C{i}" for i in range(1, 10)]  # a pilot kimarad
    fresh = out["calibration_age_at_most"]
    assert fresh["max_age_h"] == 48.0
    assert fresh["blocks"] == ["C1", "C2", "C7", "C8", "C9"]  # a 48,0 h még beletartozik
    assert fresh["excluded_older"] == ["C3", "C6"]
    assert fresh["excluded_unknown_age"] == ["C4", "C5"]
    assert fresh["raw_vs_readout_model"]["2.0"]["n"] == 5


def test_sensitivity_without_any_known_age_keeps_b_empty() -> None:
    out = sensitivity_analyses(_blocks(shift=0.0, n=3), {})
    fresh = out["calibration_age_at_most"]
    assert fresh["blocks"] == [] and fresh["excluded_unknown_age"] == ["C1", "C2", "C3"]
    assert out["all_blocks"]["raw_vs_readout_model"]["0.735"]["n"] == 3


# --- az elemző szkript (repó-checkoutból) -------------------------------------------------------


@pytest.fixture
def analyze_script(repo_root: Path) -> ModuleType:
    path = repo_root / "scripts" / "analyze_heron.py"
    if not path.is_file():
        pytest.skip("scripts/ nincs a szállított image-ben")
    spec = importlib.util.spec_from_file_location("analyze_heron_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _running(block: str) -> str:
    return f"2026-11-{int(block[1:]) + 3:02d}T08:00:01.250000+00:00"


def _write_blocks(directory: Path, blocks: list[dict[str, Any]]) -> None:
    for b in blocks:
        record = {
            **b,
            "protocol_fingerprint": protocol_fingerprint(),
            "runs": [{"timestamps": {"running": _running(str(b["block"]))}}],
        }
        name = f"{str(b['block']).lower()}.json"
        (directory / name).write_text(json.dumps(record), encoding="utf-8")


def _age(block: str, age_h: Any) -> dict[str, Any]:
    return {"block": block, "age_h": age_h, "first_job_running_utc": _running(block)}


def test_analyze_script_keeps_the_primary_result_separate_from_the_sensitivity(
    analyze_script: ModuleType, tmp_path: Path
) -> None:
    blocks = _blocks(shift=0.0)
    _write_blocks(tmp_path, [*blocks, _supplementary(40.0)])
    ages = {"blocks": [_age("C1", 9.2), _age("C9", 20.0)]}
    (tmp_path / "calibration_age.json").write_text(json.dumps(ages), encoding="utf-8")
    out_file = tmp_path / "analysis.json"
    assert analyze_script.main(["--data-dir", str(tmp_path), "--out", str(out_file)]) == 0
    out = json.loads(out_file.read_text(encoding="utf-8"))
    expected = analyze(
        blocks,
        delta=PROTOCOL["delta_mha"],
        equivalence_confidence=PROTOCOL["equivalence_confidence"],
    )
    assert out["primary"] == json.loads(json.dumps(expected))  # a C9 nem számít bele
    assert out["confirmatory_complete"] is True and out["confirmatory_blocks_expected"] == 8
    assert out["protocol_fingerprint"] == protocol_fingerprint()
    sens = out["sensitivity"]
    assert sens["all_blocks"]["blocks"] == [f"C{i}" for i in range(1, 10)]
    assert sens["calibration_age_at_most"]["max_age_h"] == 48.0
    assert sens["calibration_age_at_most"]["blocks"] == ["C1", "C9"]


def test_analyze_script_flags_an_incomplete_confirmatory_series(
    analyze_script: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_blocks(tmp_path, _blocks(shift=0.0, n=7))
    assert analyze_script.main(["--data-dir", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["confirmatory_complete"] is False
    assert "nem a végleges" in captured.err
    sens = json.loads(captured.out)["sensitivity"]["calibration_age_at_most"]
    assert sens["excluded_unknown_age"] == [f"C{i}" for i in range(1, 8)]  # nincs életkor-fájl


def test_analyze_script_ignores_stale_or_missing_age_records(
    analyze_script: ModuleType, tmp_path: Path
) -> None:
    _write_blocks(tmp_path, _blocks(shift=0.0, n=8))
    stale = {**_age("C2", 10.0), "first_job_running_utc": "2026-10-01T00:00:00+00:00"}
    ages = {
        "blocks": [
            _age("C1", 9.2),
            stale,
            _age("C3", None),
            _age("C4", 48.0001),
            _age("C5", True),
            _age("C6", float("nan")),
        ]
    }
    (tmp_path / "calibration_age.json").write_text(json.dumps(ages), encoding="utf-8")
    out_file = tmp_path / "analysis.json"
    assert analyze_script.main(["--data-dir", str(tmp_path), "--out", str(out_file)]) == 0
    fresh = json.loads(out_file.read_text(encoding="utf-8"))["sensitivity"][
        "calibration_age_at_most"
    ]
    assert fresh["blocks"] == ["C1"]
    assert fresh["excluded_older"] == ["C4"]  # 48,0001 h > 48 h (kerekítés nélkül)
    assert {"C2", "C3", "C5", "C6"} <= set(fresh["excluded_unknown_age"])


def test_a_broken_supplementary_block_cannot_block_the_primary_result(
    analyze_script: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocks = _blocks(shift=0.0)
    broken = _supplementary(1.0)
    del broken["hardware_mha"]["raw"]["2.0"]  # eltérő geometriák a C9-ben
    _write_blocks(tmp_path, [*blocks, broken])
    assert analyze_script.main(["--data-dir", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["primary"]["H1"]["decision"] == "equivalent" and out["confirmatory_complete"]
    assert "error" in out["sensitivity"] and "érzékenységi" in captured.err


def _broken(kind: str) -> list[dict[str, Any]]:
    blocks = _blocks(shift=0.0)
    if kind == "duplicate":
        blocks[1]["block"] = "C1"
    elif kind == "kind":
        blocks[2]["kind"] = "supplementary"
    elif kind == "nan":
        blocks[3]["hardware_mha"]["raw"]["1.5"] = float("nan")
    elif kind == "shots":
        blocks[4]["shots"] = 1024
    elif kind == "geometry":
        del blocks[5]["model_mha"]["no_readout"]["2.0"]
    return blocks


@pytest.mark.parametrize("kind", ["duplicate", "kind", "nan", "shots", "geometry"])
def test_analyze_script_refuses_an_inconsistent_input(
    analyze_script: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    blocks = _broken(kind)
    if kind == "duplicate":  # azonos név → külön fájlnév kell, hogy mindkettő beolvasódjon
        for i, b in enumerate(blocks):
            record = {
                **b,
                "protocol_fingerprint": protocol_fingerprint(),
                "runs": [{"timestamps": {"running": _running("C1")}}],
            }
            (tmp_path / f"c{i + 1}.json").write_text(json.dumps(record), encoding="utf-8")
    else:
        _write_blocks(tmp_path, blocks)
    assert analyze_script.main(["--data-dir", str(tmp_path)]) == 2
    assert "hibás" in capsys.readouterr().err


def test_analyze_script_refuses_a_block_from_another_protocol(
    analyze_script: ModuleType, tmp_path: Path
) -> None:
    blocks = _blocks(shift=0.0)
    _write_blocks(tmp_path, blocks)
    stale = json.loads((tmp_path / "c3.json").read_text(encoding="utf-8"))
    stale["protocol_fingerprint"] = "0" * 64
    (tmp_path / "c3.json").write_text(json.dumps(stale), encoding="utf-8")
    assert analyze_script.main(["--data-dir", str(tmp_path)]) == 2
