# TR-F01 — Fázis 1 mérési jegyzőkönyve (VQE-mag, H2 szimulátoron)

| | |
|---|---|
| **Azonosító** | TR-F01 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1 — H2-VQE szimulátoron |
| **Vizsgált verzió** | `0.2.0` |
| **Tesztterv** | [`TP-F01`](TP-F01_vqe_mag.md) |
| **Státusz** | **Lezárva — mind a 12 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

| | |
|---|---|
| Elfogadási kritériumok | **12 / 12 teljesült** |
| Automatikus tesztek (konténer) | **248 futott, 248 zöld, 0 hiba** — 10.64 s |
| Automatikus tesztek (szállított image) | 129 zöld, 119 indokolt kihagyás, 0 hiba |
| Negatív tesztek | **11 / 11 az elvárt módon elbukott** |
| Lint (`ruff check`) | 0 hiba (55 fájl) |
| Formázás (`ruff format --check`) | 55 / 55 megfelelő |
| Típusellenőrzés (`mypy --strict`) | 0 hiba (35 forrásfájl) |
| **L2 hiba a Full CI-hez képest** | **+9.33 × 10⁻¹⁵ Ha** |
| **Visszanyert korrelációs energia** | **100.000000 %** |
| A tesztelés során talált és javított hibák | **5** (lásd 8. fejezet) |

---

## 2. Tesztkörnyezet

| | |
|---|---|
| Gazdagép | Windows 11 Pro 10.0.26200, x86_64 |
| Docker | 29.1.3 (szerver: linux/amd64) |
| Image | `vqebd:0.2.0`, **1.44 GB** |
| Alap-image | `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9` |
| Python | 3.11.16 |
| Stack | qiskit 1.4.6 · qiskit-aer 0.17.2 · qiskit-nature 0.7.2 · qiskit-ibm-runtime 0.41.1 · pyscf 2.14.0 · numpy 1.26.4 · scipy 1.13.1 · ply 3.11 |
| Tranzitív fa | 53 csomag (`requirements.lock`) |
| Determinizmus | `PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` |
| Környezet-ujjlenyomat | `1d11220bf9b30930469f691f7d22dc62dd6e2fdcf8d5d2ac1c76d009ed8b9169` |

---

## 3. Kör 1 — funkcionális tesztek

### TC-101 · AC-1.1 — Image építése a teljes stackkel ✅

A build **`build-essential` nélkül** sikerült: minden csomag manylinux
bináris wheel-ként települ, így fordítóra nincs szükség. Egyedüli rendszerszintű
függőség a `libgomp1` (a PySCF OpenMP-futásideje). Ez ≈250 MB-tal kisebb image-et
ad a spike-ban használt változatnál.

### TC-102 … TC-106 · AC-1.2, AC-1.3 — A referencialánc

**Referencia-eset:** H2, 0.735 Å, STO-3G, paritás-leképezés kétqubites
redukcióval, UCCSD, SLSQP, `θ₀ = 0`.

| Mennyiség | Érték (Ha) |
|---|---|
| Magtaszítás `E_nuc` | **+0.7199689944** |
| Hartree–Fock | **−1.1169989968** |
| **L0 — PySCF Full CI** | **−1.1373060358** |
| **L1 — egzakt diagonalizáció** | **−1.1373060358** |
| **L2 — VQE** | **−1.1373060358** |
| Korrelációs energia (`E_FCI − E_HF`) | −0.0203070390 |

| Hiba | Érték | Kritérium | Állapot |
|---|---|---|---|
| Leképezés (L1 − L0) | **+1.332 × 10⁻¹⁵ Ha** | < 1 × 10⁻⁹ Ha | ✅ |
| Ansatz (L2 − L1) | **+7.994 × 10⁻¹⁵ Ha** | < 1 × 10⁻⁷ Ha | ✅ |
| Teljes (L2 − L0) | **+9.326 × 10⁻¹⁵ Ha** | < 1.5936 × 10⁻³ Ha | ✅ |
| Visszanyert korreláció | **100.000000 %** | 100 % ± 1 × 10⁻⁴ % | ✅ |

Optimalizálás: **3 iteráció, 14 célfüggvény-kiértékelés**.
Optimális paraméterek: `[−5 × 10⁻⁸, −6 × 10⁻⁸, −0.1117685]`.

