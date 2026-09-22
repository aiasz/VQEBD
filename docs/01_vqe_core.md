# 01 — A VQE-mag (Fázis 1)

| | |
|---|---|
| **Dokumentum** | `docs/01_vqe_core.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Projektverzió** | 0.2.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1 — H2-VQE szimulátoron |

---

## 1. Mit csinál ez a fázis

Kiszámolja a H2 molekula **alapállapoti energiáját** VQE-vel, zajmentes
állapotvektor-szimulátoron — és ami legalább ennyire fontos: **igazolja, hogy a
kapott szám helyes**, három egymástól független referenciához mérve.

```bash
docker run --rm vqebd:0.2.0 python -m vqebd
```

```
Molekula ............ H2 [sto3g]
Geometria ........... H 0 0 0; H 0 0 0.735000
Leképezés ........... parity (2-qubit redukcióval)
Áramkör ............. 2 qubit, 3 paraméter, 5 Pauli-tag
Backend ............. statevector
Optimalizáló ........ SLSQP (3 iteráció, 14 kiértékelés)

Energiák (Hartree):
  Hartree–Fock ...... -1.1169989968
  L0  Full CI ....... -1.1373060358
  L1  egzakt diag. .. -1.1373060358
  L2  VQE ........... -1.1373060358

Hibák:
  leképezés (L1−L0) . +1.332e-15 Ha
  ansatz (L2−L1) .... +7.994e-15 Ha
  referenciához ..... +9.326e-15 Ha
  korreláció vissza . 100.0000 %

Kémiai pontosságon belül (|Δ| < 1.6 mHa): IGEN
Variációs elv (E_VQE ≥ E_egzakt): teljesül
Konvergált: igen (Optimization terminated successfully)
Futásidő: 1.801 s
Konfiguráció-ujjlenyomat: a52e7c035a93
```

---

## 2. Az öt referenciaszint — miért nem elég egy szám

Egy VQE-eredmény önmagában értelmezhetetlen. Ha az energia eltér a valóditól,
**nem tudjuk, mi okozta**: a fermion → qubit leképezés, az ansatz korlátai, a
véges lövésszám vagy a hardverzaj. A projekt ezért egy **referencialáncot**
számol, amelyben minden láncszem egy-egy hibaforrást szigetel el.

| Szint | Mit ad | Hogyan | Fázis |
|---|---|---|---|
| **L0** | Full CI — az adott bázisban egzakt | PySCF determináns-CI | 1 ✅ |
| **L1** | A qubit-Hamiltoni legkisebb sajátértéke | NumPy `eigvalsh` | 1 ✅ |
| **L2** | VQE zajmentes állapotvektoron | saját hurok + `StatevectorEstimator` | 1 ✅ |
| **L3a** | VQE véges lövésszámmal | Aer `EstimatorV2` | 1b |
| **L3b** | VQE zajos szimulátoron / QPU-n | Aer zajmodell / IBM Runtime | 1b, 2 |

```
E_L0 ──(leképezési hiba)── E_L1 ──(ansatz-hiba)── E_L2 ──(shot-zaj)── E_L3a ──(hardverzaj)── E_L3b
```

**Miért erős az L0 ↔ L1 egyezés?** A két érték két teljesen különböző úton
születik: a PySCF a determináns-térben diagonalizál, a Qiskit + NumPy pedig egy
Pauli-operátorokból épített mátrixot. Nincs közös kódút, amelyben egy hiba
mindkettőt egyformán elronthatná. Ha egyeznek, a leképezés **bizonyítottan**
helyes.

---

## 3. Használat

### 3.1 Parancssorból

```bash
# Alapértelmezés: H2, 0.735 Å, STO-3G, paritás-leképezés, SLSQP
docker run --rm vqebd:0.2.0 python -m vqebd

# Másik geometria (disszociációs görbe egy pontja)
docker run --rm vqebd:0.2.0 python -m vqebd --bond-length 1.2

# Másik leképezés
docker run --rm vqebd:0.2.0 python -m vqebd --mapper jordan_wigner

# Másik optimalizáló
docker run --rm vqebd:0.2.0 python -m vqebd --optimizer COBYLA

# Gépi feldolgozáshoz
docker run --rm vqebd:0.2.0 python -m vqebd --json

