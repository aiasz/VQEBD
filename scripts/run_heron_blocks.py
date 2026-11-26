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
- a kiegészítő C9 (``supplementary``, rögzítve 2026-11-18-án) csak a teljes megerősítő sorozat
  (C1…C8) után indítható; az elsődleges elemzésbe nem számít bele;
- már lefutott blokk kimenete (``cN.json``) nem írható felül;
- a mért adat a blokk végén **azonnal** mentésre kerül; a végleges QPU-használat utólagos
  lekérdezése ezután, hibatűrően történik (a két job közti ütem a C1–C8-cal azonos);
- ``--dry-run``: a klasszikus számítás, a modell-előrejelzés és a kapu lefut, **beküldés nincs**.

A modul sehol nem ütemez automatikusan (ADR-0008): minden blokkot a szerző indít.

Használat::

    python scripts/run_heron_blocks.py --block B0 --dry-run
    VQEBD_ALLOW_HARDWARE=true python scripts/run_heron_blocks.py --block C1
    python scripts/run_heron_blocks.py --block C9 --dry-run      # kiegészítő blokk

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
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
BLOCK_RE = re.compile(r"^(B0|C[1-9])$")
SUPPLEMENTARY_BLOCKS = ("C9",)
"""Kiegészítő blokkok (``phase_11.md``, 2026-11-18); a ``PROTOCOL``/ujjlenyomat nem változik."""


def block_kind(block: str) -> str:
    if block == "B0":
        return "pilot"
    return "supplementary" if block in SUPPLEMENTARY_BLOCKS else "confirmatory"


def check_confirmatory_complete(data_dir: Path) -> None:
    """Kiegészítő blokk csak a teljes megerősítő sorozat (C1…C8) mentett kimenete után indulhat."""
    expected = int(PROTOCOL["confirmatory_blocks"])
    missing = [f"C{i}" for i in range(1, expected + 1) if not (data_dir / f"c{i}.json").is_file()]
    if missing:
        raise RuntimeError(
            f"a megerősítő sorozat nem teljes (hiányzik: {', '.join(missing)}) — "
            "kiegészítő blokk nem indítható"
        )


def check_protocol_arguments(args: argparse.Namespace) -> None:
    """Valódi futtatás csak a befagyasztott protokoll értékeivel (kapcsolóval nem írható felül)."""
    expected = {
        "backend": PROTOCOL["backend"],
        "shots": PROTOCOL["shots"],
        "seed": PROTOCOL["seed"],
        "model_repeats": PROTOCOL["model_repeats"],
    }
    differs = {k: getattr(args, k) for k, v in expected.items() if getattr(args, k) != v}
    if differs:
        raise RuntimeError(
            f"a(z) {differs} eltér a befagyasztott protokolltól ({expected}) — beküldés megtagadva"
        )


def check_no_partial(out: Path) -> None:
    """Megtagadja a futtatást, ha egy korábbi, megszakadt kísérlet részleges mentése megvan."""
    partial = partial_path(out)
    if partial.exists():
        raise RuntimeError(
            f"a(z) {partial} egy korábbi, megszakadt kísérlet részleges mentése — előbb őrizd meg "
            "(pl. cN_megszakadt_K.partial.json néven), utána indítható újra"
        )


def check_not_measured(out: Path) -> None:
    """Megtagadja a beküldést, ha a blokk kimenete már létezik (pl. elírt blokknév)."""
    if out.exists():
        raise RuntimeError(f"a(z) {out} már létezik — a blokk már lefutott, felülírás megtagadva")


def read_metrics(service: Any, job_id: str | None) -> dict[str, Any]:
    """Egyetlen, **hibatűrő** metrika-olvasás: hiba esetén üres szótár (a mért adat fontosabb)."""
    try:
        metrics = service.job(job_id).metrics()
    except Exception as exc:  # a metrika hiánya nem veszélyeztetheti a mentést
        print(f"  FIGYELEM: a(z) {job_id} metrikái nem olvashatók: {exc!r}", file=sys.stderr)
        return {}
    return metrics if isinstance(metrics, dict) else {}


def usage_seconds(metrics: dict[str, Any]) -> Any:
    """A metrikák ``usage.quantum_seconds`` értéke (``None``, ha hiányzik)."""
    return (metrics.get("usage") or {}).get("quantum_seconds")