> **Értelmezés.** A mért hiba a kémiai pontosságnak (1.59 × 10⁻³ Ha) nagyjából a
> **10⁻¹²-szerese**. Az első két paraméter gyakorlatilag nulla: a H2 alapállapotának
> szimmetriái miatt csak a kétszeres gerjesztés amplitúdója nem tűnik el. Ez
> fizikailag várt viselkedés, és további megerősítése annak, hogy az ansatz
> helyesen épül fel.

### TC-107 · AC-1.4 — **Az alapterv eredeti kritériuma** ✅

> „a kapott energia −1.137 Hartree körül van (±0.01 Hartree tolerancia)"

Mért érték: **−1.1373060358 Ha**, azaz az ablak közepétől 3.06 × 10⁻⁴ Ha-ra —
a megengedett tolerancia **3 %-án** belül.

### TC-108, TC-109 · AC-1.5 — Variációs elv ✅

`E_VQE − E_egzakt = +9.326 × 10⁻¹⁵ Ha > 0`, tehát a VQE **felülről** közelít,
ahogy a variációs elv előírja. A korrelációs energia `−0.0203 Ha < 0`, azaz a
Hartree–Fock valóban felső korlát.

### TC-110 · AC-1.6 — Determinizmus (D1 szint) ✅

Három egymást követő futtatás, azonos konfigurációval:

```
futás 1: -1.137306035753391
futás 2: -1.137306035753391
futás 3: -1.137306035753391

bitre azonos            : True
paraméterek azonosak    : True
kiértékelések száma     : 14 / 14 / 14
```

`config_hash = a52e7c035a93463be1f9c82f4506df64d01684c1e81f63ae607a702d83af7040`

> Az alapterv így fogalmaz: *„ne menj tovább, amíg ez nem megy stabilan, többször
> lefuttatva is ugyanazt az eredményt adja."* Ez a követelmény mostantól **gépi
> bizonyíték**, nem kézi megfigyelés: a teszt `==` egyenlőséget követel, nem
> közelítést.

### TC-111, TC-112 · AC-1.7 — Leképezés-függetlenség ✅

| Leképezés | Qubit | Pauli-tag | Paraméter | E_VQE (Ha) | Ansatz-hiba |
|---|---|---|---|---|---|
| Jordan–Wigner | 4 | 15 | 3 | −1.1373060358 | +7.860 × 10⁻¹⁴ |
| Bravyi–Kitaev | 4 | 15 | 3 | −1.1373060358 | +2.753 × 10⁻¹⁴ |
| **Paritás (2-qubit red.)** | **2** | **5** | 3 | **−1.1373060358** | **+7.994 × 10⁻¹⁵** |

Szórás a három leképezés között: **6.97 × 10⁻¹⁴ Ha** (kritérium: < 1 × 10⁻⁷ Ha).

> **Ez a projekt legerősebb keresztvalidációja.** Három különböző algebrai
> konstrukció ugyanazt a fizikai rendszert írja le; ha bármelyik implementációja
> hibás lenne, az energiák eltérnének. A paritás-leképezés ráadásul **fele annyi
> qubitet és harmadannyi Pauli-tagot** igényel — ez a mérési költséget közvetlenül
> csökkenti, ami a Fázis 2-től (valódi hardver) döntő lesz.

### TC-113 · AC-1.8 — `E(θ=0) ≡ E_HF` ✅

```
E(θ=0) : -1.116998996754 Ha    (a VQE első célfüggvény-kiértékelése)
E_HF   : -1.116998996754 Ha    (PySCF SCF)
eltérés: +1.776e-15 Ha
```

Két **teljesen független** úton ugyanaz a szám: a PySCF önkonzisztens
mezőszámításából, illetve a Qiskit-áramkör várható értékéből. Ez igazolja, hogy
az ansatz kezdőállapota valóban a Hartree–Fock determináns.

### TC-114 · AC-1.9 — Önállóan futtatható modul ✅

```
$ docker run --rm vqebd:0.2.0 python -m vqebd --version
vqebd 0.2.0
```

A teljes kimenet a [`docs/01_vqe_core.md`](../01_vqe_core.md) 1. fejezetében.
A CLI kilépési kódja **gépi ellenőrzésre** is alkalmas: `0` csak akkor, ha az
eredmény kémiai pontosságon belül van **és** a variációs elv teljesül.

### TC-115 · AC-1.10 — Minőségi kapuk ✅

```
ruff check  --no-cache .          -> All checks passed!          (55 fájl)
ruff format --no-cache --check .  -> 55 files already formatted
mypy                              -> Success: no issues found in 35 source files
```

### TC-116 · AC-1.11 — `requirements.lock` ✅

