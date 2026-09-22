"""Az optimalizáló-burkolat egységtesztjei.

Ezek a tesztek **analitikus célfüggvényeken** futnak, nem kvantumszimuláción:
így gyorsak, és a burkolat hibáit elkülönítik a fizika hibáitól. Ha egy VQE-futás
rossz eredményt ad, ezekből tudni fogjuk, hogy nem az optimalizáló a hibás.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

pytest.importorskip("scipy", reason="a SciPy optimalizálót igényli")

from vqebd.backends.estimators import EnergyEvaluator
from vqebd.config import BackendKind, OptimizerSpec
from vqebd.vqe.optimizer import SUPPORTED_METHODS, minimize_energy

pytestmark = pytest.mark.unit


class QuadraticEvaluator(EnergyEvaluator):
    """Analitikus próbafüggvény: eltolt paraboloid.

    ``f(x) = Σ (xᵢ − cᵢ)² + offset``

    A minimuma ismert (``x = c``, ``f = offset``), így az optimalizáló-burkolat
    helyessége kvantumszimuláció nélkül ellenőrizhető.
    """

    def __init__(self, center: Sequence[float], offset: float = 0.0) -> None:
        super().__init__(num_qubits=0)
        self.center = tuple(float(c) for c in center)
        self.offset = offset

    @property
    def kind(self) -> BackendKind:
        return "statevector"

    def evaluate(self, parameters: Sequence[float]) -> float:
        return sum((p - c) ** 2 for p, c in zip(parameters, self.center, strict=True)) + self.offset


# --- Alapműködés -------------------------------------------------------------


@pytest.mark.parametrize("method", sorted(SUPPORTED_METHODS))
def test_every_supported_method_finds_the_minimum(method: str) -> None:
    """Minden engedélyezett metódus megtalálja az ismert minimumot."""
    evaluator = QuadraticEvaluator(center=(0.5, -1.25, 2.0), offset=-3.0)
    outcome = minimize_energy(
        evaluator, [0.0, 0.0, 0.0], OptimizerSpec(method=method, maxiter=5000)
    )
    assert outcome.value == pytest.approx(-3.0, abs=1e-4), (
        f"{method}: a minimum {outcome.value}, a várt −3.0"
    )
    for actual, expected in zip(outcome.parameters, (0.5, -1.25, 2.0), strict=True):
        assert actual == pytest.approx(expected, abs=1e-3)


def test_evaluator_call_count_is_tracked() -> None:
    """A kiértékelések számát a kiértékelő tartja nyilván (költségmutató)."""
    evaluator = QuadraticEvaluator(center=(1.0,))
    outcome = minimize_energy(evaluator, [0.0], OptimizerSpec(method="SLSQP"))
    assert evaluator.call_count > 0
    assert outcome.n_function_evaluations > 0


def test_history_records_every_evaluation() -> None:
    """A konvergencia-napló minden kiértékelést rögzít, csökkenő trenddel."""
    evaluator = QuadraticEvaluator(center=(2.0,))
    outcome = minimize_energy(evaluator, [0.0], OptimizerSpec(method="SLSQP"))
    assert len(outcome.history) == evaluator.call_count
    assert outcome.history[-1] <= outcome.history[0], "a végérték nem jobb a kezdőértéknél"


def test_outcome_value_matches_history_minimum() -> None:
    """A visszaadott minimum nem rosszabb a naplóban látott legjobb értéknél."""
    evaluator = QuadraticEvaluator(center=(0.3, -0.7))
    outcome = minimize_energy(evaluator, [0.0, 0.0], OptimizerSpec(method="SLSQP"))
    assert outcome.value == pytest.approx(min(outcome.history), abs=1e-9)


# --- Határesetek -------------------------------------------------------------


def test_zero_parameter_ansatz_is_handled() -> None:
    """Paraméter nélküli ansatz: egyetlen kiértékelés, nincs optimalizálás.

    A SciPy üres vektorral nem tud mit kezdeni, de a feladat fizikailag értelmes
    (pl. tisztán Hartree–Fock állapot), ezért külön kezeljük.
    """
    evaluator = QuadraticEvaluator(center=(), offset=1.5)
    outcome = minimize_energy(evaluator, [], OptimizerSpec())
    assert outcome.parameters == ()
    assert outcome.value == pytest.approx(1.5)
    assert outcome.converged is True
    assert outcome.n_function_evaluations == 1


def test_maxiter_one_does_not_crash() -> None:
    """Szoros iterációs korlát mellett sem omlik össze, csak nem konvergál.

    A robusztusság feltétele, hogy a korlátba ütközés **adatot** adjon
    (``converged=False``), ne kivételt.
    """
    evaluator = QuadraticEvaluator(center=(10.0, -10.0))
    outcome = minimize_energy(evaluator, [0.0, 0.0], OptimizerSpec(method="Nelder-Mead", maxiter=1))
    assert isinstance(outcome.value, float)
    assert outcome.converged is False


def test_unknown_method_is_rejected_with_a_clear_message() -> None:
    """Az elgépelt metódusnév azonnali, beszédes hibát ad.

    A SciPy ismeretlen metódusnévnél más viselkedésre válthat; nálunk ez
    azonnal, a támogatott metódusok felsorolásával bukjon el.
    """
    evaluator = QuadraticEvaluator(center=(0.0,))
    with pytest.raises(ValueError, match="nem támogatott optimalizáló"):
        minimize_energy(evaluator, [0.0], OptimizerSpec(method="SLSQPP"))


def test_supported_methods_is_not_empty_and_contains_the_default() -> None:
    assert SUPPORTED_METHODS
    assert OptimizerSpec().method in SUPPORTED_METHODS


@pytest.mark.parametrize("method", sorted(SUPPORTED_METHODS))
def test_iteration_limit_option_is_accepted_by_every_method(method: str) -> None:
    """Minden metódus **elfogadja** a neki átadott iterációs korlát kulcsot.

    A SciPy ismeretlen opciókulcs esetén ``OptimizeWarning``-ot ad, és a
    beállítást **csendben eldobja** — a korlát ilyenkor nem érvényesülne. Ezt a
    ``minimize_energy`` hibává emeli, így ez a teszt kimutatja, ha a
    ``_MAXITER_KEY`` leképezés hiányos.

    Konkrét eset: a ``TNC`` metódus nem ``maxiter``-t, hanem ``maxfun``-t ismer.
    """
    evaluator = QuadraticEvaluator(center=(0.25,))
    outcome = minimize_energy(evaluator, [0.0], OptimizerSpec(method=method, maxiter=200))
    assert isinstance(outcome.value, float)
