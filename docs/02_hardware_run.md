# 02 — Valódi hardveres futtatás (Fázis 2)

| | |
|---|---|
| **Dokumentum** | `docs/02_hardware_run.md` |
| **Dokumentum-verzió** | 1.1.0 |
| **Dátum** | 2026-09-23 · 2026-09-25 (javítás, v0.7.1) |
| **Projektverzió** | 0.5.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 2 — Egyszeri futtatás valódi IBM-hardveren |

---

## 1. Mit csinál ez a fázis

A Fázis 2 megvalósítja az első valódi, felhőalapú fizikai kvantumhardveres futtatást
az IBM Quantum Heron szupravezető processzorán (**`ibm_kingston`**, 156 fizikai qubit).

```bash
# Kvótamentes hozzáférés-ellenőrzés (csak olvasás)
docker run --rm vqebd:0.5.0 python scripts/check_ibm_access.py

# Valódi hardveres mérés futtatása az IBM Heron QPU-n (Job beküldés)
docker run --rm vqebd:0.5.0 python scripts/run_hardware_vqe.py --backend ibm_kingston --shots 8192
```

---

## 2. A hardveres mérés eredményei

| Paraméter | Érték |
|---|---|
| **Processzor** | `ibm_kingston` (IBM Heron r2, 156 qubit) |
| **Kétqubites hiba** | eszköz-medián (CZ) 1.97·10⁻³; a **használt páron** (1, 2) 8.2·10⁻⁴ |
| **Job ID** | `dapq25kak42c73cj1hu0` |
| **Mintavételi lövésszám** | 8192 |
| **Mitigáció** | **TREX** mérésmitigáció + mérés-twirling (szerver-alapértelmezés, `resilience_level=1`) |
| **Kvótafogyasztás** | **15 QPU-másodperc** (falióra: 48.93 s, ebből 26.9 s sorban állás) |
| **Mért L5 energia** | **-1.1412691258 Ha** |
| **Eltérés a Full CI referenciától** | **−3.96 ± 12.5 mHa** (ensemble SE; `stds` = 53.3 mHa) |

### Összehasonlítás a szimulációkkal

```
L0  Full CI (PySCF) .............. -1.1373060358 Ha (elméleti alapállapot)
L1  Egzakt diagonalizáció ........ -1.1373060358 Ha (Δ = +1.33e-15 Ha)
L2  VQE állapotvektor ............ -1.1373060358 Ha (Δ = +1.49e-15 Ha)
L3a VQE (8192 lövés) ............. -1.1105387727 Ha (Δ = +2.68e-02 Ha)  [v0.7.1]
L3b VQE (FakeManilaV2) ........... -1.0954609696 Ha (Δ = +4.19e-02 Ha)  [v0.7.1]
L5  1 kiértékelés θ*-nál, Heron .. -1.1412691258 Ha (Δ = -3.96e-03 ± 1.25e-02 Ha, TREX)
```

> **Javítás (v0.7.1):** az 1.0.0 változat az L5-öt „nyers” mérésként és a ~4 mHa-t
> a hardver hibaszintjeként értelmezte. Ez téves: a szerver TREX-et alkalmazott,
> és az eltérés 0.3σ-s statisztikus ingadozás, amelyből a hardver hibaszintjére
> nem lehet következtetni. Az L3a/L3b sorok a javított mintavételi modellel
> újramért értékek. Az L5 **nem** hardveres VQE, hanem a zajmentes optimum
> egyetlen hardveres kiértékelése. Teljes indoklás:
> [TR-F02 v1.1.0](testing/TR-F02_hardware_run.md).

---

## 3. Kvótavédelem és biztonsági architektúra

1. **Hitelesítő adatok védelme:** Az API-token kizárólag a `vqebd.credentials`
   modulon keresztül, maszkolt formában töltődik be. A repóban soha nem kerül
   commitolásra, és a `tests/repo/test_secrets_hygiene.py` automatikus teszt ellenőrzi.
2. **CI-védelem:** A CI pipeline `@pytest.mark.hardware` szűréssel kizárja a valódi
   QPU-hívásokat (`pytest -m "not hardware"`), így az automatikus integrációs tesztek
   soha nem égetnek hardveres kvótát.
3. **Minimális kvótafogyasztás:** A hardveres futtatás egyetlen optimalizált Runtime
   EstimatorV2 PUB hívást végez az L2 állapotvektor által előre megtalált optimális
   $\theta^*$ paraméterpontban.
