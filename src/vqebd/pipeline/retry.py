"""Korlátos, osztályozott újrapróbálkozás hibatárolással (Fázis 6, ADR-0008).

A visszalépés determinisztikus (nincs jitter), az idő injektálható (``sleep``), így a
viselkedés valós várakozás nélkül tesztelhető. A próbálkozásszám az adatbázisban él
(``run_failures``), ezért egy újraindított folyamat folytatja, nem kezdi elölről.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from vqebd.pipeline.errors import ErrorClass, classify, scrub_secrets
from vqebd.storage import Database

__all__ = ["AttemptResult", "RetryPolicy", "run_with_retry"]

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Újrapróbálkozási politika.

    Attributes:
        max_attempts: A futásra számító próbálkozások felső korlátja (≥ 1; az első
            próbálkozást is beleértve). 1 = nincs újrapróbálás.
        base_delay_s: Az első újrapróbálás előtti várakozás.
        factor: A várakozás szorzója minden további újrapróbálás előtt (≥ 1).
        max_delay_s: A várakozás felső korlátja.
    """

    max_attempts: int = 3
    base_delay_s: float = 5.0
    factor: float = 2.0
    max_delay_s: float = 300.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts legalább 1: {self.max_attempts}")
        if self.base_delay_s < 0:
            raise ValueError(f"base_delay_s nem negatív: {self.base_delay_s}")
        if self.factor < 1:
            raise ValueError(f"factor legalább 1: {self.factor}")
        if self.max_delay_s < self.base_delay_s:
            raise ValueError(
                f"max_delay_s ({self.max_delay_s}) nem lehet kisebb a base_delay_s-nél "
                f"({self.base_delay_s})"
            )

    def delay(self, failed_attempts: int) -> float:
        """A várakozás ``failed_attempts`` sikertelen próbálkozás után, másodpercben."""
        if failed_attempts < 1:
            raise ValueError(f"failed_attempts legalább 1: {failed_attempts}")
        return min(self.base_delay_s * self.factor ** (failed_attempts - 1), self.max_delay_s)

    def limited_to(self, max_attempts: int) -> RetryPolicy:
        """A politika szigorított másolata (pl. hardveren 1 próbálkozás)."""
        return RetryPolicy(
            max_attempts=min(self.max_attempts, max_attempts),
            base_delay_s=self.base_delay_s,
            factor=self.factor,
            max_delay_s=self.max_delay_s,
        )


@dataclass(frozen=True, slots=True)
class AttemptResult(Generic[T]):
    """Egy futás próbálkozás-sorozatának eredménye.

    Attributes:
        value: A művelet visszatérési értéke siker esetén, különben ``None``.
        succeeded: Sikerült-e.
        attempts: Ebben a híváskori próbálkozások száma.
        error_class: A végső hiba osztálya (sikertelen esetben).
        error: A végső hiba titoktalanított szövege (sikertelen esetben).
    """

    value: T | None
    succeeded: bool
    attempts: int
    error_class: ErrorClass | None = None
    error: str | None = None


def run_with_retry(
    operation: Callable[[], T],
    *,
    db: Database,
    run_id: str,
    batch_id: str | None,
    policy: RetryPolicy,
    secrets: Iterable[str] = (),
    sleep: Callable[[float], None] = time.sleep,
    on_failure: Callable[[str], None] | None = None,
) -> AttemptResult[T]:
    """A művelet végrehajtása a politika szerint; minden hiba az adatbázisba kerül.

    A korlátba az adatbázisban már tárolt (nem megbocsátott) próbálkozások is
    beleszámítanak, így egy újraindított folyamat nem ismétel végtelenül.
    ``KeyboardInterrupt`` és ``SystemExit`` nem kerülnek elnyelésre.

    Args:
        operation: A futtatandó, argumentum nélküli művelet.
        db: A hibákat tároló adatbázis.
        run_id: A futás azonosítója.
        batch_id: A batch azonosítója (a hibasorhoz).
        policy: Az újrapróbálkozási politika.
        secrets: Titkok szó szerinti maszkolásához (a minta-alapú maszkolás mellett).
        sleep: A várakozás függvénye (tesztben injektálható).
        on_failure: Opcionális visszahívás a titoktalanított hibaüzenettel.
    """
    secret_values = tuple(secrets)
    attempts = 0
    while True:
        started = time.perf_counter()
        try:
            value = operation()
        except Exception as exc:
            attempts += 1
            error_class = classify(exc)
            effective = db.effective_attempts(run_id) + 1
            will_retry = error_class == "transient" and effective < policy.max_attempts
            message = scrub_secrets(f"{type(exc).__name__}: {exc}", secret_values)
            db.record_failure(
                run_id,
                batch_id=batch_id,
                error_type=type(exc).__name__,
                error_class=error_class,
                error_message=message,
                wall_time_s=time.perf_counter() - started,
                will_retry=will_retry,
            )
            if on_failure is not None:
                on_failure(message)
            if not will_retry:
                return AttemptResult(
                    value=None,
                    succeeded=False,
                    attempts=attempts,
                    error_class=error_class,
                    error=message,
                )
            sleep(policy.delay(effective))
        else:
            return AttemptResult(value=value, succeeded=True, attempts=attempts + 1)
