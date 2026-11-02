"""Fázis 6 — újrapróbálkozási politika és hibatárolás (AC-6.2, AC-6.3, AC-6.4, AC-6.8).

A várakozás injektált ``sleep``-pel történik, így a teszt valós idő nélkül, a
visszalépési képletre pontosan ellenőriz.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

from vqebd.hardware import QuotaExhaustedError
from vqebd.pipeline.retry import RetryPolicy, run_with_retry
from vqebd.storage import Database

pytestmark = pytest.mark.unit

RUN = "run-1"
BATCH = "batch-1"
TOKEN = "Zk3-" + "a" * 40


class _Flaky:
    """Az első ``failures`` híváskor a megadott kivételt dobja, utána értéket ad."""

    def __init__(self, failures: int, exc: Exception, value: int = 42) -> None:
        self.failures = failures
        self.exc = exc
        self.value = value
        self.calls = 0

    def __call__(self) -> int:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc
        return self.value


# --- a politika ---------------------------------------------------------------------


def test_delay_follows_exponential_formula_and_cap() -> None:
    policy = RetryPolicy(max_attempts=6, base_delay_s=5.0, factor=2.0, max_delay_s=30.0)
    assert [policy.delay(n) for n in (1, 2, 3, 4, 5)] == [5.0, 10.0, 20.0, 30.0, 30.0]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0},
        {"max_attempts": -1},
        {"base_delay_s": -1.0},
        {"factor": 0.5},
        {"base_delay_s": 10.0, "max_delay_s": 5.0},
    ],
)
def test_invalid_policy_is_rejected(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)  # type: ignore[arg-type]


def test_delay_rejects_nonpositive_failure_count() -> None:
    with pytest.raises(ValueError, match="legalább 1"):
        RetryPolicy().delay(0)


def test_limited_to_only_tightens() -> None:
    policy = RetryPolicy(max_attempts=3)
    assert policy.limited_to(1).max_attempts == 1
    assert policy.limited_to(10).max_attempts == 3


# --- sikeres és átmeneti eset --------------------------------------------------------


def test_success_first_try_stores_nothing() -> None:
    with Database(":memory:") as db:
        sleeps: list[float] = []
        outcome = run_with_retry(
            _Flaky(0, ConnectionError()),
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(),
            sleep=sleeps.append,
        )
        assert outcome.succeeded and outcome.value == 42 and outcome.attempts == 1
        assert db.failure_history(RUN) == []
        assert sleeps == []


def test_transient_failures_are_retried_with_backoff_then_succeed() -> None:
    """AC-6.2/6.3: két átmeneti hiba után siker; a várakozás a képlet szerinti."""
    with Database(":memory:") as db:
        sleeps: list[float] = []
        flaky = _Flaky(2, ConnectionError("hálózat"))
        outcome = run_with_retry(
            flaky,
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(max_attempts=3, base_delay_s=5.0),
            sleep=sleeps.append,
        )
        assert outcome.succeeded and outcome.attempts == 3 and flaky.calls == 3
        assert sleeps == [5.0, 10.0]
        history = db.failure_history(RUN)
        assert [(h["attempt"], h["error_class"], h["will_retry"]) for h in history] == [
            (1, "transient", 1),
            (2, "transient", 1),
        ]
        assert all(h["error_type"] == "ConnectionError" for h in history)
        assert not db.is_abandoned(RUN)  # nincs eredmény-sor, de az utolsó hiba újrapróbálható


def test_transient_failure_exhausts_max_attempts() -> None:
    """AC-6.3: legfeljebb ``max_attempts`` próbálkozás; az utolsó hiba nem újrapróbálható."""
    with Database(":memory:") as db:
        sleeps: list[float] = []
        flaky = _Flaky(99, ConnectionError("tartósan nem elérhető"))
        outcome = run_with_retry(
            flaky,
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(max_attempts=3, base_delay_s=1.0),
            sleep=sleeps.append,
        )
        assert not outcome.succeeded and outcome.attempts == 3 and flaky.calls == 3
        assert outcome.error_class == "transient"
        assert sleeps == [1.0, 2.0]
        history = db.failure_history(RUN)
        assert [h["will_retry"] for h in history] == [1, 1, 0]
        assert db.is_abandoned(RUN)


# --- tartós és kvótahiba: nincs újrapróbálás -----------------------------------------


@pytest.mark.parametrize(
    ("exc", "expected_class"),
    [
        (ValueError("rossz konfiguráció"), "permanent"),
        (PermissionError("nincs engedély"), "permanent"),
        (QuotaExhaustedError("elfogyott"), "quota"),
    ],
)
def test_permanent_and_quota_errors_are_not_retried(exc: Exception, expected_class: str) -> None:
    with Database(":memory:") as db:
        sleeps: list[float] = []
        flaky = _Flaky(99, exc)
        outcome = run_with_retry(
            flaky,
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(max_attempts=5),
            sleep=sleeps.append,
        )
        assert not outcome.succeeded and outcome.attempts == 1 and flaky.calls == 1
        assert outcome.error_class == expected_class
        assert sleeps == []
        assert [h["will_retry"] for h in db.failure_history(RUN)] == [0]
        assert db.is_abandoned(RUN)


# --- tartósított próbálkozásszám (AC-6.4) --------------------------------------------


def test_attempt_count_persists_across_invocations() -> None:
    """AC-6.4: az adatbázisban tárolt próbálkozások a korlátba számítanak."""
    with Database(":memory:") as db:
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.0)
        sleeps: list[float] = []
        # 1. „folyamat”: két átmeneti hiba, majd a folyamat „összeomlik” (itt: leáll).
        run_with_retry(
            _Flaky(2, ConnectionError()),
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(max_attempts=99),
            sleep=sleeps.append,
        )
        assert db.effective_attempts(RUN) == 2
        # 2. „folyamat”: már csak egy próbálkozás fér a korlátba (3 - 2).
        again = _Flaky(99, ConnectionError("még mindig"))
        outcome = run_with_retry(
            again, db=db, run_id=RUN, batch_id=BATCH, policy=policy, sleep=sleeps.append
        )
        assert again.calls == 1 and not outcome.succeeded
        assert db.effective_attempts(RUN) == 3
        assert db.is_abandoned(RUN)
        assert [h["attempt"] for h in db.failure_history(RUN)] == [1, 2, 3]


def test_forgive_resets_the_limit_but_keeps_history() -> None:
    with Database(":memory:") as db:
        run_with_retry(
            _Flaky(99, ValueError("rossz")),
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(),
            sleep=lambda _s: None,
        )
        assert db.is_abandoned(RUN)
        assert db.forgive_failures(batch_id=BATCH) == 1
        assert not db.is_abandoned(RUN)
        assert db.effective_attempts(RUN) == 0
        assert len(db.failure_history(RUN)) == 1  # a történet megmarad
        # A következő hiba folytonos sorszámot kap (2), de a korlátba újra 1 számít.
        run_with_retry(
            _Flaky(99, ValueError("megint")),
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(),
            sleep=lambda _s: None,
        )
        assert [h["attempt"] for h in db.failure_history(RUN)] == [1, 2]
        assert db.effective_attempts(RUN) == 1


# --- titoktalanítás a tárolásban (AC-6.8) --------------------------------------------


def test_token_in_exception_message_is_never_stored() -> None:
    with Database(":memory:") as db:
        seen: list[str] = []
        run_with_retry(
            _Flaky(99, RuntimeError(f"hitelesítési hiba, token={TOKEN}")),
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(),
            secrets=[TOKEN],
            sleep=lambda _s: None,
            on_failure=seen.append,
        )
        stored = db.failure_history(RUN)[0]["error_message"]
        assert TOKEN not in stored
        assert all(TOKEN not in message for message in seen)
        assert "RuntimeError" in stored


def test_keyboard_interrupt_is_not_swallowed() -> None:
    def interrupted() -> int:
        raise KeyboardInterrupt

    with Database(":memory:") as db, pytest.raises(KeyboardInterrupt):
        run_with_retry(
            interrupted,
            db=db,
            run_id=RUN,
            batch_id=BATCH,
            policy=RetryPolicy(),
            sleep=lambda _s: None,
        )
    with Database(":memory:") as db2:
        assert db2.failure_history(RUN) == []
