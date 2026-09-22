# VQEBD — Bővített mesterterv

| | |
|---|---|
| **Projekt** | VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard |
| **Dokumentum** | `docs/plan/00_master_plan.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Státusz** | Elfogadott — Fázis 0 végrehajtása engedélyezett |
| **Alapdokumentum** | `quantum-benchmark-projektterv.md` (v0, 2026-09-22) |
| **Licenc** | MIT |

---

## 1. Dokumentum célja és viszonya az alaptervhez

Az alapterv (`quantum-benchmark-projektterv.md`) 10 fázisban írja le a projektet, fázisonként
célokkal, feladatokkal és elfogadási kritériumokkal. **Ez a dokumentum nem helyettesíti, hanem
bővíti azt**: rögzíti azokat a konkrét, mért adatokon nyugvó műszaki döntéseket, amelyeket az
alapterv szándékosan nyitva hagyott (pontos verziók, API-k, algoritmus-variánsok, adatséma,
hibahatárok).

A bővítés alapelve: **az alapterv minden elfogadási kritériuma érvényben marad, és
szigorodhat, de nem lazulhat.**

### 1.1 A bővítés forrása: előzetes műszaki felderítés (spike)

A terv részleteit nem feltételezésekre, hanem **négy körös, konténerben végrehajtott,
reprodukálható mérésre** alapoztuk. A teljes mérési jegyzőkönyv:
[`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md).

A spike öt olyan tényt tárt fel, amely az alapterv naiv értelmezése esetén a projekt
2–3. fázisában bukott volna meg. Ezeket az 5. és 6. fejezet részletezi.

---

## 2. Rendszercél és nem-cél

### 2.1 Cél (scope)

Konténerizált, reprodukálható Python-rendszer, amely:

1. kis molekulák (H2, LiH, BeH2) elektronszerkezeti alapállapoti energiáját számolja
   VQE-vel (Variational Quantum Eigensolver);
2. ugyanazt a számítást **három referenciaszinten** futtatja — egzakt (klasszikus),
   zajmentes szimulátor, zajos szimulátor/valódi QPU;
3. **hibaenyhítési stratégiákat** (error mitigation) alkalmaz és **egymással is
   összeveti** őket;
4. minden eredményt **strukturáltan, verziózottan, a szoftverkörnyezet rögzítésével**
   tárol;
5. az eredményeket interaktív dashboardon vizualizálja;
6. publikálható, DOI-val hivatkozható közösségi benchmark.

### 2.2 Nem-cél (out of scope)

| Nem célunk | Indoklás |
|---|---|
| Új hibaenyhítési módszer kutatása | A projekt *benchmark*, nem módszertani kutatás. |
| Nagy molekulák (>14 qubit) | Sem a szimulátor, sem a mai QPU nem ad értelmes eredményt. |
| Hibatűrő (fault-tolerant) algoritmusok | NISQ-korszakra szabott projekt. |
| Gerjesztett állapotok, dinamika | Későbbi ciklus (Fázis 10) lehet. |
| Saját optimalizáló-kutatás | SciPy-implementációkat használunk, referenciával. |

### 2.3 Tudományos pontossági cél

A kvantumkémiában a **kémiai pontosság** (chemical accuracy) a bevett hibahatár:

> **1 kcal/mol = 1.5936 × 10⁻³ Hartree ≈ 1.6 mHa**

Ez a projekt minden energiakülönbségre vonatkozó elfogadási kritériumának
viszonyítási alapja. (Forrás: Helgaker–Jørgensen–Olsen, *Molecular Electronic-Structure
Theory*; lásd [`docs/references.md`](../references.md).)

---

## 3. Architektúra

### 3.1 Rétegmodell (az alapterv háromrétegű modelljének finomítása)

