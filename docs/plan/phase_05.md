# Fázis 5 — Batch-futtatás, aktív tér, statisztikai módszertan

| | |
|---|---|
| **Fázis** | 5 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-25 |
| **Státusz** | **Megvalósítás alatt** — állapot és folytatás: [`phase_05_allapot.md`](phase_05_allapot.md) (2026-09-25) |
| **Célverzió** | `v0.8.0` |
| **Előzmény** | [`phase_04.md`](phase_04.md), [`00_master_plan.md`](00_master_plan.md) 7. fejezet, v0.7.1 javítókör ([`CHANGELOG`](../../CHANGELOG.md)) |
| **Új ADR** | [`ADR-0007`](../adr/ADR-0007-batch-statisztika.md) — ismétlés, aggregálás, hibaköltségvetés |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Miért most, és miért így

Az alapterv Fázis 5-je „batch futtatás több molekulára”. A v0.7.1 javítókör
azonban két olyan tényt mért ki, amely a fázis *tartalmát* is meghatározza:

1. **Egyetlen zajos futás nem mérési eredmény, hanem egy minta.** Független
   mintavételi zaj mellett (v0.7.1) egy 8192 lövéses kiértékelés szórása
   11 mHa. Ez a H₂ teljes korrelációs energiájának (20.3 mHa) fele. Egy
   VQE-futás végeredménye ezért egy széles eloszlásból húzott érték: az
   optimalizáló visszaadott értéke egyetlen zajos húzás a végpontban (TR-F01B 6.3).
2. **A LiH/BeH₂ csak aktív térben kezelhető**, de az aktív tér választása
   önmagában hibaforrás. Az előzetes mérés (2. fejezet) szerint a „minimális”
   (2e,3o) tér a korrelációs energia 95–98%-át eldobja.

A Fázis 5 ezért három dolgot szállít: (A) aktívtér-támogatást a teljes
referencialánccal, (B) konfigurációs mátrixon futó batch-motort, (C) **ismétlésen
alapuló statisztikai módszertant**, amely minden zajos eredményt eloszlásként
kezel (átlag, szórás, SEM, konfidencia-intervallum), és a hibát forrásaira bontja.

---

## 2. Előzetes mérés — aktív terek (2026-09-25, `vqebd:0.7.1`)

STO-3G, parity + kétqubites redukció, UCCSD, SLSQP, statevector. A CASCI a PySCF
`mcscf.CASCI` független számítása; az L1 a qubit-Hamilton-operátor egzakt
legkisebb sajátértéke.

| Molekula | Aktív tér | Qubit | Pauli-tag | UCCSD param. | CX (dekomp.) | Csonkolás (CASCI − FCI) | Megtartott korreláció | L1 − CASCI | L2 − L1 | VQE idő |
|---|---|---|---|---|---|---|---|---|---|---|
| LiH | (2e,3o) | 4 | 52 | 8 | 172 | 19.32 mHa | 5.2% | 1.8e-15 | 4.4e-8 | 0.6 s |
| LiH | (2e,4o) | 6 | 95 | 15 | 560 | 18.56 mHa | 8.9% | 3.6e-15 | 8.8e-8 | 2.6 s |
| **LiH** | **(2e,5o) = frozen core** | **8** | 276 | 24 | 1276 | **0.23 mHa ✅** | **98.9%** | 6.2e-15 | 1.1e-7 | 13 s |
| LiH | (4e,5o) | 8 | 276 | 54 | 3284 | 18.36 mHa | 9.9% | 1.8e-15 | 1.2e-6 | 75 s |
| BeH₂ | (2e,3o) | 4 | 28 | 8 | 172 | 34.47 mHa | 1.6% | 5.3e-15 | 6.1e-12 | 0.3 s |
| BeH₂ | (4e,4o) | 6 | 55 | 26 | 1096 | 29.13 mHa | 16.8% | 7.1e-15 | 6.7e-7 | 6.4 s |
| BeH₂ | (4e,5o) | 8 | 156 | 54 | 3284 | 19.60 mHa | 44.0% | 0.0 | 2.4e-4 | 55 s |
| **BeH₂** | **(4e,6o) = frozen core** | **10** | 327 | 92 | 7080 | **0.34 mHa ✅** | **99.0%** | 3.9e-14 | 3.7e-4 | 220 s |

**Következtetések (a mesterterv Q3 nyitott kérdésére adott válasz):**

