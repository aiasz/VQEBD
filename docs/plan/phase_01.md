# Fázis 1 — H2-VQE szimulátoron (bővített terv)

| | |
|---|---|
| **Fázis** | 1 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Státusz** | **Elfogadott — végrehajtás alatt** |
| **Célverzió** | `v0.2.0` |
| **Előzmény** | [`phase_00.md`](phase_00.md), [`TR-F00`](../testing/TR-F00_alapinfrastruktura.md), [`TR-000`](../testing/TR-000_spike.md) |

---

## 1. Az alapterv szövege és a bővítés viszonya

Az alapterv Fázis 1-e:

> **Cél:** Egy önálló, kézzel is futtatható és ellenőrizhető Python-modul, ami H2-re
> kiszámolja az alapállapoti energiát szimulátoron.
> **Feladatok:** `src/vqe_runner.py` — egyetlen függvény: `run_vqe(molecule_config) -> float`.
> **Elfogadási kritérium:** `pytest tests/test_vqe_h2.py` — a kapott energia
> −1.137 Hartree körül van (±0.01 Hartree tolerancia).
> **Miért itt állunk meg:** …ne menj tovább, amíg ez nem megy stabilan, többször
> lefuttatva is ugyanazt az eredményt adja.

### 1.1 A bővítés három pontja

| Alapterv | Bővítés | Indok |
|---|---|---|
| „az energia −1.137 Ha körül van (±0.01 Ha)" | **±1.6 mHa** (kémiai pontosság), és **két független referenciához** mérve | A ±0.01 Ha durvább, mint a kémiai pontosság. A TR-000 mérése szerint a saját VQE **7.6 × 10⁻¹⁵** eltérést ad — a laza tolerancia elfedne egy nagyságrendekkel rosszabb, de még „átmenő" implementációt. |
| egyetlen `run_vqe() -> float` | `run_vqe() -> VQEResult` (strukturált eredmény) | A Fázis 4 adatsémája minden futás teljes kontextusát tárolja. Ha most `float`-ot adunk vissza, a Fázis 4-ben az egész hívási láncot át kell írni. A `float`-ot a `VQEResult.energy` adja. |
| „többször lefuttatva is ugyanazt az eredményt adja" | **Automatikus determinizmus-teszt** (D1 szint, bitre azonosság) | Kézi megfigyelés helyett gépi bizonyíték (ADR-0005). |

### 1.2 Mit NEM változtatunk

Az alapterv „miért itt állunk meg" elve **sérthetetlen**: ez a fázis csak
**szimulátoron**, csak **H2**-re, csak **zajmentesen** dolgozik. Zaj → Fázis 1b,
hardver → Fázis 2, hibaenyhítés → Fázis 3, több molekula → Fázis 5.

---

## 2. Tudományos háttér és a validálás logikája

### 2.1 A megoldandó feladat

A Born–Oppenheimer közelítésben rögzített magok mellett az elektronszerkezeti
Hamilton-operátor második kvantált alakja:

```
H = Σ_pq h_pq a†_p a_q  +  ½ Σ_pqrs h_pqrs a†_p a†_q a_r a_s  +  E_nuc
```

ahol `h_pq` az egytest-, `h_pqrs` a kéttest-integrálok a választott bázisban
(esetünkben STO-3G, [hehre1969]), `E_nuc` pedig a magtaszítási energia (konstans).

A VQE ([peruzzo2014], [mcclean2016]) a variációs elvre épül:

```
E_0  ≤  min_θ  ⟨ψ(θ)| H |ψ(θ)⟩
```

Azaz **bármely** paraméterezett próbaállapot várható értéke felső korlátja az
alapállapoti energiának. Ez adja a validálás alapját: **a VQE sosem adhat
alacsonyabb energiát az egzakt alapállapotnál** — ha mégis, az hibát jelez
(numerikus vagy implementációs).

### 2.2 A négy referenciaszint ebben a fázisban

A Mesterterv 3.2 szerinti L0–L3b láncból a Fázis 1 az **első hármat** valósítja meg:

