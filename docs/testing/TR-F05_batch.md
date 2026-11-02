# TR-F05 — Fázis 5 mérési jegyzőkönyve (batch, aktív tér, statisztika)

| | |
|---|---|
| **Azonosító** | TR-F05 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.1.0 (7. pont: 5.H hardveres mérés) |
| **Dátum** | 2026-09-25 (batch-futtatás) · 2026-11-02 (lezárás, 5.H) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Fázis** | 5 — Batch-futtatás, aktív tér, statisztikai módszertan |
| **Tesztterv** | [`TP-F05`](TP-F05_batch.md) |
| **Terv / döntés** | [`phase_05.md`](../plan/phase_05.md) · [`ADR-0007`](../adr/ADR-0007-batch-statisztika.md) |
| **Kódállapot** | `vqebd` 0.8.0, Docker-image `vqebd:0.8.0` |
| **Státusz** | **Lezárva — mind a 10 elfogadási kritérium teljesült.** A 7. pont a kiadás utáni 5.H hardveres méréssel egészíti ki |

---

## 1. Összefoglalás

A Fázis 5 három képességet ad a VQEBD-hez: **aktív tér** (LiH és BeH₂ 8–10 qubiten
a frozen-core redukcióval), **batch-motor** (determinisztikus, folytatható futáslista)
és **statisztikai módszertan** (t-CI, négyállapotú besorolás, hibaköltségvetés).

| | |
|---|---|
| Elfogadási kritériumok | **10 / 10 teljesült** |
| Tesztkészlet | **529 teszt: 528 sikeres, 1 kihagyott** (TC-302, a `mitiq` nincs a képben) |
| `f5-deterministic` | 50 / 50 futás, 0 hibás, összesen 2535 s |
| `f5-statistical` | 180 / 180 futás, 0 hibás |
| Új ábrák | fig07 (aktív tér), fig08 (ismétlés), fig09 (hibaköltségvetés), fig10 (hardveres PES, 5.H) |
| Új / javított megállapítás | K5 lezárva (4. pont); K8 új (3.2 pont) |

**A fázis tudományos eredménye két mondatban.** Az ismétlés a szórást N^−½ szerint
csökkenti, a torzítást nem: a torzítás ellen a *módszer* (ZNE) hat. Egyik zajos
konfiguráció sem éri el a kémiai pontosságot, és ezt a konfidenciaintervallum
statisztikailag is kizárja.

---

## 2. Elfogadási kritériumok

| AC | Teszteset | Eredmény | Bizonyíték |
|---|---|---|---|
| AC-5.1 | TC-501 | ✅ L1 ↔ CASCI ≤ 4·10⁻¹⁴ Ha | `tests/validation/test_active_space.py` |
| AC-5.2 | TC-502 | ✅ teljes térben `energy_offset == nuclear_repulsion_energy` bitre; a v0.7.1 `config_hash`-ek változatlanok | ugyanott |
| AC-5.3 | TC-503 | ✅ LiH (2e,3o): 0 ≤ L2 − L1 < 1.6 mHa mindhárom platformon; a mért legnagyobb eltérés 2.1·10⁻⁶ Ha | ugyanott; 3.1 pont |
| AC-5.4 | TC-504 | ✅ azonos spec → azonos futáslista és `run_id`; preset-méretek 50 / 180 / 5 | `tests/unit/test_batch.py` |
| AC-5.5 | TC-505 | ✅ `max_runs=2` utáni folytatás = megszakítás nélküli batch, bitre | `tests/validation/test_batch_statistics.py` |
| AC-5.6 | TC-506a–c | ✅ szintetikus meredekség −0.5 ± 0.1; valódi Aer-mintán −0.5 ± 0.15; a torzítás N = 16 és 256 mellett azonos | tesztek + fig08 (5. pont) |
| AC-5.7 | TC-507 | ✅ t-CI lefedettség N = 5-nél 95 ± 1.5%; a besorolás határesetei | `tests/unit/test_stats.py` |
| AC-5.8 | TC-508 | ✅ \|átlag − egzakt zajos érték θ_opt-ban\| < 4 SEM, lövészajos és zajos backenden | `tests/validation/test_batch_statistics.py` |
| AC-5.9 | TC-509 | ✅ v1 → v2 migráció; a v1 rekord bitre változatlan; a második megnyitás nem migrál újra | `tests/unit/test_storage.py` |
| AC-5.10 | TC-510 | ✅ mindkét batch lefutott; az ábrák és ez a jegyzőkönyv a generált JSON-ból készült | 3. és 4. pont |

