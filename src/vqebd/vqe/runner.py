"""A VQE fő belépési pontja.

Ez a modul köti össze a rétegeket:

.. code-block::

    MoleculeSpec
        └─ build_electronic_structure()   PySCF + Qiskit Nature
            └─ map_to_qubits()            fermion → qubit
                ├─ collect_references()   L0 (Full CI) és L1 (egzakt diag.)
                ├─ build_ansatz()         UCCSD + Hartree–Fock
                └─ make_energy_evaluator()
                    └─ minimize_energy()  SciPy
                        └─ VQEResult      L2 + a teljes kontextus

Önálló futtatás
---------------
A parancssori felület külön modulban van (:mod:`vqebd.cli`), hogy ez a modul
importálható maradjon anélkül, hogy ``__main__``-ként is futna::

    docker run --rm vqebd:<verzió> python -m vqebd
    docker run --rm vqebd:<verzió> python -m vqebd --bond-length 1.2 --json

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import time
import warnings
from typing import Any

from vqebd.backends.estimators import make_energy_evaluator
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.chemistry.reference import collect_references
from vqebd.config import VQEConfig
from vqebd.platforms import check_optimizer_compatibility, platform_of
from vqebd.seeds import SeedSet
from vqebd.versions import environment_fingerprint, package_versions
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.optimizer import minimize_energy
from vqebd.vqe.result import ReestimateResult, VQEResult

__all__ = ["run_vqe"]


def run_vqe(config: VQEConfig, *, compute_fci: bool = True) -> VQEResult:
    """VQE futtatás egyetlen konfigurációra.

    Args:
        config: A futtatás teljes leírása.
        compute_fci: Számoljuk-e a Full CI referenciát (L0). Nagy rendszereknél
            drága; a Fázis 1-ben mindig ``True``.

    Returns:
        A :class:`~vqebd.vqe.result.VQEResult`. Az alapterv által kért energiaérték
        ennek az ``energy`` mezője.

    Raises:
        RuntimeError: Ha az elektronszerkezeti feladat nem építhető fel.
        ValueError: Ismeretlen leképezés, ansatz, optimalizáló vagy backend esetén.
    """
    started = time.perf_counter()
    seeds = SeedSet.derive(config.seed)
    platform = platform_of(config.backend)

    # A gradiens-alapú optimalizálók alacsony pontosságú platformon CSENDBEN
    # téves minimumot találnak (TR-F01M). Ezt nem hagyjuk szó nélkül.
    incompatibility = check_optimizer_compatibility(config.backend, config.optimizer.method)
    if incompatibility is not None:
        warnings.warn(incompatibility, RuntimeWarning, stacklevel=2)

    structure = build_electronic_structure(config.molecule, config.active_space)
    hamiltonian = map_to_qubits(
        structure, config.mapper, two_qubit_reduction=config.two_qubit_reduction
    )
    reference = collect_references(structure, hamiltonian, compute_fci=compute_fci)
    ansatz = build_ansatz(structure, hamiltonian, config.ansatz, seeds)

    evaluator = make_energy_evaluator(config.backend, ansatz.circuit, hamiltonian.operator, seeds)
    outcome = minimize_energy(evaluator, ansatz.initial_point, config.optimizer)

    # A konstans eltolás: magtaszítás + aktív térben az inaktív energia (Fázis 5).
    # NEM a `nuclear_repulsion_energy` — aktív térben az Hartree-nagyságrendű hiba lenne.
    offset = hamiltonian.energy_offset

    strategy = None
    if config.mitigation.strategy != "none":
        from vqebd.mitigation import get_mitigation_strategy

        strategy = get_mitigation_strategy(
            config.mitigation.strategy,
            scale_factors=config.mitigation.scale_factors,
            extrapolator=config.mitigation.extrapolator,
        )

    def estimate_once() -> tuple[float, Any]:
        """Egy (friss) energiabecslés θ_opt-ban: hibaenyhítve vagy nyersen."""
        if strategy is None:
            return evaluator.evaluate(outcome.parameters), None
        result = strategy.execute(
            ansatz.circuit, hamiltonian.operator, evaluator, outcome.parameters, seeds
        )
        return result.mitigated_energy, result

    mitigation_res = None
    reestimate: ReestimateResult | None = None
    if config.reestimate:
        # Független újramintavételezés (G4): a kiértékelő RNG-je továbblép, így a
        # K becslés friss, az optimalizáció közbeni húzásoktól független.
        samples: list[float] = []
        for _ in range(config.reestimate):
            value, mres = estimate_once()
            samples.append(value)
            if mitigation_res is None:
                mitigation_res = mres
        reestimate = ReestimateResult(
            samples_ha=tuple(v + offset for v in samples),
            optimizer_final_ha=outcome.value + offset,
            history_min_ha=min(outcome.history) + offset,
        )
        electronic = sum(samples) / len(samples)
    elif strategy is not None:
        electronic, mitigation_res = estimate_once()
    else:
        electronic = outcome.value
    total = electronic + offset

    return VQEResult(
        energy=total,
        electronic_energy=electronic,
        nuclear_repulsion_energy=hamiltonian.nuclear_repulsion_energy,
        optimal_parameters=outcome.parameters,
        reference=reference,
        n_qubits=ansatz.num_qubits,
        n_parameters=ansatz.num_parameters,
        n_hamiltonian_terms=hamiltonian.num_terms,
        mapper=hamiltonian.kind,
        two_qubit_reduction=hamiltonian.two_qubit_reduction,
        platform=platform.platform,
        precision=platform.precision,
        backend_tolerance_ha=platform.tolerance_ha,
        n_iterations=outcome.n_iterations,
        n_function_evaluations=outcome.n_function_evaluations,
        converged=outcome.converged,
        optimizer_message=outcome.message,
        history=outcome.history,
        wall_time_s=time.perf_counter() - started,
        config=config,
        seeds=seeds,
        versions=package_versions(),
        environment_fingerprint=environment_fingerprint(),
        mitigation=mitigation_res,
        energy_offset=offset,
        reestimate=reestimate,
    )
