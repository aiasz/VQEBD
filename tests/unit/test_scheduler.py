"""Fázis 6 — ütemező: intervallum, átfedés elleni zár, hardverpolitika (AC-6.10, AC-6.11).

Az órát és az alvást a teszt injektálja: valós várakozás és valós pipeline nélkül fut.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from vqebd import scheduler
from vqebd.scheduler import LockHeldError, PipelineLock, parse_interval, run_scheduler

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("30s", 30.0),
        ("15m", 900.0),
        ("6h", 21600.0),
        ("1d", 86400.0),
        (" 2H ", 7200.0),
        ("1.5h", 5400.0),
    ],
)
def test_parse_interval(text: str, seconds: float) -> None:
    assert parse_interval(text) == seconds


@pytest.mark.parametrize("text", ["", "6", "h", "6x", "-1h", "0s", "abc", "1 hour"])
def test_parse_interval_rejects_garbage(text: str) -> None:
    with pytest.raises(ValueError):
        parse_interval(text)


# --- zár (AC-6.10) ---------------------------------------------------------------------


class _Clock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_lock_blocks_a_second_holder(tmp_path: Path) -> None:
    clock = _Clock()
    first = PipelineLock(tmp_path / "x.lock", now=clock)
    second = PipelineLock(tmp_path / "x.lock", now=clock)
    first.acquire()
    with pytest.raises(LockHeldError):
        second.acquire()
    first.release()
    second.acquire()  # elengedés után megszerezhető
    second.release()
    assert not (tmp_path / "x.lock").exists()


def test_stale_lock_is_taken_over(tmp_path: Path) -> None:
    clock = _Clock()
    old = PipelineLock(tmp_path / "x.lock", stale_after_s=3600.0, now=clock)
    old.acquire()
    clock.now += 3600.0  # pontosan a határ: már elavult
    fresh = PipelineLock(tmp_path / "x.lock", stale_after_s=3600.0, now=clock)
    fresh.acquire()
    fresh.release()


def test_lock_just_under_the_limit_is_still_held(tmp_path: Path) -> None:
    clock = _Clock()
    PipelineLock(tmp_path / "x.lock", stale_after_s=3600.0, now=clock).acquire()
    clock.now += 3599.0
    with pytest.raises(LockHeldError):
        PipelineLock(tmp_path / "x.lock", stale_after_s=3600.0, now=clock).acquire()


@pytest.mark.parametrize("content", ["", "nem json", "{}", '{"started": "x"}', "[1, 2]"])
def test_corrupt_lock_is_treated_as_stale(tmp_path: Path, content: str) -> None:
    path = tmp_path / "x.lock"
    path.write_text(content, encoding="utf-8")
    lock = PipelineLock(path)
    lock.acquire()
    assert json.loads(path.read_text(encoding="utf-8"))["started"] > 0
    lock.release()


def test_release_without_acquire_does_not_delete_a_foreign_lock(tmp_path: Path) -> None:
    clock = _Clock()
    owner = PipelineLock(tmp_path / "x.lock", now=clock)
    owner.acquire()
    PipelineLock(tmp_path / "x.lock", now=clock).release()  # nem a miénk
    assert (tmp_path / "x.lock").exists()
    owner.release()


def _counting_job(calls: list[int]) -> Callable[[], int]:
    def job() -> int:
        calls.append(1)
        return 0

    return job


# --- az ütemezési hurok ----------------------------------------------------------------


def test_once_returns_the_job_exit_code_and_releases_the_lock(tmp_path: Path) -> None:
    lock = PipelineLock(tmp_path / "x.lock")
    assert run_scheduler(lambda: 1, every_s=None, lock=lock, log=lambda _m: None) == 1
    assert not (tmp_path / "x.lock").exists()


def test_once_with_a_held_lock_skips_the_job_and_returns_2(tmp_path: Path) -> None:
    """AC-6.10: egy még futó pipeline mellé nem indul második."""
    PipelineLock(tmp_path / "x.lock").acquire()
    calls: list[int] = []
    code = run_scheduler(
        _counting_job(calls),
        every_s=None,
        lock=PipelineLock(tmp_path / "x.lock"),
        log=lambda _m: None,
    )
    assert code == 2 and calls == []


def test_repeating_mode_runs_every_period_with_injected_sleep(tmp_path: Path) -> None:
    sleeps: list[float] = []
    calls: list[int] = []
    run_scheduler(
        _counting_job(calls),
        every_s=3600.0,
        lock=PipelineLock(tmp_path / "x.lock"),
        sleep=sleeps.append,
        max_iterations=3,
        log=lambda _m: None,
    )
    assert len(calls) == 3 and sleeps == [3600.0, 3600.0]
    assert not (tmp_path / "x.lock").exists()


def test_repeating_mode_skips_overlap_but_keeps_looping(tmp_path: Path) -> None:
    PipelineLock(tmp_path / "x.lock").acquire()
    sleeps: list[float] = []
    calls: list[int] = []
    run_scheduler(
        _counting_job(calls),
        every_s=60.0,
        lock=PipelineLock(tmp_path / "x.lock"),
        sleep=sleeps.append,
        max_iterations=2,
        log=lambda _m: None,
    )
    assert calls == [] and sleeps == [60.0]


def test_lock_is_released_even_if_the_job_raises(tmp_path: Path) -> None:
    def boom() -> int:
        raise RuntimeError("összeomlás")

    with pytest.raises(RuntimeError):
        run_scheduler(
            boom, every_s=None, lock=PipelineLock(tmp_path / "x.lock"), log=lambda _m: None
        )
    assert not (tmp_path / "x.lock").exists()


# --- hardverpolitika és a compose-szolgáltatás (AC-6.11) ----------------------------------


def test_allow_hardware_is_rejected_in_repeating_mode(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        scheduler.main(["--preset", "f5-smoke", "--every", "1h", "--allow-hardware"])
    assert info.value.code == 2
    assert "nem ütemezett" in capsys.readouterr().err


def test_invalid_interval_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as info:
        scheduler.main(["--preset", "f5-smoke", "--every", "sokára"])
    assert info.value.code == 2


def test_compose_defines_a_simulator_only_scheduler_service(repo_root: Path) -> None:
    """AC-6.11: van `scheduler` szolgáltatás, az ütemezőt hívja, hardvert nem engedélyez.

    A repó-checkoutot igényli (a `repo_root` fixture a szállított image-ben kihagyja).
    """
    text = (repo_root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    assert re.search(r"^  scheduler:\s*$", text, re.MULTILINE)
    # A scheduler blokkja a Fázis 8 megjegyzéssel induló dashboard-szakaszig tart.
    block = text[text.index("  scheduler:") : text.index("  # --- Fázis 8")]
    assert "vqebd.scheduler" in block
    assert "--every" in block
    assert "allow-hardware" not in block
    assert "IBM_QUANTUM" not in block and "env_file" not in block  # titok nélkül