- **Az aktívtér-redukció helyes:** a CASCI (PySCF) és az L1 (Qiskit Nature +
  egzakt diagonalizáció) minden esetben ≤ 4·10⁻¹⁴ Ha-re egyezik — két független
  kódút.
- **A „tisztességes” aktív tér a frozen-core** (csak a mag 1s pályája
  befagyasztva): LiH (2e,5o), BeH₂ (4e,6o). A csonkolási hiba ezeknél a kémiai
  pontosság *alatt* marad.
- **A minimális (2e,3o) tér hardverközeli (4 qubit), de fizikailag gyenge:** a
  csonkolás 19–34 mHa, vagyis 12–22× a kémiai pontosság. A benchmark ezért
  **mindkettőt** futtatja, és a csonkolási hibát külön hibaforrásként közli.
- **Az UCCSD mélysége a zajos szintek fala:** már a 4 qubites (2e,3o) tér is
  ~172 CX (H₂: 4). A FakeManilaV2 ~1% CX-hibája mellett ez a várható érték
  teljes depolarizációját jelenti. A zajos szinteken (L3b, L4) a LiH/BeH₂ (2e,3o)
  futás ezt a **falat méri**, nem kémiai eredményt ad.

---

## 3. Hozzájárul-e a többféle teszt a pontossághoz? — a miért és a hogyan

A felhasználói követelmény kérdése: segíti-e a benchmark pontosságát, hogy
ugyanazt a feladatot több különböző módon futtatjuk. A válasz dimenziónként
különbözik, mert a hibák **két fajtája** eltérően viselkedik:

- **Statisztikus (véletlen) hiba:** független ismétléseknél független, átlagolva
  $\sigma/\sqrt{N}$ szerint csökken. Ez a **precizitás** (precision).
- **Szisztematikus hiba (torzítás):** minden ismétlésben ugyanaz, átlagolással
  **nem** csökken. Csak más *módszerrel* mérhető vagy korrigálható. Ez a
  **helyesség** (trueness). A kettő együtt adja a **pontosságot** (accuracy,
  ISO 5725-1).

| Dimenzió | Mit csökkent? | Miért | Hogyan mérjük | Hozzájárul? |
|---|---|---|---|---|
| **Ismétlés (seed)** | statisztikus hibát, $1/\sqrt{N}$ | a mintavételi zaj seedenként független (v0.7.1 óta **igazoltan**) | N = 1…20 seed, SEM(N) görbe (fig08) | ✅ **igen — a precizitáshoz** |
| **Független újramintavételezés θ_opt-ban** | a végső érték szórását (√K), és kizárja a kiválasztási torzítást | az optimalizáló végértéke egyetlen zajos húzás; az előzmények minimuma pedig kiválasztott (torzított) | K = 16 friss kiértékelés az optimumban | ✅ **igen — precizitás és helyesség** |
| **Platform (Qiskit/Cirq/qsim)** | semmit numerikusan | a hibák korreláltak (2·10⁻¹⁵) vagy szisztematikusak (qsim `complex64`) | L2 szórás platformok között | ❌ a pontossághoz · ✅ **a bizalomhoz** (M13) |
| **Referencia-lánc (FCI / CASCI / L1 / L2)** | semmit — **szétválasztja** a hibát | minden szint egyetlen új hibaforrást ad hozzá | hibaköltségvetés (fig09) | ✅ **az értelmezhetőséghez** |
| **Aktív tér (minimális vs. frozen core)** | a modellhibát | a csonkolás determinisztikus, mérhető | CASCI − FCI | ✅ **a helyességhez** (tudatos választás) |
| **Hibaenyhítés (ZNE)** | a torzítást, **szórásnövelés árán** | Lagrange-súlyok normája (Richardson: 2.28×) | torzítás + RMSE (TR-F03) | ⚖️ **csere** — lövésszámfüggő |
| **Kötéshossz-pásztázás** | semmit egy pontban | a hibák geometriafüggők (statikus korreláció nyújtott kötésnél) | hiba(R) görbe (fig07) | ✅ **az általánosíthatósághoz** |
| **Több molekula** | semmit egy molekulán | a skálázás és a mélységi fal csak több méreten látszik | qubit/CX vs. hiba | ✅ **az általánosíthatósághoz** |

> **A lényeg:** az ismétlés a *precizitást* javítja. A független módszerek
> (platform, referencialánc, aktív tér, újramintavételezés) a *helyességet*
> teszik mérhetővé. Az átlagolás a torzítást nem tünteti el; ezt a fázis
> ábrával (fig08: a torzítás mint vízszintes padló) és teszttel (AC-5.6) igazolja.

