# 02 — Valódi hardveres futtatás (Fázis 2)

| | |
|---|---|
| **Dokumentum** | `docs/02_hardware_run.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
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
| **Kétqubites átlaghiba** | $0.20\%$ ($0.0020$) |
| **Job ID** | `dapq25kak42c73cj1hu0` |
| **Mintavételi lövésszám** | 8192 |
| **Teljes futási idő** | 48.93 s |
| **Mért L5 energia** | **-1.1412691258 Ha** |
| **Eltérés a Full CI referenciától** | **-3.963 mHa** |

### Összehasonlítás a szimulációkkal

```
L0  Full CI (PySCF) .............. -1.1373060358 Ha (elméleti alapállapot)
L1  Egzakt diagonalizáció ........ -1.1373060358 Ha (Δ = +1.33e-15 Ha)
L2  VQE állapotvektor ............ -1.1373060358 Ha (Δ = +1.49e-15 Ha)
L3a VQE (8192 lövés) ............. -1.1213780162 Ha (Δ = +1.59e-02 Ha)
L3b VQE (FakeManilaV2) ........... -1.0938632143 Ha (Δ = +4.34e-02 Ha)
L5  VQE valódi IBM Heron QPU ..... -1.1412691258 Ha (Δ = -3.96e-03 Ha)
```

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
