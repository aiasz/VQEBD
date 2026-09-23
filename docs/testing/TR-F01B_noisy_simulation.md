# TR-F01B — Fázis 1b mérési jegyzőkönyve (Véges lövésszámú és zajos szimuláció)

| | |
|---|---|
| **Azonosító** | TR-F01B |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1b — Véges lövésszámú és zajos szimuláció (L3a / L3b) |
| **Vizsgált verzió** | `0.3.0` |
| **Tesztterv** | [`TP-F01B`](TP-F01B_noisy_simulation.md) |
| **Státusz** | **Lezárva — mind a 9 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

| | |
|---|---|
| Elfogadási kritériumok | **9 / 9 teljesült** |
| Automatikus tesztek | **366 futott, 366 zöld, 0 hiba** |
| L3a szimuláció (lövészaj) | `qiskit_aer_shot` (8192 shot, precision $1/\sqrt{8192}$) |
| L3b szimuláció (eszközzaj) | `qiskit_aer_noisy` (`FakeManilaV2` kalibrációs zajmodell) |
| Determinizmus | Bitre azonos energiasorozat azonos `SeedSet` mellett |
| ISA Transzpiláció és Layout | `observable.apply_layout(isa_circuit.layout)` működik (5 qubit) |
| Gradiens-védelem | SLSQP/gradiens-alapú optimalizálókra `RuntimeWarning` aktiválva |

---

## 2. Referenciaszintek és mérési eredmények ($H_2$, $R = 0.735\ \text{Å}$)

| Szint | Backend | Optimalizáló | Energia (Hartree) | Hiba az L1-hez (Ha) | Megjegyzés |
|---|---|---|---|---|---|
| **L0** | PySCF Full CI | — | -1.1373060358 | 0.0 | Fizikai referencia |
| **L1** | Egzakt diag. | — | -1.1373060358 | $1.33 \times 10^{-15}$ | Leképezési ellenőrzés |
| **L2** | `qiskit_statevector` | SLSQP | -1.1373060358 | $1.49 \times 10^{-15}$ | Egzakt állapotvektor |
| **L3a** | `qiskit_aer_shot` | COBYLA (8192 shot) | -1.1213780162 | $+1.59 \times 10^{-2}$ | Véges mintavételi zaj |
| **L3b** | `qiskit_aer_noisy` | COBYLA (FakeManila) | -1.0938632143 | $+4.34 \times 10^{-2}$ | Kapuhibák + T1/T2 relaxáció |

---

## 3. Tesztesetek kiértékelése

| Eset | AC | Ellenőrzés | Eredmény |
|---|---|---|---|
| **TC-1B01** | AC-1B.1 | Aer shot evaluator L3a energiát ad és jelenti a `shots` (8192) értéket. | ✅ Teljesült |
| **TC-1B02** | AC-1B.2 | Aer noisy evaluator `FakeManilaV2` zajprofilt és L3b szintet jelent. | ✅ Teljesült |
| **TC-1B03** | AC-1B.3 | ISA áramkör és observable qubit-száma egyezik; layout alkalmazva. | ✅ Teljesült |
| **TC-1B04** | AC-1B.4 | Két azonos L3a futás bitre azonos energiát ad. | ✅ Teljesült |
| **TC-1B05** | AC-1B.4 | Két azonos L3b futás bitre azonos energiát ad. | ✅ Teljesült |
| **TC-1B06** | AC-1B.5 | Backend váltás módosítja a `config.fingerprint()` értékét. | ✅ Teljesült |
| **TC-1B07** | AC-1B.6 | SLSQP figyelmeztetést ad zajos platformon, COBYLA elfogadott. | ✅ Teljesült |
| **TC-1B08** | AC-1B.7 | CLI mindkét backenddel működik; L3a/L3b címkék megjelennek. | ✅ Teljesült |
| **TC-1B09** | AC-1B.8 | Teljesen offline, FakeBackendet használ, nincs IBM token igény. | ✅ Teljesült |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
