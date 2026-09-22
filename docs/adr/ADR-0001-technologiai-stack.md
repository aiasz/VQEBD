# ADR-0001 — Technológiai stack rögzítése Qiskit 1.4.6-ra

| | |
|---|---|
| **Azonosító** | ADR-0001 |
| **Cím** | Technológiai stack rögzítése Qiskit 1.4.6-ra (a Mitiq-kompatibilis metszet) |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 0–10 (teljes projekt) |
| **Bizonyíték** | [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md), 1–3. kör |

---

## Kontextus

Az alapterv (`quantum-benchmark-projektterv.md`) a következő komponenseket írja elő:
`qiskit`, `qiskit-nature`, `qiskit-aer`, `pyscf` (Fázis 1), `mitiq` (Fázis 3),
`qiskit-ibm-runtime` (Fázis 2), `streamlit` (Fázis 7).

Verziókat nem rögzít — ezt kell most megtennünk. A naiv megközelítés („telepítsük a
legfrissebbet mindenből") a következő PyPI-állapottal találkozik **2026-09-22-én**:

| Csomag | Legfrissebb verzió |
|---|---|
| qiskit | 2.5.2 |
| qiskit-aer | 0.17.2 |
| qiskit-nature | 0.8.0 |
| qiskit-algorithms | 0.4.0 |
| qiskit-ibm-runtime | 0.49.0 |
| mitiq | **0.47.0** (kiadva 2025-09-09) |
| pyscf | 2.14.0 |

## Probléma

A legfrissebb verziók **nem telepíthetők egy környezetbe**. Gépi bizonyíték
(`pip install --dry-run`, `python:3.11-slim` konténer):

```
ERROR: Cannot install ... because these package versions have conflicting dependencies.

The conflict is caused by:
    qiskit 2.5.2 depends on numpy<3 and >=2.0
    qiskit-nature 0.8.0 depends on numpy>=2
    mitiq 0.47.0 depends on numpy<2.0.0 and >=1.22.0

ERROR: ResolutionImpossible
```

A Mitiq saját metaadata meg is erősíti a szándékot — a `qiskit` extrája:

```
qiskit~=1.4.2 ; extra == "qiskit"
qiskit-aer~=0.17.0 ; extra == "qiskit"
qiskit-ibm-runtime~=0.37.0 ; extra == "qiskit"
ply==3.11 ; extra == "qiskit"
```

Azaz: **a Mitiq 0.47.0 hivatalosan a Qiskit 1.4 ágat támogatja, a 2.x-et nem.**

## Megfontolt alternatívák

### A) Két külön környezet (Qiskit 2.x fő + Qiskit 1.4 Mitiq-sidecar)
- ➕ Mindkét komponens a legfrissebb verzión.
- ➖ Az áramkörök és eredmények szerializálása két folyamat között; a QPU-munkamenet
  (`Session`) nem osztható meg → a Fázis 3 „ugyanabban az időablakban, ugyanazon a
  backenden" követelménye sérül.
- ➖ Két Docker-image, két lock-fájl, kétszeres CI.
- ➖ A reprodukálhatóság (a projekt fő terméke) romlik.

### B) Mitiq elhagyása, csak IBM Runtime beépített ZNE
- ➕ Legfrissebb stack, egyszerű.
- ➖ Az alapterv kifejezetten Mitiq-et ír elő (Fázis 3).
- ➖ A Runtime beépített ZNE-je **csak valódi QPU-n** működik → a fejlesztés kvótát éget.
- ➖ Elvész a független, gyártófüggetlen referencia-implementáció.

### C) Stack rögzítése a Mitiq-kompatibilis metszetre ✅
- ➕ **Egy** környezet, egy image, egy lock-fájl.
- ➕ Mitiq mint független keresztvalidáció megmarad.
- ➕ A `qiskit-ibm-runtime 0.41.1` **támogatja az `ibm_quantum_platform` csatornát**
  (mérve, lásd lent) → a Fázis 2 hardveres futás nincs veszélyben.
- ➖ Nem a legfrissebb Qiskit (1.4.6 vs 2.5.2).
- ➖ Hosszú távon a 1.4 ág elavul (→ R4 kockázat).

## Döntés

**A (C) alternatívát választjuk.** A rögzített stack:

```
python          3.11
numpy           1.26.4      # a Mitiq numpy<2.0 korlátja miatt
scipy           1.13.1
qiskit          1.4.6       # az utolsó, numpy 1.x-et engedő ág (2026-06-12)
qiskit-aer      0.17.2
qiskit-nature   0.7.2       # a 0.8.0 numpy>=2-t követel -> kizárva
qiskit-ibm-runtime 0.41.1   # az utolsó, qiskit>=1.4.1-et engedő
mitiq           0.47.0      # opcionális, külön fájlban (ADR-0003, licencelkülönítés)
ply             3.11        # a mitiq[qiskit] extra rejtett függősége (M2)
pyscf           2.14.0
```

### A `qiskit-algorithms` **nincs** pinnelve — és ez szándékos

A TR-000 spike a `qiskit-algorithms==0.3.1`-et **explicit pinnel** telepítette, mert
a spike célja a metszet létezésének igazolása volt. A termelési `requirements.txt`-ben
viszont **nem szerepel**: a `qiskit-nature 0.7.2` tranzitív függősége, és a pip a
mindenkori kompatibilis legfrissebbre oldja fel (a Fázis 1 image-ében: **0.4.0**).

Ez elfogadható, mert az [ADR-0002](ADR-0002-sajat-vqe-hurok.md) értelmében **nem
hívjuk** — a VQE-hurkot saját, V2 primitívekre épülő kóddal írjuk. A tiltást
automatikus teszt kényszeríti ki
(`tests/unit/test_package.py::test_no_qiskit_algorithms_import_in_source`).

Ha a jövőben mégis szükség lenne rá, akkor — és csak akkor — kap explicit pint.
A ténylegesen telepített verziót a `requirements.lock` mindig rögzíti.

### A `ply` külön kezelése

A `ply==3.11`-et **közvetlen függőségként** vesszük fel, **nem** a `mitiq[qiskit]`
extrán keresztül. Indok: az extra egyúttal `qiskit-ibm-runtime~=0.37.0`-t is
lepinnelne, amely még a régi, 2025 júliusában megszüntetett `ibm_quantum` csatornát
célozza. Nélküle a hiba csak a Fázis 3-ban jelentkezne:

```
ModuleNotFoundError: No module named 'ply'
  .../mitiq/interface/mitiq_qiskit/conversions.py:16
  from cirq.contrib.qasm_import import circuit_from_qasm
```

## Következmények

### Pozitív
- A teljes stack **egy konténerben**, feloldott és funkcionálisan igazolt (TR-000).
- A `qiskit-ibm-runtime 0.41.1` mért csatornatámogatása:
  `channels = ['ibm_quantum_platform', 'ibm_cloud']` — az aktuális IBM Quantum
  Platformmal kompatibilis.
- A Runtime beépített hibaenyhítési opciói elérhetők:
  `ZneOptions(amplifier, noise_factors, extrapolator, extrapolated_noise_factors)`,
  `ResilienceOptionsV2(measure_mitigation, measure_noise_learning, zne_mitigation,
  zne, pec_mitigation, pec, layer_noise_learning, layer_noise_model)`.

### Negatív és az arra adott válasz
- **R4 — a Qiskit 1.4 ág elavulása.** Válasz: [ADR-0002](ADR-0002-sajat-vqe-hurok.md)
  értelmében a VQE-hurkot **V2 primitívekkel** írjuk, amelyek a Qiskit 2.x-ben is
  változatlanul léteznek. A kód így átvihető, amint a Mitiq numpy 2 támogatást kap.
  A migrációs teendőt a `docs/plan/00_master_plan.md` 11. fejezete tartja nyilván.
- **Licenc.** A Mitiq GPL-3.0; a VQEBD MIT. Kezelés:
  [ADR-0003](ADR-0003-mitigacios-architektura.md) — a Mitiq opcionális, futásidőben
  betöltött komponens, egyetlen modulba zárva.

## Felülvizsgálati feltétel

Ezt az ADR-t újra kell tárgyalni, ha:

1. megjelenik olyan Mitiq-kiadás, amely `numpy>=2`-t és Qiskit 2.x-et támogat; **vagy**
2. a `qiskit-ibm-runtime 0.41.1` már nem tud csatlakozni az IBM Quantum Platformhoz
   (kliens-elavulás); **vagy**
3. a Qiskit 1.4 ág biztonsági támogatása megszűnik.

## Hivatkozások

- [javadiabhari2024], [larose2022] — lásd [`docs/references.md`](../references.md)
- Mérési jegyzőkönyv: [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md)
- Mesterterv 4. fejezet: [`docs/plan/00_master_plan.md`](../plan/00_master_plan.md)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
