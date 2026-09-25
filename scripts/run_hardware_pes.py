#!/usr/bin/env python3
"""Fázis 5.H — H₂ disszociációs görbe valódi IBM QPU-n (``phase_05.md`` 6.4).

Kvótatakarékos kialakítás: a H₂ UCCSD-áramköre minden kötéshossznál azonos, csak a
θ*(R) és a Hamilton-operátor változik. Ezért **mitigációs szintenként egyetlen
job** fut, benne kötéshosszanként egy PUB (alapértelmezés: 5 geometria × 2 szint =
2 job, 10 PUB).

Védőkorlátok (``vqebd.hardware``):

- beküldés csak ``VQEBD_ALLOW_HARDWARE=true`` mellett;
- beküldés előtt kvóta-lekérdezés; ha a becsült igény nem fér bele, **megtagad**;
- ``--dry-run``: minden klasszikus számítás és a kvótaellenőrzés lefut, beküldés nincs.

Minden PUB-hoz a bizonytalanság (``stds``, ``ensemble_standard_error``), a
szerveroldali mitigációs metaadat, a job azonosítója és a számlázott QPU-idő
kerül a kimeneti JSON-ba (TR-F02 v1.1.0 tanulsága).

Használat::

    python scripts/run_hardware_pes.py --dry-run
    VQEBD_ALLOW_HARDWARE=true python scripts/run_hardware_pes.py

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from vqebd import __version__
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import AnsatzSpec, VQEConfig
from vqebd.hardware import (
    QuotaExhaustedError,
    assert_hardware_allowed,
    assert_quota_available,
    connect_service,
    quota_summary,
)
from vqebd.seeds import SeedSet
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.runner import run_vqe

DEFAULT_BONDS = (0.5, 0.735, 1.0, 1.5, 2.0)
SECONDS_PER_JOB_ESTIMATE = 60.0
"""Konzervatív becslés jobonként (5 PUB × 8192 lövés, twirlinggel). Mérési alap: a
Fázis 2 egyetlen PUB-os jobja 15 QPU-s volt; a becslés ennek négyszerese."""


def same_ansatz(a: Any, b: Any, *, trials: int = 3) -> bool:
    """Két paraméteres áramkör ugyanazt az unitért valósítja-e meg.

    A ``QuantumCircuit.__eq__`` itt nem használható: minden ``build_ansatz`` hívás
    új ``Parameter`` objektumokat (új UUID-val) hoz létre, így két szerkezetileg
    azonos áramkör is „különbözik”. A helyes próba: azonos paraméternév-sorrend és
    azonos unitér véletlen (rögzített seedű) paraméterekre.
    """
    import numpy as np
    from qiskit.quantum_info import Operator

    if [x.name for x in a.parameters] != [x.name for x in b.parameters]:
        return False
    rng = np.random.default_rng(20260925)
    for _ in range(trials):
        theta = rng.uniform(-np.pi, np.pi, a.num_parameters)
        ua = Operator(a.assign_parameters(theta)).data
        ub = Operator(b.assign_parameters(theta)).data
        if not np.allclose(ua, ub, atol=1e-12):
            return False
    return True


def prepare(bonds: tuple[float, ...], seed: int) -> dict[str, Any]:
    """Klasszikus előkészítés: θ*(R), referenciák és a közös ansatz-áramkör."""
    points: list[dict[str, Any]] = []
    circuit = None
    seeds = SeedSet.derive(seed)
    for bond in bonds:
        mol = h2(bond)
        l2 = run_vqe(VQEConfig(molecule=mol, seed=seed))
        structure = build_electronic_structure(mol)
        hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
        ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(), seeds)
        if circuit is None:
            circuit = ansatz.circuit
        elif not same_ansatz(ansatz.circuit, circuit):
            raise RuntimeError(f"az R={bond} Å ansatz-áramköre eltér — egy job nem elég")
        points.append(
            {
                "bond_length": bond,
                "theta_star": list(l2.optimal_parameters),
                "observable": hamiltonian.operator,
                "energy_offset_ha": hamiltonian.energy_offset,
                "hartree_fock_ha": l2.reference.hartree_fock,
                "full_ci_ha": l2.reference.full_ci,
                "l2_statevector_ha": l2.energy,
            }
        )
    return {"points": points, "circuit": circuit, "seeds": seeds}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H2 PES valódi IBM QPU-n (Fázis 5.H)")
    parser.add_argument("--backend", default="ibm_kingston")
    parser.add_argument("--shots", type=int, default=8192)
    parser.add_argument("--bonds", type=float, nargs="+", default=list(DEFAULT_BONDS))
    parser.add_argument("--levels", type=int, nargs="+", default=[0, 1], choices=(0, 1, 2))
    parser.add_argument("--seed", type=int, default=20260922)
    parser.add_argument("--out", type=Path, default=Path("docs/figures/data/hardware_h2_pes.json"))
    parser.add_argument("--dry-run", action="store_true", help="beküldés nélkül")
    args = parser.parse_args(argv)

    required = SECONDS_PER_JOB_ESTIMATE * len(args.levels)
    print(f"Terv: {len(args.bonds)} geometria × {len(args.levels)} szint = {len(args.levels)} job")
    print(f"Becsült QPU-igény: ≤ {required:.0f} s")

    prepared = prepare(tuple(args.bonds), args.seed)
    for p in prepared["points"]:
        print(f"  R={p['bond_length']:<6} θ*={p['theta_star']}  L2={p['l2_statevector_ha']:+.10f}")

    service = connect_service()
    usage = quota_summary(service.usage())
    print(f"Kvóta: {json.dumps(usage, default=str)}")
    try:
        assert_quota_available(usage, required)
    except QuotaExhaustedError as exc:
        print(f"MEGTAGADVA: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        print("Dry run: a kvóta elegendő, beküldés nem történt.")
        return 0
    assert_hardware_allowed()

    from vqebd.backends.estimators import IBMQpuEnergyEvaluator

    runs: list[dict[str, Any]] = []
    for level in args.levels:
        evaluator = IBMQpuEnergyEvaluator(
            prepared["circuit"],
            prepared["points"][0]["observable"],
            prepared["seeds"],
            backend_name=args.backend,
            shots=args.shots,
            resilience_level=level,
        )
        started = time.perf_counter()
        results = evaluator.evaluate_observables(
            [p["observable"] for p in prepared["points"]],
            [p["theta_star"] for p in prepared["points"]],
        )
        job_id = evaluator.last_job_id
        job = service.job(job_id)
        metrics = job.metrics()
        runs.append(
            {
                "resilience_level": level,
                "job_id": job_id,
                "wall_time_s": time.perf_counter() - started,
                "quantum_seconds": metrics.get("usage", {}).get("quantum_seconds"),
                "timestamps": metrics.get("timestamps", {}),
                "result_metadata": evaluator.last_metadata.get("result"),
                "isa_qubits": evaluator.describe()["isa_qubits"],
                "points": [
                    {
                        "bond_length": p["bond_length"],
                        "energy_ha": r["evs"] + p["energy_offset_ha"],
                        "error_vs_fci_ha": r["evs"] + p["energy_offset_ha"] - p["full_ci_ha"],
                        "stds_ha": r["stds"],
                        "ensemble_standard_error_ha": r["ensemble_standard_error"],
                        "pub_metadata": r["metadata"],
                    }
                    for p, r in zip(prepared["points"], results, strict=True)
                ],
            }
        )
        print(f"  szint {level}: job {job_id}, {runs[-1]['quantum_seconds']} QPU-s")

    payload = {
        "vqebd_version": __version__,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": args.backend,
        "shots": args.shots,
        "quota_before": usage,
        "quota_after": quota_summary(service.usage()),
        "references": [
            {k: v for k, v in p.items() if k != "observable"} for p in prepared["points"]
        ],
        "runs": runs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    print(f"Mentve: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
