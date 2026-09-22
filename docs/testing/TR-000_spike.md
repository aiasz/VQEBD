# TR-000 — Előzetes műszaki felderítés (spike) mérési jegyzőkönyve

| | |
|---|---|
| **Azonosító** | TR-000 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Státusz** | **Lezárva — a mérések alapján az ADR-0001…0005 elfogadva** |
| **Szkriptek** | [`scripts/spike/`](../../scripts/spike/) |

---

## 1. A mérés célja

Az alapterv (`quantum-benchmark-projektterv.md`) verziókat és API-kat nem rögzít.
A kvantum-szoftverstack gyorsan változik, ezért a tervdöntéseket **nem feltételezésre,
hanem mérésre** alapozzuk. E jegyzőkönyv célja, hogy **egyetlen sor termelési kód
megírása előtt** eldöntse:

- **K1** — Telepíthető-e egyáltalán a szükséges csomagkészlet egy környezetbe?
- **K2** — Működik-e a `qiskit-nature` → qubit-Hamilton-operátor lánc, és **helyes-e
  fizikailag**?
- **K3** — Működik-e a VQE V2 primitívekkel, `qiskit-algorithms` nélkül?
- **K4** — Használható-e a Mitiq valódi kémiai áramkörön?
- **K5** — Fejleszthető-e a hardveres fázis IBM-kvóta elégetése nélkül?
- **K6** — Mekkorák valójában a tervezett molekulák?

## 2. Mérési környezet

| | |
|---|---|
| **Gazdagép** | Windows 11 Pro 10.0.26200, x86_64 |
| **Docker** | 29.1.3, szerver OS=linux, arch=x86_64, 8 165 470 208 B memória |
| **Docker Compose** | v5.0.0-desktop.1 |
| **Alap-image** | `python:3.11-slim` |
| **Konténer Python** | 3.11.15 |
| **Mérés dátuma** | 2026-09-22 |

> **Megjegyzés.** Minden mérés konténerben futott. Ennek oka nem csak a
> reprodukálhatóság: a **PySCF nem támogatja natívan a Windowst**, így a gazdagépen
> a lánc eleve nem futna (R8 kockázat).

---

## 3. Első kör — függőségfeloldás és funkcionális alapok

### 3.1 K1 — a naiv („legfrissebb mindenből") feloldás **megbukik**

Bemenet (`scripts/spike/resolve.txt`), a PyPI-n 2026-09-22-én elérhető legfrissebb
verziókkal. Parancs: `pip install --dry-run -r resolve.txt`.

**Eredmény: `ResolutionImpossible`.**

```
The conflict is caused by:
    qiskit 2.5.2 depends on numpy<3 and >=2.0
    qiskit-aer 0.17.2 depends on numpy>=1.16.3
    qiskit-nature 0.8.0 depends on numpy>=2
    qiskit-algorithms 0.4.0 depends on numpy>=1.17
    qiskit-ibm-runtime 0.49.0 depends on numpy>=1.26.2
    mitiq 0.47.0 depends on numpy<2.0.0 and >=1.22.0
```

**Megállapítás M1.** A Mitiq 0.47.0 és a Qiskit 2.x kölcsönösen kizárja egymást.

### 3.2 A Mitiq metaadatának ellenőrzése (PyPI JSON API)

| Mitiq | Kiadás | `numpy` | a `qiskit` extra tartalma |
|---|---|---|---|
| 0.47.0 | 2025-09-09 | `<2.0.0,>=1.22.0` | `qiskit~=1.4.2`, `qiskit-aer~=0.17.0`, `qiskit-ibm-runtime~=0.37.0`, `ply==3.11` |
| 0.46.0 | 2025-07-09 | `<2.0.0,>=1.22.0` | ugyanaz |
| 0.45.1 | 2025-05-29 | `<2.0.0,>=1.22.0` | ugyanaz |
| 0.43.0 | 2025-02-12 | `>=1.22.0` | `qiskit~=1.3.1` |

A 0.47.0 a legfrissebb kiadás; **nincs olyan Mitiq-verzió, amely Qiskit 2.x-et
támogatna.** A korlát szándékos, nem elnézés.

### 3.3 A kompatibilis metszet meghatározása

`numpy < 2.0` kényszer mellett, a csomagok deklarált függőségeiből:

