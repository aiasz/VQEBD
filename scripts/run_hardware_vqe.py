#!/usr/bin/env python3
"""Fázis 2 — Valódi IBM Quantum QPU mérés futtatása (H2, Heron QPU).

Ez a szkript végzi el a valódi fizikai mérést a legkisebb hibájú IBM Heron QPU-n
(alapértelmezés: ``ibm_kingston``).

Biztonsági és kvótavédelmi alapelvek
-----------------------------------
- Nem fut automatikusan a CI tesztek során.
- Egyetlen PUB feladatot küld be a runtime EstimatorV2-vel, az L2-n megtalált
  optimális paramétervektorral (\\theta^*), minimalizálva a sorbanállást és
  a kvótafogyasztást.
- Az eredményt, a bizonytalanságot (``stds``, ``ensemble_standard_error``) és a
  szerveroldali mitigációs metaadatokat a ``--out`` fájlba menti (alapértelmezés:
  ``docs/figures/data/hardware_h2_kingston.json``).
- A ``resilience_level`` mindig explicit (TR-F02, 1. javítási kör).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from vqebd.backends.estimators import IBMQpuEnergyEvaluator
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.chemistry.reference import collect_references
from vqebd.config import AnsatzSpec, OptimizerSpec, VQEConfig
from vqebd.credentials import load_ibm_credentials
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


def main() -> int:
    parser = argparse.ArgumentParser(description="VQE futtatása valódi IBM Heron QPU-n (Fázis 2)")
    parser.add_argument(
        "--backend",
        default="ibm_kingston",
        help="Az IBM Quantum backend neve (alapértelmezés: ibm_kingston)",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=8192,
        help="Mintavételi lövésszám (alapértelmezés: 8192)",
    )
    parser.add_argument(
        "--resilience-level",
        type=int,
        default=1,
        choices=(0, 1, 2),
        help=(
            "IBM Runtime mitigációs szint, MINDIG explicit (0 = nyers, "
            "1 = TREX mérésmitigáció [alapértelmezés], 2 = +ZNE)"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/figures/data/hardware_h2_kingston.json"),
        help="A nyers mérési adatok célfájlja",
    )
    args = parser.parse_args()

    print("=" * 76)
    print(f"VQEBD Fázis 2 — Valódi hardveres mérés ({args.backend})")
    print("=" * 76)

    # 1. Hitelesítő adatok ellenőrzése
    try:
        creds = load_ibm_credentials()
        print(f"Hitelesítés forrása : {creds.source}")
        print(f"Token (maszkolva)   : {creds.masked()}")
    except Exception as exc:
        print(f"HIBA: Nem sikerült betölteni a hitelesítő adatokat: {exc}", file=sys.stderr)
        return 1

    # 2. Molekula és elméleti referenciák felépítése
    print("\n[1/4] Molekula és állapotvektoros referencia számítása...")
    mol = h2(H2_REFERENCE_BOND_LENGTH)
    structure = build_electronic_structure(mol)
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    references = collect_references(structure, hamiltonian, compute_fci=True)

    # L2 állapotvektoros futtatás az optimális \theta* paraméterért
    config_l2 = VQEConfig(
        molecule=mol,
        mapper="parity",
        two_qubit_reduction=True,
        backend="qiskit_statevector",
        optimizer=OptimizerSpec(method="SLSQP"),
        ansatz=AnsatzSpec(kind="uccsd"),
    )
    res_l2 = run_vqe(config_l2)
    opt_params = list(res_l2.optimal_parameters)

    print(f"  L0 Full CI energia ......... {references.full_ci:+.10f} Ha")
    print(f"  L1 Egzakt diagonalizáció ... {references.exact_diagonalization:+.10f} Ha")
    print(f"  L2 VQE (statevector) ....... {res_l2.energy:+.10f} Ha")
    print(f"  Optimális paraméterek (θ*) .. {opt_params}")

    # Védőkorlátok beküldés előtt: explicit engedély és kvóta (vqebd.hardware).
    assert_hardware_allowed()
    usage = quota_summary(connect_service().usage())
    try:
        assert_quota_available(usage, required_seconds=30.0)
    except QuotaExhaustedError as exc:
        print(f"MEGTAGADVA: {exc}", file=sys.stderr)
        return 2

    # 3. Transzpiláció és beküldés az IBM Heron QPU-ra
    print(f"\n[2/4] Csatlakozás és ISA transzpiláció a(z) {args.backend} eszközre...")
    seeds = SeedSet.derive(config_l2.seed)
    ansatz = build_ansatz(structure, hamiltonian, config_l2.ansatz, seeds)

    evaluator = IBMQpuEnergyEvaluator(
        circuit=ansatz.circuit,
        observable=hamiltonian.operator,
        seeds=seeds,
        backend_name=args.backend,
        shots=args.shots,
        resilience_level=args.resilience_level,
    )
    desc = evaluator.describe()
    print(f"  Eszköz fizikai qubitszáma ... {desc['isa_qubits']}")
    print(f"  Lövésszám (shots) ........... {desc['shots']}")
    print(f"  Optimális szint ............. {desc['optimization_level']}")
    print(f"  Mitigációs szint ............ {desc['resilience_level']}")

    print("\n[3/4] Mérés futtatása az IBM Heron QPU-n (várás a feladatra)...")
    start_time = time.perf_counter()
    electronic_energy = evaluator.evaluate(opt_params)
    total_energy = electronic_energy + hamiltonian.nuclear_repulsion_energy
    duration = time.perf_counter() - start_time

    job_id = evaluator.last_job_id
    print(f"  Job ID ...................... {job_id}")
    print(f"  Végrehajtási idő ............ {duration:.2f} s")
    print(f"  Mért elektronos energia ..... {electronic_energy:+.10f} Ha")
    print(f"  Mért teljes energia (L5) .... {total_energy:+.10f} Ha")
    std = evaluator.last_std
    ens = evaluator.last_ensemble_standard_error
    print(f"  Szórás (stds) ............... {std if std is not None else float('nan'):.3e} Ha")
    print(f"  Ensemble standard hiba ...... {ens if ens is not None else float('nan'):.3e} Ha")

    err_vs_l0 = total_energy - references.full_ci if references.full_ci is not None else 0.0
    err_vs_l1 = (
        total_energy - references.exact_diagonalization
        if references.exact_diagonalization is not None
        else 0.0
    )
    print(f"  Eltérés az L0 referenciától . {err_vs_l0:+.3e} Ha")
    print(f"  Eltérés az L1 egzakt szinttől {err_vs_l1:+.3e} Ha")

    # 4. Mentés JSON-be
    print(f"\n[4/4] Adatok mentése: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": "ibm_qpu",
        "ibm_backend_name": args.backend,
        "job_id": job_id,
        "shots": args.shots,
        "resilience_level": args.resilience_level,
        "duration_s": duration,
        "optimal_parameters": opt_params,
        "energies": {
            "hartree_fock_ha": references.hartree_fock,
            "l0_full_ci_ha": references.full_ci,
            "l1_exact_diag_ha": references.exact_diagonalization,
            "l2_statevector_ha": res_l2.energy,
            "l5_hardware_ha": total_energy,
        },
        "errors_ha": {
            "error_vs_l0_ha": err_vs_l0,
            "error_vs_l1_ha": err_vs_l1,
        },
        "nuclear_repulsion_ha": hamiltonian.nuclear_repulsion_energy,
        "electronic_energy_ha": electronic_energy,
        "uncertainty_ha": {
            "stds": std,
            "ensemble_standard_error": ens,
        },
        "runtime_metadata": evaluator.last_metadata,
    }
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    print("Mérés sikeresen befejeződött és dokumentálva lett.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
