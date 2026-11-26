"""Fázis 11 — a Heron-modell segédfüggvényei és a blokkfuttató védelmei (hálózat és kvóta nélkül).

A blokkfuttató (``scripts/run_heron_blocks.py``) kvótakapuját, a protokoll-befagyasztást és a
blokkterv költségvetését teszteli; az IBM-szolgáltatás mockolt, beküldés nem történik.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator

from vqebd.hardware import (
    HardwareNotAllowedError,
    QuotaExhaustedError,
    assert_block_within_budget,
)
from vqebd.heron_model import (
    PROTOCOL,
    calibration_snapshot,
    model_samples,
    model_seeds,
    protocol_fingerprint,
)

pytestmark = pytest.mark.unit


# --- védőkorlát: a használat nem lépheti át a 80%-ot -----------------------------------------


def _usage(consumed: float, limit: float = 600.0) -> dict[str, Any]:
    return {"usage_consumed_seconds": consumed, "usage_limit_seconds": limit}


def test_block_budget_allows_up_to_exactly_eighty_percent() -> None:
    assert_block_within_budget(_usage(445.0), 35.0)  # pontosan 480 s


def test_block_budget_refuses_when_the_projection_exceeds_eighty_percent() -> None:
    with pytest.raises(QuotaExhaustedError, match="80%"):
        assert_block_within_budget(_usage(446.0), 35.0)


def test_block_budget_refuses_when_usage_is_unknown() -> None:
    with pytest.raises(QuotaExhaustedError, match="nem ismert"):
        assert_block_within_budget({}, 10.0)
    with pytest.raises(ValueError, match="max_used_fraction"):
        assert_block_within_budget(_usage(0.0), 1.0, max_used_fraction=1.5)


# --- protokoll és seedek ----------------------------------------------------------------------


def test_protocol_fingerprint_is_stable_and_detects_any_change() -> None:
    assert protocol_fingerprint() == protocol_fingerprint(dict(PROTOCOL))
    changed = {**PROTOCOL, "delta_mha": 1.6}
    assert protocol_fingerprint(changed) != protocol_fingerprint()
    assert len(protocol_fingerprint()) == 64


def test_protocol_matches_the_approved_plan() -> None:
    """A szerző jóváhagyta: δ = 3,0 mHa; {0,735; 1,5; 2,0} Å; 8 megerősítő blokk; 80%."""
    assert PROTOCOL["delta_mha"] == 3.0
    assert PROTOCOL["block_bonds"] == [0.735, 1.5, 2.0]
    assert PROTOCOL["confirmatory_blocks"] == 8
    assert PROTOCOL["max_used_fraction"] == 0.80
    assert PROTOCOL["physical_qubits"] == [1, 2]  # előre rögzítve, az 5.H párja


def test_build_simulator_really_toggles_the_readout_error() -> None:
    """Regresszió: az ``AerSimulator.from_backend(readout_error=False)`` a kulcsszót elnyeli."""
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2

    from vqebd.heron_model import build_simulator

    backend = FakeManilaV2()
    with_readout = build_simulator(backend, readout=True).options.noise_model
    without = build_simulator(backend, readout=False).options.noise_model
    assert "measure" in with_readout.noise_instructions
    assert "measure" not in without.noise_instructions


def test_model_seeds_are_distinct_and_deterministic() -> None:
    seeds = model_seeds(20260922, 10)
    assert len(set(seeds)) == 10
    assert seeds == model_seeds(20260922, 10)
    assert seeds != model_seeds(20260923, 10)
    with pytest.raises(ValueError):
        model_seeds(1, 0)


def test_model_samples_use_a_different_shot_noise_per_seed() -> None:
    """A v0.7.1-es hiba ellenőrzése: ismétlésenként más lövészaj, azonos seed → azonos érték."""
    theta = Parameter("t")
    circuit = QuantumCircuit(1)
    circuit.ry(theta, 0)
    obs = SparsePauliOp("Z")
    sim = AerSimulator()
    values = model_samples(circuit, obs, [0.7], sim, shots=512, seeds=model_seeds(5, 6))
    assert len(set(values)) > 1
    again = model_samples(circuit, obs, [0.7], sim, shots=512, seeds=model_seeds(5, 6))
    assert values == again
    with pytest.raises(ValueError, match="shots"):
        model_samples(circuit, obs, [0.7], sim, shots=0, seeds=[1])


def test_calibration_snapshot_reads_only_the_used_qubits() -> None:
    gates = [
        SimpleNamespace(gate="cz", qubits=[1, 2]),
        SimpleNamespace(gate="cz", qubits=[2, 1]),
        SimpleNamespace(gate="cz", qubits=[7, 8]),
        SimpleNamespace(gate="sx", qubits=[1]),
    ]
    props = SimpleNamespace(
        last_update_date=dt.datetime(2026, 11, 2, 14, 46, tzinfo=dt.UTC),
        gates=gates,
        t1=lambda q: 3e-4 + q * 1e-6,
        t2=lambda q: 6e-4,
        readout_error=lambda q: 0.01,
        gate_error=lambda g, q: 1e-3 if g != "cz" else 2e-3,
    )
    backend = SimpleNamespace(name="ibm_test", properties=lambda: props)
    snap = calibration_snapshot(backend, [2, 1, 2])
    assert snap["physical_qubits"] == [1, 2]
    assert set(snap["qubits"]) == {"1", "2"}
    assert set(snap["cz_errors"]) == {"1-2", "2-1"}
    assert snap["last_update_date"].startswith("2026-11-02T14:46")
    assert snap["backend"] == "ibm_test"
    json.dumps(snap)  # JSON-szerializálható


# --- a blokkfuttató szkript (repó-checkoutból) --------------------------------------------------


@pytest.fixture
def runner(repo_root: Path) -> ModuleType:
    path = repo_root / "scripts" / "run_heron_blocks.py"
    if not path.is_file():
        pytest.skip("scripts/ nincs a szállított image-ben")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("run_heron_blocks_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_block_costs_follow_the_measured_per_pub_rates(runner: ModuleType) -> None:
    assert runner.estimated_qpu_seconds(5) == pytest.approx(57.0)
    assert runner.estimated_qpu_seconds(3) == pytest.approx(34.2)
    assert runner.block_bonds("B0") == (0.5, 0.735, 1.0, 1.5, 2.0)
    assert runner.block_bonds("C3") == (0.735, 1.5, 2.0)


def test_the_whole_schedule_stays_below_eighty_percent_even_with_the_gate_safety(
    runner: ModuleType,
) -> None:
    """A 57 s meglévő használattal, minden blokk előtt az 1,25-ös biztonsági szorzós kapuval."""
    consumed = 57.0
    for block in ["B0", *[f"C{i}" for i in range(1, 9)]]:
        bonds = runner.block_bonds(block)
        gate = runner.estimated_qpu_seconds(len(bonds), safety=PROTOCOL["gate_safety_factor"])
        assert_block_within_budget(_usage(consumed), gate)
        consumed += runner.estimated_qpu_seconds(len(bonds))
    assert consumed <= 0.8 * 600.0
    assert 600.0 - consumed >= 0.2 * 600.0


def test_level_order_alternates_between_blocks(runner: ModuleType) -> None:
    orders = {b: runner.level_order(b) for b in ("B0", "C1", "C2", "C3")}
    assert orders["B0"] == [0, 1] and orders["C1"] == [1, 0]
    assert orders["C2"] == [0, 1] and orders["C3"] == [1, 0]


def test_submission_is_refused_without_a_frozen_protocol(
    runner: ModuleType, tmp_path: Path
) -> None:
    with pytest.raises(RuntimeError, match="nincs befagyasztva"):
        runner.check_frozen(tmp_path)
    (tmp_path / "FROZEN").write_text("0" * 64 + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="módosult"):
        runner.check_frozen(tmp_path)
    (tmp_path / "FROZEN").write_text(protocol_fingerprint() + " abc123\n", encoding="utf-8")
    runner.check_frozen(tmp_path)  # egyezik: nem dob


def test_a_confirmatory_block_needs_the_pilot_layout(runner: ModuleType, tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="pilot"):
        runner.pilot_layout(tmp_path)
    (tmp_path / "b0.json").write_text(json.dumps({"physical_qubits": [1, 2]}), encoding="utf-8")
    assert runner.pilot_layout(tmp_path) == [1, 2]


class _FakeService:
    def __init__(self, consumed: float) -> None:
        self._consumed = consumed

    def usage(self) -> dict[str, Any]:
        return _usage(self._consumed)


def _stub_runner(runner: ModuleType, monkeypatch: pytest.MonkeyPatch, consumed: float) -> None:
    monkeypatch.setattr(runner, "connect_service", lambda: _FakeService(consumed))
    monkeypatch.setattr(
        runner.prep, "prepare", lambda bonds, seed: {"points": [], "circuit": None, "seeds": None}
    )

    def _no_evaluator(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a kvótakapu előtt/helyett nem jöhet létre kiértékelő")

    monkeypatch.setattr(runner, "IBMQpuEnergyEvaluator", _no_evaluator)


def test_runner_refuses_a_block_that_would_cross_the_limit(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_runner(runner, monkeypatch, consumed=470.0)
    code = runner.main(["--block", "B0", "--dry-run", "--data-dir", str(tmp_path)])
    assert code == 2


def test_runner_refuses_real_submission_without_permission(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_runner(runner, monkeypatch, consumed=57.0)
    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    with pytest.raises(HardwareNotAllowedError):
        runner.main(["--block", "B0", "--data-dir", str(tmp_path)])


def test_runner_refuses_real_submission_without_a_frozen_protocol(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_runner(runner, monkeypatch, consumed=57.0)
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    with pytest.raises(RuntimeError, match="nincs befagyasztva"):
        runner.main(["--block", "B0", "--data-dir", str(tmp_path)])


@pytest.mark.parametrize("name", ["C10", "C0", "B1", "X1", "c9"])
def test_runner_rejects_an_unknown_block_name(runner: ModuleType, name: str) -> None:
    with pytest.raises(SystemExit):
        runner.main(["--block", name, "--dry-run"])


# --- a kiegészítő C9 blokk (phase_11.md, 2026-11-18) ----------------------------------------------


def test_c9_is_a_supplementary_block_with_trex_first(runner: ModuleType) -> None:
    assert runner.BLOCK_RE.match("C9")
    assert runner.block_kind("C9") == "supplementary"
    assert runner.block_kind("C8") == "confirmatory" and runner.block_kind("B0") == "pilot"
    assert runner.block_bonds("C9") == runner.block_bonds("C8")
    assert runner.level_order("C9") == [1, 0]  # páratlan: TREX először
    assert runner.level_order("C8") == [0, 1]
    assert PROTOCOL["confirmatory_blocks"] == 8  # a PROTOCOL nem változott


def test_c9_needs_the_complete_confirmatory_series(runner: ModuleType, tmp_path: Path) -> None:
    for i in range(1, 8):
        (tmp_path / f"c{i}.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="C8"):
        runner.check_confirmatory_complete(tmp_path)
    (tmp_path / "c8.json").write_text("{}", encoding="utf-8")
    runner.check_confirmatory_complete(tmp_path)  # teljes: nem dob


def test_runner_refuses_c9_before_the_confirmatory_series_is_complete(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stub_runner(runner, monkeypatch, consumed=426.0)
    with pytest.raises(RuntimeError, match="nem teljes"):
        runner.main(["--block", "C9", "--dry-run", "--data-dir", str(tmp_path)])


def test_c9_fits_the_eighty_percent_rule_after_the_measured_c1_to_c8(runner: ModuleType) -> None:
    """A tényleges 426 s után (C8 vége) a C9 kapuja 426 + 42,75 = 468,75 s ≤ 480 s."""
    bonds = runner.block_bonds("C9")
    gate = runner.estimated_qpu_seconds(len(bonds), safety=PROTOCOL["gate_safety_factor"])
    assert_block_within_budget(_usage(426.0), gate)
    assert 600.0 - (426.0 + 39.0) >= 0.2 * 600.0


class _MetricsService:
    """Hamis szolgáltatás: a ``metrics()`` hívások egymás után a megadott állapotokat adják."""

    def __init__(self, sequence: list[dict[str, Any]]) -> None:
        self._sequence = list(sequence)
        self.calls = 0

    def job(self, job_id: str) -> SimpleNamespace:
        def metrics() -> dict[str, Any]:
            index = min(self.calls, len(self._sequence) - 1)
            self.calls += 1
            return self._sequence[index]

        return SimpleNamespace(metrics=metrics)


def test_final_metrics_waits_for_the_completed_usage(runner: ModuleType) -> None:
    """A C8 TREX jobjánál a befejezéskor még 0 QPU-s állt; a futtató várja meg a véglegeset."""
    service = _MetricsService(
        [
            {"usage": {"quantum_seconds": 0, "seconds": 0}},
            {"usage": {"quantum_seconds": 0, "seconds": 0, "status": "pending"}},
            {"usage": {"quantum_seconds": 24, "seconds": 24, "status": "complete"}},
        ]
    )
    waits: list[float] = []
    metrics, final = runner.final_metrics(service, "job", wait_s=0.5, sleep=waits.append)
    assert final is True and metrics["usage"]["quantum_seconds"] == 24
    assert service.calls == 3 and waits == [0.5, 0.5]


def test_final_metrics_accepts_a_positive_usage_without_status(runner: ModuleType) -> None:
    service = _MetricsService([{"usage": {"quantum_seconds": 15}}])
    metrics, final = runner.final_metrics(service, "job", sleep=lambda _: None)
    assert final is True and metrics["usage"]["quantum_seconds"] == 15 and service.calls == 1


def test_final_metrics_gives_up_and_flags_a_non_final_usage(runner: ModuleType) -> None:
    service = _MetricsService([{"usage": {"quantum_seconds": 0}}])
    waits: list[float] = []
    metrics, final = runner.final_metrics(service, "job", attempts=4, sleep=waits.append)
    assert final is False and metrics["usage"]["quantum_seconds"] == 0
    assert service.calls == 4 and len(waits) == 3


def test_final_metrics_does_not_accept_a_complete_but_zero_usage(runner: ModuleType) -> None:
    """A ``status: complete`` 0 másodperccel nem végleges (a C8 TREX jobjának hibája)."""
    service = _MetricsService(
        [
            {"usage": {"quantum_seconds": 0, "seconds": 0, "status": "complete"}},
            {"usage": {"quantum_seconds": 24, "seconds": 24, "status": "complete"}},
        ]
    )
    metrics, final = runner.final_metrics(service, "job", sleep=lambda _: None)
    assert final is True and metrics["usage"]["quantum_seconds"] == 24 and service.calls == 2


class _BrokenService:
    def job(self, job_id: str) -> Any:
        raise RuntimeError("az API nem elérhető")


def test_metrics_errors_and_null_usage_are_not_fatal(runner: ModuleType) -> None:
    assert runner.read_metrics(_BrokenService(), "job") == {}
    metrics, final = runner.final_metrics(_BrokenService(), "job", attempts=3, sleep=lambda _: None)
    assert metrics == {} and final is False
    null_usage: dict[str, Any] = {"usage": None, "timestamps": None}
    assert runner.usage_seconds(null_usage) is None
    assert runner.usage_is_final(null_usage) is False


def test_a_measured_block_is_never_overwritten(runner: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "c8.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="már létezik"):
        runner.check_not_measured(tmp_path / "c8.json")
    runner.check_not_measured(tmp_path / "c9.json")  # még nem létezik: nem dob


# --- a beküldési út hamis szolgáltatással (hálózat és QPU nélkül) ---------------------------------


class _FakeJobService:
    """Hamis IBM-szolgáltatás: kvóta és jobonkénti metrika-sorozat (kivétel is lehet benne)."""

    def __init__(self, metrics_by_job: dict[str, list[Any]], *, consumed: float = 426.0) -> None:
        self.metrics_by_job = metrics_by_job
        self.calls = dict.fromkeys(metrics_by_job, 0)
        self.consumed = consumed
        self.usage_calls = 0
        self.fail_usage_after: int | None = None

    def usage(self) -> dict[str, Any]:
        self.usage_calls += 1
        if self.fail_usage_after is not None and self.usage_calls > self.fail_usage_after:
            raise RuntimeError("a kvóta nem olvasható")
        return _usage(self.consumed)

    def job(self, job_id: str) -> SimpleNamespace:
        sequence = self.metrics_by_job[job_id]

        def metrics() -> dict[str, Any]:
            item = sequence[min(self.calls[job_id], len(sequence) - 1)]
            self.calls[job_id] += 1
            if isinstance(item, Exception):
                raise item
            return dict(item)

        return SimpleNamespace(metrics=metrics)


def _prepared(bonds: tuple[float, ...], seed: int) -> dict[str, Any]:
    points = [
        {
            "bond_length": b,
            "observable": object(),
            "theta_star": [0.1],
            "energy_offset_ha": 0.5,
            "full_ci_ha": -1.0,
        }
        for b in bonds
    ]
    return {"points": points, "circuit": None, "seeds": None}


def _stub_submission(
    runner: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    data_dir: Path,
    service: _FakeJobService,
    log: list[tuple[int, dict[str, int]]],
    *,
    snapshot_fails_after: int | None = None,
    fail_level: int | None = None,
) -> None:
    snapshots = {"n": 0}

    def snapshot(backend: Any, qubits: Any) -> dict[str, Any]:
        snapshots["n"] += 1
        if snapshot_fails_after is not None and snapshots["n"] > snapshot_fails_after:
            raise RuntimeError("a kalibráció nem olvasható")
        return {"last_update_date": "2026-11-26T07:25:12+00:00", "qubits": {}, "cz_errors": {}}

    class FakeEvaluator:
        def __init__(self, *args: Any, resilience_level: int, initial_layout: Any, **kw: Any):
            self.level = resilience_level
            self.physical_qubits = sorted(int(q) for q in initial_layout)
            self.backend = SimpleNamespace(name=kw["backend_name"])
            self.last_job_id: str | None = None

        def evaluate_observables(self, observables: Any, thetas: Any) -> list[dict[str, float]]:
            log.append((self.level, dict(service.calls)))
            if self.level == fail_level:
                raise RuntimeError("a job megszakadt")
            self.last_job_id = f"job-{self.level}"
            return [
                {"evs": -1.47, "stds": 0.003, "ensemble_standard_error": 0.003} for _ in observables
            ]

    monkeypatch.setattr(runner, "connect_service", lambda: service)
    monkeypatch.setattr(runner.prep, "prepare", _prepared)
    monkeypatch.setattr(runner, "calibration_snapshot", snapshot)
    monkeypatch.setattr(
        runner,
        "model_predictions",
        lambda *a, **k: {"readout": {"0.735": 24.0}, "no_readout": {"0.735": 7.0}},
    )
    monkeypatch.setattr(runner, "IBMQpuEnergyEvaluator", FakeEvaluator)
    monkeypatch.setattr(runner.time, "sleep", lambda _s: None)
    monkeypatch.setenv("VQEBD_ALLOW_HARDWARE", "true")
    (data_dir / "FROZEN").write_text(protocol_fingerprint() + "\n", encoding="utf-8")
    (data_dir / "b0.json").write_text(json.dumps({"physical_qubits": [1, 2]}), encoding="utf-8")
    for i in range(1, 9):
        (data_dir / f"c{i}.json").write_text("{}", encoding="utf-8")


_RUN = {"running": "2026-11-26T08:00:01Z", "created": "2026-11-26T08:00:00Z"}


def test_c9_submission_keeps_the_c1_c8_rhythm_and_records_the_final_usage(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _FakeJobService(
        {
            "job-1": [  # TREX: a befejezéskor még 0 s (mint a C8-nál), később 24 s
                {"usage": {"quantum_seconds": 0, "status": "complete"}, "timestamps": _RUN},
                {"usage": {"quantum_seconds": 24, "status": "complete"}, "timestamps": _RUN},
            ],
            "job-0": [{"usage": {"quantum_seconds": 15, "status": "complete"}, "timestamps": _RUN}],
        }
    )
    log: list[tuple[int, dict[str, int]]] = []
    _stub_submission(runner, monkeypatch, tmp_path, service, log)
    assert runner.main(["--block", "C9", "--data-dir", str(tmp_path)]) == 0

    assert [level for level, _ in log] == [1, 0]  # TREX először
    assert log[1][1]["job-1"] == 1  # a két job között pontosan egy metrika-olvasás
    saved = json.loads((tmp_path / "c9.json").read_text(encoding="utf-8"))
    assert saved["block"] == "C9" and saved["kind"] == "supplementary"
    assert saved["protocol_fingerprint"] == protocol_fingerprint()
    trex, raw = saved["runs"]
    assert trex["resilience_level"] == 1 and raw["resilience_level"] == 0
    assert trex["quantum_seconds"] == 24 and trex["quantum_seconds_initial"] == 0
    assert trex["usage_final"] is True and raw["usage_final"] is True
    assert raw["quantum_seconds"] == 15 and "quantum_seconds_initial" not in raw
    assert set(saved["hardware_mha"]) == {"raw", "trex"}

    assert not (tmp_path / "c9.partial.json").exists()  # a részleges mentés törölve
    assert not (tmp_path / ".c9.json.tmp").exists()  # az atomi írás nem hagy szemetet

    # második indítás (pl. elírt blokknév): felülírás megtagadva, új job nem indul
    with pytest.raises(RuntimeError, match="már létezik"):
        runner.main(["--block", "C9", "--data-dir", str(tmp_path)])
    assert len(log) == 2


def test_the_measured_data_are_saved_even_if_every_follow_up_query_fails(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broken = RuntimeError("az API nem elérhető")
    service = _FakeJobService({"job-1": [broken], "job-0": [broken]})
    service.fail_usage_after = 1  # a blokk előtti kvóta még olvasható, utána nem
    log: list[tuple[int, dict[str, int]]] = []
    _stub_submission(runner, monkeypatch, tmp_path, service, log, snapshot_fails_after=1)
    assert runner.main(["--block", "C9", "--data-dir", str(tmp_path)]) == 0
    saved = json.loads((tmp_path / "c9.json").read_text(encoding="utf-8"))
    assert [r["job_id"] for r in saved["runs"]] == ["job-1", "job-0"]
    assert all(r["usage_final"] is False and r["quantum_seconds"] is None for r in saved["runs"])
    assert saved["quota_after"] is None and saved["calibration_after"] is None
    assert saved["hardware_mha"]["trex"] and saved["hardware_mha"]["raw"]


def test_c9_dry_run_passes_the_gates_without_submitting(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _FakeJobService({})
    log: list[tuple[int, dict[str, int]]] = []
    _stub_submission(runner, monkeypatch, tmp_path, service, log)
    monkeypatch.delenv("VQEBD_ALLOW_HARDWARE", raising=False)
    assert runner.main(["--block", "C9", "--dry-run", "--data-dir", str(tmp_path)]) == 0
    assert log == [] and not (tmp_path / "c9.json").exists()


def test_the_first_job_survives_on_disk_if_the_second_job_fails(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _FakeJobService(
        {"job-1": [{"usage": {"quantum_seconds": 24, "status": "complete"}, "timestamps": _RUN}]}
    )
    log: list[tuple[int, dict[str, int]]] = []
    _stub_submission(runner, monkeypatch, tmp_path, service, log, fail_level=0)
    with pytest.raises(RuntimeError, match="megszakadt"):
        runner.main(["--block", "C9", "--data-dir", str(tmp_path)])
    assert not (tmp_path / "c9.json").exists()
    partial = json.loads((tmp_path / "c9.partial.json").read_text(encoding="utf-8"))
    assert partial["partial"] is True and partial["kind"] == "supplementary"
    assert [r["job_id"] for r in partial["runs"]] == ["job-1"]
    assert partial["runs"][0]["points"]  # a TREX job energiái megvannak


def test_a_crash_while_finalizing_keeps_the_saved_block(
    runner: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _FakeJobService(
        {
            "job-1": [{"usage": {"quantum_seconds": 0}, "timestamps": _RUN}],
            "job-0": [{"usage": {"quantum_seconds": 15}, "timestamps": _RUN}],
        }
    )
    log: list[tuple[int, dict[str, int]]] = []
    _stub_submission(runner, monkeypatch, tmp_path, service, log)

    def explode(*args: Any, **kwargs: Any) -> bool:
        raise RuntimeError("váratlan hiba")

    monkeypatch.setattr(runner, "finalize_usage", explode)
    assert runner.main(["--block", "C9", "--data-dir", str(tmp_path)]) == 0
    saved = json.loads((tmp_path / "c9.json").read_text(encoding="utf-8"))
    assert saved["runs"][0]["usage_final"] is False and saved["runs"][1]["usage_final"] is True
    assert not (tmp_path / "c9.partial.json").exists()


def test_finalize_fills_a_missing_timestamp_even_if_the_usage_stays_non_final(
    runner: ModuleType,
) -> None:
    runs: list[dict[str, Any]] = [
        {"job_id": "j", "usage_final": False, "quantum_seconds": None, "timestamps": {}}
    ]
    service = _MetricsService(
        [{"usage": {"quantum_seconds": 0}, "timestamps": {"running": "2026-11-26T08:00:02Z"}}]
    )
    assert runner.finalize_usage(service, runs, attempts=2, sleep=lambda _: None) is True
    assert runs[0]["timestamps"]["running"] == "2026-11-26T08:00:02Z"
    assert runs[0]["usage_final"] is False and runs[0]["quantum_seconds"] is None