53 csomag rögzítve. A `tests/repo/test_requirements.py` ellenőrzi:

- minden kötelező csomag `==` pinnel szerepel a `requirements.txt`-ben;
- a lock ugyanazt a verziót rögzíti;
- nincs verzióütközés a kettő között;
- a GPL-3.0 licencű `mitiq` **nem** közvetlen függőség (ADR-0003);
- minden közvetlen függőség bekerül a `vqebd.versions.TRACKED_PACKAGES` listába.

### TC-117 · AC-1.12 — Futásidő ✅

| Tesztkör | Tesztek | Idő |
|---|---|---|
| `tests/validation` | 23 | **6.83 s** (korlát: 300 s) |
| `tests/integration` | 12 | 2.79 s |
| `tests/unit` | 94 | 1.15 s |
| `tests/repo` | 119 | 3.57 s |
| **Összesen** | **248** | **10.64 s** |

A leglassabb egyedi teszt: `test_optimizers_agree[Nelder-Mead]`, 1.30 s.

---

## 4. Kör 2 — robusztussági és negatív tesztek

### 4.1 Hibakezelés (TC-201 … TC-210) ✅

Minden vizsgált határeset **beszédes, azonosítható hibát** ad, nem mély
könyvtárbeli kivételt vagy csendes rossz eredményt:

| Eset | Bemenet | Viselkedés |
|---|---|---|
| Üres molekulanév, üres geometria, negatív spin, nempozitív kötéshossz | `MoleculeSpec(...)` | `ValueError` a mezőt megnevezve |
| `maxiter ≤ 0`, `tol ≤ 0` | `OptimizerSpec(...)` | `ValueError` |
| `--basis nincs-ilyen-bazis` | CLI | kilépési kód **2**, saját hibaüzenet |
| `--optimizer NINCS_ILYEN` | CLI | kilépési kód **2**, „nem támogatott optimalizáló" |
| `--mapper nincs_ilyen` | CLI | argparse szintű hiba |
| `maxiter=1` | optimalizáló | `converged=False`, **nem** kivétel |
| Paraméter nélküli ansatz | optimalizáló | egyetlen kiértékelés, nincs összeomlás |
| Konfiguráció mezőmódosítása | `VQEConfig` | `FrozenInstanceError` |

### 4.2 Negatív tesztek — a védelmek bizonyítása ✅

A [`scripts/negative_test_harness.py`](../../scripts/negative_test_harness.py)
**izolált repó-másolaton** ront el dolgokat; az eredeti repó változatlan marad.
A Fázis 1-ben három új eset került be.

**Előfeltétel:** a sértetlen másolaton minden teszt zöld. ✅

| Eset | Rontás | Elvárt bukás | Eredmény |
|---|---|---|---|
| TC-N1 … TC-N8 | (Fázis 0 esetei) | — | ✅ mind |
| **TC-N9** | A `requirements.txt` numpy-pinje `1.26.4` → `1.26.3` | `test_required_package_is_pinned` | ✅ |
| **TC-N10** | A GPL-3.0 licencű `mitiq` felvétele közvetlen függőségként | `test_gpl_package_is_not_a_direct_dependency` | ✅ |
| **TC-N11** | A seed-származtatás elválasztója `:` → `\|` | `test_seed_set_matches_golden_values` | ✅ |

```
Eredmény: 11/11 negatív eset bukott el az elvárt módon.
Minden védelmi teszt bizonyítottan képes hibát jelezni.
```

---

## 5. Kör 3 — keresztvalidáció

| Eset | Két (vagy több) független út | Eredmény |
|---|---|---|
| **TC-X101** | PySCF Full CI ↔ qubit-Hamiltoni egzakt diagonalizáció | egyezés 1.33 × 10⁻¹⁵ Ha-ig ✅ |
| **TC-X102** | Jordan–Wigner ↔ paritás ↔ Bravyi–Kitaev | szórás 6.97 × 10⁻¹⁴ Ha ✅ |
| **TC-X103** | SLSQP ↔ COBYLA ↔ Nelder-Mead ↔ L-BFGS-B ↔ Powell | mind kémiai pontosságon belül ✅ |
| **TC-X104** | Qiskit `StatevectorEstimator` ↔ közvetlen `⟨ψ\|H\|ψ⟩` mátrixszorzás | egyezés 1 × 10⁻⁹ Ha-ig ✅ |
| **TC-X105** | PySCF Hartree–Fock ↔ VQE `θ = 0`-nál | eltérés 1.78 × 10⁻¹⁵ Ha ✅ |
| **TC-X106** | 2-qubit redukcióval ↔ anélkül | azonos energia, 2 qubit különbség ✅ |
| **TC-X107** | Disszociációs görbe alakja | U-alakú, minimum a helyén ✅ |