---

## 4. Célkitűzések

| # | Cél | Szállítandó |
|---|---|---|
| G1 | Aktívtér-támogatás teljes referencialánccal | `ActiveSpaceSpec`, `energy_offset`, CASCI-referencia (L0′) |
| G2 | Batch-motor konfigurációs mátrixra | `vqebd.batch`: mátrix-kifejtés, determinisztikus `run_id`, folytathatóság |
| G3 | Statisztikai aggregálás | `vqebd.stats`: átlag, szórás, SEM, t-alapú 95% CI, RMSE, kémiai pontossági besorolás |
| G4 | Torzításmentes végső energia zajos szinteken | független újramintavételezés (K friss kiértékelés θ_opt-ban) |
| G5 | Hibaköltségvetés | csonkolás / leképezés / ansatz / zaj-torzítás / statisztikus hiba |
| G6 | Adatséma v2 | új oszlopok + **v1 → v2 migráció** (append-only elv megmarad) |
| G7 | Vizualizáció | fig07 (PES + csonkolás), fig08 (SEM vs. N + torzítás-padló), fig09 (hibaköltségvetés) |

---

## 5. Architektúra

### 5.1 Az energiaeltolás szétválasztása (G1) — a legkockázatosabb lépés

Aktív térben a Hamilton-operátor konstans tagja **két részből** áll: a
magtaszításból és a befagyasztott (inaktív) elektronok energiájából
(`ActiveSpaceTransformer` → `hamiltonian.constants`). A kód jelenleg 23 helyen
`nuclear_repulsion_energy`-t használ eltolásként. Aktív térben ez **csendben
hibás teljes energiát** adna, nagyságrendileg az inaktív energia mértékével (LiH:
~−7 Ha).

**Döntés:** új mező, `energy_offset` = Σ `hamiltonian.constants`. A
`nuclear_repulsion_energy` megmarad a valódi magtaszításnak (tárolásra); minden
**eltolásként** használt hely az `energy_offset`-re vált. Teljes térben a kettő
bitre egyenlő — ezt regressziós teszt őrzi (AC-5.2), így a Fázis 1–4 eredményei
változatlanok.

### 5.2 Referencialánc aktív térben

```
 L0   FCI (PySCF, teljes tér)                     fizikai igazság
  │   ← aktívtér-csonkolás (determinisztikus)      = CASCI − FCI
 L0′  CASCI (PySCF mcscf, aktív tér)              független kódút
  │   ← leképezés                                  = L1 − CASCI  (≈ 1e-14)
 L1   egzakt diagonalizáció (qubit-H, aktív tér)
  │   ← ansatz + optimalizáló                      = L2 − L1
 L2   VQE állapotvektor (3 platform)
  │   ← zaj-torzítás (szisztematikus)              = átlag(L3) − L2
 L3   VQE zajos (N seed → eloszlás)
  │   ← statisztikus hiba                          = SEM = s/√N
 L4   hibaenyhített (torzítás ↓, szórás ↑)
```

A **módszer** minőségét az L1-hez mért hiba méri (ennél jobbat a VQE az adott
aktív térben elvileg sem érhet el). A **fizikai** hibát az L0-hoz mért adja. A
rekord mindkettőt tárolja; a kémiai pontossági jelző az L0-hoz mér (fizikai
jelentés), a módszerjelző az L1-hez.

### 5.3 Új és módosuló modulok

```
src/vqebd/
├── config.py              + ActiveSpaceSpec(num_electrons, num_spatial_orbitals); VQEConfig.active_space
├── chemistry/problem.py   + aktív tér transzformáció, energy_offset, inactive_energy
├── chemistry/reference.py + casci_energy() (PySCF mcscf), ReferenceEnergies.casci
├── chemistry/mapping.py   ~ QubitHamiltonian.energy_offset
├── vqe/runner.py          ~ eltolás: energy_offset; + reestimate (G4)
├── vqe/result.py          ~ energy_offset, casci, reestimate-mezők
├── stats.py               ÚJ — aggregálás, CI, besorolás, hibaköltségvetés
├── batch/                 ÚJ
│   ├── spec.py            — BatchSpec, MatrixAxis; előre definiált mátrixok (preset)
│   ├── expand.py          — mátrix → futáslista, determinisztikus run_id
│   └── run.py             — végrehajtás, folytatás (meglévő run_id kihagyása), hibaizoláció
└── storage/schema.py      ~ SCHEMA_V2 + migrate_v1_to_v2()
scripts/run_batch.py       ÚJ — CLI: --preset, --db, --out, --max-runs
```

