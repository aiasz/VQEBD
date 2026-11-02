#!/usr/bin/env python3
"""Fázis 11 — egy hardveres blokk futtatása a gördülő 28 napos ingyenes keretbe darabolva.

Egy blokk = két job (nyers és TREX), azonos ISA-áramkörrel és **fix fizikai qubitpárral**, a
blokk elején és végén kalibrációs pillanatképpel, valamint a Heron-zajmodell előrejelzésével
(kiolvasási hibával és anélkül). A tervet és a szabályokat a ``docs/plan/phase_11.md`` rögzíti.

Védőkorlátok (a ``vqebd.hardware`` meglévő K7-védelme fölött):

- beküldés csak ``VQEBD_ALLOW_HARDWARE=true`` mellett;
- a befagyasztott protokoll ujjlenyomata egyezzen a ``docs/figures/data/f11/FROZEN`` fájllal;
- **az élő ``usage()`` alapján a blokk után sem lehet a használat a keret 80%-a fölött**;
- megerősítő blokk csak a pilot (B0) fix qubitpárjával fut;
- ``--dry-run``: a klasszikus számítás, a modell-előrejelzés és a kapu lefut, **beküldés nincs**.

A modul sehol nem ütemez automatikusan (ADR-0008): minden blokkot a szerző indít.

Használat::

    python scripts/run_heron_blocks.py --block B0 --dry-run
    VQEBD_ALLOW_HARDWARE=true python scripts/run_heron_blocks.py --block C1

Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_hardware_pes as prep
from vqebd import __version__
from vqebd.backends.estimators import IBMQpuEnergyEvaluator
from vqebd.hardware import (
    QuotaExhaustedError,
    assert_block_within_budget,
    assert_hardware_allowed,
    connect_service,
    quota_summary,
)
from vqebd.heron_model import (
    BLOCK_BONDS,
    PILOT_BONDS,
    PROTOCOL,
    build_simulator,
    calibration_snapshot,
    model_samples,
    model_seeds,
    protocol_fingerprint,
)

DATA_DIR = Path("docs/figures/data/f11")
BLOCK_RE = re.compile(r"^(B0|C[1-8])$")


def block_kind(block: str) -> str:
    return "pilot" if block == "B0" else "confirmatory"


def block_bonds(block: str) -> tuple[float, ...]:
    return PILOT_BONDS if block == "B0" else BLOCK_BONDS


def estimated_qpu_seconds(n_bonds: int, *, safety: float = 1.0) -> float:
    """A blokk becsült QPU-igénye: geometriánként egy nyers és egy TREX PUB."""
    per_pub = PROTOCOL["per_pub_seconds"]
    return n_bonds * (per_pub["raw"] + per_pub["trex"]) * safety


def level_order(block: str) -> list[int]:
    """A nyers/TREX sorrend blokkonként váltakozik (az idő hatása ne egy feltételhez tapadjon)."""
    index = 0 if block == "B0" else int(block[1:])
    return [0, 1] if index % 2 == 0 else [1, 0]


def check_frozen(data_dir: Path) -> None:
    """Megtagadja a beküldést, ha a protokoll nincs befagyasztva vagy utólag módosult."""
    frozen = data_dir / "FROZEN"
    if not frozen.is_file():
        raise RuntimeError(
            f"a protokoll nincs befagyasztva ({frozen} hiányzik) — beküldés megtagadva"
        )
    recorded = frozen.read_text(encoding="utf-8").split()[0]
    if recorded != protocol_fingerprint():
        raise RuntimeError(
            "a protokoll módosult a befagyasztás óta (ujjlenyomat-eltérés) — új protokoll kell, "
            "beküldés megtagadva"
        )


def pilot_layout(data_dir: Path) -> list[int]:
    """A pilot (B0) mentett fizikai qubitpárja; nélküle megerősítő blokk nem indítható."""
    pilot = data_dir / "b0.json"
    if not pilot.is_file():
        raise RuntimeError(f"a pilot ({pilot}) még nem futott — megerősítő blokk nem indítható")
    qubits = json.loads(pilot.read_text(encoding="utf-8"))["physical_qubits"]
    return [int(q) for q in qubits]


def model_predictions(
    evaluator: IBMQpuEnergyEvaluator, prepared: dict[str, Any], shots: int, repeats: int, seed: int
) -> dict[str, dict[str, float]]:
    """A modell átlagos hibája (mHa, a Full CI-hez) geometriánként, kiolvasással és anélkül."""
    import numpy as np

    isa = evaluator.isa_circuit
    seeds = model_seeds(seed, repeats)
    out: dict[str, dict[str, float]] = {"readout": {}, "no_readout": {}}
    for label, readout in (("readout", True), ("no_readout", False)):
        simulator = build_simulator(evaluator.backend, readout=readout)
        for point in prepared["points"]:
            obs = point["observable"].apply_layout(isa.layout)
            samples = model_samples(
                isa, obs, point["theta_star"], simulator, shots=shots, seeds=seeds
            )
            errors = [(e + point["energy_offset_ha"] - point["full_ci_ha"]) * 1e3 for e in samples]
            out[label][str(point["bond_length"])] = float(np.mean(errors))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fázis 11 — egy hardveres blokk")
    parser.add_argument("--block", required=True, help="B0 (pilot) vagy C1…C8")
    parser.add_argument("--backend", default=PROTOCOL["backend"])
    parser.add_argument("--shots", type=int, default=PROTOCOL["shots"])
    parser.add_argument("--seed", type=int, default=PROTOCOL["seed"])
    parser.add_argument("--model-repeats", type=int, default=PROTOCOL["model_repeats"])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--dry-run", action="store_true", help="beküldés nélkül")
    args = parser.parse_args(argv)

    if not BLOCK_RE.match(args.block):
        parser.error("a blokk B0 vagy C1…C8 lehet")
    bonds = block_bonds(args.block)
    kind = block_kind(args.block)
    required = estimated_qpu_seconds(len(bonds))
    gate_required = estimated_qpu_seconds(len(bonds), safety=PROTOCOL["gate_safety_factor"])
    print(f"Blokk {args.block} ({kind}): {len(bonds)} geometria × (nyers + TREX), R = {bonds} Å")
    print(f"Becsült QPU-igény: {required:.1f} s (a kapu {gate_required:.1f} s-mal számol)")

    layout = [int(q) for q in PROTOCOL["physical_qubits"]]
    if args.block != "B0" and pilot_layout(args.data_dir) != layout:
        raise RuntimeError(
            "a pilot qubitpárja eltér a protokollban rögzítettől — új protokoll kell"
        )
    prepared = prep.prepare(bonds, args.seed)

    # kvótakapu az ÉLŐ használat alapján — beküldés nélkül is lefut
    service = connect_service()
    usage = quota_summary(service.usage())
    print(f"Kvóta: {json.dumps(usage, default=str)}")
    try:
        assert_block_within_budget(
            usage, gate_required, max_used_fraction=PROTOCOL["max_used_fraction"]
        )
    except QuotaExhaustedError as exc:
        print(f"MEGTAGADVA: {exc}", file=sys.stderr)
        return 2
    if not args.dry_run:
        assert_hardware_allowed()
        check_frozen(args.data_dir)

    def make(level: int) -> IBMQpuEnergyEvaluator:
        return IBMQpuEnergyEvaluator(
            prepared["circuit"],
            prepared["points"][0]["observable"],
            prepared["seeds"],
            backend_name=args.backend,
            shots=args.shots,
            resilience_level=level,
            initial_layout=layout,
        )

    evaluators = {level: make(level) for level in level_order(args.block)}
    first = next(iter(evaluators.values()))
    qubits = first.physical_qubits
    print(f"Fizikai qubitek: {qubits} (a protokollban előre rögzítve)")
    if qubits != sorted(layout):
        raise RuntimeError(f"a transzpilálás eltért a rögzített qubitpártól: {qubits} ≠ {layout}")

    snapshot_before = calibration_snapshot(first.backend, qubits)
    print(f"Kalibráció: {snapshot_before['last_update_date']}")
    print("Modell-előrejelzés (kvóta nélkül)…")
    model = model_predictions(first, prepared, args.shots, args.model_repeats, args.seed)
    for label, vals in model.items():
        print(f"  modell ({label}): " + ", ".join(f"{g}: {v:+.2f}" for g, v in vals.items()))
    if args.dry_run:
        print("Dry run: a kapu elengedi, beküldés nem történt.")
        return 0

    runs: list[dict[str, Any]] = []
    hardware: dict[str, dict[str, float]] = {"raw": {}, "trex": {}}
    for level, evaluator in evaluators.items():
        started = time.perf_counter()
        results = evaluator.evaluate_observables(
            [p["observable"] for p in prepared["points"]],
            [p["theta_star"] for p in prepared["points"]],
        )
        job_id = evaluator.last_job_id
        metrics = service.job(job_id).metrics()
        label = "raw" if level == 0 else "trex"
        for p, r in zip(prepared["points"], results, strict=True):
            error = (r["evs"] + p["energy_offset_ha"] - p["full_ci_ha"]) * 1e3
            hardware[label][str(p["bond_length"])] = float(error)
        runs.append(
            {
                "resilience_level": level,
                "job_id": job_id,
                "wall_time_s": time.perf_counter() - started,
                "quantum_seconds": metrics.get("usage", {}).get("quantum_seconds"),
                "timestamps": metrics.get("timestamps", {}),
                "points": [
                    {
                        "bond_length": p["bond_length"],
                        "energy_ha": r["evs"] + p["energy_offset_ha"],
                        "stds_ha": r["stds"],
                        "ensemble_standard_error_ha": r["ensemble_standard_error"],
                    }
                    for p, r in zip(prepared["points"], results, strict=True)
                ],
            }
        )
        print(f"  szint {level}: job {job_id}, {runs[-1]['quantum_seconds']} QPU-s")

    snapshot_after = calibration_snapshot(first.backend, qubits)
    payload = {
        "block": args.block,
        "kind": kind,
        "vqebd_version": __version__,
        "protocol_fingerprint": protocol_fingerprint(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": args.backend,
        "shots": args.shots,
        "physical_qubits": qubits,
        "quota_before": usage,
        "quota_after": quota_summary(service.usage()),
        "calibration_before": snapshot_before,
        "calibration_after": snapshot_after,
        "hardware_mha": hardware,
        "model_mha": model,
        "runs": runs,
    }
    out = args.data_dir / f"{args.block.lower()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    print(f"Mentve: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
