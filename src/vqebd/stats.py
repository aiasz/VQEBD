"""Statisztikai aggregálás — ismételt futások kiértékelése (Fázis 5, ADR-0007).

Miért kell ez a modul?
----------------------
A v0.7.1 óta a zajos kiértékelők mintavételi zaja **kiértékelésenként független**.
Egyetlen zajos VQE-futás végeredménye ezért egy széles eloszlásból húzott érték
(egy 8192 lövéses kiértékelés szórása ~11 mHa). Egy ilyen szám csak az
eloszlásával együtt értelmezhető: átlag, szórás, standard hiba (SEM) és
konfidencia-intervallum.

A két hibafajta szétválasztása (ISO 5725-1):

- **precizitás** — a statisztikus hiba; független ismétléssel ``σ/√N`` szerint csökken;
- **helyesség** — a torzítás; ismétléssel **nem** csökken, csak más módszerrel
  mérhető (referencialánc, újramintavételezés, hibaenyhítés).

A :func:`block_mean_spread` ezt empirikusan is kimutatja (AC-5.6, fig08).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Literal

from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA

__all__ = [
    "AccuracyClass",
    "ErrorBudget",
    "SampleSummary",
    "block_mean_spread",
    "classify_chemical_accuracy",
    "error_budget",
    "loglog_slope",
    "rmse",
    "summarize",
]

AccuracyClass = Literal["confirmed", "consistent", "excluded", "undetermined"]
"""Kémiai pontossági besorolás a hiba CI-je alapján (``docs/plan/phase_05.md`` 5.6).

- ``confirmed`` — a hiba teljes konfidencia-intervalluma a ±1.6 mHa sávon belül;
- ``consistent`` — a CI metszi a sávot, de nincs teljesen benne;
- ``excluded`` — a CI teljesen a sávon kívül;
- ``undetermined`` — egyetlen **zajos** minta: a bizonytalanság nem becsülhető.