A negatív és robusztussági ellenőrzések (TP-F05 3. pont) a fenti tesztfájlokban
futnak, és mind zöldek.

---

## 3. Determinisztikus batch — `f5-deterministic`

Adat: [`docs/figures/data/f5_deterministic.json`](../figures/data/f5_deterministic.json)
(50 / 50 futás; minden futás konvergált). Referencia: LiH és BeH₂ aktív térben a
CASCI (L0′), H₂-n a Full CI.

### 3.1 Platformok egyezése

| Rendszer | Platformok | Legnagyobb \|L2 − ref\| | Platformok közti szórás |
|---|---|---|---|
| H₂ (6 geometria) | Qiskit, Cirq, qsim | 4.7·10⁻⁸ Ha | ≤ 4.7·10⁻⁸ Ha |
| LiH (2e,3o), 4 geometria | Qiskit, Cirq, qsim | 2.1·10⁻⁶ Ha | ≤ 2.1·10⁻⁶ Ha |
| BeH₂ (2e,3o), 3 geometria | Qiskit, Cirq, qsim | 2.6·10⁻⁶ Ha | ≤ 2.6·10⁻⁶ Ha |
| LiH (2e,5o), 3 geometria | Qiskit, Cirq | 1.3·10⁻¹⁰ Ha | ≤ 7.2·10⁻¹¹ Ha |
| LiH (2e,5o), 1.595 Å | Qiskit, Cirq, **qsim** | **2.8·10⁻⁵ Ha** | **2.8·10⁻⁵ Ha** (qsim) |
| BeH₂ (4e,6o), 1.33 Å | Qiskit, Cirq | 3.7·10⁻⁴ Ha | 1.7·10⁻¹¹ Ha |

A két `complex128` platform (Qiskit, Cirq) frozen-core térben is 10⁻¹⁰–10⁻¹¹ Ha
pontossággal egyezik. A qsim (`complex64`) eltérése a tér méretével nő.

### 3.2 Új megállapítás (K8): a qsim LiH (2e,5o)-n túllépi a platformtűrést

A qsim névleges tűrése `1·10⁻⁵ Ha` (`platforms.py`). A LiH (2e,5o) 1.595 Å pontján
az eltérés **2.8·10⁻⁵ Ha, a tűrés 2.8-szorosa**. Ez nem hibás eredmény, mert a
kémiai pontosság 1.6·10⁻³ Ha, és az eltérés ennek 1.8%-a. A tűrést viszont
nem teljesíti, és erre egyik teszt sem figyel: a TC-503 csak a LiH (2e,3o)-t fedi.

**Ok (mérve, 2026-11-02).** Ugyanaz a feladat (LiH (2e,5o), 1.595 Å, 24 paraméter),
ugyanaz a Powell (`maxiter=2000`, seed 20260922), `complex128` Qiskit-en:

| Futás | Optimalizáló | Kiértékelés | E − CASCI |
|---|---|---|---|
| Qiskit `complex128` | SLSQP | 226 | 2.1·10⁻¹¹ Ha |
| Qiskit `complex128` | **Powell** | 4309 | **9·10⁻¹² Ha** |
| qsim `complex64` | **Powell** | 7178 | **2.8·10⁻⁵ Ha** |