### 5.4 Determinisztikus `run_id`

`run_id = f"{batch_id}:{config_fingerprint}:r{repeat:02d}"`. Az ismétlés seedje
`master_seed + repeat`. Egy megszakadt batch újraindítva a meglévő `run_id`-kat
kihagyja (folytathatóság), és ugyanazt az eredményt adja, mint egy megszakítás
nélküli futás (AC-5.5).

### 5.5 Végső energia zajos szinteken (G4)

Két kézenfekvő végső érték is hibás volna:

- Az optimalizáló **visszaadott** értéke egyetlen zajos húzás. SciPy COBYLA-nál
  ez a végpontban mért utolsó érték (mérve 3 seeden: `fun` = az előzmények utolsó
  eleme, nem a minimuma). Torzítatlan, de σ ≈ 11 mHa szórású.
- Az előzmények **minimuma** kiválasztási torzítást hordoz, mert a kedvező húzást
  választja. H₂-n mérve: −20…−37 mHa, vagyis a variációs határ alá visz.

A végső energia ezért **K = 16 friss, független kiértékelés** θ_opt-ban. A
kiértékelő seedelt RNG-je továbblép, így a minták determinisztikusak, de az
optimalizáció közbeni húzásoktól függetlenek. A rekord mind a négy mennyiséget
tárolja: az optimalizáló végértékét, az előzmény-minimumot, az újramintavételezett
átlagot és ennek SEM-jét. A statisztika az újramintavételezett értékre épül; az
előzmény-minimum és az átlag különbsége a „minimumot közlő” stratégia mért torzítása.

### 5.6 Statisztikai aggregálás (G3)

Csoport = azonos konfiguráció, különböző seed. Kiszámított mennyiségek:
átlag, korrigált tapasztalati szórás, SEM, **Student-t alapú 95% CI**, medián,
RMSE a referenciához, torzítás.

**Kémiai pontossági besorolás** (a ±1.6 mHa sávhoz mérve, a CI alapján):

| Besorolás | Feltétel | Jelentés |
|---|---|---|
| `confirmed` | a teljes CI a sávon belül | statisztikailag igazoltan kémiailag pontos |
| `consistent` | a CI metszi a sávot, de nincs benne teljesen | összeférhető, de nem igazolt — több ismétlés kell |
| `excluded` | a CI teljesen a sávon kívül | statisztikailag igazoltan NEM kémiailag pontos |
| `undetermined` | N = 1, **zajos** backend | egyetlen zajos minta nem minősíthető |

Egzakt (zajmentes) backend egyetlen értékénél a CI egy pontra fajul, így a
besorolás `confirmed` vagy `excluded`. Ez helyes, mert nincs statisztikus
bizonytalanság. A zajos esetekre a „kémiailag pontos-e?” kérdés így
**háromállapotú** választ kap az eddigi bináris helyett. A bináris válasz egyetlen
zajos mintán félrevezető volt (lásd L5: `undetermined`).

---

## 6. A batch-mátrix (preset-ek)

### 6.1 `f5-deterministic` — L2, platformdimenzió

| Molekula / aktív tér | Kötéshosszak (Å) | Platformok | Optimalizáló | Futás |
|---|---|---|---|---|
| H₂ (teljes, 2 q) | 0.5, 0.735, 1.0, 1.5, 2.0, 2.5 | Qiskit, Cirq, qsim | SLSQP / SLSQP / Powell | 18 |
| LiH (2e,3o) (4 q) | 1.2, 1.595, 2.2, 3.0 | Qiskit, Cirq, qsim | – " – | 12 |
| LiH (2e,5o) (8 q) | 1.2, 1.595, 2.2, 3.0 | Qiskit, Cirq | SLSQP | 8 |
| LiH (2e,5o) (8 q) | 1.595 | qsim | Powell | 1 |
| BeH₂ (2e,3o) (4 q) | 1.0, 1.33, 1.8 | Qiskit, Cirq, qsim | – " – | 9 |
| BeH₂ (4e,6o) (10 q) | 1.33 | Qiskit, Cirq | SLSQP | 2 |
| | | | **összesen** | **50** |