### TC-X104 — az estimator-réteg megkerülése

Az energiát a Qiskit primitív megkerülésével, tisztán lineáris algebrával is
kiszámoltuk: `Statevector(bound_circuit)` → `ψ`, `SparsePauliOp.to_matrix()` → `H`,
majd `⟨ψ|H|ψ⟩`. A két érték 10⁻⁹ Ha-on belül egyezik. Ez a primitív-használatunk
független ellenőrzése: egy elcsúszott paraméter-sorrendet vagy egy illesztetlen
observable-t azonnal kimutatna.

### TC-X107 — H2 disszociációs görbe

14 pont, 1.65 s (0.118 s/pont), `compute_fci=False`:

| r (Å) | E (Ha) | | r (Å) | E (Ha) |
|---|---|---|---|---|
| 0.300 | −0.60180371 | | 0.900 | −1.12056028 |
| 0.400 | −0.91414970 | | 1.000 | −1.10115033 |
| 0.500 | −1.05515979 | | 1.200 | −1.05674075 |
| 0.600 | −1.11628601 | | 1.500 | −0.99814935 |
| 0.700 | −1.13618945 | | 2.000 | −0.94864111 |
| **0.735** | **−1.13730604** | | 2.500 | −0.93605492 |
| 0.800 | −1.13414767 | | 3.000 | −0.93363184 |

```
minimum: r = 0.735 Å, E = −1.13730604 Ha
U-alak : E(0.3) = −0.601804  >  E(min) = −1.137306  <  E(3.0) = −0.933632   -> OK
```

A görbe fizikailag helyes: rövid távolságon a magtaszítás, nagy távolságon a
kötés hiánya emeli az energiát. A minimum a vizsgált rácson pontosan a
referencia-geometriánál van.

> **Módszertani megjegyzés.** A nagy távolságú határérték (−0.9336 Ha, r = 3 Å)
> nem éri el a két izolált hidrogénatom energiáját (−1.0 Ha). Ez **nem hiba**,
> hanem a restricted Hartree–Fock referenciaállapot ismert korlátja: a zárt héjú
> RHF nem írja le helyesen a homolitikus kötéshasadást. A jelenség jól ismert, és
> a Fázis 5 disszociációs vizsgálatainál külön dokumentálandó lesz.

---

## 6. Elfogadási kritériumok — összesítés

| # | Kritérium | Mért érték | Állapot |
|---|---|---|---|
| **AC-1.1** | `docker build` a teljes stackkel | kilépési kód 0, 1.44 GB | ✅ |
| **AC-1.2** | L0 ≡ L1, \|Δ\| < 1e-9 Ha | **1.33 × 10⁻¹⁵ Ha** | ✅ |
| **AC-1.3** | L2 ≈ L1, \|Δ\| < 1.6 mHa | **7.99 × 10⁻¹⁵ Ha** | ✅ |
| **AC-1.4** | **Alapterv:** E ∈ −1.137 ± 0.01 Ha | **−1.1373060358 Ha** | ✅ |
| **AC-1.5** | Variációs elv | +9.33 × 10⁻¹⁵ Ha > 0 | ✅ |
| **AC-1.6** | Determinizmus: bitre azonos | 3/3 futás azonos | ✅ |
| **AC-1.7** | Leképezés-függetlenség | szórás 6.97 × 10⁻¹⁴ Ha | ✅ |
| **AC-1.8** | E(θ=0) ≡ E_HF | 1.78 × 10⁻¹⁵ Ha | ✅ |
| **AC-1.9** | Önállóan futtatható modul | `python -m vqebd` | ✅ |
| **AC-1.10** | Lint, típus, tesztek | 0 + 0 + 0 hiba | ✅ |
| **AC-1.11** | `requirements.lock` konzisztens | 53 csomag, 0 ütközés | ✅ |
| **AC-1.12** | Validáció < 300 s | **6.83 s** | ✅ |

---

## 7. A hibaforrások szétválasztása — amit a referencialánc megmutat

Ez a fázis legfontosabb módszertani eredménye. Az L0–L2 lánc számszerűsíti, hogy
a végső hibából mennyit ad az egyes forrás:

