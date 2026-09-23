# TP-F02 — Fázis 2 tesztterv (Valódi IBM hardveres futtatás)

| | |
|---|---|
| **Azonosító** | TP-F02 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Fázis** | 2 — Valódi hardveres futtatás |
| **Terv** | [`phase_02.md`](../plan/phase_02.md) |

## 1. Referencialánc

```
L0  Full CI (PySCF, klasszikus referencia)
 └── L1  Egzakt diagonalizáció (leképezés igazolása)
      └── L2  VQE állapotvektoron (ansatz igazolása)
           └── L3a VQE véges lövésszámmal (8192 shot)
                └── L3b VQE FakeManilaV2 zajmodellel (zajmodell szimuláció)
                     └── L5  VQE valódi IBM Heron hardveren (ibm_kingston)
```

## 2. Tesztesetek

| Eset | AC | Ellenőrzés |
|---|---|---|
| **TC-201** | AC-2.1 | `IBMQpuEnergyEvaluator` sikeresen inicializál `QiskitRuntimeService` kapcsolaton keresztül. |
| **TC-202** | AC-2.2 | A Heron QPU 156-qubites topológiájára transzpilált áramkör és az observable illeszkedik (`apply_layout`). |
| **TC-203** | AC-2.3 | Éles futás az `ibm_kingston` QPU-n fizikailag reális energiát ad ($E \approx -1.137 \pm 0.1\ \text{Ha}$). |
| **TC-204** | AC-2.4 | A futási rekord tartalmazza a Job ID-t, a backend nevét, a fizikai qubiteket és az időbélyeget. |
| **TC-205** | AC-2.5 | `requires_quota=True`, és a CI automatikusan kizárja a hardveres teszteket (`not hardware`). |
| **TC-206** | AC-2.1 | Hiányzó vagy érvénytelen hitelesítő adat esetén egyértelmű hibaüzenet keletkezik. |
| **TC-207** | AC-2.1 | A CLI támogatja az `--backend ibm_qpu` opciót. |
| **TC-208** | AC-2.3 | Az L5 hardveres eredmény összevethető a teljes referencialánccal (L0, L1, L2, L3a, L3b). |

## 3. Negatív és kvótavédelmi ellenőrzések

- Automatikus CI-körökben (`pytest -m "not hardware"`) egyetlen valódi QPU-hívás sem történhet.
- Ha az IBM token érvénytelen vagy hiányzik, az `IBMQpuEnergyEvaluator` azonnal elbukik a hálózat terhelése előtt.
- Nem támogatott vagy inaktív backend esetén a rendszer figyelmeztet vagy felajánlja a legkisebb hibájú aktív QPU-t.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