| Szint | Mit számolunk | Mivel | Mit igazol |
|---|---|---|---|
| **L0** | Full CI energia | PySCF `fci` | A „fizikai igazság" az adott bázison. Független implementáció, független elmélet. |
| **L1** | A qubit-Hamilton-operátor legkisebb sajátértéke | `numpy.linalg.eigvalsh` | Hogy a fermion→qubit **leképezés helyes**: L1 ≡ L0 kell. |
| **L2** | VQE zajmentes állapotvektoron | saját hurok + `StatevectorEstimator` | Hogy az **ansatz és az optimalizáló** működik: L2 ≥ L1, és H2-re L2 ≈ L1. |

Ez a **hármas keresztvalidáció** a fázis lényege. Az alapterv egyetlen számot kér;
mi hármat számolunk, és a köztük lévő eltéréseket külön-külön korlátozzuk.

### 2.3 Miért éppen H2 / 0.735 Å / STO-3G?

| Választás | Indok |
|---|---|
| **H2** | A legkisebb nemtriviális molekula. STO-3G bázisban 2 térbeli pálya → 4 spin-pálya → **4 qubit** (JW), paritás-leképezéssel 2-qubit redukcióval **2 qubit**. Az egzakt megoldás klasszikusan triviális, így a referencia kétség nélküli. |
| **0.735 Å** | A kísérleti egyensúlyi kötéshossz; az alapterv ezt írja elő. |
| **STO-3G** | Minimális bázis ([hehre1969]); a legkisebb értelmes modell. A korlátait a 2.4 szakasz rögzíti. |
| **UCCSD ansatz** | Kémiailag motivált, nem heurisztikus ([romero2019]). H2-re **egzakt** (a 3 paraméteres UCCSD a teljes 2-qubites teret lefedi), ezért L2 ≡ L1 várható. |

### 2.4 Amit ez a modell **nem** ad meg — őszinte korlátok

A számított `−1.1373 Ha` **nem** a H2 valódi, kísérleti energiája. Ez az STO-3G
bázisban vett **egzakt** (Full CI) energia. A különbség:

| Mennyiség | Érték | Megjegyzés |
|---|---|---|
| E(FCI / STO-3G) | ≈ −1.1373 Ha | **Ezt számoljuk.** |
| E(FCI / teljes bázishatár) | ≈ −1.1745 Ha | Irodalmi érték; a bázishiba ≈ 37 mHa. |
| Kísérleti disszociációs energia | — | További korrekciókat igényel (relativisztikus, nem-Born–Oppenheimer). |

**A benchmark szempontjából ez nem probléma**: a kvantumszámítást mindig az
**ugyanazon bázisban vett egzakt** megoldáshoz mérjük. A bázishiba klasszikus
modellhiba, nem a kvantumalgoritmus hibája — és a keverésük a terület egyik
gyakori félreértése. A séma ezért mindig az adott modellhez tartozó referenciát
tárolja.

---

## 3. Architektúra és modulterv

### 3.1 Modulok

```
src/vqebd/
├── config.py                 ÚJ  — a futtatás konfigurációja (fagyasztott dataclass-ok)
├── seeds.py                  ÚJ  — SeedSet, determinisztikus seed-származtatás (ADR-0005)
├── versions.py               ÚJ  — környezet-ujjlenyomat (csomagverziók) a Fázis 4-hez
├── chemistry/
│   ├── molecule.py           ÚJ  — molekula-definíciók, geometria
│   ├── problem.py            ÚJ  — PySCF driver -> ElectronicStructureProblem
│   ├── mapping.py            ÚJ  — fermion -> qubit leképezés (JW, parity, BK)
│   └── reference.py          ÚJ  — L0 (FCI) és L1 (egzakt diagonalizáció)
├── vqe/
│   ├── ansatz.py             ÚJ  — UCCSD + HartreeFock, és a kezdőpont
│   ├── optimizer.py          ÚJ  — SciPy-burkolat, konvergencia-napló
│   ├── result.py             ÚJ  — VQEResult (strukturált eredmény)
│   └── runner.py             ÚJ  — run_vqe(): a fő belépési pont
└── backends/
    └── estimators.py         ÚJ  — estimator-gyár (Fázis 1: csak statevector)
```

### 3.2 A fő belépési pont szerződése

```python
def run_vqe(config: VQEConfig) -> VQEResult:
    """VQE futtatás egyetlen konfigurációra."""
```

