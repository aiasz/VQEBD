#!/usr/bin/env python3
"""VQEBD — IBM Quantum hozzáférés ellenőrzése (KVÓTAMENTES).

Mit csinál
----------
Csatlakozik az IBM Quantum Platformhoz, és **kizárólag olvasási** műveleteket
végez: felsorolja az elérhető backendeket, azok qubit-számát, státuszát és
kalibrációs adatait.

**Nem küld be egyetlen feladatot sem**, ezért nem fogyaszt QPU-időt. Az Open Plan
kvótája (10 perc / 28 nap) érintetlen marad.

Miért kell
----------
A Fázis 2 (valódi hardveres futtatás) előtt tudni kell:

1. érvényes-e a hitelesítő adat;
2. mely backendek érhetők el, és melyik a legkisebb elegendő (a H2 2 qubites);
3. mekkora a várakozási sor.

Ez a három kérdés kvóta nélkül megválaszolható — a Fázis 2 így nem hibakereséssel
kezdődik.

Biztonság
---------
A token **soha nem jelenik meg** a kimenetben: a szkript kizárólag a maszkolt
alakot írja ki. A hitelesítő adat betöltése a :mod:`vqebd.credentials` modulon
keresztül történik.

Használat
---------
    python scripts/check_ibm_access.py [--json] [--repo .]

Kilépési kód: 0 siker, 2 hitelesítési vagy kapcsolati hiba.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vqebd.credentials import CredentialsNotFoundError, IbmCredentials, load_ibm_credentials


def mask_instance(crn: str | None) -> str:
    """A szolgáltatáspéldány CRN-jének maszkolása naplózáshoz.

    A CRN önmagában nem hitelesítő adat (vele nem lehet bejelentkezni), **de
    tartalmazza a fiókazonosítót**, ezért kimenetben csak a nem érzékeny részeit
    mutatjuk: a szolgáltatás nevét és a régiót.

    Példa::

        crn:v1:bluemix:public:quantum-computing:us-east:a/<fiók>:<példány>::
        →  quantum-computing / us-east / <maszkolva>
    """
    if not crn:
        return "(nincs megadva)"
    parts = crn.split(":")
    if len(parts) < 7 or parts[0] != "crn":
        return f"{crn[:12]}… ({len(crn)} karakter)"
    service, region = parts[4], parts[5]
    return f"{service} / {region} / <maszkolva, {len(crn)} karakter>"


IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
RESOURCE_CONTROLLER_URL = (
    "https://resource-controller.cloud.ibm.com/v2/resource_instances?limit=100"
)

PROVISIONING_HELP = """\
TEENDŐ — Qiskit Runtime szolgáltatáspéldány létrehozása
────────────────────────────────────────────────────────────────────────────
Az API-kulcs érvényes, de az IBM Cloud fiókban NINCS provisionált Qiskit
Runtime szolgáltatás, ezért nincs mihez kapcsolódni.

A 2025 júliusi platformváltás óta az IBM Quantum hozzáférés két részből áll:

    (1) IBM Cloud API-kulcs   -> megvan, érvényes
    (2) Qiskit Runtime példány -> HIÁNYZIK

A példány létrehozása (egyszeri, a böngészőben):

  1. Nyisd meg: https://quantum.cloud.ibm.com/
  2. Jelentkezz be ugyanazzal az IBM Cloud fiókkal, amelyhez az API-kulcs tartozik.
  3. Hozz létre egy **Open Plan** példányt (ingyenes; 10 perc QPU-idő / 28 nap).
  4. A példány oldalán másold ki a CRN-t (Cloud Resource Name), amely így kezdődik:
         crn:v1:bluemix:public:quantum-computing:...
  5. Írd be a repó gyökerében lévő .env fájlba:
         IBM_QUANTUM_INSTANCE=crn:v1:bluemix:public:quantum-computing:...
     (vagy vedd fel az IBM.token JSON-ba `crn` kulccsal)
  6. Futtasd újra ezt a szkriptet.