# Súgó
docker run --rm vqebd:0.2.0 python -m vqebd --help
```

#### Kilépési kód

| Kód | Jelentés |
|---|---|
| `0` | Az eredmény **kémiai pontosságon belül van** *és* a variációs elv teljesül. |
| `1` | A számítás lefutott, de nem érte el a kémiai pontosságot, vagy sérült a variációs elv. |
| `2` | Hiba (pl. ismeretlen bázis vagy optimalizáló). |

A `0` tehát **nem** azt jelenti, hogy „nem szállt el a program", hanem hogy az
eredmény fizikailag elfogadható. Így a parancs gépi ellenőrzésre is alkalmas.

### 3.2 Python API-ként

```python
from vqebd.chemistry.molecule import h2
from vqebd.config import VQEConfig
from vqebd.vqe.runner import run_vqe

result = run_vqe(VQEConfig(molecule=h2(0.735)))

print(result.energy)  # -1.1373060358... (Ha)  <- az alapterv kért értéke
print(result.reference.full_ci)  # L0
print(result.reference.exact_diagonalization)  # L1
print(result.within_chemical_accuracy)  # True
print(result.correlation_energy_recovered)  # 1.0 (100 %)
```

---

## 4. Architektúra

```
MoleculeSpec  (vqebd.config)
    │
    ├─ build_electronic_structure()      vqebd.chemistry.problem
    │      PySCF: Hartree–Fock + molekulaintegrálok
    │      -> ElectronicStructure (típusos burkolat)
    │
    ├─ map_to_qubits()                   vqebd.chemistry.mapping
    │      fermionos H  ->  qubit-H (Jordan–Wigner / paritás / Bravyi–Kitaev)
    │      -> QubitHamiltonian
    │
    ├─ collect_references()              vqebd.chemistry.reference
    │      L0: PySCF Full CI      L1: numpy.linalg.eigvalsh
    │      -> ReferenceEnergies
    │
    ├─ build_ansatz()                    vqebd.vqe.ansatz
    │      UCCSD + HartreeFock kezdőállapot,  θ₀ = 0
    │      -> AnsatzBundle
    │
    ├─ make_energy_evaluator()           vqebd.backends.estimators
    │      θ -> ⟨ψ(θ)|H|ψ(θ)⟩   (V2 primitív)
    │
    └─ minimize_energy()                 vqebd.vqe.optimizer
           SciPy;  konvergencia-napló
           -> OptimizationOutcome
                   │
                   └─> VQEResult         vqebd.vqe.result