```
┌───────────────────────────────────────────────────────────────────────┐
│  BEMUTATÁSI RÉTEG                                                     │
│  dashboard/  —  Streamlit                                             │
│  Csak olvas. Nem futtat kvantumszámítást. Nem ír adatbázist.          │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │ load_results()  (read-only)
┌────────────────────────────────┴──────────────────────────────────────┐
│  ADATTÁROLÁSI RÉTEG                                                   │
│  src/vqebd/storage/  —  SQLite (kanonikus) + CSV/Parquet (export)     │
│  Sémaverziózott. Append-only. Minden rekord rögzíti a környezetét.    │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │ save_result(record)
┌────────────────────────────────┴──────────────────────────────────────┐
│  VÉGREHAJTÁSI RÉTEG                                                   │
│                                                                       │
│  src/vqebd/chemistry/  molekula → fermionos H → qubit-Hamiltoni       │
│                        (PySCF + Qiskit Nature)                        │
│  src/vqebd/vqe/        ansatz + saját optimalizáló-hurok              │
│                        (Qiskit V2 primitívek + SciPy)                 │
│  src/vqebd/mitigation/ hibaenyhítési stratégiák (pluginok)            │
│  src/vqebd/backends/   backend-absztrakció (egzakt / Aer / QPU)       │
│  src/vqebd/experiment/ kombinációs mátrix bejárása, batch futtatás    │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 Alapelv: a négy referenciaszint

A benchmark értelmezhetősége azon áll, hogy **minden mérésnek van egy nála
megbízhatóbb referenciája**. Négy szintet definiálunk:

| Szint | Jelölés | Mit ad | Zajforrás | Szerepe |
|---|---|---|---|---|
| **L0** | `fci` | Klasszikus egzakt megoldás (Full CI, PySCF) | nincs | A "fizikai igazság" az adott bázison. |
| **L1** | `exact_diag` | A **qubit**-Hamiltoni egzakt legkisebb sajátértéke | nincs | Igazolja, hogy a leképezés (mapping) helyes: L1 ≡ L0. |
| **L2** | `statevector` | VQE zajmentes állapotvektoron | csak ansatz-korlát | Megadja, mennyit veszítünk az ansatz miatt. |
| **L3a** | `shot` | VQE véges lövésszámmal, zaj nélkül | statisztikus | Elkülöníti a shot-zajt a hardverzajtól. |
| **L3b** | `noisy` / `qpu` | VQE zajos szimulátoron vagy QPU-n | statisztikus + hardver | A tényleges mérés. |

**Ez az alapterv legfontosabb bővítése.** Az alapterv három értéket említ (szimulált /
nyers hardver / mitigált hardver). A gyakorlatban ez nem elég a hibák szétválasztásához:
ha L3b eltér L0-tól, e három érték alapján nem tudjuk megmondani, hogy a leképezés, az
ansatz, a shot-zaj vagy a hardverzaj a felelős. Az L0–L3b lánc **mindegyik hibaforrást
külön számszerűsíti**:

```
E_L0 ──(mapping hiba)── E_L1 ──(ansatz hiba)── E_L2 ──(shot zaj)── E_L3a ──(hardver zaj)── E_L3b
                                                                                    │
                                                                        (hibaenyhítés)│
                                                                                    ▼
                                                                                E_mitigated
```

**Mért igazolás (spike, TR-000):** H2 / 0.735 Å / STO-3G esetén
`E_L0 = −1.13730604 Ha`, `E_L1 = −1.13730604 Ha` (eltérés 4.4 × 10⁻¹⁶),
`E_L2 = −1.13730604 Ha` (eltérés 7.6 × 10⁻¹⁵). Azaz a mapping és az UCCSD-ansatz
H2-re **gépi pontossággal egzakt** — minden ennél nagyobb eltérés zajból származik.

---

## 4. Technológiai stack — a döntés és a kényszer

### 4.1 A kritikus felfedezés

> **A Mitiq 0.47.0 (a legfrissebb kiadás, 2025-09-09) `numpy<2.0.0`-ra épül, a Qiskit 2.x
> viszont `numpy>=2.0`-t követel. A kettő egy környezetben nem telepíthető.**

Gépi bizonyíték (pip resolver, python:3.11-slim konténer):

```
ERROR: ResolutionImpossible
    qiskit 2.5.2 depends on numpy<3 and >=2.0
    mitiq 0.47.0 depends on numpy<2.0.0 and >=1.22.0
