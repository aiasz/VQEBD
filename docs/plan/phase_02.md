# Fázis 2 — Egyszeri futtatás valódi IBM-hardveren

| | |
|---|---|
| **Fázis** | 2 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Státusz** | Tervezés alatt |
| **Célverzió** | `v0.5.0` |
| **Előzmény** | [`phase_01m.md`](phase_01m.md), [`phase_01b.md`](phase_01b.md), [`TR-F01B`](../testing/TR-F01B_noisy_simulation.md) |

## 1. Cél

A szimulációs referencialánc (L0, L1, L2, L3a, L3b) elkészülte és a
kvótamentes zajos tesztelés után a VQEBD kiszámítja a $H_2$ molekula alapállapoti
energiáját valódi, fizikai szupravezető kvantumprocesszoron (**L5** referenciaszint).

Célhardver: **`ibm_kingston`** (156 qubites Heron QPU, mért 2-qubites kapuhinta: $0.0020$).

A fázis célja:
1. Valódi hardveres várhatóérték-mérés elvégzése IBM Qiskit Runtime EstimatorV2 segítségével.
2. A fizikai hardverzaj hatásának pontos számszerűsítése az L0/L1/L2 elméleti referenciákhoz és az L3b FakeBackend szimulációhoz képest.
3. Kvótavédelmi garanciák kialakítása (véletlen hardverfuttatás kizárása, CI védelem).

## 2. Referencialánc

```
L0  Full CI (PySCF, klasszikus referencia)
 └── L1  Egzakt diagonalizáció (leképezés igazolása)
      └── L2  VQE állapotvektoron (ansatz igazolása)
           └── L3a VQE véges lövésszámmal (8192 shot)
                └── L3b VQE FakeManilaV2 zajmodellel (zajmodell szimuláció)
                     └── L5  VQE valódi IBM Heron hardveren (ibm_kingston)
```

## 3. Kvótavédelem és technikai megfontolások

Az IBM Open Plan **10 perc összesített QPU-időt biztosít 28 napos gördülő ablakban**.
Egy több tucat iterációból álló felhőalapú VQE-optimalizálási ciklus egyenként beküldött
jobokkal túlzott sorbanállási időt és kvótát emésztene fel.

Ezért a Fázis 2 a következő, biztonságos stratégiát követi:
1. **Kiértékelés az optimális paramétervektornál ($\theta^*$):** Az L2 állapotvektoros vagy L3a futás során megtalált optimális paraméterekkel történik a hardveres kiértékelés 8192 vagy 10000 lövéssel, egyetlen optimalizált Qiskit Runtime EstimatorV2 jobban.
2. **Közvetlen hardveres VQE-futás (opcionális, korlátozott lépésszám):** Bounded SPSA vagy COBYLA futtatás (max. 5–10 lépés) csak explicit paraméterezéssel.
3. **Hardveres biztonsági kapcsoló (`requires_quota=True`):** Valódi QPU hívás kizárólag érvényes API-kulcs és explicit backend-választás (`--backend ibm_qpu`) esetén indulhat.
4. **CI-védelem:** A CI pipeline `@pytest.mark.hardware` jelöléssel kizárja a valódi hardveres teszteket (`pytest -m "not hardware"`).

## 4. Tervezett feladatok

1. `vqebd.config.BackendKind` bővítése `"ibm_qpu"` értékkel.
2. `vqebd.platforms.PLATFORMS` bővítése az `ibm_qpu` metaadatokkal (`requires_quota=True`, `exact=False`, `deterministic=False`).
3. `IBMQpuEnergyEvaluator` megvalósítása a `vqebd.backends.estimators` modulban, Qiskit Runtime EstimatorV2 és hitelesítés (`vqebd.credentials`) integrációjával.
4. ISA transzpiláció a Heron 156-qubites fizikai coupling mapjére.
5. Manuális mérési jegyzőkönyv (`docs/testing/TR-F02_hardware_run.md`) elkészítése az éles futás eredményeivel (Job ID, backend adatok, mért energia, futásidő).

## 5. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| AC-2.1 | `IBMQpuEnergyEvaluator` sikeresen csatlakozik és beküldi a feladatot az IBM Heron QPU-ra | manuális / hardware teszt |
| AC-2.2 | A hardveres futás validált ISA áramkört és layoutolt observable-t használ | egységteszt |
| AC-2.3 | A kapott hardveres energia fizikailag értelmezhető tartományban van ($E \approx -1.137 \pm 0.1\ \text{Ha}$) | mérési jegyzőkönyv |
| AC-2.4 | A futási metaadatok (Job ID, backend név, állapot, paraméterek) rögzítésre kerülnek | mérési jegyzőkönyv |
| AC-2.5 | A CI és az automatikus tesztkészlet kvótát nem fogyaszt (`not hardware`) | CI audit |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
