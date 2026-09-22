"""A VQE klasszikus optimalizáló-hurka (SciPy).

Ez a modul valósítja meg az [ADR-0002](../../docs/adr/ADR-0002-sajat-vqe-hurok.md)
szerinti saját hurkot a ``qiskit-algorithms`` helyett. A cél nem a kerék
újrafeltalálása, hanem:

- **előre-hordozhatóság** — V2 primitívekre épül, így Qiskit 2.x-ben is fut;
- **átláthatóság** — minden iteráció naplózódik, a konvergencia utólag elemezhető;
- **egyetlen kódút** — ugyanez a hurok fut egzakt, zajos és QPU-backenden.

Támogatott optimalizálók
------------------------
=================  =================  ====================================
Metódus            Hivatkozás         Mikor használjuk
=================  =================  ====================================
``SLSQP``          [kraft1988]        Zajmentes eset; gyors és pontos.
``COBYLA``         [powell1994]       Deriváltmentes; zajos célfüggvényhez.
``Nelder-Mead``    [nelder1965]       Robusztus, de sok kiértékelést igényel.
``L-BFGS-B``       —                  Kvázi-Newton alternatíva.
``Powell``         —                  Irány-készletes, deriváltmentes.
=================  =================  ====================================

A gradiens-alapú módszerek (``SLSQP``, ``L-BFGS-B``) véges differenciákkal
becsülnek gradienst, ami **zajos** célfüggvényen félrevezető. A Fázis 1b-től
ezért a ``COBYLA`` vagy az ``SPSA`` [spall1992] lesz az ajánlott választás; a
Fázis 1 zajmentes esetében az ``SLSQP`` a leghatékonyabb.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from vqebd.backends.estimators import EnergyEvaluator
from vqebd.config import OptimizerSpec

__all__ = ["SUPPORTED_METHODS", "OptimizationOutcome", "minimize_energy"]

SUPPORTED_METHODS: Final[frozenset[str]] = frozenset(
    {"SLSQP", "COBYLA", "Nelder-Mead", "L-BFGS-B", "Powell", "BFGS", "CG", "TNC"}
)
"""A SciPy metódusok, amelyeket engedünk.

Szándékosan zárt lista: egy elgépelt metódusnév a SciPy-ban csendben más
viselkedésre válthat, nálunk viszont azonnali, beszédes hibát adjon.
"""

# Az iterációs korlát opciókulcsa metódusonként eltér a SciPy-ban. Ha rossz
# kulcsot adunk át, a SciPy `OptimizeWarning`-gal **csendben eldobja** a
# beállítást, és a korlát nem érvényesül — ezért kell ez az explicit leképezés.
_MAXITER_KEY: Final[dict[str, str]] = {
    "TNC": "maxfun",  # a TNC függvényhívás-korlátot ismer, iterációkorlátot nem
}
_DEFAULT_MAXITER_KEY: Final[str] = "maxiter"


@dataclass(frozen=True, slots=True)
class OptimizationOutcome:
    """A klasszikus optimalizálás eredménye.

    Attributes:
        parameters: Az optimális paraméterek.
        value: A célfüggvény (elektronos energia) minimuma, Ha.
        n_iterations: Az optimalizáló iterációinak száma.
        n_function_evaluations: A célfüggvény-kiértékelések száma. **Ez a valódi
            költségmutató** — hardveren ez fordul QPU-időre.
        converged: A SciPy szerint sikeres volt-e a konvergencia.
        message: A SciPy állapotüzenete.
        history: Iterációnkénti energia; a konvergencia utólagos elemzéséhez.
    """

    parameters: tuple[float, ...]
    value: float
    n_iterations: int
    n_function_evaluations: int
    converged: bool
    message: str
    history: tuple[float, ...]


def minimize_energy(
    evaluator: EnergyEvaluator,
    initial_parameters: Sequence[float],
    spec: OptimizerSpec,
) -> OptimizationOutcome:
    """Az energia minimalizálása a variációs paraméterek szerint.

    Args:
        evaluator: A kiértékelő; ``θ → ⟨ψ(θ)|H|ψ(θ)⟩``.
        initial_parameters: A kezdőparaméterek.
        spec: Az optimalizáló beállításai.

    Returns:
        Az :class:`OptimizationOutcome`.

    Raises:
        ValueError: Nem támogatott metódus esetén.
    """
    if spec.method not in SUPPORTED_METHODS:
        raise ValueError(
            f"nem támogatott optimalizáló: {spec.method!r}. "
            f"Engedélyezett: {sorted(SUPPORTED_METHODS)}"
        )

    import numpy as np
    import numpy.typing as npt
    from scipy.optimize import OptimizeWarning, minimize

    history: list[float] = []

    def objective(parameters: npt.NDArray[np.float64]) -> float:
        energy = evaluator(parameters.tolist())
        history.append(energy)
        return energy

    x0 = np.asarray(initial_parameters, dtype=float)

    # Speciális eset: paraméter nélküli ansatz (pl. csak Hartree–Fock állapot).
    # A SciPy üres vektorral nem tud mit kezdeni, de a feladat értelmes.
    if x0.size == 0:
        value = objective(x0)
        return OptimizationOutcome(
            parameters=(),
            value=value,
            n_iterations=0,
            n_function_evaluations=1,
            converged=True,
            message="paraméter nélküli ansatz — nincs mit optimalizálni",
            history=(value,),
        )

    options: dict[str, int] = {_MAXITER_KEY.get(spec.method, _DEFAULT_MAXITER_KEY): spec.maxiter}

    # A SciPy `OptimizeWarning`-ot ad, ha ismeretlen opciókulcsot kap, és a
    # beállítást eldobja. Ezt nem hagyhatjuk csendben: ha megtörténik, az a
    # `_MAXITER_KEY` leképezés hibája, és a korlát nem érvényesülne.
    with warnings.catch_warnings():
        warnings.simplefilter("error", OptimizeWarning)
        try:
            result = minimize(objective, x0, method=spec.method, tol=spec.tol, options=options)
        except OptimizeWarning as warning:
            raise ValueError(
                f"a(z) {spec.method!r} metódus nem fogadja el a megadott opciókat "
                f"({options}): {warning}. Egészítsd ki a _MAXITER_KEY leképezést."
            ) from warning

    # A `nit` mezőt nem minden SciPy-metódus adja meg (pl. a COBYLA nem).
    n_iterations = int(getattr(result, "nit", 0) or 0)

    return OptimizationOutcome(
        parameters=tuple(float(v) for v in np.atleast_1d(result.x)),
        value=float(result.fun),
        n_iterations=n_iterations,
        n_function_evaluations=int(result.nfev),
        converged=bool(result.success),
        message=str(result.message),
        history=tuple(history),
    )
