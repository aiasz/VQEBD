#!/usr/bin/env python3
"""Fázis 11 — a szerzői átnézés kérdéseinek felderítő vizsgálata (TR-F11 21. szakasz).

**Utólagos, felderítő; nem része az előre rögzített elemzésnek, az elsődleges eredményt nem
érinti.** Jobot nem küld be, QPU-időt nem használ: a mentett blokkfájlokat olvassa, az IBM-től csak
a történeti kalibrációt kérdezi le (``backend.properties(datetime=…)``), a többi helyi szimuláció.

Részei:

1. a mentett adatokból: a C1 kiugrás felbontása (kiolvasási / egyéb rész), a szintek sorrendjének
   és a sorban állásnak a kapcsolata a reziduummal, és a „tökéletes kiolvasás-modell” felső becslése
   (a gép saját nyers − TREX különbségével);
2. a protokoll-modell **újraépítése** a történeti kalibrációból (ellenőrzés: egyezik a mentett
   előrejelzéssel), majd ellentényes változatok: **aszimmetrikus** kiolvasási hiba
   (``prob_meas1_prep0`` / ``prob_meas0_prep1``) mind a 9 blokkra, és a C7 modellje a C8 egy-egy
   paraméterével;
3. Pauli-tagonkénti bontás (ideális és modellezett várható értékek, a C8 kalibrációjával);
4. a qubitpár szomszédainak kalibrációja, az áramkör és a kiolvasás időtartama.

Használat (~35 perc)::

    python scripts/explore_heron_review.py    # → docs/figures/data/f11/explore_review.json

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import math
import statistics as st
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import run_hardware_pes as prep
from vqebd.heron_calibration_age import first_job_running
from vqebd.heron_model import BLOCK_BONDS, PROTOCOL, model_samples, model_seeds

DATA_DIR = Path("docs/figures/data/f11")
GEOMS = ("0.735", "1.5", "2.0")
T90 = {8: 1.8946, 9: 1.8595}  # t₀,₉₅ (7, ill. 8 szabadsági fok): a 90%-os kétoldali intervallumhoz


def _utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def _summary(values: list[float]) -> dict[str, Any]:
    n = len(values)
    mean, sd = st.mean(values), st.stdev(values)
    half = T90[n] * sd / math.sqrt(n) if n in T90 else None
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "ci90": None if half is None else [mean - half, mean + half],
        "values": values,
    }


def from_saved_files(blocks: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """1. rész: csak a mentett blokkfájlokból."""
    out: dict[str, Any] = {
        "decomposition_0735": {},
        "order": {},
        "queue": {},
        "perfect_readout": {},
    }
    g = "0.735"
    for i, b in blocks.items():
        hw, m = b["hardware_mha"], b["model_mha"]
        out["decomposition_0735"][f"C{i}"] = {
            "hw_readout_part": hw["raw"][g] - hw["trex"][g],
            "model_readout_part": m["readout"][g] - m["no_readout"][g],
            "excess_readout": (hw["raw"][g] - hw["trex"][g])
            - (m["readout"][g] - m["no_readout"][g]),
            "excess_other": hw["trex"][g] - m["no_readout"][g],
        }
    raw_first, trex_first = (2, 4, 6, 8), (1, 3, 5, 7, 9)
    for label, hw_key, model_key in (("raw", "raw", "readout"), ("trex", "trex", "no_readout")):
        out["order"][label] = {}
        for geom in GEOMS:

            def res(i: int, geom: str = geom, hk: str = hw_key, mk: str = model_key) -> float:
                return float(blocks[i]["hardware_mha"][hk][geom] - blocks[i]["model_mha"][mk][geom])

            out["order"][label][geom] = {
                "raw_first_mean": st.mean(res(i) for i in raw_first),
                "trex_first_mean": st.mean(res(i) for i in trex_first),
                "trex_first_mean_without_c1": st.mean(res(i) for i in trex_first[1:]),
            }
    waits, gaps = {}, {}
    for i, b in blocks.items():
        runs = b["runs"]
        waits[i] = max(
            (_utc(r["timestamps"]["running"]) - _utc(r["timestamps"]["created"])).total_seconds()
            for r in runs
        )
        gaps[i] = (
            _utc(runs[1]["timestamps"]["running"]) - _utc(runs[0]["timestamps"]["finished"])
        ).total_seconds()
    out["queue"]["max_wait_min"] = {f"C{i}": w / 60 for i, w in waits.items()}
    out["queue"]["gap_between_jobs_s"] = {f"C{i}": s for i, s in gaps.items()}
    for geom in GEOMS:
        w = [waits[i] for i in blocks]
        raw = [
            blocks[i]["hardware_mha"]["raw"][geom] - blocks[i]["model_mha"]["readout"][geom]
            for i in blocks
        ]
        trex = [
            blocks[i]["hardware_mha"]["trex"][geom] - blocks[i]["model_mha"]["no_readout"][geom]
            for i in blocks
        ]
        out["queue"][f"r_wait_raw_{geom}"] = st.correlation(w, raw)
        out["queue"][f"r_wait_trex_{geom}"] = st.correlation(w, trex)
        out["perfect_readout"][geom] = {"current": _summary(raw), "perfect_readout": _summary(trex)}
    return out


def _qprop(props: Any, qubit: int, name: str) -> float | None:
    for item in props.qubits[qubit]:
        if item.name == name:
            return float(item.value)
    return None


def with_hardware(blocks: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """2–4. rész: történeti kalibráció (csak olvasás) és helyi szimuláció."""
    from qiskit.primitives import BackendEstimatorV2
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError
    from qiskit_ibm_runtime.utils.backend_converter import convert_to_target

    from vqebd.backends.estimators import IBMQpuEnergyEvaluator
    from vqebd.hardware import connect_service

    backend = connect_service().backend(PROTOCOL["backend"])
    config = backend.configuration()
    layout = [int(q) for q in PROTOCOL["physical_qubits"]]
    prepared = prep.prepare(BLOCK_BONDS, PROTOCOL["seed"])
    isa = IBMQpuEnergyEvaluator(
        prepared["circuit"],
        prepared["points"][0]["observable"],
        prepared["seeds"],
        backend_name=PROTOCOL["backend"],
        shots=PROTOCOL["shots"],
        resilience_level=0,
        initial_layout=layout,
    ).isa_circuit
    seeds = model_seeds(PROTOCOL["seed"], PROTOCOL["model_repeats"])

    def simulator(target: Any, asym: dict[int, tuple[float, float]] | None = None) -> Any:
        fake = SimpleNamespace(
            version=2,
            operation_names=list(target.operation_names),
            target=target,
            dt=backend.dt,
            coupling_map=target.build_coupling_map(),
            name="historical",
        )
        noise = NoiseModel.from_backend(fake, readout_error=asym is None)
        for q, (p01, p10) in (asym or {}).items():  # p01 = P(1|0), p10 = P(0|1)
            noise.add_readout_error(ReadoutError([[1 - p01, p01], [p10, 1 - p10]]), [q])
        return AerSimulator(
            noise_model=noise, basis_gates=noise.basis_gates, coupling_map=fake.coupling_map
        )

    def model_errors(sim: Any) -> dict[str, float]:
        out = {}
        for p in prepared["points"]:
            obs = p["observable"].apply_layout(isa.layout)
            vals = model_samples(
                isa, obs, p["theta_star"], sim, shots=PROTOCOL["shots"], seeds=seeds
            )
            out[str(p["bond_length"])] = float(
                np.mean([(e + p["energy_offset_ha"] - p["full_ci_ha"]) * 1e3 for e in vals])
            )
        return out

    result: dict[str, Any] = {"blocks": {}, "counterfactual_c7": {}, "pauli_c8": {}}
    targets = {}
    for i, b in blocks.items():
        props = backend.properties(datetime=first_job_running(b))
        target = convert_to_target(config, props)
        targets[i] = target
        asym = {
            q: (
                _qprop(props, q, "prob_meas1_prep0") or 0.0,
                _qprop(props, q, "prob_meas0_prep1") or 0.0,
            )
            for q in layout
        }
        result["blocks"][f"C{i}"] = {
            "prob_meas1_prep0": {str(q): asym[q][0] for q in layout},
            "prob_meas0_prep1": {str(q): asym[q][1] for q in layout},
            "model_saved": b["model_mha"]["readout"],
            "model_rebuilt": model_errors(simulator(target)),
            "model_asymmetric_readout": model_errors(simulator(target, asym)),
            "hw_raw": b["hardware_mha"]["raw"],
        }
        print(f"C{i}: kész", flush=True)

    t7, t8 = targets[7], targets[8]
    variants: dict[str, Any] = {}
    tt = copy.deepcopy(t7)
    tt.qubit_properties[1].t2 = t8.qubit_properties[1].t2
    variants["q1_T2_from_C8"] = tt
    tt = copy.deepcopy(t7)
    prop = tt["measure"][(1,)]
    prop.error = t8["measure"][(1,)].error
    tt.update_instruction_properties("measure", (1,), prop)
    variants["q1_readout_from_C8"] = tt
    tt = copy.deepcopy(t7)
    for q in layout:
        tt.qubit_properties[q].t1 = t8.qubit_properties[q].t1
        tt.qubit_properties[q].t2 = t8.qubit_properties[q].t2
    variants["T1_T2_both_from_C8"] = tt
    for name, target in variants.items():
        result["counterfactual_c7"][name] = model_errors(simulator(target))

    sim8 = simulator(t8)
    for p in prepared["points"]:
        op = p["observable"]
        terms = [
            (lbl, float(np.real(c)))
            for lbl, c in zip(op.paulis.to_labels(), op.coeffs, strict=True)
        ]
        state = Statevector(prepared["circuit"].assign_parameters(p["theta_star"]))
        est = BackendEstimatorV2(
            backend=sim8, options={"default_precision": 1 / math.sqrt(2**18), "seed_simulator": 7}
        )
        obs = [SparsePauliOp(lbl).apply_layout(isa.layout) for lbl, _ in terms]
        noisy = est.run([(isa, obs, list(p["theta_star"]))]).result()[0].data.evs
        rows = []
        for (lbl, coeff), value in zip(terms, noisy, strict=True):
            ideal = float(np.real(state.expectation_value(SparsePauliOp(lbl))))
            rows.append(
                {
                    "label": lbl,
                    "coeff_ha": coeff,
                    "ideal": ideal,
                    "model_c8": float(value),
                    "contribution_mha": coeff * (float(value) - ideal) * 1e3,
                }
            )
        result["pauli_c8"][str(p["bond_length"])] = {
            "terms": rows,
            "ideal_z_probabilities": {k: float(v) for k, v in state.probabilities_dict().items()},
        }

    edges = backend.coupling_map.get_edges()
    neighbours = sorted(
        {q for edge in edges if set(edge) & set(layout) for q in edge} - set(layout)
    )
    result["neighbours"] = {"qubits": neighbours}
    for i in (1, 5, 8, 9):
        props = backend.properties(datetime=first_job_running(blocks[i]))
        result["neighbours"][f"C{i}"] = {
            str(q): {n: _qprop(props, q, n) for n in ("T1", "T2", "readout_error")}
            for q in neighbours
        }
    noise_now = NoiseModel.from_backend(backend)
    result["timing"] = {
        "isa_duration_s": isa.estimate_duration(backend.target, unit="s"),
        "measure_duration_s": {str(q): backend.target["measure"][(q,)].duration for q in layout},
        "gate_ops_with_quantum_error": sorted(getattr(noise_now, "_local_quantum_errors", {})),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fázis 11 — az átnézés kérdései (felderítő)")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--offline", action="store_true", help="csak a mentett fájlokból (1. rész)")
    args = parser.parse_args(argv)
    started = time.time()
    blocks = {
        i: json.loads((args.data_dir / f"c{i}.json").read_text(encoding="utf-8"))
        for i in range(1, 10)
    }
    payload: dict[str, Any] = {
        "note": "utólagos, felderítő vizsgálat (TR-F11 21.); az elsődleges eredményt nem érinti",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "saved_files": from_saved_files(blocks),
    }
    if not args.offline:
        payload["simulation"] = with_hardware(blocks)
    out = args.data_dir / "explore_review.json"
    out.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Mentve: {out} ({time.time() - started:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