def usage_is_final(metrics: dict[str, Any]) -> bool:
    """Végleges-e a használati adat: pozitív ``quantum_seconds``, és a ``status`` (ha van) kész.

    QPU-n lefutott job sosem 0 másodperces; a ``complete`` állapot önmagában nem elég (a C8 TREX
    jobjánál a mentéskor 0 QPU-s állt, a valós érték 24 s volt).
    """
    usage = metrics.get("usage") or {}
    return (usage.get("quantum_seconds") or 0) > 0 and usage.get("status") in (None, "complete")


def final_metrics(
    service: Any,
    job_id: str,
    *,
    attempts: int = 40,
    wait_s: float = 5.0,
    sleep: Any = None,
) -> tuple[dict[str, Any], bool]:
    """A job metrikái a **végleges** használati adattal (hibatűrő, ismételt olvasás).

    Visszaadja az utolsó metrikákat és azt, hogy véglegesek-e; a kísérletek elfogyása vagy
    olvasási hiba esetén ``False``-szal. Kivételt nem dob.
    """
    pause = sleep or time.sleep
    metrics: dict[str, Any] = {}
    for attempt in range(max(1, attempts)):
        metrics = read_metrics(service, job_id)
        if usage_is_final(metrics):
            return metrics, True
        if attempt < attempts - 1:
            pause(wait_s)
    return metrics, False


def finalize_usage(service: Any, runs: list[dict[str, Any]], **kwargs: Any) -> bool:
    """A mentett futások QPU-használatának véglegesítése (a mentés **után**, kivétel nélkül).

    A nem végleges futásoknál újra lekérdez; ha a végleges érték eltér, a mentéskori értéket
    ``quantum_seconds_initial`` néven megőrzi. Igaz, ha bármi változott.
    """
    changed = False
    for run in runs:
        if run.get("usage_final"):
            continue
        metrics, final = final_metrics(service, str(run["job_id"]), **kwargs)
        # az időbélyeg a végleges használattól függetlenül pótlandó (a kalibráció-életkorhoz kell)
        if not (run.get("timestamps") or {}).get("running") and metrics.get("timestamps"):
            run["timestamps"] = metrics["timestamps"]
            changed = True
        if final:
            if usage_seconds(metrics) != run.get("quantum_seconds"):
                run["quantum_seconds_initial"] = run.get("quantum_seconds")
                run["quantum_seconds"] = usage_seconds(metrics)
            run["usage_final"] = True
            changed = True
    return changed


def _optional(label: str, func: Any, *args: Any) -> Any:
    """Kiegészítő lekérdezés a mentés előtt: hiba esetén ``None`` (a mért adat nem veszhet el)."""
    try:
        return func(*args)
    except Exception as exc:
        print(f"  FIGYELEM: {label} nem olvasható: {exc!r}", file=sys.stderr)
        return None