**Miért nem `run_vqe(molecule_config) -> float`?**
Az alapterv `float`-ot kér. A `VQEResult.energy` **pontosan ez a float**, tehát a
kritérium teljesül. A strukturált visszatérés viszont elkerüli, hogy a Fázis 4-ben
(adatséma) a teljes hívási láncot át kelljen írni: már most eltároljuk az
iterációszámot, a kiértékelések számát, a konvergencia-naplót, a seedeket és a
környezet-ujjlenyomatot. Ez az alapterv „nem lépünk tovább félig működő alapokon"
elvének betartása — a `float`-os API félig működő alap lenne.

### 3.3 `VQEConfig` — a futtatás teljes leírása

```python
@dataclass(frozen=True)
class MoleculeSpec:
    name: str  # "H2"
    atom: str  # "H 0 0 0; H 0 0 0.735"
    basis: str = "sto3g"
    charge: int = 0
    spin: int = 0  # 2S, nem 2S+1
    bond_length: float | None = None  # Å, dokumentációs célra


@dataclass(frozen=True)
class AnsatzSpec:
    kind: Literal["uccsd"] = "uccsd"
    initial_point: Literal["zeros", "random"] = "zeros"


@dataclass(frozen=True)
class OptimizerSpec:
    method: str = "SLSQP"  # SciPy method
    maxiter: int = 300
    tol: float | None = 1e-10


@dataclass(frozen=True)
class VQEConfig:
    molecule: MoleculeSpec
    mapper: Literal["jordan_wigner", "parity", "bravyi_kitaev"] = "parity"
    two_qubit_reduction: bool = True
    ansatz: AnsatzSpec = AnsatzSpec()
    optimizer: OptimizerSpec = OptimizerSpec()
    backend: Literal["statevector"] = "statevector"  # Fázis 1b-ben bővül
    seed: int = 20260922
```

Minden mező **fagyasztott** (`frozen=True`) és **hash-elhető**, mert a Fázis 4-ben
a konfiguráció hash-e lesz a futás azonosítója (`config_hash`).

### 3.4 `VQEResult` — a strukturált eredmény

```python
@dataclass(frozen=True)
class VQEResult:
    energy: float  # Ha — az ALAPTERV által kért érték
    electronic_energy: float  # Ha — magtaszítás nélkül
    nuclear_repulsion_energy: float  # Ha
    optimal_parameters: tuple[float, ...]
    reference: ReferenceEnergies  # L0, L1 és a Hartree–Fock energia
    n_qubits: int
    n_parameters: int
    n_hamiltonian_terms: int
    n_iterations: int
    n_function_evaluations: int
    converged: bool
    optimizer_message: str
    history: tuple[float, ...]  # iterációnkénti energia
    wall_time_s: float
    config: VQEConfig
    seeds: SeedSet
    versions: Mapping[str, str]  # qiskit, qiskit-nature, pyscf, numpy, scipy
```

---

## 4. Implementációs döntések

### 4.1 Leképezés: paritás 2-qubit redukcióval (alapértelmezés)

A TR-000 4. körének mérése alapján:

| Leképezés | H2 qubit-szám | Hamilton-tagok |
|---|---|---|
| Jordan–Wigner [jordan1928] | 4 | 15 |
| Paritás + 2-qubit redukció | **2** | **5** |

A 2-qubit redukció a részecskeszám- és spin-megmaradást használja ki
([bravyi2017 / tapering]; a Qiskit Nature `ParityMapper(num_particles=…)`
implementálja). **Mindkét leképezésre ugyanazt az energiát kell kapni** — ezt
automatikus teszt ellenőrzi, és ez a leképezés-implementáció keresztvalidációja.

A Bravyi–Kitaev leképezést [bravyi2002], [seeley2012] is támogatjuk, de a
Fázis 1-ben csak tesztben használjuk (harmadik független út ugyanarra az energiára).

### 4.2 Optimalizáló: SLSQP alapértelmezésben

| Optimalizáló | Hivatkozás | Mikor |
|---|---|---|
| **SLSQP** | [kraft1988] | **Alapértelmezés zajmentes esetben.** A TR-000 mérése: 4 iteráció, 17 kiértékelés, gépi pontosság. |
| COBYLA | [powell1994] | Deriváltmentes; zajos esetben (Fázis 1b) reálisabb. |
| Nelder–Mead | [nelder1965] | Robusztus, de lassú; összehasonlításra. |
| L-BFGS-B | — | Gradiens-alapú alternatíva. |

