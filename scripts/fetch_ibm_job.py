#!/usr/bin/env python3
"""Egy már lefutott IBM Quantum job tárolt eredményének visszaolvasása.

**QPU-kvótát NEM fogyaszt:** a ``QiskitRuntimeService.job(id).result()`` a szerveren
tárolt eredményt tölti le, új feladatot nem küld be. Ezért ez a helyes eszköz egy
korábbi hardveres mérés hiányzó adatainak (bizonytalanság, mitigációs beállítások,
kvótahasználat) utólagos, ellenőrizhető rögzítésére.

Keletkezése: a TR-F02 1. javítási köre (2026-09-25) megállapította, hogy a Fázis 2
futtatás a ``stds`` szórást eldobta, és a ``resilience_level`` nem volt megadva.
A hiányzó adatokat ez a szkript a ``dapq25kak42c73cj1hu0`` jobból pótolta.

Használat::

    python scripts/fetch_ibm_job.py --data docs/figures/data/hardware_h2_kingston.json

A job azonosítóját alapértelmezésben az adatfájl ``job_id`` mezőjéből veszi.
A tokent és a CRN-t nem írja ki.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def fetch(job_id: str) -> dict[str, Any]:
    """A job tárolt eredményének és metaadatainak lekérése (csak olvasás)."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    from vqebd.credentials import load_ibm_credentials

    creds = load_ibm_credentials()
    kwargs: dict[str, Any] = {"channel": creds.channel, "token": creds.reveal()}
    if creds.instance:
        kwargs["instance"] = creds.instance
    service = QiskitRuntimeService(**kwargs)

    job = service.job(job_id)
    result = job.result()
    pub = result[0]
    data = pub.data
    metrics = job.metrics()
    return {
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "job_status": str(job.status()),
        "ibm_backend_name": job.backend().name,
        "evs": float(data.evs),
        "stds": float(data.stds),
        "ensemble_standard_error": (
            float(data.ensemble_standard_error)
            if hasattr(data, "ensemble_standard_error")
            else None
        ),
        "input_options": job.inputs.get("options", {}),
        "input_resilience_level": job.inputs.get("resilience_level"),
        "pub_metadata": dict(pub.metadata),
        "result_metadata": dict(result.metadata),
        "quantum_seconds": metrics.get("usage", {}).get("quantum_seconds"),
        "timestamps": metrics.get("timestamps", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tárolt IBM job visszaolvasása (kvóta nélkül)")
    parser.add_argument("--data", type=Path, required=True, help="A kiegészítendő adatfájl")
    parser.add_argument("--job-id", default=None, help="Felülírja az adatfájl job_id-ját")
    args = parser.parse_args()

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    job_id = args.job_id or payload["job_id"]
    info = fetch(job_id)

    # Konzisztencia-ellenőrzés: a letöltött érték UGYANAZ a mérés kell legyen.
    stored = payload.get("electronic_energy_ha")
    if stored is not None and abs(info["evs"] - stored) > 1e-12:
        print(
            f"HIBA: a letöltött evs ({info['evs']!r}) eltér a tárolttól ({stored!r})",
            file=sys.stderr,
        )
        return 1

    payload["resilience_level"] = info["input_resilience_level"]
    payload["uncertainty_ha"] = {
        "stds": info["stds"],
        "ensemble_standard_error": info["ensemble_standard_error"],
    }
    payload["runtime_metadata"] = {
        "pub": info["pub_metadata"],
        "result": info["result_metadata"],
        "input_options": info["input_options"],
    }
    payload["quantum_seconds"] = info["quantum_seconds"]
    payload["job_timestamps"] = info["timestamps"]
    payload["provenance_note"] = (
        f"uncertainty_ha, runtime_metadata, quantum_seconds: utólag visszaolvasva "
        f"a tárolt jobból ({info['retrieved_at']}, scripts/fetch_ibm_job.py, "
        f"QPU-futtatás nélkül). resilience_level=None: a kliens nem adta meg, a "
        f"szerver alapértelmezése érvényesült (runtime_metadata.result.resilience)."
    )
    args.data.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"job {job_id}: evs={info['evs']:+.10f} Ha  stds={info['stds']:.3e} Ha")
    print(f"ensemble_standard_error={info['ensemble_standard_error']}")
    print(f"quantum_seconds={info['quantum_seconds']}")
    print(f"Frissítve: {args.data}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
