"""Fázis 11: a blokkok kalibráció-életkora (a ``phase_11.md`` 2026-11-19-i definíciója szerint).

Definíció: egy blokk kalibráció-életkora = az **első job indulása** (``running`` időbélyeg) és a
fix qubitpár **T1, T2, kiolvasási hiba és cz-hiba** paraméterei közül a **legrégebbi mérési
időpont** közötti idő, órában. Az sx/x hiba kimarad (ritkán frissül, a modellben kis súlyú). A
``last_update_date`` **nem** számít: frissülhet úgy is, hogy a párt nem mérik újra.

Tiszta réteg: a ``properties`` bemenet bármely objektum lehet, amely a Qiskit
``BackendProperties`` szerkezetét követi (``qubits[q]`` elemei ``name``/``value``/``date``
mezővel, ``gates`` elemei ``gate``/``qubits``/``parameters`` mezővel); a hálózati lekérdezést a
``scripts/heron_calibration_age.py`` végzi.

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "QUBIT_PARAMETERS",
    "block_calibration_age",
    "calibration_age_hours",
    "first_job_running",
    "pair_parameters",
]

QUBIT_PARAMETERS = ("T1", "T2", "readout_error")
"""Az életkorba számító qubit-paraméterek (a cz-hiba mellett)."""

_SNAPSHOT_KEYS = {"T1": "t1_s", "T2": "t2_s", "readout_error": "readout_error"}
_UNIT_SCALE = {"": 1.0, "s": 1.0, "ms": 1e-3, "us": 1e-6, "µs": 1e-6, "ns": 1e-9}


def _utc(value: dt.datetime | str) -> dt.datetime:
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError(f"időzóna nélküli időpont: {value!r}")
    return value.astimezone(dt.UTC)


def pair_parameters(properties: Any, qubits: Sequence[int]) -> list[dict[str, Any]]:
    """A qubitpár életkorba számító paraméterei: név, érték, mérési időpont (UTC).

    Raises:
        ValueError: Ha valamelyik szükséges paraméter hiányzik a kalibrációs adatból.
    """
    pair = [int(q) for q in qubits]
    found: list[dict[str, Any]] = []
    for q in pair:
        names = set()
        for item in properties.qubits[q]:
            if item.name in QUBIT_PARAMETERS:
                found.append(
                    {
                        "name": f"q{q} {item.name}",
                        "value": float(item.value),
                        "unit": str(getattr(item, "unit", "") or ""),
                        "date": _utc(item.date),
                    }
                )
                names.add(item.name)
        missing = set(QUBIT_PARAMETERS) - names
        if missing:
            raise ValueError(f"a q{q} kalibrációjából hiányzik: {sorted(missing)}")
    cz = [
        (par, [int(q) for q in gate.qubits])
        for gate in properties.gates
        if gate.gate == "cz" and sorted(int(q) for q in gate.qubits) == sorted(pair)
        for par in gate.parameters
        if par.name == "gate_error"
    ]
    if not cz:
        raise ValueError(f"a {pair} pár cz-hibája hiányzik a kalibrációból")
    oldest_cz, oldest_qubits = min(cz, key=lambda item: _utc(item[0].date))
    found.append(
        {
            "name": "cz gate_error",
            "value": float(oldest_cz.value),
            "unit": str(getattr(oldest_cz, "unit", "") or ""),
            "date": _utc(oldest_cz.date),
            "qubits": oldest_qubits,
        }
    )
    return found


def first_job_running(block: Mapping[str, Any]) -> dt.datetime:
    """A blokk első jobjának indulása (a ``runs[*].timestamps.running`` legkorábbi értéke).

    Raises:
        ValueError: Ha nincs futás, vagy **bármelyik** futásnál hiányzik a ``running`` időbélyeg
            (különben a legkorábbi indulás csendben a későbbi jobra csúszhatna).
    """
    runs = block.get("runs") or []
    running = [(run.get("timestamps") or {}).get("running") for run in runs]
    if not runs or not all(running):
        raise ValueError(f"a(z) {block.get('block')} blokkban hiányzik a ``running`` időbélyeg")
    return min(_utc(str(t)) for t in running)


def calibration_age_hours(
    first_running: dt.datetime, parameters: Sequence[Mapping[str, Any]]
) -> tuple[float, Mapping[str, Any]]:
    """Az életkor órában és a legrégebbi paraméter.

    Raises:
        ValueError: Üres paraméterlista vagy a job indulása utáni mérési időpont esetén.
    """
    if not parameters:
        raise ValueError("nincs kalibrációs paraméter")
    oldest = min(parameters, key=lambda p: p["date"])
    newest = max(parameters, key=lambda p: p["date"])
    start = _utc(first_running)
    if newest["date"] > start:
        raise ValueError(
            f"a(z) {newest['name']} mérése ({newest['date']}) későbbi a job indulásánál ({start})"
        )
    return (start - oldest["date"]).total_seconds() / 3600.0, oldest


def _matches_snapshot(
    block: Mapping[str, Any], parameters: Sequence[Mapping[str, Any]], rel_tol: float
) -> bool | None:
    """Egyeznek-e a lekérdezett értékek a blokkban mentett pillanatképpel (a modell bemenetével)."""
    snapshot = block.get("calibration_before")
    if not snapshot:
        return None
    for p in parameters:
        if p["name"] == "cz gate_error":
            cz_errors = snapshot.get("cz_errors", {})
            key = "-".join(str(q) for q in p.get("qubits", []))
            saved = [cz_errors[key]] if key in cz_errors else list(cz_errors.values())
            if not any(math.isclose(p["value"], float(v), rel_tol=rel_tol) for v in saved):
                return False
            continue
        qubit, name = p["name"].split(" ", 1)
        saved_value = snapshot.get("qubits", {}).get(qubit[1:], {}).get(_SNAPSHOT_KEYS[name])
        if saved_value is None:
            return False
        scale = _UNIT_SCALE.get(p.get("unit", ""))
        if scale is None:
            return False
        if not math.isclose(p["value"] * scale, float(saved_value), rel_tol=rel_tol):
            return False
    return True


def block_calibration_age(
    block: Mapping[str, Any], properties: Any, *, rel_tol: float = 1e-9
) -> dict[str, Any]:
    """Egy blokk kalibráció-életkorának rekordja (JSON-szerializálható).

    A ``properties`` a blokk első jobjának indulásakor érvényes kalibráció (pl.
    ``backend.properties(datetime=first_job_running(block))``). A ``matches_snapshot`` azt mutatja,
    hogy a lekérdezett értékek azonosak-e a blokk elején mentett pillanatképpel (ellenőrzés).
    """
    start = first_job_running(block)
    parameters = pair_parameters(properties, block["physical_qubits"])
    age, oldest = calibration_age_hours(start, parameters)
    last_update = getattr(properties, "last_update_date", None)
    return {
        "block": block["block"],
        "kind": block.get("kind"),
        "first_job_running_utc": start.isoformat(),
        "oldest_parameter": oldest["name"],
        "oldest_parameter_date_utc": oldest["date"].isoformat(timespec="seconds"),
        "age_h": age,  # kerekítés nélkül: a 48 órás határt a pontos érték dönti el
        "properties_last_update_utc": None
        if last_update is None
        else _utc(last_update).isoformat(timespec="seconds"),
        "matches_snapshot": _matches_snapshot(block, parameters, rel_tol),
        "parameters": [
            {
                "name": p["name"],
                "value": p["value"],
                "unit": p["unit"],
                "date_utc": p["date"].isoformat(timespec="seconds"),
                **({"qubits": p["qubits"]} if "qubits" in p else {}),
            }
            for p in parameters
        ],
    }