A Powell tehát `complex128`-on 10⁻¹¹ Ha-ra konvergál, így **nem az optimalizáló
az ok**: az eltérés a `complex64` aritmetikából ered (közvetlenül, vagy úgy, hogy a
Powell vonalkeresése a ~10⁻⁷ nagyságrendű energiazajon korábban megáll; a kettőt
nem választottuk szét). **Korlát:** egyetlen mérési pont, egyetlen seed.

**Döntés:** a névleges `1·10⁻⁵ Ha` tűrést **nem módosítjuk** egyetlen pont alapján.
A tűrés a qsim-re a (2e,3o) terekben igaz (legnagyobb eltérés 2.1·10⁻⁶ Ha), a
24 paraméteres frozen-core térben nem. Ez a tűrés érvényességi tartományának
korlátja, nem hibás eredmény: a 2.8·10⁻⁵ Ha a kémiai pontosság 1.8%-a. A
`within_backend_tolerance` nincs az adatbázisban tárolva, így a rekord nem jelzi a
túllépést; az erre vonatkozó állítás ebből a jegyzőkönyvből olvasható ki.
**Nyitott:** a tűrés mérete-függő pontosítása több pont (pl. a BeH₂ qsim-cellái,
több seed) mérése után indokolt.

### 3.3 BeH₂ (4e,6o): az ansatz-hiba

A Qiskit és a Cirq egyaránt L2 − CASCI = **+0.371 mHa** értéket ad. Ez az UCCSD
ansatz hibája, nem a platformé (a két érték 1.7·10⁻¹¹ Ha-ra egyezik). A teljes hiba
a Full CI-hez **0.71 mHa** = csonkolás 0.34 + ansatz 0.37, kémiai pontosságon belül
(fig09, utolsó sor).

### 3.4 Futásidő

Összesen 2535 s. A leghosszabbak: BeH₂ (4e,6o) Cirq 951 s, Qiskit 370 s; LiH (2e,5o)
qsim 623 s. A qsim + Powell költsége a paraméterszámmal meredeken nő
(`spec.py`, `_f5_deterministic` docstring).

---

## 4. Statisztikai batch — `f5-statistical`

Adat: [`docs/figures/data/f5_statistical.json`](../figures/data/f5_statistical.json)
(180 / 180 futás). Hiba a Full CI-hez, mHa; N seed, K = 16 friss kiértékelés
futásonként; 95%-os t-konfidenciaintervallum.

| Konfiguráció | N | átlag | szórás | 95% CI | RMSE | besorolás |
|---|---|---|---|---|---|---|
| H₂ 0.735 · lövészaj | 20 | +11.59 | 8.27 | [+7.72, +15.46] | 14.12 | excluded |
| H₂ 0.735 · zajos | 20 | +38.15 | 8.38 | [+34.23, +42.07] | 39.02 | excluded |
| H₂ 0.735 · ZNE lineáris | 20 | +15.52 | 8.17 | [+11.70, +19.35] | 17.45 | excluded |
| H₂ 0.735 · ZNE Richardson | 20 | +11.54 | 10.03 | [+6.84, +16.23] | 15.12 | excluded |
| H₂ 1.5 · lövészaj | 20 | +15.23 | 8.56 | [+11.22, +19.24] | 17.37 | excluded |
| H₂ 1.5 · zajos | 20 | +29.63 | 9.02 | [+25.41, +33.85] | 30.91 | excluded |
| H₂ 1.5 · ZNE lineáris | 20 | +19.00 | 8.99 | [+14.79, +23.21] | 20.92 | excluded |
| H₂ 1.5 · ZNE Richardson | 20 | +17.24 | 8.63 | [+13.20, +21.28] | 19.19 | excluded |
| LiH (2e,3o) · lövészaj | 10 | +28.04 | 7.65 | [+22.57, +33.52] | 28.97 | excluded |
| LiH (2e,3o) · zajos | 10 | **+465.65** | 13.11 | [+456.27, +475.03] | 465.82 | excluded |

**Értelmezés.**

