r"""Extrapolációs modellek a ZNE határérték-számításához (λ → 0) (ADR-0003).

Ez a modul valósítja meg a különböző matematikai modelleket a zajmentes
határérték ($\lim_{\lambda \to 0} E(\lambda)$) becslésére a skálázott mérési
pontokból:
1. **Richardson-extrapoláció** (Lagrange polinom $\lambda=0$-ra kiértékelve)
2. **Lineáris illesztés** ($E(\lambda) = a\lambda + b$)
3. **Polinomiális illesztés** (tetszőleges fokszámú legkisebb négyzetek)
4. **Exponenciális illesztés** ($E(\lambda) = a e^{b\lambda} + c$)

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

__all__ = [
    "exponential_extrapolate",
    "extrapolate",
    "linear_extrapolate",
    "polynomial_extrapolate",
    "richardson_extrapolate",
]


def _validate_inputs(scale_factors: Sequence[float], values: Sequence[float]) -> None:
    """Bemeneti pontok ellenőrzése."""
    if len(scale_factors) != len(values):
        raise ValueError(
            f"a skálafaktorok száma ({len(scale_factors)}) és az értékek száma "
            f"({len(values)}) nem egyezik meg"
        )
    if len(scale_factors) < 2:
        raise ValueError("az extrapolációhoz legalább 2 mérési pont szükséges")
    if len(set(scale_factors)) != len(scale_factors):
        raise ValueError("a skálafaktorok között nem lehet duplikáció")
    if any(s <= 0 for s in scale_factors):
        raise ValueError("minden skálafaktornak pozitívnak kell lennie")


def richardson_extrapolate(
    scale_factors: Sequence[float], values: Sequence[float]
) -> tuple[float, float | None]:
    """Richardson-extrapoláció Lagrange polinommal λ=0-ra.

    Args:
        scale_factors: A zajszorzók (λ_j).
        values: A mért értékek (E(λ_j)).

    Returns:
        (mitigált_érték, reziduum).
    """
    _validate_inputs(scale_factors, values)
    scales = np.asarray(scale_factors, dtype=np.float64)
    vals = np.asarray(values, dtype=np.float64)
    m = len(scales)

    # Lagrange együtthatók λ=0-ra: c_j = \prod_{k \ne j} (-\lambda_k) / (\lambda_j - \lambda_k)
    coeffs = np.zeros(m, dtype=np.float64)
    for j in range(m):
        others = np.delete(scales, j)
        denom = np.prod(scales[j] - others)
        numer = np.prod(-others)
        coeffs[j] = numer / denom

    extrapolated = float(np.sum(coeffs * vals))
    return extrapolated, None


def linear_extrapolate(
    scale_factors: Sequence[float], values: Sequence[float]
) -> tuple[float, float | None]:
    """Lineáris extrapoláció legkisebb négyzetekkel (fokszám = 1)."""
    return polynomial_extrapolate(scale_factors, values, deg=1)


def polynomial_extrapolate(
    scale_factors: Sequence[float], values: Sequence[float], deg: int = 2
) -> tuple[float, float | None]:
    """Polinomiális extrapoláció legkisebb négyzetekkel a megadott fokszámra.

    Args:
        scale_factors: A zajszorzók.
        values: A mért értékek.
        deg: A polinom fokszáma (1 = lineáris, 2 = másodfokú, stb.).

    Returns:
        (mitigált_érték, reziduum).
    """
    _validate_inputs(scale_factors, values)
    scales = np.asarray(scale_factors, dtype=np.float64)
    vals = np.asarray(values, dtype=np.float64)

    # A fokszám nem haladhatja meg a pontok száma - 1-et
    effective_deg = min(deg, len(scales) - 1)
    poly_coeffs, residuals, _, _, _ = np.polyfit(scales, vals, deg=effective_deg, full=True)

    # A konstans tag (λ=0 értéke) a legkisebb kitevőjű együttható
    extrapolated = float(poly_coeffs[-1])
    res_val = float(residuals[0]) if len(residuals) > 0 else None
    return extrapolated, res_val


def exponential_extrapolate(
    scale_factors: Sequence[float], values: Sequence[float]
) -> tuple[float, float | None]:
    """Exponenciális extrapoláció: E(λ) = a * exp(-b * λ) + c.

    Ha a nemlineáris illesztés nem konvergál, biztonsági tartalékként
    másodfokú polinomiális extrapolációra vált.
    """
    _validate_inputs(scale_factors, values)
    from scipy.optimize import curve_fit

    scales = np.asarray(scale_factors, dtype=np.float64)
    vals = np.asarray(values, dtype=np.float64)

    def _exp_model(x: Any, a: float, b: float, c: float) -> Any:
        return a * np.exp(-b * x) + c

    import warnings

    from scipy.optimize import OptimizeWarning

    p0 = [vals[0] - vals[-1], 0.1, vals[-1]]
    try:
        with warnings.catch_warnings():
            # 3 pont / 3 paraméter: az illesztés PONTOS, a kovariancia elvileg nem
            # becsülhető — a SciPy erre OptimizeWarning-ot ad. Ez nem hiba, a
            # kovarianciát nem is használjuk. Több pontnál a jelzés megmarad.
            if len(scales) == 3:
                warnings.simplefilter("ignore", OptimizeWarning)
            popt, _ = curve_fit(_exp_model, scales, vals, p0=p0, maxfev=5000)
        extrapolated = float(_exp_model(0.0, *popt))
        fitted = _exp_model(scales, *popt)
        residuals = float(np.sum((vals - fitted) ** 2))
        return extrapolated, residuals
    except (RuntimeError, ValueError) as exc:
        # A tartalék NEM csendes: az eredményrekord „exponential” címkét kap,
        # ezért jelezni kell, hogy valójában másodfokú illesztés történt.
        warnings.warn(
            f"az exponenciális illesztés nem konvergált ({exc}); "
            f"másodfokú polinomiális tartalék használva",
            RuntimeWarning,
            stacklevel=2,
        )
        return polynomial_extrapolate(scale_factors, values, deg=2)


def extrapolate(
    method: str, scale_factors: Sequence[float], values: Sequence[float]
) -> tuple[float, float | None]:
    """Diszpécser függvény a megadott extrapolációs módszerhez.

    Args:
        method: "richardson", "linear", "quadratic", "exponential".
        scale_factors: A zajszorzók.
        values: A mért értékek.

    Returns:
        (mitigált_érték, illesztési_reziduum).
    """
    m = method.lower()
    if m in ("richardson", "lagrange"):
        return richardson_extrapolate(scale_factors, values)
    if m == "linear":
        return linear_extrapolate(scale_factors, values)
    if m in ("quadratic", "polynomial", "poly2"):
        return polynomial_extrapolate(scale_factors, values, deg=2)
    if m == "exponential":
        return exponential_extrapolate(scale_factors, values)

    raise ValueError(
        f"ismeretlen extrapolációs modell: {method!r}. "
        f"Támogatott modellek: 'richardson', 'linear', 'quadratic', 'exponential'"
    )