```
E_L0 = −1.1373060358 Ha        Full CI (PySCF)
   │   leképezési hiba:  +1.33 × 10⁻¹⁵ Ha    (0.014 % a teljes hibából)
E_L1 = −1.1373060358 Ha        egzakt diagonalizáció
   │   ansatz-hiba:      +7.99 × 10⁻¹⁵ Ha    (0.086 % a teljes hibából)
E_L2 = −1.1373060358 Ha        VQE
       teljes hiba:      +9.33 × 10⁻¹⁵ Ha
```

**Következmény a további fázisokra:** mivel a leképezés és az ansatz hibája
gépi pontosság nagyságrendű, a Fázis 1b-től mért **minden** eltérés
egyértelműen a **zajból** (statisztikus vagy hardveres) származik. A
hibaenyhítés hatását így tisztán, zavaró tényezők nélkül lehet mérni.

---

## 8. A tesztelés során talált és javított hibák

### H-05 — A `scipy.optimize` TNC metódusa csendben eldobta az iterációs korlátot

*Megtalálta:* `OptimizeWarning` a teszt-kimenetben.
*Ok:* a SciPy metódusai eltérő opciókulcsot használnak az iterációs korlátra: a
`TNC` nem `maxiter`-t, hanem `maxfun`-t ismer. Ismeretlen kulcs esetén a SciPy
**figyelmeztet és eldobja** a beállítást — a korlát tehát **nem érvényesült**,
csendben.
*Javítás:* explicit `_MAXITER_KEY` leképezés, **és** az `OptimizeWarning` hibává
emelése: ha egy metódus nem fogadja el az opciót, azonnali `ValueError` jelez.
Új teszt (`test_iteration_limit_option_is_accepted_by_every_method`) minden
támogatott metódusra ellenőrzi.
*Tanulság:* a csendben eldobott beállítás veszélyesebb a hangos hibánál. Ahol egy
könyvtár figyelmeztetéssel nyel el egy paramétert, ott a figyelmeztetést hibává
kell emelni.

### H-06 — A `qiskit-nature` több mezője lehet `None`

*Megtalálta:* `mypy --strict`.
*Ok:* a `qiskit-nature` **szállít** típusannotációkat, és azok szerint a
`num_particles`, a `num_spatial_orbitals` és a `nuclear_repulsion_energy`
egyaránt `| None` típusú (a meghajtó nem minden feladatra tölti ki őket). A
kódom ezt nem kezelte.
*Javítás:* mind a négy mezőre explicit ellenőrzés, molekulanevet tartalmazó,
beszédes `RuntimeError`-ral.
*Tanulság:* a szigorú típusellenőrzés olyan határeseteket tár fel, amelyek H2-n
sosem jelentkeznének — de egy szokatlan molekulánál (Fázis 5) futásidejű
`NoneType`-hibaként bukkannának elő, a számítás közepén.

### H-07 — A CLI egyszerre volt csomagimport és `__main__`

*Megtalálta:* `RuntimeWarning` a `runpy`-tól az első füstteszt során.
*Ok:* a `vqebd.vqe.runner` modult a csomag `__init__.py`-ja importálta, miközben
`python -m vqebd.vqe.runner` néven futtatva a Python **újra** végrehajtotta.
*Javítás:* a CLI külön modulba (`vqebd.cli`) került, a belépési pont
`python -m vqebd` lett (`__main__.py`).
*Tanulság:* a „futtatható modul" és a „csomag által importált modul" szerepe
ne keveredjen; a kettő szétválasztása egyúttal tesztelhetőbb CLI-t ad.

### H-08 — A negatív harness TC-N8 esete verziófüggő volt

*Megtalálta:* maga a negatív harness, a `0.2.0`-ra emelés után.
*Ok:* a rontás a `## [0.1.0]` szakaszcímre volt **konkrét verziószámmal**
kódolva. A verzióemelés után a legfelső kiadás `0.2.0` lett, így a csere már nem
a legfelső bejegyzést érintette — a negatív eset csendben hatástalanná vált.
*Javítás:* a rontás mostantól **mintát** keres (az első nem-`Unreleased`
szakaszcímet), nem konkrét számot.
*Tanulság:* **a tesztelő eszköz maga is tesztelendő.** Ha a negatív harness nem
jelzett volna, azt hittük volna, hogy a CHANGELOG-védelem működik — miközben
nem. Ez pontosan az a hibaosztály, amelynek felderítésére a negatív kör létezik.

### H-09 — A titokszűrő a jegyzőkönyv saját hash-eire jelzett

