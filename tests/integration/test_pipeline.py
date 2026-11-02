"""Fázis 6 — a pipeline végponttól végpontig (AC-6.1, AC-6.5, AC-6.6, AC-6.7, AC-6.8).

Szimulátoron fut; valódi QPU-t egyik teszt sem ér el (a hardveres ágat a ``run_vqe``
lecserélése és az engedély hiánya zárja ki).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("qiskit_aer", reason="a pipeline-teszt Aer szimulátort igényel")

import vqebd.batch.run as batch_run
import vqebd.pipeline.runner as pipeline_runner
from vqebd.batch import get_preset, run_batch
from vqebd.batch.spec import BatchCell, BatchSpec
from vqebd.chemistry.molecule import h2, lih
from vqebd.config import ActiveSpaceSpec, OptimizerSpec
from vqebd.hardware import QuotaExhaustedError
from vqebd.pipeline.retry import RetryPolicy
from vqebd.pipeline.runner import EXIT_FATAL, EXIT_OK, EXIT_PARTIAL, run_pipeline
from vqebd.storage import Database
from vqebd.vqe.runner import run_vqe as real_run_vqe

pytestmark = pytest.mark.integration

FAST = OptimizerSpec(method="SLSQP", maxiter=50)
TOKEN = "Zk3-" + "a" * 40
CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef:11111111-2222::"


def _mixed_spec() -> BatchSpec:
    """Két jó futás és egy futásidőben elbukó (érvénytelen aktív tér, a Fázis 5 előmérése)."""
    return BatchSpec(
        batch_id="p6-mixed",
        description="hibainjektálás",
        cells=(
            BatchCell(h2(0.735), "qiskit_statevector", FAST),
            BatchCell(lih(1.595), "qiskit_statevector", FAST, active_space=ActiveSpaceSpec(2, 50)),
            BatchCell(h2(0.9), "qiskit_statevector", FAST),
        ),
    )


def _events(log_path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


# --- AC-6.6: dry run -----------------------------------------------------------------


def test_dry_run_runs_the_whole_chain_without_error(tmp_path: Path) -> None:
    """AC-6.6: előellenőrzés → batch → export → összegzés, 0 kilépési kóddal, naplóval."""
    export = tmp_path / "export.json"
    result = run_pipeline(
        "f5-smoke",
        db_path=tmp_path / "db.sqlite",
        export_path=export,
        log_dir=tmp_path / "logs",
        sleep=lambda _s: None,
    )
    assert result.exit_code == EXIT_OK, result.message
    assert result.report is not None and len(result.report.completed) == 5
    payload = json.loads(export.read_text(encoding="utf-8"))
    assert payload["batch_id"] == "f5-smoke" and payload["stored_runs"] == 5
    steps = [(e["step"], e["status"]) for e in _events(result.log_path)]
    assert steps[0] == ("preflight", "ok")
    assert ("batch", "done") in steps and ("export", "ok") in steps
    assert steps[-1] == ("summary", "ok")


def test_pipeline_matches_plain_run_batch_bitwise(tmp_path: Path) -> None:
    """Keresztvalidáció: a pipeline eredménye bitre egyezik a Fázis 5 ``run_batch``-ével."""
    result = run_pipeline(
        "f5-smoke",
        db_path=tmp_path / "pipe.sqlite",
        log_dir=tmp_path / "logs",
        sleep=lambda _s: None,
    )
    assert result.exit_code == EXIT_OK
    with Database(tmp_path / "plain.sqlite") as plain:
        run_batch(get_preset("f5-smoke"), plain)
        expected = plain.batch_results("f5-smoke")
    with Database(tmp_path / "pipe.sqlite") as piped:
        actual = piped.batch_results("f5-smoke")
    keys = ("run_id", "energy_ha", "config_hash", "optimal_parameters_json")
    assert [{k: r[k] for k in keys} for r in actual] == [{k: r[k] for k in keys} for r in expected]


def test_second_invocation_resumes_without_rerunning(tmp_path: Path) -> None:
    kwargs: dict[str, Any] = {
        "db_path": tmp_path / "db.sqlite",
        "log_dir": tmp_path / "logs",
        "sleep": lambda _s: None,
    }
    first = run_pipeline("f5-smoke", **kwargs)
    second = run_pipeline("f5-smoke", **kwargs)
    assert first.exit_code == second.exit_code == EXIT_OK
    assert second.report is not None
    assert len(second.report.completed) == 0 and len(second.report.skipped) == 5


# --- AC-6.1, AC-6.7: hibainjektálás ---------------------------------------------------


def test_failing_run_is_stored_logged_and_does_not_crash_the_pipeline(tmp_path: Path) -> None:
    """AC-6.1/6.7: a hibás futás sorként tárolódik, a pipeline folytatja, a kilépési kód 1."""
    export = tmp_path / "export.json"
    result = run_pipeline(
        spec=_mixed_spec(),
        db_path=tmp_path / "db.sqlite",
        export_path=export,
        log_dir=tmp_path / "logs",
        sleep=lambda _s: None,
    )
    assert result.exit_code == EXIT_PARTIAL
    assert result.report is not None
    assert len(result.report.completed) == 2 and len(result.report.failed) == 1

    with Database(tmp_path / "db.sqlite") as db:
        (failure,) = db.failures("p6-mixed")
        assert failure["error_type"] == "ValueError"
        assert failure["error_class"] == "permanent" and failure["will_retry"] == 0
        assert failure["attempt"] == 1 and "aktív tér" in failure["error_message"]
        assert db.count() == 2

    events = _events(result.log_path)
    batch_done = next(e for e in events if (e["step"], e["status"]) == ("batch", "done"))
    assert batch_done["failed"] == 1 and batch_done["completed"] == 2
    assert any("HIBA" in e.get("message", "") for e in events)
    assert events[-1]["status"] == "partial" and events[-1]["exit_code"] == EXIT_PARTIAL
    exported = json.loads(export.read_text(encoding="utf-8"))
    assert len(exported["failed"]) == 1 and exported["stored_runs"] == 2


def test_permanent_failure_is_abandoned_until_retry_abandoned(tmp_path: Path) -> None:
    """AC-6.4: a második indítás nem futtatja újra; a --retry-abandoned visszaállítja."""
    kwargs: dict[str, Any] = {
        "spec": _mixed_spec(),
        "db_path": tmp_path / "db.sqlite",
        "log_dir": tmp_path / "logs",
        "sleep": lambda _s: None,
    }
    run_pipeline(**kwargs)

    second = run_pipeline(**kwargs)
    assert second.exit_code == EXIT_PARTIAL and second.report is not None
    assert len(second.report.abandoned) == 1 and second.report.failed == []
    with Database(tmp_path / "db.sqlite") as db:
        assert len(db.failures()) == 1  # nem jött új hibasor: a futás meg sem indult

    third = run_pipeline(retry_abandoned=True, **kwargs)
    assert third.report is not None and len(third.report.failed) == 1
    assert third.report.abandoned == []
    with Database(tmp_path / "db.sqlite") as db:
        rows = db.failures()
        assert [r["attempt"] for r in rows] == [1, 2]
        assert [r["forgiven"] for r in rows] == [1, 0]
    forgiven = next(e for e in _events(third.log_path) if e["step"] == "retry_abandoned")
    assert forgiven["forgiven_rows"] == 1


def test_transient_failure_is_retried_and_the_run_completes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Átmeneti hiba kétszer, majd siker: a futás tárolódik, a hibák is."""
    real = real_run_vqe
    calls = {"n": 0}

    def flaky(config: Any, *args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ConnectionError("a hálózat átmenetileg nem elérhető")
        return real(config, *args, **kwargs)

    monkeypatch.setattr(batch_run, "run_vqe", flaky)
    spec = BatchSpec(
        batch_id="p6-flaky",
        description="átmeneti hiba",
        cells=(BatchCell(h2(0.735), "qiskit_statevector", FAST),),
    )
    sleeps: list[float] = []
    result = run_pipeline(
        spec=spec,
        db_path=tmp_path / "db.sqlite",
        log_dir=tmp_path / "logs",
        policy=RetryPolicy(max_attempts=3, base_delay_s=5.0),
        sleep=sleeps.append,
    )
    assert result.exit_code == EXIT_OK and result.report is not None
    assert len(result.report.completed) == 1 and sleeps == [5.0, 10.0]
    with Database(tmp_path / "db.sqlite") as db:
        history = db.failures("p6-flaky")
        assert [(f["error_class"], f["will_retry"]) for f in history] == [
            ("transient", 1),
            ("transient", 1),
        ]
        assert db.count() == 1


# --- előellenőrzés és hardver ----------------------------------------------------------


def test_unknown_preset_is_fatal_not_an_exception(tmp_path: Path) -> None:
    result = run_pipeline("nincs-ilyen", db_path=tmp_path / "db.sqlite", log_dir=tmp_path / "l")
    assert result.exit_code == EXIT_FATAL and "ismeretlen batch-preset" in result.message
    assert _events(result.log_path)[-1]["status"] == "fatal"
    assert not (tmp_path / "db.sqlite").exists()  # az adatbázis nem is jött létre


def test_pipeline_requires_spec_or_preset(tmp_path: Path) -> None:
    result = run_pipeline(db_path=tmp_path / "db.sqlite", log_dir=tmp_path / "l")
    assert result.exit_code == EXIT_FATAL


def _hardware_spec() -> BatchSpec:
    return BatchSpec(
        batch_id="p6-hw",
        description="hardver",
        cells=(BatchCell(h2(), "ibm_qpu", OptimizerSpec(method="COBYLA", maxiter=5)),),
    )


def test_hardware_batch_is_refused_unless_explicitly_allowed(tmp_path: Path) -> None:
    """AC-6.11 szellemében: a pipeline alapértelmezésben nem indít valódi QPU-t."""
    result = run_pipeline(
        spec=_hardware_spec(), db_path=tmp_path / "db.sqlite", log_dir=tmp_path / "logs"
    )
    assert result.exit_code == EXIT_FATAL and "--allow-hardware" in result.message
    assert not (tmp_path / "db.sqlite").exists()


def test_allow_hardware_still_needs_the_environment_permission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Két kulcs kell: a kapcsoló és a VQEBD_ALLOW_HARDWARE környezeti változó."""
    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    result = run_pipeline(
        spec=_hardware_spec(),
        db_path=tmp_path / "db.sqlite",
        log_dir=tmp_path / "logs",
        allow_hardware=True,
    )
    assert result.exit_code == EXIT_FATAL and "VQEBD_ALLOW_HARDWARE" in result.message


def test_hardware_runs_get_a_single_attempt_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6.5: hardveren egy átmeneti hiba sem ismétlődik (egy újrapróbálás kvótát fogyasztana)."""
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    monkeypatch.setattr(pipeline_runner, "guard_hardware_vqe", lambda *a, **k: 0.0)
    calls = {"n": 0}

    def always_fails(config: Any, *args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        raise ConnectionError("hálózat")

    monkeypatch.setattr(batch_run, "run_vqe", always_fails)
    sleeps: list[float] = []
    result = run_pipeline(
        spec=_hardware_spec(),
        db_path=tmp_path / "db.sqlite",
        log_dir=tmp_path / "logs",
        allow_hardware=True,
        policy=RetryPolicy(max_attempts=5),
        sleep=sleeps.append,
    )
    assert result.exit_code == EXIT_PARTIAL
    assert calls["n"] == 1 and sleeps == []
    with Database(tmp_path / "db.sqlite") as db:
        (failure,) = db.failures("p6-hw")
        assert failure["error_class"] == "transient" and failure["will_retry"] == 0


def test_batch_level_quota_gate_covers_the_whole_batch_with_reserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A kapu a batch összes hardveres futásának legrosszabb esetére, +20% tartalékkal kérdez."""
    seen: dict[str, Any] = {}

    def gate(max_evaluations: int, **kwargs: Any) -> float:
        seen["evaluations"] = max_evaluations
        seen.update(kwargs)
        raise QuotaExhaustedError("a hátralévő kvóta kevesebb a becsült igénynél")

    monkeypatch.setattr(pipeline_runner, "guard_hardware_vqe", gate)
    spec = BatchSpec(
        batch_id="p6-gate",
        description="kapu",
        cells=(
            BatchCell(
                h2(), "ibm_qpu", OptimizerSpec(method="COBYLA", maxiter=5), repeats=2, reestimate=3
            ),
        ),
    )
    result = run_pipeline(
        spec=spec, db_path=tmp_path / "db.sqlite", log_dir=tmp_path / "logs", allow_hardware=True
    )
    assert result.exit_code == EXIT_FATAL and "kvóta" in result.message
    # 2 ismétlés × (maxiter 5 + újramintavétel 3) = 16 kiértékelés, 20% tartalékkal
    assert seen["evaluations"] == 16 and seen["reserve"] == pytest.approx(1.2)
    assert not (tmp_path / "db.sqlite").exists()  # a kapu a batch előtt megállított


def test_quota_gate_is_not_consulted_for_simulator_batches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> float:
        raise AssertionError("szimulátoros batchnél nincs kvótakapu")

    monkeypatch.setattr(pipeline_runner, "guard_hardware_vqe", forbidden)
    spec = BatchSpec(
        batch_id="p6-sim",
        description="szimulátor",
        cells=(BatchCell(h2(), "qiskit_statevector", FAST),),
    )
    result = run_pipeline(
        spec=spec, db_path=tmp_path / "db.sqlite", log_dir=tmp_path / "logs", allow_hardware=True
    )
    assert result.exit_code == EXIT_OK


# --- AC-6.8: titoktalanítás ------------------------------------------------------------


def test_secrets_never_reach_the_database_the_log_or_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6.8: a token és a CRN a hibaüzenetből sem a táblába, sem a naplóba, sem a jelentésbe."""
    monkeypatch.setenv("IBM_QUANTUM_TOKEN", TOKEN)

    def leaks(config: Any, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"hitelesítési hiba: token={TOKEN} instance={CRN}")

    monkeypatch.setattr(batch_run, "run_vqe", leaks)
    spec = BatchSpec(
        batch_id="p6-secret",
        description="titok",
        cells=(BatchCell(h2(), "qiskit_statevector", FAST),),
    )
    export = tmp_path / "export.json"
    result = run_pipeline(
        spec=spec,
        db_path=tmp_path / "db.sqlite",
        export_path=export,
        log_dir=tmp_path / "logs",
        sleep=lambda _s: None,
    )
    assert result.exit_code == EXIT_PARTIAL and result.report is not None

    with Database(tmp_path / "db.sqlite") as db:
        stored = " ".join(f["error_message"] for f in db.failures())
    surfaces = {
        "adatbázis": stored,
        "napló": result.log_path.read_text(encoding="utf-8"),
        "jelentés": " ".join(message for _r, message in result.report.failed),
        "export": export.read_text(encoding="utf-8"),
        "üzenet": result.message,
    }
    for name, text in surfaces.items():
        assert TOKEN not in text, name
        assert "crn:v1" not in text, name
    assert "RuntimeError" in stored  # a hiba típusa megmarad, csak a titok tűnik el