**Miért szűkített a qsim a nagy aktív tereken?** A qsim `complex64` pontossága
miatt deriváltmentes optimalizáló kell (ADR-0006), a Powell költsége viszont a
paraméterszámmal meredeken nő. A tervezéskor mérve (LiH (2e,5o), 24 paraméter):
**7178 kiértékelés, 486 s**, a hiba pedig 2.8·10⁻⁵ Ha (3 → 8 → 24 paraméter:
3·10⁻⁸ → 1.7·10⁻⁶ → 2.8·10⁻⁵ Ha). A 92 paraméteres BeH₂ (4e,6o) órákig tartana.
A qsim ezért a frozen-core LiH-n csak egyensúlyi geometriában fut, a BeH₂
(4e,6o)-n nem. Ez maga is benchmark-eredmény: az egyszeres pontosság ára a
paraméterszámmal nő.

### 6.2 `f5-statistical` — L3a/L3b/L4, ismétlésdimenzió

| Molekula | R (Å) | Backend | Mitigáció | Seed (N) | Újramintavétel (K) | Futás |
|---|---|---|---|---|---|---|
| H₂ | 0.735, 1.5 | `qiskit_aer_shot` | none | 20 | 16 | 40 |
| H₂ | 0.735, 1.5 | `qiskit_aer_noisy` | none, zne_local/linear, zne_local/richardson | 20 | 16 | 120 |
| LiH (2e,3o) | 1.595 | `qiskit_aer_shot`, `qiskit_aer_noisy` | none | 10 | 16 | 20 |
| | | | | | **összesen** | **180** |

Az optimalizáló a zajos szinteken COBYLA (deriváltmentes, ADR-0006), `maxiter=300`.

### 6.3 Futásidő-becslés

A statevector-mérések (2. fejezet) alapján: `f5-deterministic` ≈ 25–40 perc (a
BeH₂ (4e,6o) három platformon a domináns tag), `f5-statistical` ≈ 10–20 perc. A
pontos értékeket a TR-F05 rögzíti.

### 6.4 Hardveres kiegészítés (5.H) — **csak felhasználói jóváhagyással**

H₂ PES a valódi `ibm_kingston`-on: 5 kötéshossz × {`resilience_level` 0, 1} ×
1 kiértékelés θ*(R)-ben. Becsült kvóta: 10 job × ~15 QPU-s ≈ **150 QPU-s** a 600
QPU-s / 28 nap Open Plan keretből. **Nem része az elfogadási kritériumoknak.** Csak
akkor fut, ha a felhasználó kifejezetten jóváhagyja (`VQEBD_ALLOW_HARDWARE=true`).
Minden job a v0.7.1 óta rögzített bizonytalansággal és mitigációs metaadattal
tárolódik.

**Megvalósítás és állapot (2026-09-25).**

- **Jóváhagyva** (a felhasználó, 2026-09-25).
- **Kvótatakarékosabb kialakítás, mint a becslés:** a H₂ UCCSD-áramköre minden
  kötéshosszon unitérekvivalens (ellenőrizve: 3 véletlen θ-ra `allclose`). Ezért
  szintenként **egyetlen job** fut 5 PUB-bal: 2 job a 10 helyett, becsült igény
  ≤ 120 QPU-s. Eszköz: `scripts/run_hardware_pes.py`,
  `IBMQpuEnergyEvaluator.evaluate_observables`.
- **Beküldés előtti kvótaellenőrzés** (`vqebd.hardware`): a `service.usage()` szerint
  630 / 600 s felhasznált, `usage_limit_reached = true`, újra elérhető
  **2026-10-21**. A szkript ezért `--dry-run` módban is megtagadja a beküldést
  (exit 2). **Job nem keletkezett.**
- **Elhalasztva** a kvóta visszatéréséig. Futtatás:
  `VQEBD_ALLOW_HARDWARE=true python scripts/run_hardware_pes.py`

---

## 7. Adatséma v2 (G6)

Új, nullázható oszlopok (a v1 rekordok értéke `NULL` — a jelentésük: „nem
aktív tér / nem batch”):

| Oszlop | Típus | Jelentés |
|---|---|---|
| `active_electrons`, `active_orbitals` | INTEGER | az aktív tér; `NULL` = teljes tér |
| `casci_ha` | REAL | L0′ referencia |
| `energy_offset_ha` | REAL | magtaszítás + inaktív energia |
| `batch_id`, `repeat_index` | TEXT, INTEGER | a batch és az ismétlés azonosítója |
| `optimizer_final_ha` | REAL | az optimalizáló visszaadott értéke (egyetlen zajos húzás) |
| `optimizer_history_min_ha` | REAL | az optimalizálás közbeni kiértékelések minimuma (kiválasztott, torzított) |
| `reestimate_mean_ha`, `reestimate_sem_ha`, `reestimate_n` | REAL, REAL, INTEGER | G4 |