| Csomag | Választott | Kizárva, mert |
|---|---|---|
| qiskit | **1.4.6** (2026-06-12) | 2.x → `numpy>=2` |
| qiskit-nature | **0.7.2** | 0.8.0 → `numpy>=2` |
| qiskit-ibm-runtime | **0.41.1** | 0.45.0+ → `qiskit>=2.0.0` |
| qiskit-aer | **0.17.2** | — (`qiskit>=1.1.0`, megfelel) |
| qiskit-algorithms | **0.3.1** | — (tranzitív) |
| pyscf | **2.14.0** | — |

**A feloldás sikeres.** Ténylegesen telepített verziók:

```
numpy 1.26.4 · scipy 1.13.1 · qiskit 1.4.6 · qiskit-aer 0.17.2
qiskit-nature 0.7.2 · qiskit-algorithms 0.3.1 · qiskit-ibm-runtime 0.41.1
mitiq 0.47.0 · pyscf 2.14.0 · cirq-core 1.4.1 · Python 3.11.15
```

### 3.4 Funkcionális próba (`spike_test.py`, 13 lépés)

| # | Lépés | Eredmény |
|---|---|---|
| 1 | Importok, verziók | ✅ a fenti lista |
| 2 | PySCF HF + FCI (H2, 0.735 Å, STO-3G) | ✅ `E_HF = −1.11699900`, `E_FCI = −1.13730604`, `E_nuc = 0.71996899` Ha |
| 3 | `PySCFDriver` | ✅ 2 térbeli pálya, (1,1) részecske, `reference_energy = −1.11699900` |
| 4 | Jordan–Wigner és parity-leképezés | ✅ JW: **4 qubit / 15 tag**; parity 2-qubit redukcióval: **2 qubit / 5 tag** |
| 5 | Egzakt diagonalizáció | ✅ JW: −1.13730604 (Δ=+4.4e−16); parity: −1.13730604 (Δ=+1.3e−15) |
| 6 | UCCSD + HartreeFock ansatz | ✅ 2 qubit, **3 paraméter**, dekomponált mélység 18 |
| 7 | **Saját VQE** (`StatevectorEstimator` + SciPy SLSQP) | ✅ **−1.13730604 Ha (Δ = +7.6e−15)**, 4 iteráció, 17 kiértékelés |
| 8 | Aer `EstimatorV2` shot-alapú (8192) | ✅ −1.151261 Ha (shot-zaj −1.4e−2) |
| 9 | Mitiq qiskit→cirq konverzió | ❌ **`ModuleNotFoundError: No module named 'ply'`** |
| 10 | Mitiq `execute_with_zne` | ❌ ugyanaz |
| 11 | IBM Runtime csatornák | ✅ `['ibm_quantum_platform', 'ibm_cloud']` |
| 12 | Runtime beépített ZNE-opciók | ✅ lásd lent |
| 13 | FakeBackend + `NoiseModel.from_backend` | ✅ FakeManilaV2 (5 qubit), FakeSherbrooke (127 qubit) |

**Megállapítás M2 (9–10. lépés).** A `mitiq` alaptelepítés **nem elegendő**: a
qiskit-interfész `ply`-t igényel. Ez a `mitiq[qiskit]` extrában van, de az extra
egyúttal `qiskit-ibm-runtime~=0.37.0`-t is lepinnelne. → a `ply==3.11` **közvetlen
függőség** lesz.

**K2 megválaszolva.** A lánc működik, és a **leképezés fizikailag igazolt**: a
PySCF FCI (független implementáció, független elmélet) és a qubit-Hamilton-operátor
egzakt sajátértéke **10⁻¹⁵ nagyságrendig egyezik**, mindkét leképezéssel.

**K3 megválaszolva.** A saját VQE-hurok V2 primitívekkel `qiskit-algorithms` nélkül
**gépi pontossággal** eltalálja a referenciát → [ADR-0002](../adr/ADR-0002-sajat-vqe-hurok.md).

**K5 részben megválaszolva (11–13. lépés).**
- A `qiskit-ibm-runtime 0.41.1` támogatja az aktuális `ibm_quantum_platform` csatornát.
- Beépített hibaenyhítési opciók elérhetők:
  `ZneOptions(amplifier, noise_factors, extrapolator, extrapolated_noise_factors)`,
  `ResilienceOptionsV2(measure_mitigation, measure_noise_learning, zne_mitigation, zne,
  pec_mitigation, pec, layer_noise_learning, layer_noise_model)`.