1. **Egyik zajos konfiguráció sem éri el a kémiai pontosságot** (1.6 mHa), és a CI
   ezt ki is zárja (`excluded`), nem csupán „nem sikerült".
2. **Lövészajnál is +11.6 mHa a hiba**, pedig a lövészaj rögzített θ-nál
   torzítatlan. A hiba az *optimalizálásból* ered: a H₂ korrelációs energiája
   (~1.8σ) a zajban elvész, ezért a COBYLA nem θ*-ban áll meg. A fig09 ezt
   „optimalizálás zajban" (+11.66) és „eszközzaj θ_opt-ban" (−0.07) tagokra bontja.
3. **A ZNE csökkenti a hibát** (+38.2 → +11.5 mHa a Richardson-nal), de nem viszi
   a sávba. K = 16-nál a Richardson RMSE-je jobb a lineárisénál (15.1 vs. 17.5 mHa),
   fordítva, mint a TR-F03 K = 1-es elemzésében. Ez egybevág a „lövésszámfüggő
   extrapolátor-választás" állítással: nagyobb K-nál a szórás kisebb, ezért a
   torzítás dominál.
4. **LiH (2e,3o) zajosan: +466 mHa**, messze a Hartree–Fock fölött. Ez az UCCSD
   mélységi fala: ~170 CX a FakeManilaV2 ~1%-os CX-hibája mellett.
5. **A kiválasztási torzítás valós és nagy.** Az előzmény-minimum 25–34 mHa-val
   van a friss átlag alatt (a hibaenyhítés nélküli cellákban). Ennyit tévedne az az implementáció, amely a zajos
   kiértékelések minimumát közölné. A VQEBD ezt nem teszi (G4).

Az előzmény-minimum és a friss átlag különbségét (kiválasztási torzítás) csak
hibaenyhítés nélküli cellákra adjuk meg: hibaenyhített cellában az előzmény nyers,
az átlag mitigált, a kettő nem összehasonlítható.

---

## 5. Az ismétlés hatása — fig08 és AC-5.6

Adat: [`ismetles.json`](../figures/data/ismetles.json), 1024 minta, H₂ θ*-ban.

| Sorozat | log-log meredekség (elmélet: −0.5) | átlag − padló | padló |
|---|---|---|---|
| lövészaj | −0.53 | +2.06 SEM | 0 |
| FakeManilaV2 nyers | −0.48 | −0.29 SEM | +27.52 mHa |
| FakeManilaV2 + ZNE Richardson | −0.55 | +0.32 SEM | +0.23 mHa |