A választás a `OptimizerSpec.method` mezőn keresztül a benchmark **dimenziója** lesz
(Fázis 5). A Fázis 1 mindegyiket teszteli, de az alapértelmezés az SLSQP.

### 4.3 Kezdőpont: nullvektor = Hartree–Fock állapot

Az UCCSD ansatz `θ = 0`-nál **pontosan a Hartree–Fock determinánst** adja
(mert `exp(0) = I`, és a kezdőállapot a HF-állapot). Ez:

- **determinisztikus** (nincs véletlen kezdőpont → ADR-0005),
- **fizikailag motivált** (a HF a legjobb egydetermináns-közelítés),
- **csökkenti a barren-plateau kockázatot** (R7), mert a jó megoldás közelében indulunk.

Automatikus teszt igazolja: `E(θ=0) == E_HF` (a PySCF-től függetlenül számolva).

### 4.4 Estimator: `StatevectorEstimator` (V2 primitív)

ADR-0002 szerint. A Fázis 1b-ben ugyanez a hurok `AerEstimatorV2`-vel fut — a
`run_vqe()` kódja **nem változik**, csak az estimator-gyár ad mást.

---

## 5. Függőségek — a Fázis 1 image

A `requirements.txt` az ADR-0001 szerinti, **már feloldott és funkcionálisan
igazolt** stackkel töltődik fel:

```
numpy==1.26.4
scipy==1.13.1
qiskit==1.4.6
qiskit-aer==0.17.2
qiskit-nature==0.7.2
qiskit-ibm-runtime==0.41.1
pyscf==2.14.0
ply==3.11
```

Megjegyzések:

- A `qiskit-algorithms==0.3.1` **tranzitívan** települ (a `qiskit-nature` függősége).
  Nem hívjuk; a tiltást a Fázis 0-ban bevezetett automatikus teszt őrzi (ADR-0002).
- A `mitiq` **nem** kerül ide (GPL-3.0 elkülönítés, ADR-0003) — a Fázis 3-ban,
  külön `requirements-mitiq.txt` fájlban.
- A Dockerfile-ba `build-essential` és `libgomp1` kerül: a PySCF OpenMP-t igényel.
  (A TR-000 spike-image is ezekkel épült.)
- **Új szállítandó:** `requirements.lock` — a **tranzitív** függőségek is rögzítve
  (`pip freeze` a megépült image-ből). Ez a reprodukálhatóság záró eleme.

---

## 6. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés | Forrás |
|---|---|---|---|
| **AC-1.1** | `docker build` a teljes stackkel sikeres | manuális + CI | alapterv |
| **AC-1.2** | **L0 ≡ L1**: a qubit-Hamilton-operátor egzakt sajátértéke megegyezik a PySCF FCI energiájával, \|Δ\| < **1 × 10⁻⁹ Ha** | automatikus teszt | bővítés |
| **AC-1.3** | **L2 ≈ L1**: a VQE energiája \|Δ\| < **1.6 mHa** (kémiai pontosság) az L1-től | automatikus teszt | bővítés |
| **AC-1.4** | Az alapterv kritériuma: E ∈ [−1.147, −1.127] Ha (−1.137 ± 0.01) | automatikus teszt | **alapterv** |
| **AC-1.5** | **Variációs elv**: E_VQE ≥ E_exact − 1 × 10⁻⁹ Ha (numerikus tűrés) | automatikus teszt | bővítés |
| **AC-1.6** | **Determinizmus (D1)**: azonos konfiguráció kétszeri futtatása **bitre azonos** energiát ad | automatikus teszt | bővítés |
| **AC-1.7** | **Leképezés-függetlenség**: JW, paritás és Bravyi–Kitaev ugyanazt az energiát adja, \|Δ\| < 1 × 10⁻⁹ Ha | automatikus teszt | bővítés |
| **AC-1.8** | **E(θ=0) ≡ E_HF**, \|Δ\| < 1 × 10⁻⁹ Ha | automatikus teszt | bővítés |
| **AC-1.9** | A modul önállóan futtatható: `docker run … python -m vqebd.vqe.runner` értelmes kimenetet ad | manuális + teszt | alapterv |
| **AC-1.10** | `ruff`, `mypy --strict`, teljes tesztkészlet zöld | CI | Fázis 0 öröklés |
| **AC-1.11** | `requirements.lock` létezik, és a tranzitív verziók egyeznek az image-ével | automatikus teszt | bővítés |
| **AC-1.12** | A validációs tesztkészlet **< 300 s** alatt lefut | mérés | Mesterterv 9.1 |