```

### 4.1 Modulonkénti felelősség

| Modul | Felelősség |
|---|---|
| `vqebd.config` | Fagyasztott, hash-elhető konfiguráció; stabil SHA-256 ujjlenyomat. |
| `vqebd.seeds` | Determinisztikus seed-származtatás egyetlen mester-seedből. |
| `vqebd.versions` | Környezet-ujjlenyomat (csomagverziók, platform). |
| `vqebd.chemistry.molecule` | Molekula-definíciók, geometria. |
| `vqebd.chemistry.problem` | PySCF-meghajtó típusos burkolata. |
| `vqebd.chemistry.mapping` | Fermion → qubit leképezés. |
| `vqebd.chemistry.reference` | L0 és L1 referenciaenergiák. |
| `vqebd.vqe.ansatz` | UCCSD + Hartree–Fock kezdőállapot. |
| `vqebd.backends.estimators` | Energiakiértékelés (backend-független interfész). |
| `vqebd.vqe.optimizer` | Klasszikus optimalizáló-hurok. |
| `vqebd.vqe.result` | Strukturált eredmény és származtatott mutatók. |
| `vqebd.vqe.runner` | A `run_vqe()` belépési pont. |
| `vqebd.cli` | Parancssori felület. |

---

## 5. Miért ezek a választások

### 5.1 Paritás-leképezés, kétqubites redukcióval

| Leképezés | H2 qubit-szám | Pauli-tagok |
|---|---|---|
| Jordan–Wigner [jordan1928] | 4 | 15 |
| Bravyi–Kitaev [bravyi2002], [seeley2012] | 4 | 15 |
| **Paritás + 2-qubit redukció** | **2** | **5** |

A redukció a részecskeszám- és spin-megmaradást használja ki: a Hamilton-operátor
blokkdiagonális ezekben a szektorokban, így két qubit kiejthető. Mindhárom
leképezés **ugyanazt az energiát** adja — ezt automatikus teszt ellenőrzi
(AC-1.7), és ez a leképezés-implementáció független validálása.

### 5.2 UCCSD ansatz

Kémiailag motivált próbaállapot [romero2019]: a paraméterek gerjesztési
amplitúdók, nem önkényes forgatási szögek. Előnyei a „hardware-efficient"
alternatívával [kandala2017] szemben:

- részecskeszám-megőrző → a variációs minimum fizikailag értelmes;
- kisebb barren-plateau kockázat;
- **H2-re egzakt**: 3 paraméter, és az L2 ≡ L1 gépi pontossággal.

Ára a mélyebb áramkör; ez a Fázis 1b-től (zaj) válik lényegessé, és ott önálló
benchmark-dimenzióként lesz összevetve.

### 5.3 A kezdőpont: `θ = 0` = Hartree–Fock

`exp(0) = I`, tehát `|ψ(0)⟩ = |HF⟩` és `E(0) = E_HF`. Ez

- **determinisztikus** (ADR-0005),
- fizikailag motivált,
- és **automatikusan ellenőrizhető**: az AC-1.8 teszt a VQE első
  célfüggvény-kiértékelését veti össze a PySCF SCF energiájával — két független
  úton ugyanaz a szám.

### 5.4 Saját optimalizáló-hurok a `qiskit-algorithms` helyett

Lásd [ADR-0002](adr/ADR-0002-sajat-vqe-hurok.md). Röviden: a Qiskit 2.0
eltávolította a V1 primitíveket, amelyekre a `qiskit-algorithms` épül. A V2
primitívekre írt saját hurok **előre-hordozható**, és ugyanaz a kód fut majd
egzakt, zajos és QPU-backenden.

---

## 6. Mért eredmények (H2, 0.735 Å, STO-3G)

| Mennyiség | Érték (Ha) |
|---|---|
| Magtaszítás `E_nuc` | +0.7199689900 |
| Hartree–Fock | −1.1169989968 |
| **L0 — Full CI** | **−1.1373060358** |
| **L1 — egzakt diagonalizáció** | **−1.1373060358** |
| **L2 — VQE** | **−1.1373060358** |
| Korrelációs energia | −0.0203070390 |

| Hiba | Érték |
|---|---|
| Leképezés (L1 − L0) | +1.33 × 10⁻¹⁵ Ha |
| Ansatz (L2 − L1) | +7.99 × 10⁻¹⁵ Ha |
| Összesen (L2 − L0) | +9.33 × 10⁻¹⁵ Ha |
| Visszanyert korreláció | **100.0000 %** |

Összehasonlításul: a kémiai pontosság 1.59 × 10⁻³ Ha. A mért hiba ennek
körülbelül **10⁻¹²-szerese** — az eredmény tehát a gépi pontosság határán egzakt.

### Leképezésenként

| Leképezés | Qubit | Pauli-tag | E_VQE (Ha) | Ansatz-hiba |
|---|---|---|---|---|
| Jordan–Wigner | 4 | 15 | −1.1373060358 | +7.86 × 10⁻¹⁴ |
| Bravyi–Kitaev | 4 | 15 | −1.1373060358 | +2.75 × 10⁻¹⁴ |
| Paritás (2-qubit red.) | 2 | 5 | −1.1373060358 | +7.99 × 10⁻¹⁵ |

---

## 7. Amit ez a modell **nem** ad meg — őszinte korlátok

A `−1.1373 Ha` **nem** a H2 valódi, kísérleti energiája, hanem az STO-3G
bázisban vett egzakt érték.

| Mennyiség | Érték | Megjegyzés |
|---|---|---|
| E(FCI / STO-3G) | ≈ −1.1373 Ha | **Ezt számoljuk.** |
| E(FCI / teljes bázishatár) | ≈ −1.1745 Ha | A bázishiba ≈ 37 mHa. |

**A benchmark szempontjából ez nem probléma**, sőt módszertanilag lényeges: a
kvantumszámítást mindig az **ugyanazon modellen** vett egzakt megoldáshoz mérjük.
A bázishiba klasszikus modellhiba, nem a kvantumalgoritmusé — a kettő
összekeverése a terület egyik gyakori félreértése. Az adatséma ezért mindig az
adott modellhez tartozó referenciát tárolja.

További korlátok:

- Csak **zajmentes** szimuláció (L3a és L3b: Fázis 1b és 2).
- Csak **H2** validálva (LiH, BeH2: Fázis 5).
- Nincs adatbázis-tárolás (Fázis 4) — a `VQEResult` viszont már tartalmazza a
  teljes kontextust.

---

## 8. Determinizmus

Az alapterv előírja: *„többször lefuttatva is ugyanazt az eredményt adja."*
Ezt gépi bizonyítékká tettük (AC-1.6): azonos konfiguráció kétszeri futtatása
**bitre azonos** energiát ad.

Az ehhez szükséges beállítások:

| Beállítás | Hol | Miért |
|---|---|---|
| `PYTHONHASHSEED=0` | Dockerfile | a Python hash-randomizáció kikapcsolása |
| `OMP_NUM_THREADS=1` | Dockerfile | a többszálú OpenMP-redukciók összegzési sorrendje ingadozhat |
| `OPENBLAS_NUM_THREADS=1` | Dockerfile | ugyanez a BLAS-ban |
| `MKL_NUM_THREADS=1` | Dockerfile | ugyanez az MKL-ben |
| `θ₀ = 0` | alapértelmezés | determinisztikus kezdőpont |

A mester-seedből a rendszer BLAKE2b-vel származtat komponensenkénti seedeket
(`vqebd.seeds`), és **mindet** eltárolja az eredményrekordban.

---

## 9. Ismert figyelmeztetések

| Figyelmeztetés | Forrás | Kezelés |
|---|---|---|
| `PendingDeprecationWarning: NLocal is pending deprecation` | a `qiskit-nature 0.7.2` UCCSD-je a Qiskit 1.4 `NLocal` osztályát használja | Külső csomag, nem a mi kódunk. A `qiskit-nature` következő, Qiskit 2.x-kompatibilis ágán megszűnik. Nem befolyásolja a helyességet. |
| `UserWarning: Basis may be available in basis-set-exchange` | PySCF, ismeretlen bázisnév esetén | Csak a hibakezelési tesztben jelentkezik, szándékosan. |

---

## 10. Elfogadási kritériumok

A teljes lista és a mérési eredmények:
[`docs/testing/TR-F01_vqe_mag.md`](testing/TR-F01_vqe_mag.md).

| # | Kritérium | Állapot |
|---|---|---|
| AC-1.1 | `docker build` a teljes stackkel sikeres | ✅ |
| AC-1.2 | L0 ≡ L1, \|Δ\| < 1e-9 Ha | ✅ |
| AC-1.3 | L2 ≈ L1, \|Δ\| < 1.6 mHa | ✅ |
| AC-1.4 | **Az alapterv kritériuma:** E ∈ −1.137 ± 0.01 Ha | ✅ |
| AC-1.5 | Variációs elv teljesül | ✅ |
| AC-1.6 | Determinizmus: bitre azonos | ✅ |
| AC-1.7 | Mindhárom leképezés egyezik | ✅ |
| AC-1.8 | E(θ=0) ≡ E_HF | ✅ |
| AC-1.9 | Önállóan futtatható modul | ✅ |
| AC-1.10 | `ruff`, `mypy --strict`, tesztek zöld | ✅ |
| AC-1.11 | `requirements.lock` konzisztens | ✅ |
| AC-1.12 | Validáció < 300 s | ✅ |

---

## 11. Következő lépés

**Fázis 1b** — zajos szimuláció FakeBackend-en (kvótamentes). Ez az alaptervhez
képest **új** fázis, a [`TR-000`](testing/TR-000_spike.md) M6 megállapítása
alapján: az IBM `FakeBackend`-ek valódi kalibrációs adatból építenek zajmodellt,
így a hardveres fázis teljes egészében kvóta nélkül fejleszthető és tesztelhető.

---

## 12. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás (Fázis 1). |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