**Az ismétlés a szórást N^−½ szerint csökkenti, a torzítást nem.** A nyers zajos
sorozat egy +27.5 mHa-s vízszintes padlóra áll; a ZNE ezt +0.23 mHa-ra viszi. A
felhasználói kérdésre („hozzájárul-e a több teszt a pontossághoz?") a mért válasz:
a **statisztikus** hibához igen, a **szisztematikus** hibához nem.

**Megjegyzés a +2.06 SEM-ről.** A lövészaj-sorozat átlaga a nulla padlótól 2.06 SEM-re
van. Egy 3 soros táblázatban ez egy 2σ-s ingadozás, amely nem utal torzításra; a
TC-506c külön teszteli, hogy a torzítás N-től független. Nem vontunk le belőle
következtetést.

---

## 6. K5 — az optimalizáló végértéke a friss átlag fölött: lezárva

**Kiinduló megfigyelés.** Hibaenyhítés nélküli cellákban (6 cella, 100 futás) az
optimalizáló végértéke a θ_opt-beli friss átlagnál átlagosan **+2.51 ± 0.99 mHa**-val
magasabb volt (2.5σ). A K5 szerint ez COBYLA-leállási sajátosság lehetett.

**Vizsgálat.** A [`optimizer.py`](../../src/vqebd/vqe/optimizer.py) szerint a
végérték a SciPy `result.fun`-ja. 300 független seeddel (7000–7299), lövészajos H₂
0.735 Å-n, K = 64 friss kiértékeléssel:

| Mérés | Eredmény |
|---|---|
| A végérték az **utolsó** kiértékelés | 300 / 300 futásban |
| A végérték az előzmény minimuma | 3 / 300 futásban |
| Az utolsó kiértékelés helye az előzményben | az esetszám 99%-ánál |
| **Végérték − friss átlag** | **−0.79 ± 0.62 mHa** (szórás 10.70) |
| Előzmény-minimum − friss átlag | −26.53 mHa |

**Következtetés.** A végérték egyetlen zajos minta θ_opt-ban, tehát torzítatlan
becslő, nem a minimum. Független seedeken az eltérés nullával egyezik (−0.79 ± 0.62).
A batch +2.51 ± 0.99-es értéke ezért **nem optimalizálói sajátosság**. A cellák
ugyanazt a 20 seedet használják (`master_seed + repeat`), így a 100 futás **nem
független**, és a pooled SEM alulbecsült. Ez magyarázat, nem bizonyíték: a batch
seedjein nem futtattuk újra a vizsgálatot.

**Zajos backend (`qiskit_aer_noisy`, FakeManilaV2).** Ugyanez a vizsgálat 100
független seeddel: végérték − friss átlag = **−1.05 ± 1.02 mHa** (szórás 10.18);
a végérték 100 / 100 futásban az utolsó kiértékelés, 2 / 100-ban az előzmény
minimuma; előzmény-minimum − friss átlag = −26.71 mHa. A kép azonos a lövészajos
esettel: nulla körüli eltérés, a kiválasztási torzítás az előzmény-minimumban van.

**Korlát.** A vizsgálat a H₂ 0.735 Å esetre vonatkozik (lövészaj 300, zajos 100
seed). LiH-ra nem futtattuk. ZNE-cellákban a végérték nyers, a friss átlag
mitigált, a kettő nem összehasonlítható (4. pont megjegyzése), ezért azokra a K5
nem értelmezhető. A vizsgálat szkriptje a munkamenet ideiglenes könyvtárában
készült, a repóban nincs; az eredmény a fenti értékekkel reprodukálható, ha a
`run_vqe` mellett az `optimizer.minimize_energy` visszatérési értékét (`value`,
`history`) kiolvassuk.

---

## 7. Hardveres H₂ disszociációs görbe — 5.H (2026-11-02)

Adat: [`hardware_h2_pes.json`](../figures/data/hardware_h2_pes.json) · ábra:
`fig10_hardver_pes.png` · szkript: `scripts/run_hardware_pes.py`.

**Beállítás.** `ibm_kingston` (156 qubit, Heron r2), H₂ STO-3G, 5 geometria, 8192
lövés/pont, θ* a **zajmentes** (L2) optimumból. Optimalizálás hardveren **nem**
történt, a mért hiba tehát az eszköz hibája θ*-ban, nem a VQE hibája. Két job,
mindkettő 5 PUB-bal: `dbk5lf1ffo6c73bas75g` (resilience 0, nyers) és
`dbk5mu9kdqps7391qe0g` (resilience 1: TREX + twirling, 32 randomizáció).

**Kvóta.** Előtte 600 / 600 s szabad. A két job számlázott ideje **24 + 33 =
57 QPU-s**; utána 543 s maradt. A becslés ≤ 120 s volt.

**Hiba a Full CI-hez, mHa (± 1 SEM, `ensemble_standard_error`).**

| R (Å) | nyers (resilience 0) | TREX (resilience 1) | TREX javítása |
|---|---|---|---|
| 0.5 | +27.72 ± 3.03 | +12.07 ± 3.57 | 15.65 |
| 0.735 | +22.20 ± 2.80 | +17.56 ± 3.15 | 4.64 |
| 1.0 | +17.38 ± 2.69 | +5.42 ± 2.87 | 11.96 |
| 1.5 | +12.43 ± 2.41 | **−0.68 ± 2.52** | 13.11 |
| 2.0 | +12.16 ± 1.71 | +5.52 ± 1.89 | 6.64 |

**Értelmezés.**

1. **A nyers hiba 12–28 mHa**, és a TREX mind az 5 pontban csökkenti (4.6–15.7
   mHa-val).
2. **Egyetlen pont, az R = 1.5 Å egyeztethető össze a kémiai pontossággal**
   (−0.68 ± 2.52 mHa, a ±1.6 mHa sáv az 1σ-sávon belül van). A sáv széléhez mért
   távolság a TREX-es pontokra: R = 0.5 Å 2.9σ, R = 0.735 Å 5.1σ, R = 2.0 Å 2.1σ
   (ezek 95%-on kívül esnek a sávon), R = 1.0 Å 1.3σ (95%-on nem zárható ki).
   **A hardver tehát a görbén nem éri el a kémiai pontosságot**, a TREX sem.
3. **A hiba nem monoton R-ben.** A TREX-es hiba R = 0.735 Å-nél (+17.56) nagyobb,
   mint R = 1.0–2.0 Å-nél. Az okát nem vizsgáltuk; a θ*-függő kapuk és a
   kalibrációs állapot egyaránt szóba jön. Következtetést nem vontunk le belőle.
4. **A variációs elv nem sérül:** minden pont a Full CI fölött van, az egyetlen
   negatív érték (−0.68) 0.3σ-n belül van.
5. **Összevetés a Fázis 2 mérésével** (R = 0.735 Å, TREX, 1 PUB: −3.96 ± 12.5
   mHa, [TR-F02](TR-F02_hardware_run.md)): a mostani +17.56 ± 3.15 mHa-tól 21.5
   mHa-ra van, az együttes bizonytalanság 12.9 mHa, azaz **1.7σ**. A két mérés
   összeférhető; a Fázis 2 értéke azért nem volt feloldó, mert körülbelül
   négyszer nagyobb hibasávval készült.

**Korlátok.** (a) **Pontonként egyetlen futás**, nincs seed- vagy időbeli
ismétlés, ezért a hibasáv csak a lövés- és twirling-zajt tartalmazza, a
kalibrációs driftet nem. (b) A két szint **külön jobban, külön időpontban**
futott, a különbségük tartalmazhat driftet is. (c) A nyers szint SEM-je
(`num_randomizations = 1`) a lövészaj becslése. (d) A θ* a zajmentes optimum; a
hardveren optimalizált θ jobb lehet (nem mértük).

---

## 8. Ami nem része a lezárásnak

- **K7 — hardveres VQE-útvonal kvótavédelem nélkül** (`run_vqe`, `--backend ibm_qpu`).
  Ez fogyasztotta el a 2026-09-23-i keretet (42 job × 15 s). **Javítva a v0.8.0
  után** (CHANGELOG, Unreleased): engedély, kvóta-előellenőrzés és kemény
  kiértékelési keret; 7 új egységteszt. Ez a jegyzőkönyv a v0.8.0 állapotát
  rögzíti, a javítás nem része a 10 elfogadási kritérium bizonyítékának.
- **K8 — qsim platformtűrés** (3.2 pont): az ok megmérve (`complex64`, nem a Powell); a tűrés számát nem módosítottuk.

---

## 9. Reprodukálás

```bash
docker build -f docker/Dockerfile -t vqebd:0.8.0 .
RUN="docker run --rm -v $PWD:/repo -w /repo -e PYTHONPATH=/repo/src \
     -e PYTHONHASHSEED=0 -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
     vqebd:0.8.0"
$RUN python -W ignore -m pytest -q
$RUN python -W ignore scripts/run_batch.py --preset f5-deterministic \
     --db data/db/f5.sqlite --export docs/figures/data/f5_deterministic.json
$RUN python -W ignore scripts/gen_report_figures.py --only aktiv_ter
$RUN python -W ignore scripts/gen_report_figures.py --only hibakoltsegvetes
```

Windows / Git Bash alatt a `MSYS_NO_PATHCONV=1` előtag kell.

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