*Megtalálta:* `test_no_token_like_strings_in_tracked_files`, a záró ellenőrzésen.
*Ok:* ebbe a jegyzőkönyvbe bekerült a mért `config_hash`
(`a52e7c03…`) és a környezet-ujjlenyomat (`1d11220b…`). Mindkettő 64 hexa
karakter — pontosan olyan alakú, mint egy IBM API-token.
*Javítás:* az `ALLOWED_CONTEXTS` lista kibővítve a `config_hash`, `fingerprint`,
`ujjlenyomat` és `commit` címkékkel. **Nem a mintát lazítottuk**, hanem a
*környezetet* ismerjük fel: egy valódi token soha nem jelenik meg ilyen címke
mellett, míg a mi reprodukálhatósági azonosítóink mindig.
*Tanulság:* ez **nem kódhiba, hanem a védelem helyes működése**. Fontos
megkülönböztetni: egy biztonsági szűrő téves riasztása nem ok a szűrő
gyengítésére — a helyes válasz a jogos eset *nevesített* engedélyezése,
dokumentált indoklással. Az ellenkezője (a szabály tágítása) észrevétlenül
kinyitná az ajtót a valódi szivárgás előtt.

> **Módszertani megjegyzés.** Mind az öt megállapítást **gépi ellenőrzés** tette
> (figyelmeztetés, típusellenőrző, negatív harness, titokszűrő) — egyiket sem kézi
> átnézés. Kettő közülük „csendes" hiba volt: az eldobott SciPy-beállítás (H-05) és
> a hatástalanná vált negatív eset (H-08) egyaránt **zöld tesztek mellett** fordult
> elő. Ezt a hibaosztályt kizárólag a többkörös, negatív eseteket is futtató
> eljárás képes felderíteni.

---

## 9. Ismert, külső eredetű figyelmeztetések

| Figyelmeztetés | Forrás | Hatás | Kezelés |
|---|---|---|---|
| `PendingDeprecationWarning: NLocal is pending deprecation` (21 + 10 alkalom) | `qiskit-nature 0.7.2` UCCSD-je a Qiskit 1.4 `NLocal` osztályát használja | nincs — a helyességet nem érinti | Külső csomag; a `qiskit-nature` Qiskit 2.x-kompatibilis ágán megszűnik. Az ADR-0001 felülvizsgálati feltételei között nyilvántartva. |
| `UserWarning: Basis may be available in basis-set-exchange` | PySCF, ismeretlen bázisnév esetén | nincs | Csak a hibakezelési tesztben jelentkezik, szándékosan. |

A `pyproject.toml` `filterwarnings` beállítása a **saját** kódunk
(`vqebd.*`) elavultsági figyelmeztetéseit hibává emeli; a külső csomagokét nem,
mert azokra nincs ráhatásunk.

---

## 10. Nyitott pontok a következő fázisra

| # | Pont | Hol dől el |
|---|---|---|
| O5 | Mennyi lövés kell a kémiai pontossághoz H2-re? (TR-000 Q1) | Fázis 1b |
| O6 | Melyik optimalizáló bírja legjobban a shot-zajt? (SLSQP véges differenciái zajon félrevezetők) | Fázis 1b |
| O7 | Az RHF-referencia disszociációs korlátja — hogyan dokumentáljuk a Fázis 5 görbéin? | Fázis 5 |
| O8 | Az image mérete 1.44 GB; szükséges-e többlépcsős build? | Fázis 8 |
| O9 | A `qiskit-nature` `NLocal` elavulása mikor válik blokkolóvá? | ADR-0001 felülvizsgálat |

---

## 11. Kilépési nyilatkozat

A [`TP-F01`](TP-F01_vqe_mag.md) 5. fejezete szerinti **mind a hét** kilépési
feltétel teljesült:

1. ✅ TC-101 … TC-117 zöld;
2. ✅ TC-201 … TC-210 zöld;
3. ✅ TC-N1 … TC-N11 az elvárt módon elbukott, izolált másolaton;
4. ✅ TC-X101 … TC-X107 zöld;
5. ✅ az eredmények rögzítve ebben a jegyzőkönyvben;
6. ✅ [`docs/01_vqe_core.md`](../01_vqe_core.md) elkészült;
7. ✅ `CHANGELOG.md` `0.2.0` bejegyzése kész; `v0.2.0` annotált Git-tag létrehozva.

**A Fázis 1 lezárható. A Fázis 1b megkezdhető.**

---

## 12. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. 12/12 elfogadási kritérium, 5 megállapítás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
