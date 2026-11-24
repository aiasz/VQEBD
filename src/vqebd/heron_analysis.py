"""Fázis 11: az előre kimondott hipotézisvizsgálatok (``phase_11.md`` 3. fejezet).

Tiszta statisztikai réteg: nem ismer hardvert, szimulátort vagy fájlt. A statisztikai egység a
**blokk** (egy időben összetartozó hardveres futássorozat); a blokkon belüli PUB-ok nem függetlenek.
Az elemzést a mérések **előtt** írtuk meg, szintetikus adaton teszteljük (AC-11.3), hogy a döntési
szabály ne alakulhasson a kapott adat szerint.

Blokk-rekord (a hardveres futtató kimenete; hibák mHa-ban a Full CI-hez képest)::

    {"block": "C1", "kind": "confirmatory",
     "hardware_mha": {"raw": {"0.735": 22.2, ...}, "trex": {...}},
     "model_mha": {"readout": {"0.735": 21.9, ...}, "no_readout": {...}}}

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy import stats

__all__ = [
    "AnalysisError",
    "TostResult",
    "analyze",
    "decide_h1",
    "describe_differences",
    "paired_improvement",
    "sensitivity_analyses",
    "tost_equivalence",
]


class AnalysisError(ValueError):
    """Az elemzés bemenete nem elég (pl. < 2 blokk) vagy hiányos."""


@dataclass(frozen=True)
class TostResult:
    """Egy páros eltérés-sorozat egyenértékűségi vizsgálata (TOST, 1 − 2α szintű CI)."""

    n: int
    mean: float
    se: float
    ci_low: float
    ci_high: float
    delta: float
    equivalent: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def tost_equivalence(
    differences: Sequence[float], *, delta: float, confidence: float = 0.90
) -> TostResult:
    """Egyenértékű-e az átlageltérés a nullával a ±``delta`` sávon belül.

    A TOST két egyoldali, 5%-os tesztje a **90%-os kétoldali CI**-vel egyenértékű (``confidence``);
    egyenértékű, ha a **teljes** CI a ``(−delta, +delta)`` nyílt sávon belül van.

    Raises:
        AnalysisError: Kevesebb mint 2 blokk esetén (nincs szórásbecslés).
    """
    values = np.asarray(differences, dtype=float)
    n = int(values.size)
    if n < 2:
        raise AnalysisError(f"legalább 2 blokk kell a szórásbecsléshez, kapott: {n}")
    if delta <= 0:
        raise ValueError(f"delta pozitív legyen, kapott: {delta}")
    mean = float(values.mean())
    se = float(values.std(ddof=1) / math.sqrt(n))
    crit = float(stats.t.ppf(0.5 + confidence / 2.0, n - 1))
    low, high = mean - crit * se, mean + crit * se
    return TostResult(
        n=n,
        mean=mean,
        se=se,
        ci_low=low,
        ci_high=high,
        delta=delta,
        equivalent=bool(low > -delta and high < delta),
    )


def decide_h1(per_geometry: Mapping[str, TostResult]) -> str:
    """H1 döntése az előre kimondott szabály szerint.

    - ``"equivalent"`` — minden geometriára egyenértékű;
    - ``"partial"`` — a geometriák legalább kétharmadára, de nem mindegyikre (3-ból 2);
    - ``"rejected"`` — egyébként.
    """
    if not per_geometry:
        raise AnalysisError("nincs geometria")
    total = len(per_geometry)
    passed = sum(1 for r in per_geometry.values() if r.equivalent)
    if passed == total:
        return "equivalent"
    if passed >= math.ceil(2 * total / 3):
        return "partial"
    return "rejected"


def paired_improvement(
    error_a: Sequence[float], error_b: Sequence[float], *, confidence: float = 0.95
) -> dict[str, Any]:
    """Páros különbség ``error_a − error_b`` (blokkonként), kétoldali ``confidence`` szintű CI-vel.

    Pozitív érték: a **b** feltétel négyzetes hibája kisebb. ``supported``: a CI alsó széle > 0.
    """
    a = np.asarray(error_a, dtype=float)
    b = np.asarray(error_b, dtype=float)
    if a.shape != b.shape:
        raise AnalysisError("a két hibasorozat hossza eltér")
    d = a - b
    n = int(d.size)
    if n < 2:
        raise AnalysisError(f"legalább 2 blokk kell, kapott: {n}")
    mean = float(d.mean())
    se = float(d.std(ddof=1) / math.sqrt(n))
    crit = float(stats.t.ppf(0.5 + confidence / 2.0, n - 1))
    low, high = mean - crit * se, mean + crit * se
    return {
        "n": n,
        "mean_difference": mean,
        "ci_low": low,
        "ci_high": high,
        "supported": bool(low > 0.0),
    }


def _by_geometry(block: Mapping[str, Any], section: str, key: str) -> dict[str, float]:
    try:
        data = block[section][key]
    except KeyError as exc:
        raise AnalysisError(
            f"a(z) {block.get('block')} blokkból hiányzik: {section}.{key}"
        ) from exc
    return {str(g): float(v) for g, v in data.items()}


def _mean_sq(
    hw: Mapping[str, float], model: Mapping[str, float], geometries: Sequence[str]
) -> float:
    return float(np.mean([(hw[g] - model[g]) ** 2 for g in geometries]))


def analyze(
    blocks: Sequence[Mapping[str, Any]], *, delta: float, equivalence_confidence: float = 0.90
) -> dict[str, Any]:
    """H1–H4 kiértékelése a megerősítő blokkokon.

    A ``kind == "pilot"`` blokk csak H4 referenciájaként szerepel (a rögzített kalibrációs modell);
    a megerősítő végpontokba nem számít bele.

    Raises:
        AnalysisError: Ha kevesebb mint 2 megerősítő blokk van, vagy a geometriák nem azonosak.
    """
    confirmatory = [b for b in blocks if b.get("kind") == "confirmatory"]
    pilots = [b for b in blocks if b.get("kind") == "pilot"]
    if len(confirmatory) < 2:
        raise AnalysisError(f"legalább 2 megerősítő blokk kell, kapott: {len(confirmatory)}")

    geoms = sorted(_by_geometry(confirmatory[0], "hardware_mha", "raw"), key=float)
    for b in confirmatory:
        if sorted(_by_geometry(b, "hardware_mha", "raw"), key=float) != geoms:
            raise AnalysisError(f"a(z) {b.get('block')} blokk geometriái eltérnek")

    hw_raw = [_by_geometry(b, "hardware_mha", "raw") for b in confirmatory]
    hw_trex = [_by_geometry(b, "hardware_mha", "trex") for b in confirmatory]
    m_ro = [_by_geometry(b, "model_mha", "readout") for b in confirmatory]
    m_no = [_by_geometry(b, "model_mha", "no_readout") for b in confirmatory]

    h1 = {
        g: tost_equivalence(
            [hw_raw[i][g] - m_ro[i][g] for i in range(len(confirmatory))],
            delta=delta,
            confidence=equivalence_confidence,
        )
        for g in geoms
    }
    h3 = {
        g: tost_equivalence(
            [hw_trex[i][g] - m_no[i][g] for i in range(len(confirmatory))],
            delta=delta,
            confidence=equivalence_confidence,
        )
        for g in geoms
    }
    err_ro = [_mean_sq(hw_raw[i], m_ro[i], geoms) for i in range(len(confirmatory))]
    err_no = [_mean_sq(hw_raw[i], m_no[i], geoms) for i in range(len(confirmatory))]

    result: dict[str, Any] = {
        "n_confirmatory_blocks": len(confirmatory),
        "geometries": geoms,
        "delta_mha": delta,
        "H1": {
            "decision": decide_h1(h1),
            "per_geometry": {g: r.as_dict() for g, r in h1.items()},
        },
        "H2": paired_improvement(err_no, err_ro),
        "H3_exploratory": {g: r.as_dict() for g, r in h3.items()},
        "H4": None,
    }
    if pilots:
        fixed = _by_geometry(pilots[0], "model_mha", "readout")
        if all(g in fixed for g in geoms):
            err_fixed = [_mean_sq(hw_raw[i], fixed, geoms) for i in range(len(confirmatory))]
            result["H4"] = paired_improvement(err_fixed, err_ro)
    return result


# --- előre rögzített, csak leíró érzékenységi vizsgálatok (phase_11.md, 2026-11-18) -------------
#
# Az elsődleges elemzést (``analyze``) nem érintik: döntési szabályuk nincs, a kimenetük külön
# táblázatba kerül. (a) az összes megerősítő + kiegészítő blokk (C1–C9); (b) csak azok, amelyeknél
# a kalibráció az első job indulásakor legfeljebb ``max_age_h`` órás volt.

_ANALYSED_KINDS = ("confirmatory", "supplementary")


def _summary(values: Sequence[float], blocks: Sequence[str], confidence: float) -> dict[str, Any]:
    v = np.asarray(values, dtype=float)
    n = int(v.size)
    out: dict[str, Any] = {
        "n": n,
        "blocks": list(blocks),
        "mean": float(v.mean()) if n else None,
        "sd": None,
        "ci_low": None,
        "ci_high": None,
    }
    if n >= 2:
        sd = float(v.std(ddof=1))
        crit = float(stats.t.ppf(0.5 + confidence / 2.0, n - 1))
        half = crit * sd / math.sqrt(n)
        out.update(sd=sd, ci_low=out["mean"] - half, ci_high=out["mean"] + half)
    return out


def describe_differences(
    blocks: Sequence[Mapping[str, Any]], *, confidence: float = 0.90
) -> dict[str, Any]:
    """Leíró összesítés geometriánként (nincs döntés): a H1 és a H3 páros eltérései.

    ``raw_vs_readout_model``: nyers hardver − kiolvasásos modell; ``trex_vs_no_readout_model``:
    TREX hardver − kiolvasás nélküli modell. Geometriánként ``n``, a blokkok, átlag, szórás és
    ``confidence`` szintű t-intervallum (csak leíró; 2 blokk alatt ``None``).
    """
    names = [str(b.get("block")) for b in blocks]
    if not blocks:
        return {"blocks": [], "raw_vs_readout_model": {}, "trex_vs_no_readout_model": {}}
    geoms = sorted(_by_geometry(blocks[0], "hardware_mha", "raw"), key=float)
    for b in blocks:
        if sorted(_by_geometry(b, "hardware_mha", "raw"), key=float) != geoms:
            raise AnalysisError(f"a(z) {b.get('block')} blokk geometriái eltérnek")
    pairs = {
        "raw_vs_readout_model": (("hardware_mha", "raw"), ("model_mha", "readout")),
        "trex_vs_no_readout_model": (("hardware_mha", "trex"), ("model_mha", "no_readout")),
    }
    out: dict[str, Any] = {"blocks": names}
    for label, (hw_key, model_key) in pairs.items():
        hw = [_by_geometry(b, *hw_key) for b in blocks]
        model = [_by_geometry(b, *model_key) for b in blocks]
        out[label] = {
            g: _summary([hw[i][g] - model[i][g] for i in range(len(blocks))], names, confidence)
            for g in geoms
        }
    return out


def sensitivity_analyses(
    blocks: Sequence[Mapping[str, Any]],
    ages_h: Mapping[str, float],
    *,
    max_age_h: float = 48.0,
    confidence: float = 0.90,
) -> dict[str, Any]:
    """Az előre rögzített két leíró érzékenységi vizsgálat (döntési szabály nélkül).

    Args:
        blocks: Blokk-rekordok; a ``pilot`` kimarad, a ``confirmatory`` és a ``supplementary``
            számít.
        ages_h: Blokkonkénti kalibráció-életkor órában (``vqebd.heron_calibration_age``).
        max_age_h: A (b) vizsgálat határa (a határ még beletartozik).
    """
    analysed = [b for b in blocks if b.get("kind") in _ANALYSED_KINDS]
    fresh = [
        b
        for b in analysed
        if str(b.get("block")) in ages_h and float(ages_h[str(b.get("block"))]) <= max_age_h
    ]
    return {
        "decision_rule": None,
        "all_blocks": describe_differences(analysed, confidence=confidence),
        "calibration_age_at_most": {
            "max_age_h": max_age_h,
            "excluded_older": [
                str(b.get("block"))
                for b in analysed
                if str(b.get("block")) in ages_h and float(ages_h[str(b.get("block"))]) > max_age_h
            ],
            "excluded_unknown_age": [
                str(b.get("block")) for b in analysed if str(b.get("block")) not in ages_h
            ],
            **describe_differences(fresh, confidence=confidence),
        },
    }