- A `FakeBackend`-ek valódi kalibrációs adatból építenek zajmodellt → **M6**.

---

## 4. Második kör — Mitiq valódi kémiai áramkörön

`scripts/spike/spike_test2.py`, a `ply==3.11` pótlása után.

| # | Lépés | Eredmény |
|---|---|---|
| A | `ply` jelen | ✅ 3.11 |
| B | H2 + parity + UCCSD + egzakt VQE-paraméterek | ✅ `E_ref = −1.13730604`, paraméterek `[−0.0, −0.0, −0.111768]` |
| C | Bound UCCSD → ISA (FakeManilaV2, `opt_level=3`) | ✅ **5 qubit**, mélység 12, `{rz: 8, sx: 7, cx: 2}`, observable **5 qubit / 5 tag** |
| D | Zajos referencia (Aer `from_backend`) | ✅ `E_noisy = −1.122803`, hiba **+14.5 mHa** |
| E | Mitiq konverzió az ISA-áramkörön | ⚠️ `qiskit(5q, d=12) → cirq(17 művelet, **2 qubit**) → qiskit(**2 qubit**)` |
| F | Mitiq folding skálafaktorok | ✅ alap 17 → global 2× : 33, 3× : 51 |
| G | **Teljes Mitiq ZNE-hurok az ISA-áramkörön** | ❌ **`ValueError`** (lásd lent) |
| H | Mitiq `execute_with_zne` szignatúra | ✅ `[circuit, executor, observable, factory, scale_noise, num_to_average]` |

### A G lépés hibája

```
ValueError: The number of qubits of the circuit (2) does not match
            the number of qubits of the ()-th observable (5).
```

**Megállapítás M3.** A Mitiq `qiskit ↔ cirq` konverziója **eldobja azokat a
qubiteket, amelyeken nincs művelet**, és újraindexel. Egy backendre transzpilált
(ISA) áramkörnél ez a qubit-szám csökkenéséhez vezet, így a `apply_layout()`-tal
ellátott observable nem illeszkedik.

**K4 megválaszolva:** a Mitiq használható, de **nem ISA-szinten** — a ZNE-t a
transzpilálás *előtti*, logikai áramkörre kell alkalmazni, és a fizikai leképezést
az executorba kell tenni.

---

## 5. Harmadik kör — ZNE-stratégiák összehasonlítása

`scripts/spike/spike_test3.py`. Cél: az M3 megkerülése és a saját implementáció
validálása.

### 5.1 Saját, ISA-biztos globális hajtogatás

Implementáció: `C → C (C† C)^n`, `λ = 2n+1`, a **qubit-szám és a regiszterek
megőrzésével** (`copy_empty_like` + `compose`), majd bázis-visszafordítás
`transpile(..., optimization_level=0)`-val.

| λ | Hajtogatás után | Bázis-visszafordítás után |
|---|---|---|
| 1 | 5 qubit, mélység 13, 19 kapu | mélység 13, 19 kapu |
| 3 | 5 qubit, mélység 39, 57 kapu | mélység 59, **85 kapu** |
| 5 | 5 qubit, mélység 65, 95 kapu | mélység 105, **151 kapu** |

> **Dokumentálandó korlát.** A hajtogatás `sxdg`-t hoz létre, amely nincs a
> FakeManilaV2 bázisában (`['delay','measure','reset','if_else','id','rz','x','cx',
> 'for_loop','switch_case','sx']`), és három kapura bomlik. Az **egyqubites**
> kapuszám ezért nem lineáris λ-ban. A **kétqubites** (`cx`) kapuszám viszont
> pontosan lineáris (2 / 6 / 10), és a hiba ezekben dominál. → a séma tárolja a
> tényleges `two_qubit_gate_count`-ot.

### 5.2 Zajskálázási mérési pontok

`AerSimulator.from_backend(FakeManilaV2, seed=2024)`, `precision = 0.0015`:

| λ | Energia (Ha) |
|---|---|
| 1 | −1.121556 |
| 3 | −1.091321 |
| 5 | −1.061844 |

