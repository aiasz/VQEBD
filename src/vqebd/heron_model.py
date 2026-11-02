"""Fázis 11: a kalibrációból épített Heron-zajmodell, kiolvasási hibával és anélkül.

A modul a ``phase_11.md`` 5. fejezetének C1–C4 elemeit adja, **kvóta nélkül** (csak olvasás a
szolgáltatótól és helyi szimuláció):

- :func:`build_simulator` — ``AerSimulator.from_backend``; a kiolvasási hiba be-/kikapcsolható;
- :func:`model_samples` — a modell energiabecslései **kiolvasást is modellező** becslővel
  (``BackendEstimatorV2``; az Aer ``EstimatorV2`` nem modellezi a kiolvasási hibát, ADR-0003
  1. kiegészítés), minden ismétléshez más szimulátor-seeddel;
- :func:`calibration_snapshot` — a használt qubitek kalibrációja és időbélyege (C3);
- :data:`PROTOCOL` és :func:`protocol_fingerprint` — a befagyasztott protokoll ujjlenyomata, amit
  a hardveres futtató beküldés előtt ellenőriz (R4: nincs utólagos küszöb- vagy geometriamódosítás).

Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from collections.abc import Sequence
from typing import Any

import numpy as np

__all__ = [
    "BLOCK_BONDS",
    "PILOT_BONDS",
    "PROTOCOL",
    "build_simulator",
    "calibration_snapshot",
    "model_samples",
    "model_seeds",
    "protocol_fingerprint",
]

PILOT_BONDS: tuple[float, ...] = (0.5, 0.735, 1.0, 1.5, 2.0)
"""A pilot (B0) geometriái (Å)."""

BLOCK_BONDS: tuple[float, ...] = (0.735, 1.5, 2.0)
"""A megerősítő blokkok (C1…C8) geometriái (Å) — a szerző jóváhagyta (2026-11-02)."""

PROTOCOL: dict[str, Any] = {
    "phase": 11,
    "delta_mha": 3.0,
    "equivalence_confidence": 0.90,
    "pilot_bonds": list(PILOT_BONDS),
    "block_bonds": list(BLOCK_BONDS),
    "confirmatory_blocks": 8,
    "shots": 8192,
    "model_repeats": 10,
    "optimization_level": 3,
    "resilience_levels": [0, 1],
    "backend": "ibm_kingston",
    "physical_qubits": [1, 2],
    "seed": 20260922,
    "max_used_fraction": 0.80,
    "per_pub_seconds": {"raw": 4.8, "trex": 6.6},
    "gate_safety_factor": 1.25,
}
"""A befagyasztott protokoll. Módosítása **új protokoll** (``phase_11.md`` 3. fejezet); a hardveres
futtató csak akkor küld be, ha a ``docs/figures/data/f11/FROZEN`` ujjlenyomata egyezik."""


def protocol_fingerprint(protocol: dict[str, Any] | None = None) -> str:
    """A protokoll kanonikus JSON-jának SHA-256 ujjlenyomata."""
    canonical = json.dumps(protocol if protocol is not None else PROTOCOL, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def model_seeds(base_seed: int, count: int) -> list[int]:
    """``count`` különböző szimulátor-seed, determinisztikusan a ``base_seed``-ből.

    Az ismétlésenként **más** seed kötelező: egyetlen közös seed minden ismétlésnél azonos
    "lövészajt" adna (a v0.7.1-ben javított hiba).
    """
    if count < 1:
        raise ValueError(f"count pozitív legyen, kapott: {count}")
    rng = np.random.default_rng(base_seed)
    seeds = rng.integers(1, 2**31 - 1, size=count)
    return [int(x) for x in seeds]


def build_simulator(backend: Any, *, readout: bool = True) -> Any:
    """A backend **jelenlegi** kalibrációjából épített Aer-szimulátor.

    A zajmodellt közvetlenül a ``NoiseModel.from_backend``-ből építjük. Az
    ``AerSimulator.from_backend(backend, readout_error=False)`` **nem jó**: a kulcsszót
    szimulátor-opcióként kezeli és figyelmen kívül hagyja, így a kiolvasás nélküli és a kiolvasásos
    modell azonos lenne (a Fázis 11 első szárazfutása tárta fel).

    Args:
        backend: IBM-backend (pl. ``service.backend("ibm_kingston")``).
        readout: ``True`` — a kiolvasási hibát is modellezi; ``False`` — kikapcsolja (H2/H3).
    """
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel

    noise_model = NoiseModel.from_backend(backend, readout_error=readout)
    return AerSimulator(
        noise_model=noise_model,
        basis_gates=noise_model.basis_gates,
        coupling_map=backend.coupling_map,
    )


def model_samples(
    isa_circuit: Any,
    observable: Any,
    parameters: Sequence[float],
    simulator: Any,
    *,
    shots: int,
    seeds: Sequence[int],
) -> list[float]:
    """A modell elektronos energiabecslései (Ha) — ismétlésenként egy, seedenként más.

    Args:
        isa_circuit: A hardveres méréssel azonos ISA-áramkör.
        observable: Az ISA-layoutra már leképezett observable.
        parameters: A paraméterek (θ*).
        simulator: :func:`build_simulator` eredménye.
        shots: A hardveres lövésszám (a becslő precíziója ``1/sqrt(shots)``).
        seeds: Ismétlésenként egy szimulátor-seed (:func:`model_seeds`).
    """
    from qiskit.primitives import BackendEstimatorV2

    if shots < 1:
        raise ValueError(f"shots pozitív legyen, kapott: {shots}")
    precision = 1.0 / float(np.sqrt(shots))
    values: list[float] = []
    for seed in seeds:
        estimator = BackendEstimatorV2(
            backend=simulator,
            options={"default_precision": precision, "seed_simulator": int(seed)},
        )
        result = estimator.run([(isa_circuit, observable, list(parameters))]).result()
        values.append(float(result[0].data.evs))
    return values


def calibration_snapshot(backend: Any, physical_qubits: Sequence[int]) -> dict[str, Any]:
    """A használt qubitek kalibrációs pillanatképe (csak olvasás, QPU-idő nélkül).

    Tartalma: a backend neve, a kalibráció ``last_update_date``-je, a pillanatkép UTC ideje,
    qubitenként T1, T2 (s), kiolvasási hiba, ``sx`` és ``x`` kapuhiba, valamint a használt qubitek
    közötti ``cz`` kapuhibák.
    """
    props = backend.properties()
    qubits = sorted({int(q) for q in physical_qubits})
    per_qubit: dict[str, dict[str, float]] = {}
    for q in qubits:
        per_qubit[str(q)] = {
            "t1_s": float(props.t1(q)),
            "t2_s": float(props.t2(q)),
            "readout_error": float(props.readout_error(q)),
            "sx_error": float(props.gate_error("sx", q)),
            "x_error": float(props.gate_error("x", q)),
        }
    cz: dict[str, float] = {}
    for gate in props.gates:
        if gate.gate != "cz":
            continue
        a, b = (int(x) for x in gate.qubits)
        if a in qubits and b in qubits:
            cz[f"{a}-{b}"] = float(props.gate_error("cz", [a, b]))
    last_update = props.last_update_date
    return {
        "backend": str(backend.name),
        "last_update_date": last_update.isoformat() if last_update is not None else None,
        "captured_utc": _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "physical_qubits": qubits,
        "qubits": per_qubit,
        "cz_errors": cz,
    }