---

## 7. Tesztelési terv (összefoglaló)

Részletek: [`TP-F01`](../testing/TP-F01_vqe_mag.md).

### Kör 1 — funkcionális
AC-1.1 … AC-1.9 automatikus ellenőrzése.

### Kör 2 — robusztussági és negatív
| Eset | Mit vizsgál |
|---|---|
| Hibás molekulaleírás | értelmes kivétel, nem `IndexError` a mélyben |
| Ismeretlen bázis | értelmes kivétel |
| `maxiter=1` | `converged=False`, de nem összeomlás |
| Negatív: elrontott magtaszítás | az AC-1.2 tesztnek buknia kell |
| Negatív: rossz kezdőállapot | az AC-1.8 tesztnek buknia kell |
| Negatív: tolerancia 10⁻¹⁵-re szigorítva | az AC-1.3 tesztnek buknia kell |

### Kör 3 — keresztvalidáció
| Eset | Két független út ugyanarra |
|---|---|
| **X-1** | PySCF FCI ↔ qubit-Hamilton-operátor egzakt diagonalizációja |
| **X-2** | JW ↔ paritás ↔ Bravyi–Kitaev leképezés |
| **X-3** | SLSQP ↔ COBYLA ↔ Nelder–Mead optimalizáló |
| **X-4** | `StatevectorEstimator` ↔ közvetlen `⟨ψ\|H\|ψ⟩` mátrixszorzás |
| **X-5** | PySCF HF ↔ VQE `θ=0`-nál |

Az X-4 külön érdekes: az estimator kikerülésével, tisztán lineáris algebrával
is kiszámoljuk a várható értéket — ez a Qiskit primitív-rétegének független
ellenőrzése.

---

## 8. Kockázatok

| # | Kockázat | Ellenintézkedés |
|---|---|---|
| R1.1 | A `qiskit-nature 0.7.2` (2024) és a `qiskit 1.4.6` (2026) között rejtett inkompatibilitás | A TR-000 1. köre már igazolta a működést; a Fázis 1 tesztjei ezt kiterjesztik. |
| R1.2 | A PySCF OpenMP-hívásai nem determinisztikusak szálanként | `OMP_NUM_THREADS=1` a konténerben; a determinizmus-teszt ezt kimutatná. |
| R1.3 | Az image mérete jelentősen nő (pyscf + qiskit ≈ 1 GB) | Mérjük és dokumentáljuk; `--no-install-recommends`, többlépcsős build megfontolása. |
| R1.4 | A `frozen=True` dataclass nem hash-elhető, ha lista mezőt tartalmaz | Csak `tuple` és skalár mezők; teszt ellenőrzi a hash-elhetőséget. |
| R1.5 | A build ideje a CI-ben túl hosszú | Rétegcache + `cache-from: type=gha`; mérjük. |

---

## 9. Amit ez a fázis **nem** tartalmaz

- Zaj (→ Fázis 1b), hardver (→ Fázis 2), hibaenyhítés (→ Fázis 3).
- Adatbázis (→ Fázis 4) — a `VQEResult` **készen áll** rá, de nem tárolunk.
- Több molekula (→ Fázis 5). A `MoleculeSpec` általános, de csak H2-t validálunk.
- Véges lövésszám (L3a, → Fázis 1b).

---

## 10. Kilépési feltétel

1. Mind a 12 elfogadási kritérium dokumentáltan teljesül a
   [`TR-F01`](../testing/TR-F01_vqe_mag.md) jegyzőkönyvben;
2. a három tesztkör lefutott, a negatív esetek a várt módon buktak;
3. `docs/01_vqe_core.md` elkészült (az alapterv által előírt fázis-dokumentum);
4. `CHANGELOG.md` `0.2.0` bejegyzése kész;
5. `v0.2.0` annotált Git-tag létrehozva.

---

## 11. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