A pontok monoton csökkenő trendet mutatnak — a hajtogatás **valóban erősíti a zajt**,
ahogy a ZNE feltételezi [temme2017], [giurgicatiron2020].

### 5.3 Extrapolátorok — saját implementáció

Referencia: `E_L2 = −1.137306 Ha`. Kémiai pontosság: |Δ| < 1.6 mHa.

| Módszer | Energia (Ha) | Δ | Kémiai pontosság |
|---|---|---|---|
| Nyers (λ=1) | −1.121556 | **+15.75 mHa** | ❌ |
| Richardson (Lagrange) | −1.136959 | **+0.35 mHa** | ✅ |
| Lineáris | −1.136357 | +0.95 mHa | ✅ |
| Kvadratikus | −1.136959 | +0.35 mHa | ✅ |
| Exponenciális | −1.136965 | **+0.34 mHa** | ✅ |

**A ZNE a hibát 45-szörösére csökkentette** (15.75 → 0.35 mHa).

### 5.4 Mitiq logikai szinten — az M3 megkerülése

A logikai (transzpilálatlan, de bázisra fordított) áramkörre alkalmazva, az executor
végzi a fizikai leképezést:

| Módszer | Energia (Ha) | Δ |
|---|---|---|
| Nyers, logikai (`opt_level=0`) | −1.100236 | +37.07 mHa |
| Mitiq / Richardson | −1.137885 | **−0.58 mHa** ✅ |
| Mitiq / lineáris | −1.132967 | +4.34 mHa |

**Mellékes megfigyelés.** A nyers hiba `opt_level=3` ISA-áramkörön +15.75 mHa,
`opt_level=0` logikai áramkörön +37.07 mHa. **A transzpiláló optimalizálási szintje
tehát maga is zajcsökkentő tényező** → önálló benchmark-dimenzió lesz.

### 5.5 Kereszt-validáció: saját vs. Mitiq hajtogatás

Ugyanaz a logikai áramkör, ugyanazok a skálafaktorok, kapuszám összevetése:

| λ | Mitiq `fold_global` | Saját `fold_global` | Egyezés |
|---|---|---|---|
| 1 | 23 | 23 | ✅ |
| 3 | 69 | 69 | ✅ |
| 5 | 115 | 115 | ✅ |

**Megállapítás M4.** A saját implementáció **bitre egyező** a Mitiq
referencia-implementációjával. → [ADR-0003](../adr/ADR-0003-mitigacios-architektura.md)

### 5.6 Readout-hiba

FakeManilaV2 mérési hibák qubitenként: `[0.0353, 0.0219, 0.0964, 0.0144, 0.0186]`.
Zajmodell-műveletek: `['cx', 'id', 'measure', 'reset', 'sx', 'x']`.

**Megállapítás M5.** A `measure` zaj jelen van, de a unitáris hajtogatás **nem
skálázza** (a mérés nem unitáris). A ZNE tehát szisztematikus maradékhibát hagy.
→ a mérési hibaenyhítés önálló sémadimenzió [nation2021].

---

## 6. Negyedik kör — molekulaméretek és futásidő

`scripts/spike/spike_test4.py`. Cél: a Fázis 5 kombinációs mátrix reális tervezése.

| Molekula | Aktív tér | Térbeli pálya | Részecske | JW qubit | Parity qubit | Ham. tagok | UCCSD param. | E_HF (Ha) | E_egzakt (Ha) | Idő |
|---|---|---|---|---|---|---|---|---|---|---|
| H2 | teljes | 2 | (1,1) | 4 | **2** | 5 | 3 | −1.11700 | −1.137306 | 0.2 s |
| LiH | teljes | 6 | (2,2) | 12 | 10 | 631 | 92 | −7.86202 | −7.882402 | 2.1 s |
| LiH | (2e, 3o) | 3 | (1,1) | 6 | **4** | 52 | 8 | −7.86202 | −7.863078 | 0.3 s |
| BeH2 | teljes | 7 | (3,3) | 14 | 12 | 666 | 204 | −15.56010 | −15.595118 | 37.2 s |
| BeH2 | (2e, 3o) | 3 | (1,1) | 6 | **4** | 28 | 8 | −15.56010 | −15.560650 | 0.3 s |

**K6 megválaszolva.**
- A parity-leképezés 2-qubit redukcióval **minden esetben 2 qubittel kevesebbet**
  igényel a JW-nél → alapértelmezett leképezés.