def write_payload(out: Path, payload: dict[str, Any]) -> None:
    """Atomi írás: ideiglenes fájl, majd csere (megszakadáskor sem marad csonka fájl)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    tmp.replace(out)


def partial_path(out: Path) -> Path:
    """A részleges mentés helye (``c9.partial.json``: az elemzés és a rekonstrukció nem olvassa)."""
    return out.with_name(f"{out.stem}.partial.json")


def block_bonds(block: str) -> tuple[float, ...]:
    return PILOT_BONDS if block == "B0" else BLOCK_BONDS


def estimated_qpu_seconds(n_bonds: int, *, safety: float = 1.0) -> float:
    """A blokk becsült QPU-igénye: geometriánként egy nyers és egy TREX PUB."""
    per_pub = PROTOCOL["per_pub_seconds"]
    return float(n_bonds * (per_pub["raw"] + per_pub["trex"]) * safety)


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
    parser.add_argument(
        "--block", required=True, help="B0 (pilot), C1…C8 (megerősítő) vagy C9 (kiegészítő)"
    )
    parser.add_argument("--backend", default=PROTOCOL["backend"])
    parser.add_argument("--shots", type=int, default=PROTOCOL["shots"])
    parser.add_argument("--seed", type=int, default=PROTOCOL["seed"])
    parser.add_argument("--model-repeats", type=int, default=PROTOCOL["model_repeats"])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--dry-run", action="store_true", help="beküldés nélkül")
    args = parser.parse_args(argv)

    if not BLOCK_RE.match(args.block):
        parser.error("a blokk B0, C1…C8 vagy a kiegészítő C9 lehet")
    bonds = block_bonds(args.block)
    kind = block_kind(args.block)
    if kind == "supplementary":
        check_confirmatory_complete(args.data_dir)
    out = args.data_dir / f"{args.block.lower()}.json"
    if args.dry_run and out.exists():
        print(f"FIGYELEM: a(z) {out} már létezik — valódi futtatás felülírást nem engedne")
    if args.dry_run and partial_path(out).exists():
        print(f"FIGYELEM: a(z) {partial_path(out)} megvan — valódi futtatás előbb az őrzését kérné")
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
        check_protocol_arguments(args)
        check_not_measured(out)
        check_no_partial(out)

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
    for (
        level,
        evaluator,
    ) in evaluators.items():  # mindkét szint ugyanarra a párra, azonos áramkörrel
        if evaluator.physical_qubits != sorted(layout):
            raise RuntimeError(
                f"a(z) {level}. szint transzpilálása eltért a rögzített qubitpártól: "
                f"{evaluator.physical_qubits} ≠ {layout}"
            )
        if dict(evaluator.isa_circuit.count_ops()) != dict(first.isa_circuit.count_ops()):
            raise RuntimeError(f"a(z) {level}. szint ISA-áramköre eltér az elsőétől")

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
        metrics = read_metrics(service, job_id)  # egyetlen olvasás, mint a C1–C8-nál
        label = "raw" if level == 0 else "trex"
        for p, r in zip(prepared["points"], results, strict=True):
            error = (r["evs"] + p["energy_offset_ha"] - p["full_ci_ha"]) * 1e3
            hardware[label][str(p["bond_length"])] = float(error)
        runs.append(
            {
                "resilience_level": level,
                "job_id": job_id,
                "wall_time_s": time.perf_counter() - started,
                "quantum_seconds": usage_seconds(metrics),
                "usage_final": usage_is_final(metrics),
                "timestamps": metrics.get("timestamps") or {},
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
        note = "" if runs[-1]["usage_final"] else " (a használati adat még nem végleges)"
        print(f"  szint {level}: job {job_id}, {runs[-1]['quantum_seconds']} QPU-s{note}")
        try:  # részleges mentés: ha a következő job megszakad, ez a job nem vész el
            write_payload(
                partial_path(out),
                {"block": args.block, "kind": kind, "partial": True, "runs": runs},
            )
        except OSError as exc:
            print(f"  FIGYELEM: a részleges mentés nem sikerült: {exc!r}", file=sys.stderr)

    snapshot_after = _optional(
        "a blokk utáni kalibráció", calibration_snapshot, first.backend, qubits
    )
    raw_usage_after = _optional("a blokk utáni kvóta", service.usage)
    payload = {
        "block": args.block,
        "kind": kind,
        "vqebd_version": __version__,
        "protocol_fingerprint": protocol_fingerprint(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": args.backend,
        "shots": args.shots,
        "seed": args.seed,
        "model_repeats": args.model_repeats,
        "physical_qubits": qubits,
        "quota_before": usage,
        "quota_after": None if raw_usage_after is None else quota_summary(raw_usage_after),
        "calibration_before": snapshot_before,
        "calibration_after": snapshot_after,
        "hardware_mha": hardware,
        "model_mha": model,
        "runs": runs,
    }
    write_payload(out, payload)  # a mért adat azonnal biztonságban
    partial_path(out).unlink(missing_ok=True)
    print(f"Mentve: {out}")

    # a végleges QPU-használat utólagos lekérdezése (a mentés után; hiba esetén is marad a fájl)
    if not all(run["usage_final"] for run in runs):
        print("A végleges QPU-használat lekérdezése…")
        try:
            if finalize_usage(service, runs):
                write_payload(out, payload)
        except Exception as exc:
            print(f"  FIGYELEM: a véglegesítés megszakadt: {exc!r}", file=sys.stderr)
        for run in runs:
            state = "végleges" if run["usage_final"] else "NEM végleges"
            print(f"  job {run['job_id']}: {run['quantum_seconds']} QPU-s ({state})")
        print(f"Frissítve: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