```

A Mitiq `qiskit` extrája ezt meg is erősíti: `qiskit~=1.4.2`, `qiskit-aer~=0.17.0`.

### 4.2 A választott stack (a Mitiq-kompatibilis metszet)

| Csomag | Verzió | Miért pont ez |
|---|---|---|
| Python | **3.11** | Mitiq: `>=3.10,<3.13`. A 3.11 minden függőségnél bizonyított. |
| numpy | **1.26.4** | A Mitiq `<2.0` korlátja miatt; az utolsó 1.x kiadás. |
| scipy | **1.13.1** | numpy 1.26-tal bizonyítottan működő párosítás. |
| qiskit | **1.4.6** | Az utolsó, numpy 1.x-et engedő ág (2026-06-12, aktívan karbantartott). |
| qiskit-aer | **0.17.2** | `qiskit>=1.1.0`; zajos szimuláció + `from_backend`. |
| qiskit-nature | **0.7.2** | A 0.8.0 `numpy>=2`-t követel → kizárva. |
| qiskit-algorithms | *(nem pinnelt)* | A qiskit-nature tranzitív függősége; **nem hívjuk** (ADR-0002), ezért nem pinneljük. A Fázis 1 image-ében 0.4.0-ra oldódik fel; a tényleges verziót a `requirements.lock` rögzíti. |
| qiskit-ibm-runtime | **0.41.1** | Az utolsó, `qiskit>=1.4.1`-et engedő; **támogatja az `ibm_quantum_platform` csatornát**. |
| mitiq | **0.47.0** | Referencia-implementáció a ZNE keresztvalidációhoz. |
| **ply** | **3.11** | **Rejtett függőség** — a Mitiq qiskit↔cirq konverziója nélküle `ModuleNotFoundError`. |
| pyscf | **2.14.0** | Elektronszerkezeti driver + FCI referencia (L0). |
| cirq-core | 1.4.1 | A Mitiq belső áramkör-reprezentációja (tranzitív). |

Ez a metszet **empirikusan feloldva és 13+8+11 lépéses funkcionális próbán átment**
(TR-000).

### 4.3 A `ply` eset — miért nem elég a `pip install mitiq`

A `mitiq[qiskit]` extra tartalmazza a `ply==3.11`-et, **de egyúttal
`qiskit-ibm-runtime~=0.37.0`-t is lepinnelne**, ami már nem támogatja az aktuális
IBM Quantum Platformot. Ezért a `ply==3.11`-et **közvetlen függőségként** vesszük fel,
az extrát nem használjuk. Ez a `requirements.txt`-ben kommentben is szerepel, mert
egy jövőbeli "takarítás" könnyen kitörölné.

### 4.4 Verziórögzítési politika

- A `requirements.txt` **kizárólag `==` pinneket** tartalmaz (tranzitív függőségekkel
  együtt, `requirements.lock` formájában), mert a reprodukálhatóság a projekt terméke.
- A Docker image **digest-tel** hivatkozik az alap-image-re, nem csak tag-gel.
- Minden eredményrekord eltárolja a futáskori `qiskit`, `qiskit-nature`, `qiskit-aer`,
  `mitiq`, `pyscf`, `numpy` verziót (Fázis 4 sémája).

---

## 5. A spike öt kritikus megállapítása

Ezek nélkül a projekt a 2–3. fázisban elakadt volna. Mindegyik mért, nem feltételezett.

### M1 — Mitiq × Qiskit 2.x inkompatibilitás
Lásd 4.1. **Következmény:** a stack Qiskit 1.4.6-ra rögzítve. **Kockázat:** a Qiskit 1.4
ág egyszer elavul. **Ellenintézkedés:** ADR-0002 (saját VQE-hurok V2 primitívekkel) a
kódot előre-hordozhatóvá teszi.

### M2 — A `ply` rejtett függőség
Lásd 4.3. A hiba `ModuleNotFoundError: No module named 'ply'` formában, **csak a Mitiq
qiskit-interfészének első használatakor** jelentkezik — vagyis pont a Fázis 3-ban,
a legdrágább ponton.

### M3 — A Mitiq konverzió eldobja az inaktív qubiteket
Mért: egy 5 qubites ISA-áramkör (FakeManilaV2-re transzpilálva, 2 aktív qubittel)
`from_qiskit()` után **2 qubites** cirq-áramkör lesz. Visszakonvertálva szintén 2 qubites.
Az 5 qubites, layout-tal ellátott observable ezért nem illeszkedik:

```
ValueError: The number of qubits of the circuit (2) does not match
            the number of qubits of the ()-th observable (5).