**Migráció:** `ALTER TABLE … ADD COLUMN` + `meta.schema_version = 2`, egyetlen
tranzakcióban. Az append-only elv megmarad: meglévő sort nem módosít. Egy v1
adatbázis megnyitása automatikusan migrál, és a migrációt a `meta` táblában
naplózza (`migrated_v1_to_v2_at`).

---

## 8. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-5.1** | Aktív térben L1 = CASCI (PySCF) ≤ 1·10⁻¹⁰ Ha pontossággal LiH (2e,3o), (2e,5o) és BeH₂ (2e,3o) esetén | validációs teszt |
| **AC-5.2** | Teljes térben `energy_offset == nuclear_repulsion_energy` bitre; a Fázis 1 H₂-eredmények változatlanok | regressziós teszt |
| **AC-5.3** | Aktív térben a teljes energia helyes: L2 − L1 < 1.6 mHa LiH (2e,3o)-ra mindhárom platformon | validációs teszt |
| **AC-5.4** | A batch-kifejtés determinisztikus: azonos spec → azonos futáslista és `run_id`-k | egységteszt |
| **AC-5.5** | Megszakított batch folytatása ugyanazt az adatbázis-tartalmat adja, mint egy megszakítás nélküli futás | integrációs teszt |
| **AC-5.6** | Az ismétlés a statisztikus hibát csökkenti, a torzítást nem: SEM(N) ∝ N^−½ (log-log meredekség −0.5 ± 0.15), a torzítás N-től független | validációs teszt + fig08 |
| **AC-5.7** | A statisztikai függvények ismert eloszláson helyesek (CI-lefedettség ~95%, besorolás határesetei) | egységteszt |
| **AC-5.8** | Az újramintavételezett végső energia torzítatlan: zajos backenden |átlag − egzakt zajos várható érték| < 4·SEM | validációs teszt |
| **AC-5.9** | Séma v1 → v2 migráció: egy v1 adatbázis megnyitva migrál, a v1 rekordok bitre változatlanok | egységteszt |
| **AC-5.10** | Az `f5-deterministic` és `f5-statistical` batch lefut; az eredmények, ábrák és a TR-F05 generált adatokból készülnek | végrehajtás + TR-F05 |

---

## 9. Tesztelési terv (összefoglaló; részletesen: TP-F05)

- **1. kör — funkcionális:** aktív tér, energy_offset, CASCI, batch-kifejtés, statisztika.
- **2. kör — negatív és robusztussági:** érvénytelen aktív tér (több elektron,
  mint amennyi pálya elfér; páratlan elektronszám zárt héjon); ismeretlen
  preset; sérült/idegen verziójú adatbázis; egy futás kivétele nem állítja le a batchet.
- **3. kör — keresztvalidáció:** CASCI ↔ L1; platformok ↔ egymás aktív térben;
  statisztika ↔ szintetikus, ismert eloszlás; migráció ↔ friss v2 adatbázis.

---

## 10. Amit ez a fázis NEM tartalmaz

- **Heron-zajmodell** (`ibm_kingston` kalibrációjából, kvóta nélkül építhető) —
  az L3b ↔ L5 generációs egyezéséhez. A pinelt `qiskit-ibm-runtime` 0.41.1-ben
  nincs Heron FakeBackend (mérve: az egyetlen >100 qubites a FakeWashingtonV2,
  Eagle r1). → Fázis 6 jelölt.
- **Szimulált readout-hiba** (Sampler-alapú becslő) — az Aer Estimator nem
  modellezi (ADR-0003, 1. kieg.). → Fázis 6 jelölt.
- **Hardverhatékony ansatz** a mélységi fal ellen — a benchmark jelenleg az UCCSD-t méri. → Fázis 6+ jelölt.
- **Újrapróbálkozási politika, ütemezés** — Fázis 6 (alapterv).

---

## 11. Kilépési feltétel

AC-5.1 … AC-5.10 teljesül; TP-F05 és TR-F05 elkészült; README (HU/EN), CHANGELOG,
`v0.8.0`; minőségi kapuk (ruff, mypy strict, teljes tesztkészlet) zöldek.

---

## 12. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-25 | Első változat, az aktívtér-előmérés (2. fejezet) alapján |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