Egzakt (zajmentes) backend egyetlen értékénél a CI egy pontra fajul, így a
besorolás ``confirmed`` vagy ``excluded`` — ez helyes, mert statisztikus
bizonytalanság nincs.
"""


@dataclass(frozen=True, slots=True)
class SampleSummary:
    """Egy mintasokaság leíró statisztikája.

    Attributes:
        n: A minták száma.
        mean: Az átlag.
        sd: A korrigált tapasztalati szórás (``ddof=1``); ``n = 1`` esetén 0.
        sem: Az átlag standard hibája, ``sd/√n``.
        median: A medián.
        ci_low, ci_high: A Student-t alapú, kétoldali konfidencia-intervallum
            az átlagra; ``n = 1`` esetén mindkettő az átlag.
        ci_level: A konfidenciaszint (alapértelmezés 0.95).
    """

    n: int
    mean: float
    sd: float
    sem: float
    median: float
    ci_low: float
    ci_high: float
    ci_level: float

    def to_dict(self) -> dict[str, float | int]:
        """Szótár-alak az exporthoz (``n`` egész marad)."""
        return {k: (int(v) if k == "n" else float(v)) for k, v in asdict(self).items()}


def summarize(values: Sequence[float], *, ci_level: float = 0.95) -> SampleSummary:
    """Leíró statisztika Student-t alapú konfidencia-intervallummal.

    A t-eloszlás (nem a normális) a helyes választás, mert a szórást is a
    mintából becsüljük; kis N-nél (pl. 10 seed) a különbség érdemi:
    ``t₀.₉₇₅(9) = 2.26`` vs. ``z = 1.96``.

    Args:
        values: A minták (legalább 1).
        ci_level: A konfidenciaszint, ``(0, 1)``.

    Raises:
        ValueError: Üres minta, nem véges érték vagy érvénytelen szint esetén.
    """
    if not values:
        raise ValueError("üres mintából nem számolható statisztika")
    if not 0.0 < ci_level < 1.0:
        raise ValueError(f"a konfidenciaszint (0, 1)-ben legyen: {ci_level}")
    data = [float(v) for v in values]
    if not all(math.isfinite(v) for v in data):
        raise ValueError("a minta nem véges értéket (NaN/inf) tartalmaz")

    import numpy as np
    from scipy import stats as sps

    arr = np.asarray(data, dtype=np.float64)
    n = int(arr.size)
    mean = float(arr.mean())
    median = float(np.median(arr))
    if n == 1:
        return SampleSummary(1, mean, 0.0, 0.0, median, mean, mean, ci_level)
    sd = float(arr.std(ddof=1))
    sem = sd / math.sqrt(n)
    t_crit = float(sps.t.ppf(0.5 + ci_level / 2.0, df=n - 1))
    return SampleSummary(
        n=n,
        mean=mean,
        sd=sd,
        sem=sem,
        median=median,
        ci_low=mean - t_crit * sem,
        ci_high=mean + t_crit * sem,
        ci_level=ci_level,
    )


def classify_chemical_accuracy(
    error_summary: SampleSummary,
    *,
    threshold: float = CHEMICAL_ACCURACY_HA,
    exact: bool = False,
) -> AccuracyClass:
    """Kémiai pontossági besorolás a **hiba** konfidencia-intervalluma alapján.

    Args:
        error_summary: A referenciához mért hibák (``E − E_ref``) összegzése, Ha.
        threshold: A sáv félszélessége (alapértelmezés: 1.5936 mHa).
        exact: Zajmentes backend-e. Ha nem, és csak egy minta van, a
            besorolás ``undetermined`` — egyetlen zajos minta nem minősíthető.

    Returns:
        A :data:`AccuracyClass` egyik értéke.
    """
    if threshold <= 0:
        raise ValueError(f"a küszöb pozitív legyen: {threshold}")
    if error_summary.n == 1 and not exact:
        return "undetermined"
    lo, hi = error_summary.ci_low, error_summary.ci_high
    if -threshold < lo and hi < threshold:
        return "confirmed"
    if hi <= -threshold or lo >= threshold:
        return "excluded"
    return "consistent"


def rmse(errors: Sequence[float]) -> float:
    """Négyzetes középhiba: ``sqrt(mean(e²))`` — torzítás és szórás együtt."""
    if not errors:
        raise ValueError("üres hibalistából nem számolható RMSE")
    return math.sqrt(sum(float(e) ** 2 for e in errors) / len(errors))


def block_mean_spread(values: Sequence[float], block_sizes: Sequence[int]) -> dict[int, float]:
    """Az N-elemű blokkátlagok szórása, N-enként — az ismétlés hatásának mérése.

    A mintát egymást nem átfedő, N hosszú blokkokra bontja, és a blokkátlagok
    korrigált szórását adja vissza. Független mintáknál ez ``σ/√N`` — vagyis a
    log-log meredekség −½ (:func:`loglog_slope`). Ez az AC-5.6 empirikus próbája:
    **ha a zaj nem független** (mint v0.7.1 előtt), a meredekség 0 lenne.

    Args:
        values: A független(nek feltételezett) minták.
        block_sizes: A vizsgált blokkméretek; mindegyikből legalább 2 blokk kell.

    Raises:
        ValueError: Ha egy blokkméretből 2-nél kevesebb blokk jön ki.
    """
    import numpy as np

    arr = np.asarray([float(v) for v in values], dtype=np.float64)
    out: dict[int, float] = {}
    for size in block_sizes:
        if size < 1:
            raise ValueError(f"a blokkméret legalább 1: {size}")
        n_blocks = arr.size // size
        if n_blocks < 2:
            raise ValueError(
                f"{arr.size} mintából N={size} blokkmérettel csak {n_blocks} blokk "
                "jön ki (legalább 2 kell)"
            )
        means = arr[: n_blocks * size].reshape(n_blocks, size).mean(axis=1)
        out[int(size)] = float(means.std(ddof=1))
    return out


def loglog_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    """A ``log y`` – ``log x`` egyenes meredeksége legkisebb négyzetekkel."""
    import numpy as np

    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("legalább 2, azonos hosszú pontsor kell")
    if min(xs) <= 0 or min(ys) <= 0:
        raise ValueError("log-log illesztéshez minden érték pozitív kell legyen")
    slope, _ = np.polyfit(np.log(np.asarray(xs, float)), np.log(np.asarray(ys, float)), 1)
    return float(slope)


@dataclass(frozen=True, slots=True)
class ErrorBudget:
    """A teljes hiba felbontása forrásaira (Ha; ``None`` = az adott szint nem mért).

    A felbontás a referencialánc egymást követő szintjeinek különbsége
    (``docs/plan/phase_05.md`` 5.2), így az összeg **telescopikus**: a tagok összege
    pontosan a teljes hiba (``total``), kerekítési hibán belül.

    Attributes:
        truncation: Aktívtér-csonkolás, ``CASCI − FCI`` (teljes térben ``None``).
        mapping: Leképezés, ``L1 − CASCI`` (vagy ``L1 − FCI``).
        ansatz: Ansatz + optimalizáló, ``L2 − L1``.
        noise_bias: Zaj okozta torzítás, ``átlag(zajos) − L2``.
        statistical: A zajos átlag standard hibája (SEM) — **nem** additív tag,
            a torzítás bizonytalansága.
        total: ``átlag(zajos) − FCI`` (vagy ``L2 − FCI``, ha nincs zajos szint).
    """

    truncation: float | None
    mapping: float | None
    ansatz: float | None
    noise_bias: float | None
    statistical: float | None
    total: float | None

    def to_dict(self) -> dict[str, float | None]:
        """Szótár-alak az exporthoz."""
        return dict(asdict(self))


def error_budget(
    *,
    full_ci: float | None,
    casci: float | None,
    exact_diagonalization: float | None,
    statevector: float | None,
    noisy: SampleSummary | None = None,
) -> ErrorBudget:
    """Hibaköltségvetés a referencialánc szintjeiből (G5).

    Args:
        full_ci: L0 (Ha).
        casci: L0′ (Ha); teljes térben ``None``.
        exact_diagonalization: L1 (Ha).
        statevector: L2 (Ha) — a zajmentes VQE eredménye.
        noisy: A zajos szint (L3/L4) ismételt futásainak összegzése.
    """
    exact_ref = casci if casci is not None else full_ci

    def diff(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else a - b

    final = noisy.mean if noisy is not None else statevector
    return ErrorBudget(
        truncation=diff(casci, full_ci),
        mapping=diff(exact_diagonalization, exact_ref),
        ansatz=diff(statevector, exact_diagonalization),
        noise_bias=diff(noisy.mean if noisy is not None else None, statevector),
        statistical=noisy.sem if noisy is not None else None,
        total=diff(final, full_ci),
    )