- A **teljes** BeH2 (12 qubit, 204 paraméter) szimulátoron is nehéz, valódi hardveren
  a mai zajszinten értelmetlen → a Fázis 5 **aktív tér redukciót** használ.
- Az aktív tér ára mérhető: LiH esetén a (2e,3o) tér **19.3 mHa korrelációt veszít**
  (−7.882402 vs −7.863078), BeH2 esetén **34.5 mHa**-t. Ez nem hiba, hanem
  a modell tudatos egyszerűsítése — a séma ezért **mindig az adott aktív térhez
  tartozó egzakt értéket** tárolja referenciaként, nem a teljes FCI-t.

### H2 disszociációs görbe — időzítés és fizikai helyesség

26 pont, r ∈ [0.3, 2.8] Å, 0.1 Å lépésköz, statevector VQE:

```
26 pont 5.1 s  (0.20 s/pont)
minimum: r = 0.70 Å,  E = −1.136189 Ha
U-alak ellenőrzés: E(0.3) = −0.6018 > E(min) = −1.1362 < E(2.8) = −0.9342  ->  OK
```

A minimum a 0.1 Å-ös rácson 0.70 Å-nél van, összhangban az STO-3G egyensúlyi
kötéshosszal (≈0.735 Å). A görbe alakja fizikailag helyes.

---

## 7. Összesített megállapítások

| # | Megállapítás | Következmény |
|---|---|---|
| **M1** | Mitiq 0.47.0 ⊥ Qiskit 2.x (numpy<2 vs ≥2) | ADR-0001: stack Qiskit 1.4.6-ra rögzítve |
| **M2** | `ply==3.11` rejtett függőség | Közvetlen függőségként felvéve |
| **M3** | Mitiq-konverzió eldobja az inaktív qubiteket | ADR-0003: logikai szintű Mitiq-ZNE |
| **M4** | Saját folding ≡ Mitiq folding (bitre) | ADR-0003: saját ISA-biztos `zne_local` |
| **M5** | ZNE nem javítja a readout-hibát | ADR-0003: `measurement_mitigation` külön dimenzió |
| **M6** | FakeBackend realisztikus zaj kvóta nélkül | Új **Fázis 1b**; kvótavédelem |
| **M7** | A transzpiláló `optimization_level`-je zajcsökkentő | Új benchmark-dimenzió |
| **M8** | Aktív tér nélkül LiH/BeH2 kezelhetetlen | Fázis 5: aktív tér redukció |
| **M9** | PySCF nem fut natívan Windowson | Minden számítás konténerben |

## 8. A mérés reprodukálása

```bash
cd scripts/spike
docker build -f Dockerfile.spike -t vqebd-spike:py311 .
docker run --rm -v "$PWD:/spike" -w /spike vqebd-spike:py311 python spike_test.py
docker run --rm -v "$PWD:/spike" -w /spike vqebd-spike:py311 \
    sh -c "pip install -q ply==3.11 && python spike_test2.py"
docker run --rm -v "$PWD:/spike" -w /spike vqebd-spike:py311 \
    sh -c "pip install -q ply==3.11 && python spike_test3.py"
docker run --rm -v "$PWD:/spike" -w /spike vqebd-spike:py311 python spike_test4.py
```

> **Figyelem.** A spike-szkriptek **nem** a termelési kód részei, és nem is válnak
> azzá. Céljuk a fenti megállapítások reprodukálhatósága. A termelési implementáció
> a `src/vqebd/` alatt, saját tesztekkel készül.

## 9. Nyitott kérdések a következő fázisokra

| # | Kérdés | Hol dől el |
|---|---|---|
| Q1 | Mennyi lövés kell a kémiai pontossághoz molekulánként? | Fázis 1b |
| Q2 | Mely IBM backend elérhető és milyen kvótával? | Fázis 2 |
| Q3 | Melyik aktív tér a „tisztességes" LiH/BeH2-re? | Fázis 5 terve |
| Q4 | A `zne_local` és `zne_mitiq` egyezik-e statisztikailag zajos futáson is? | Fázis 3 |
| Q5 | Skálázódik-e a Richardson-extrapoláció λ>5-re a lövészaj mellett? | Fázis 3 |

---

## 10. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. 4 mérési kör, 9 megállapítás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