```

**Következmény:** a Mitiq-alapú ZNE-t **logikai szinten** kell alkalmazni (transzpilálás
*előtt*), és a fizikai leképezést az executorba kell tenni. Lásd ADR-0003.

### M4 — A saját folding és a Mitiq folding bitre egyezik
Kereszt-validáció (UCCSD/H2, `rz,sx,x,cx` bázis):

| scale factor λ | Mitiq `fold_global` kapuszám | Saját `fold_global` kapuszám | Egyezés |
|---|---|---|---|
| 1 | 23 | 23 | ✅ |
| 3 | 69 | 69 | ✅ |
| 5 | 115 | 115 | ✅ |

**Következmény:** biztonsággal használhatunk saját, ISA-biztos folding-implementációt
(ADR-0003), és a Mitiq megmarad **független referencia-implementációnak** — ez erősíti,
nem gyengíti a benchmark hitelességét.

### M5 — A readout-hiba ZNE-vel nem javítható
Mért readout-hibák FakeManilaV2-n: `[0.0353, 0.0219, 0.0964, 0.0144, 0.0186]`.
A unitáris folding **nem skálázza** a mérési hibát (a mérés nem unitáris), így a ZNE
szisztematikus maradékhibát hagy. **Következmény:** a `measurement mitigation` nem
opcionális extra, hanem a mitigációs mátrix önálló dimenziója (Fázis 3 bővítés).

### M6 (bónusz) — A FakeBackend-ek realisztikus zajmodellt adnak, kvóta nélkül
`AerSimulator.from_backend(FakeManilaV2())` valódi kalibrációs adatokból épít zajmodellt.
Mért ZNE-eredmény ezen (H2, UCCSD, Richardson λ∈{1,3,5}):

| | Energia (Ha) | Eltérés a referenciától |
|---|---|---|
| Referencia (L2) | −1.137306 | — |
| Nyers, zajos (L3b) | −1.121556 | **+15.75 mHa** |
| ZNE / Richardson | −1.136959 | **+0.35 mHa** ✅ kémiai pontosságon belül |
| ZNE / lineáris | −1.136357 | +0.95 mHa |
| ZNE / exponenciális | −1.136965 | +0.34 mHa |

**Következmény:** a Fázis 2–3–5–6 teljes egészében kvótamentesen fejleszthető és
tesztelhető, a valódi QPU-t csak a végső validálásra tartjuk fenn. Ez az alapterv
"kvótavédelem" alapelvének a legerősebb megvalósítása.

---

## 6. Architektúra-döntések (ADR-ek)

A részletes indoklás külön fájlokban:

| ADR | Cím | Állapot |
|---|---|---|
| [ADR-0001](../adr/ADR-0001-technologiai-stack.md) | Technológiai stack rögzítése Qiskit 1.4.6-ra | Elfogadott |
| [ADR-0002](../adr/ADR-0002-sajat-vqe-hurok.md) | Saját VQE-hurok a `qiskit-algorithms` helyett | Elfogadott |
| [ADR-0003](../adr/ADR-0003-mitigacios-architektura.md) | Pluginalapú hibaenyhítés, saját ISA-biztos ZNE | Elfogadott |
| [ADR-0004](../adr/ADR-0004-adattarolas.md) | SQLite mint kanonikus tároló, sémaverziózással | Elfogadott |
| [ADR-0005](../adr/ADR-0005-determinizmus.md) | Determinizmus- és seed-politika | Elfogadott |

---

## 7. Felülvizsgált fázisterv

Az alapterv 10 fázisa megmarad. A változások:

| Fázis | Alapterv szerint | Bővítés / szigorítás |
|---|---|---|
| **0** | Repó + Docker | + verziópolitika, CI-váz, licenc, hivatkozásjegyzék, ADR-keret |
| **1** | H2-VQE szimulátoron | + **L0/L1/L2 hármas keresztvalidáció** (FCI ↔ egzakt diag ↔ VQE), nem csak a ±0.01 Ha ablak. Szigorítás: **±1.6 mHa** (kémiai pontosság). |
| **1b** *(új)* | — | **Zajos szimuláció FakeBackend-en.** Az alaptervben a Fázis 2 az első zajos futás; ez kvótát éget hibakereséssel. Beiktatunk egy kvótamentes zajos fázist. |
| **2** | Valódi hardver | Változatlan cél, de az 1b után már *validált* kóddal futunk rá. |
| **3** | Mitiq ZNE | + saját ISA-biztos ZNE, + measurement mitigation (M5), + extrapolátor-összehasonlítás, + Mitiq-keresztvalidáció (M4) |
| **4** | Adatséma | + sémaverzió, + környezet-ujjlenyomat, + provenance-mezők, + FAIR-elvek |
| **5** | Batch futtatás | + aktív tér (active space) redukció LiH/BeH2-re (mért indoklás: 4. fejezet táblázata) |
| **6** | Automatizálás | + strukturált hibatárolás, + újrapróbálkozási politika |
| **7** | Dashboard | változatlan, 4 belső lépés |
| **8** | Konténerizáció | változatlan |
| **9** | Publikálás | + CITATION.cff, + Zenodo |
| **10** | Közösség | változatlan |

Minden fázishoz **külön bővített tervdokumentum** készül (`docs/plan/phase_NN.md`)
**a megvalósítás megkezdése előtt**, és **külön tesztdokumentum-pár**
(`docs/testing/TP-FNN_*.md` tesztterv + `TR-FNN_*.md` mérési jegyzőkönyv) utána.
A `TR-000_spike.md` kivétel: az előzetes felderítés jegyzőkönyve, amelyhez nem
tartozik tesztterv.

---

## 8. Verziózási politika

### 8.1 Szoftververzió (Semantic Versioning 2.0.0)

`MAJOR.MINOR.PATCH`, ahol a fázislezárások a MINOR-t léptetik:

| Verzió | Mérföldkő |
|---|---|
| `0.1.0` | Fázis 0 lezárva |
| `0.2.0` | Fázis 1 lezárva |
| `0.3.0` | Fázis 1b lezárva |
| … | … |
| `1.0.0` | Fázis 9 lezárva (első publikált release, DOI) |

A `VERSION` fájl a forrás, a `CHANGELOG.md` a *Keep a Changelog* formátumot követi.

### 8.2 Adatséma-verzió

Független a szoftververziótól: `schema_version` mező minden rekordban
(`1`, `2`, …). Migrációk: `src/vqebd/storage/migrations/`.

### 8.3 Dokumentum-verzió

Minden `docs/` dokumentum fejlécében `Dokumentum-verzió` és `Dátum`.
A tervdokumentumok a végrehajtás közben nem íródnak át: ha a valóság eltér,
**új verzió készül, a régi megmarad**, és a változást a „Változásnapló" szakasz rögzíti.

### 8.4 Git-konvenciók

- Branch: `main` (védett), `phase/NN-rovid-nev` munkaágak.
- Commit: [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.
- Tag: `v0.1.0` formátum, minden fázislezáráskor, annotált tag a fázis
  elfogadási kritériumának teljesülésével a tag-üzenetben.

---

## 9. Tesztelési politika

### 9.1 Teszt-piramis

| Réteg | Hol | Mit | Futásidő-cél |
|---|---|---|---|
| **Unit** | `tests/unit/` | Egy függvény, mockolt környezet. Nincs kvantumszimuláció. | < 5 s összesen |
| **Integration** | `tests/integration/` | Több modul együtt, szimulátorral. | < 120 s |
| **Validation** | `tests/validation/` | **Fizikai helyesség** ismert irodalmi értékekkel szemben. | < 300 s |
| **Manual / protocol** | `docs/testing/TR-*.md` | Valódi hardver — nem automatizálható. | — |

### 9.2 Dokumentumpár minden fázishoz

- **`TP-NNN_*.md` (Test Plan):** mit, miért, milyen kritériummal — *a megvalósítás előtt*.
- **`TR-NNN_*.md` (Test Report):** mi történt, milyen számok jöttek ki, mi tért el —
  *a megvalósítás után*, a tényleges kimenettel.

### 9.3 Többkörös hibakeresés (az 5. felhasználói követelmény)

Minden fázis lezárása előtt **három kör**:

1. **Kör 1 — funkcionális:** teljesül-e az elfogadási kritérium?
2. **Kör 2 — robusztussági:** határesetek, hibás bemenetek, determinizmus
   (ugyanaz a seed ⇒ ugyanaz az eredmény), ismételt futtatás.
3. **Kör 3 — keresztvalidáció:** független úton is kijön-e ugyanaz?
   (pl. PySCF FCI ↔ Qiskit egzakt diagonalizáció; saját ZNE ↔ Mitiq ZNE)

A három kör eredménye a `TR-NNN` jegyzőkönyvben külön szakaszként jelenik meg.

### 9.4 Statikus ellenőrzés

`ruff` (lint + format), `mypy` (típusellenőrzés a `src/vqebd/` felett).
CI-ben kötelező, `make check` néven helyben is futtatható.

---

## 10. Determinizmus és reprodukálhatóság

| Véletlenforrás | Kezelés |
|---|---|
| Szimulátor lövések | `seed_simulator` minden futtatásban, rekordba mentve |
| Transzpiláció | `seed_transpiler` rögzítve |
| Optimalizáló kezdőpont | Explicit `x0` (alapértelmezés: nullvektor = Hartree–Fock állapot) |
| Sztochasztikus optimalizálók (SPSA) | `seed` paraméter, rekordba mentve |
| Mitiq véletlen folding | `seed` paraméter |
| Python hash | `PYTHONHASHSEED=0` a konténerben |

**Elvárás:** azonos seed + azonos verziók ⇒ **bitre azonos** energia szimulátoron.
Ez a Fázis 1 egyik automatikus tesztje lesz.

---

## 11. Kockázatnyilvántartás

| # | Kockázat | Hatás | Val. | Ellenintézkedés | Állapot |
|---|---|---|---|---|---|
| R1 | Mitiq ↔ Qiskit 2.x inkompatibilitás | Magas | **Bekövetkezett** | Stack Qiskit 1.4.6-ra rögzítve (ADR-0001) | Kezelve |
| R2 | Mitiq konverzió qubit-vesztés | Magas | **Bekövetkezett** | Saját ISA-biztos ZNE (ADR-0003) | Kezelve |
| R3 | IBM kvóta kimerül hibakereséssel | Magas | Közepes | Fázis 1b: FakeBackend-es fejlesztés (M6) | Kezelve |
| R4 | A Qiskit 1.4 ág elavul | Közepes | Magas (hosszú táv) | Saját VQE V2 primitívekkel → előre-hordozható (ADR-0002) | Figyelt |
| R5 | IBM Runtime API-változás | Közepes | Közepes | Backend-absztrakció; runtime-hívás egy modulba zárva | Figyelt |
| R6 | ZNE nem javít (readout-hiba) | Alacsony | **Bekövetkezett** | Measurement mitigation külön dimenzióként (M5) | Kezelve |
| R7 | Barren plateau nagyobb molekulánál | Közepes | Közepes | Aktív tér redukció; UCCSD + HF kezdőállapot | Figyelt |
| R8 | pyscf nem fut Windows-on natívan | Alacsony | **Bekövetkezett** | Minden számítás konténerben (Linux) | Kezelve |

---

## 12. Fogalomtár

| Rövidítés | Jelentés |
|---|---|
| VQE | Variational Quantum Eigensolver |
| UCCSD | Unitary Coupled Cluster, Single & Double excitations |
| HF | Hartree–Fock |
| FCI | Full Configuration Interaction (egzakt az adott bázison) |
| STO-3G | Slater-Type Orbital, 3 Gaussian — minimális bázis |
| JW | Jordan–Wigner leképezés |
| ZNE | Zero-Noise Extrapolation |
| PEC | Probabilistic Error Cancellation |
| ISA | Instruction Set Architecture — a backend natív kapukészletére transzpilált áramkör |
| Ha | Hartree (atomi energiaegység), 1 Ha = 27.211386 eV |
| mHa | milli-Hartree = 10⁻³ Ha |
| QPU | Quantum Processing Unit |
| NISQ | Noisy Intermediate-Scale Quantum |

---

## 13. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. Alapterv bővítése a TR-000 spike mérései alapján. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
