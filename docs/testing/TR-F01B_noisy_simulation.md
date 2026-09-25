# TR-F01B — Fázis 1b mérési jegyzőkönyve (Véges lövésszámú és zajos szimuláció)

| | |
|---|---|
| **Azonosító** | TR-F01B |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.1.0 (javítási melléklet: 6. szakasz) |
| **Dátum** | 2026-09-23 · 2026-09-25 (6. szakasz, v0.7.1) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1b — Véges lövésszámú és zajos szimuláció (L3a / L3b) |
| **Vizsgált verzió** | `0.3.0` |
| **Tesztterv** | [`TP-F01B`](TP-F01B_noisy_simulation.md) |
| **Státusz** | **Lezárva — 9/9 AC teljesült; az L3a/L3b számértékek javítva (6. szakasz)** |

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

## 6. Javítási melléklet (v0.7.1, 2026-09-25)

### 6.1 A hiba

A 2. szakasz L3a/L3b értékei a v0.3.0–v0.7.0 kóddal készültek, és egy
mintavételi hibát hordoznak (részletesen: TR-F03 v1.1.0, J4). Az Aer
`EstimatorV2` minden `run()` hívásnál `numpy.random.default_rng(seed_simulator)`-t
hozott létre, és abból húzott `N(evs, precision)`-t. Rögzített seed mellett
tehát **minden kiértékelés ugyanazt a z·σ eltolást kapta**:

- az L3a „lövészaj-hibája” (+15.93 mHa) valójában **állandó torzítás** volt
  (z ≈ 1.44, σ = 11.05 mHa), a COBYLA pedig egy eltolt, **zajmentes** felületen
  konvergált θ*-hoz;
- a TC-1B04/05 determinizmus-tesztek ettől függetlenül helyesek voltak, de a
  „véges mintavétel” modellt nem fedték le.

A v0.7.1 az egzakt várható értékhez saját, hívásonként továbblépő,
`seeds.simulator`-ból indított generátorral ad zajt. A futás így továbbra is
bitre determinisztikus, a zaj viszont kiértékelésenként független; ezt a
TC-1B10 regressziós tesztek őrzik (300 minta szórása σ ± 15%-on belül).

### 6.2 Újramérés azonos konfigurációval

Konfiguráció (a v0.7.0 image-ben pontosan reprodukálva):
`python -m vqebd --backend <b> --optimizer COBYLA`
(`maxiter=300`, seed 20260922, 8192 lövés, `FakeManilaV2`).

| Szint | v0.7.0 (hibás mintavétel) | v0.7.1 (független zaj) | Kiértékelések |
|---|---|---|---|
| **L3a** `qiskit_aer_shot` | −1.1213780162 (+15.93 mHa) | **−1.1105387727 (+26.77 mHa)** | 116 → 78 |
| **L3b** `qiskit_aer_noisy` | −1.0938632143 (+43.44 mHa) | **−1.0954609696 (+41.85 mHa)** | 118 → 79 |

### 6.3 Értelmezés

- **A H₂ korrelációs energiája (20.3 mHa) mindössze ~1.8σ** egyetlen, 8192
  lövéses kiértékelés szórásához képest. Ilyen jel/zaj arány mellett a COBYLA
  bizalmi tartománya a zajt követi, és a HF-közeli régióban áll meg (+26.8 mHa ≈
  HF-energia + zaj). Ez **fizikai korlát**, nem optimalizáló-hiba.
- Egyetlen zajos VQE-futás végeredménye **egy minta** egy széles eloszlásból.
  Ugyanez a konfiguráció `maxiter=50`-nel (a Fázis 4 exportja) −4.82 mHa-t adott,
  vagyis a variációs határ **alá** került. Ez a zajos célfüggvény minimumának
  kiválasztási torzítása: az optimalizáló a kedvező zajhúzásokat „választja ki”.
- **Következmény a benchmarkra:** zajos szinteken a végső energiát
  (1) a θ-ban **független újramintavételezéssel**, (2) **több seed** átlagaként,
  szórással/SEM-mel kell közölni. Ez a Fázis 5 módszertani alapja
  ([`phase_05.md`](../plan/phase_05.md)).

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