Amíg ez nincs meg, a Fázis 2 (valódi hardveres futtatás) nem indítható. A
Fázis 1M és 1b viszont teljes egészében kvótamentes szimulátorokon fut, tehát
a fejlesztés nem áll meg.
────────────────────────────────────────────────────────────────────────────"""


def diagnose_account(credentials: IbmCredentials) -> dict[str, Any]:
    """Az IBM Cloud fiók állapotának felderítése, ha a kapcsolódás elbukott.

    Két kérdést válaszol meg, hogy a rejtélyes ``No matching instances found``
    hibából használható teendő legyen:

    1. **Érvényes-e egyáltalán az API-kulcs?** — IAM token-csere.
    2. **Van-e provisionált szolgáltatás a fiókban?** — Resource Controller.

    A token itt sem kerül a kimenetbe.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    result: dict[str, Any] = {"api_key_valid": False, "instances": None, "error": None}

    try:
        body = urllib.parse.urlencode(
            {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": credentials.reveal(),
            }
        ).encode()
        request = urllib.request.Request(
            IAM_TOKEN_URL,
            data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            access_token = json.load(response).get("access_token", "")
    except urllib.error.HTTPError as exc:
        result["error"] = f"IAM HTTP {exc.code} — az API-kulcs valószínűleg érvénytelen"
        return result
    except Exception as exc:
        result["error"] = f"IAM kapcsolati hiba: {type(exc).__name__}: {exc}"
        return result

    result["api_key_valid"] = bool(access_token)
    if not access_token:
        return result

    try:
        request = urllib.request.Request(
            RESOURCE_CONTROLLER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            resources = json.load(response).get("resources", [])
        result["instances"] = [
            {
                "name": item.get("name"),
                "state": item.get("state"),
                "region": item.get("region_id"),
                "crn": item.get("crn"),
                "is_quantum": "quantum" in str(item.get("resource_id", "")).lower(),
            }
            for item in resources
        ]
    except Exception as exc:
        result["error"] = f"a szolgáltatáslista lekérdezése nem sikerült: {type(exc).__name__}"

    return result


def connect(credentials: IbmCredentials) -> Any:
    """Kapcsolódás az IBM Quantum Platformhoz.

    A ``QiskitRuntimeService`` konstruktora az egyetlen hely, ahol a nyers token
    előkerül (:meth:`IbmCredentials.reveal`).
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    kwargs: dict[str, Any] = {
        "channel": credentials.channel,
        "token": credentials.reveal(),
    }
    if credentials.instance:
        kwargs["instance"] = credentials.instance
    return QiskitRuntimeService(**kwargs)


def describe_backend(backend: Any) -> dict[str, Any]:
    """Egy backend gépileg feldolgozható leírása, hibatűrően.

    A Runtime API mezői verziónként és backendenként eltérhetnek, ezért minden
    lekérdezés védett: a hiányzó adat ``None`` lesz, nem kivétel.
    """
    info: dict[str, Any] = {"name": getattr(backend, "name", "?")}

    for key, getter in (
        ("num_qubits", lambda b: int(b.num_qubits)),
        ("simulator", lambda b: bool(b.simulator)),
        ("operational", lambda b: bool(b.status().operational)),
        ("pending_jobs", lambda b: int(b.status().pending_jobs)),
        ("basis_gates", lambda b: sorted(b.operation_names)),
        ("processor_type", lambda b: dict(b.processor_type or {})),
    ):
        try:
            info[key] = getter(backend)
        except Exception:  # a hiányzó mező nem hiba, csak ismeretlen
            info[key] = None

    # Átlagos kétqubites hibaarány — a benchmark szempontjából a legfontosabb
    # egyetlen minőségi mutató.
    try:
        target = backend.target
        errors = [
            props.error
            for name in ("cx", "ecr", "cz")
            if name in target
            for props in target[name].values()
            if props is not None and props.error is not None
        ]
        info["median_two_qubit_error"] = float(sorted(errors)[len(errors) // 2]) if errors else None
    except Exception:
        info["median_two_qubit_error"] = None

    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/check_ibm_access.py",
        description="IBM Quantum hozzáférés ellenőrzése — kvótamentes, csak olvasás.",
    )
    parser.add_argument("--repo", default=".", type=Path, help="a repó gyökere")
    parser.add_argument("--json", action="store_true", help="JSON kimenet")
    args = parser.parse_args(argv)

    # --- 1. Hitelesítő adat -------------------------------------------------
    try:
        credentials = load_ibm_credentials(args.repo)
    except (CredentialsNotFoundError, ValueError) as exc:
        print(f"HIBA: {exc}", file=sys.stderr)
        return 2

    if not args.json:
        print("=" * 76)
        print("IBM Quantum hozzáférés ellenőrzése — KVÓTAMENTES (csak olvasás)")
        print("=" * 76)
        print(f"Hitelesítő adat forrása : {credentials.source}")
        print(f"Token (maszkolva)       : {credentials.masked()}")
        print(f"Csatorna                : {credentials.channel}")
        print(f"Példány (instance)      : {mask_instance(credentials.instance)}")
        print()

    # --- 2. Kapcsolódás ------------------------------------------------------
    try:
        service = connect(credentials)
    except Exception as exc:
        # A Runtime hibaüzenete ilyenkor rejtélyes ("No matching instances found").
        # Felderítjük, hogy az API-kulcs vagy a szolgáltatáspéldány hiányzik-e.
        diagnosis = diagnose_account(credentials)
        if args.json:
            print(
                json.dumps(
                    {"error": str(exc), "diagnosis": diagnosis}, indent=2, ensure_ascii=False
                )
            )
            return 2

        print(f"HIBA: nem sikerült csatlakozni: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print("── Diagnosztika ──────────────────────────────────────────", file=sys.stderr)
        if diagnosis["error"]:
            print(f"   {diagnosis['error']}", file=sys.stderr)
        print(
            f"   API-kulcs érvényes      : {'IGEN' if diagnosis['api_key_valid'] else 'NEM'}",
            file=sys.stderr,
        )
        instances = diagnosis["instances"]
        if instances is not None:
            quantum = [i for i in instances if i["is_quantum"]]
            print(f"   Szolgáltatáspéldányok   : {len(instances)}", file=sys.stderr)
            print(f"   Ebből Quantum           : {len(quantum)}", file=sys.stderr)
            for item in quantum:
                print(
                    f"      - {item['name']} [{item['state']}, {item['region']}]", file=sys.stderr
                )
                print(f"        CRN: {mask_instance(item['crn'])}", file=sys.stderr)
        print(file=sys.stderr)
        if diagnosis["api_key_valid"] and not (instances or []):
            print(PROVISIONING_HELP, file=sys.stderr)
        return 2

    # --- 3. Backendek felsorolása -------------------------------------------
    try:
        backends = [describe_backend(b) for b in service.backends()]
    except Exception as exc:
        print(
            f"HIBA: a backendek lekérdezése nem sikerült: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    payload = {
        "credentials_source": credentials.source,
        "channel": credentials.channel,
        "instance": mask_instance(credentials.instance),
        "backend_count": len(backends),
        "backends": backends,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"Elérhető backendek: {len(backends)}\n")
    header = f"{'név':<24}{'qubit':>6}{'sor':>6}{'2q hiba':>10}  {'státusz':<12}típus"
    print(header)
    print("-" * len(header))
    for info in sorted(backends, key=lambda b: (b["simulator"] is True, -(b["num_qubits"] or 0))):
        error = info["median_two_qubit_error"]
        status = "üzemel" if info["operational"] else "NEM üzemel"
        kind = "szimulátor" if info["simulator"] else "QPU"
        processor = (info.get("processor_type") or {}).get("family", "")
        print(
            f"{info['name']:<24}{info['num_qubits'] or 0:>6}"
            f"{info['pending_jobs'] if info['pending_jobs'] is not None else 0:>6}"
            f"{(f'{error:.4f}' if error is not None else '—'):>10}  "
            f"{status:<12}{kind} {processor}".rstrip()
        )

    # --- 4. Javaslat a Fázis 2-höz ------------------------------------------
    usable = [
        b
        for b in backends
        if not b["simulator"] and b["operational"] and (b["num_qubits"] or 0) >= 2
    ]
    print()
    if usable:
        best = min(
            usable,
            key=lambda b: (
                b["median_two_qubit_error"] if b["median_two_qubit_error"] is not None else 1.0,
                b["pending_jobs"] or 0,
            ),
        )
        print(
            f"Fázis 2 javaslat (legkisebb 2q hiba): {best['name']} "
            f"({best['num_qubits']} qubit, 2q hiba "
            f"{best['median_two_qubit_error']:.4f}, sor: {best['pending_jobs']})"
        )
    else:
        print("FIGYELEM: nem található üzemelő QPU. A Fázis 2 nem indítható.")

    print()
    print("Megjegyzés: ez a futtatás NEM küldött be feladatot, tehát nem fogyasztott")
    print("QPU-időt. Az Open Plan kvótája (10 perc / 28 nap) érintetlen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
