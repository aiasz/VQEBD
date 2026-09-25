# VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard

[![Licenc: MIT](https://img.shields.io/badge/licenc-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Verzió](https://img.shields.io/badge/verzió-0.7.1-orange.svg)](CHANGELOG.md)
[![Fázis](https://img.shields.io/badge/fázis-4%2F10%20lezárva-brightgreen.svg)](docs/plan/00_master_plan.md)
[![Tesztek](https://img.shields.io/badge/tesztek-455%20zöld-brightgreen.svg)](docs/testing/TR-F03_mitigation.md)
[![Platformok](https://img.shields.io/badge/platformok-Qiskit%20%7C%20Cirq%20%7C%20qsim%20%7C%20IBM%20Heron%20%7C%20SQLite-blueviolet.svg)](docs/01m_multiplatform.md)

**🇭🇺 [Magyar](#magyar) | 🇬🇧 [English](#english)**

---

## Magyar

> Reprodukálható, konténerizált benchmark kis molekulák VQE-alapú
> alapállapoti-energia számítására, hibaenyhítési stratégiák összehasonlításával —
> szimulátoron és valódi IBM-kvantumhardveren.

**Készítők:** Kormos Attila · Claude AI (Anthropic, Claude Opus 5)

### ⚠️ A projekt állapota

Ez a projekt **fejlesztés alatt áll**, lépcsőzetes fázisokban.
Jelenlegi állapot: **Fázis 4 lezárva, javítókör (`v0.7.1`)** — a VQE-mag működik
három platformon (Qiskit, Cirq, qsim), véges lövésszámmal (L3a), kalibrációs
zajmodellen (L3b), éles fizikai méréssel az IBM 156-qubites Heron QPU-ján
(`ibm_kingston`, L5), ISA-szintű Zero-Noise Extrapolation hibaenyhítéssel (L4, a
Mitiq-kel keresztvalidálva), és strukturált SQLite adattárolással (`vqebd.storage`).

> **v0.7.1 — javítókör (2026-09-25).** A Fázis 5 előtti átvizsgálás három mérési
> hibát tárt fel és javított: (1) az Aer-mintavétel minden kiértékelésnél ugyanazt
> az eltolást adta, vagyis a „lövészaj” állandó torzítás volt; (2) a ZNE
> hajtogatását a transzpiler részben kiejtette; (3) a hardveres mérés
> bizonytalansága és mitigációs szintje (TREX) nem volt rögzítve. A korábban
> közölt „ZNE → +0.35 mHa ✅” a TR-000 spike száma volt, nem a leszállított
> kódé. **Az alábbi értékek már a javított kóddal mértek.** Részletek:
> [`CHANGELOG.md`](CHANGELOG.md), [TR-F03 v1.1.0](docs/testing/TR-F03_mitigation.md).

| Fázis | Tartalom | Állapot |
|---|---|---|
| 0 | Repó + Docker alapinfrastruktúra | ✅ **Lezárva** (`v0.1.0`) |
| 1 | H2-VQE szimulátoron | ✅ **Lezárva** (`v0.2.0`) |
| **1M** | **Többplatformos validáció (Qiskit ↔ Cirq ↔ qsim)** *(ADR-0006)* | ✅ **Lezárva** (`v0.3.0`) |
| **1b** | **Zajos szimuláció FakeBackend-en (L3a / L3b)** | ✅ **Lezárva** (`v0.4.0`) |
| **2** | **Egyszeri futás valódi IBM-hardveren (`ibm_kingston` Heron QPU, L5)** | ✅ **Lezárva** (`v0.5.0`) |
| **3** | **Hibaenyhítés (ISA ZNE + Mitiq keresztvalidáció, L4)** | ✅ **Lezárva** (`v0.6.0`) |
| **4** | **Adatséma és perzisztens tárolás (SQLite / CSV / JSON)** | ✅ **Lezárva** (`v0.7.0`) |
| 5 | Batch futtatás, több molekula (LiH, BeH2) | ⏳ **Következő** (`v0.8.0`) |
| 6 | Automatizálás és ütemezés | ⬜ Tervezett |
| 7 | Streamlit dashboard | ⬜ Tervezett |
| 8 | Teljes konténerizáció | ⬜ Tervezett |
| 9 | Dokumentáció és publikálás (Zenodo DOI) | ⬜ Tervezett |
| 10 | Közösségi visszacsatolás | ⬜ Tervezett |

### Mit old meg ez a projekt?

A NISQ-korszakban egy VQE-eredmény önmagában értelmezhetetlen: ha egy energiaérték
eltér a valóditól, **nem tudjuk, mi okozta** — a fermion→qubit leképezés, az
ansatz korlátai, a véges lövésszám vagy a hardverzaj.

A VQEBD ezért **öt referenciaszinten** futtatja ugyanazt a számítást, és a
hibaforrásokat külön-külön számszerűsíti:

```
 L0  FCI (klasszikus egzakt)
  │  ← leképezési hiba
 L1  a qubit-Hamilton-operátor egzakt legkisebb sajátértéke
  │  ← ansatz-hiba
 L2  VQE zajmentes állapotvektoron
  │  ← statisztikus (shot-) zaj
 L3a VQE véges lövésszámmal
  │  ← hardverzaj
 L3b VQE zajos szimulátoron / valódi QPU-n
  │  ← hibaenyhítés
 E_mitigated
```

Mért példa (H2, 0.735 Å, STO-3G, `FakeManilaV2` zajmodell, a zajmentes optimumban,
`v0.7.1` — részletek: [TR-F03](docs/testing/TR-F03_mitigation.md)):

| Szint | Hiba a Full CI-hez | Mit mutat |
|---|---|---|
| L1 — egzakt diagonalizáció | 1.3 × 10⁻¹⁵ Ha | leképezési hiba |
| L2 — VQE (állapotvektor) | ~10⁻¹⁴ Ha | ansatz-hiba |
| L3b — zajos, nyers (egzakt várható érték) | +27.5 mHa ❌ | kapuzaj |
| L4 — ZNE Richardson, **torzítás** | **+0.23 mHa ✅** | a módszer rendszeres hibája |
| L4 — ZNE Richardson, **1 futás, 8192 lövés** | −5.7 **± 26.2** mHa | a lövészajt 2.28× felerősíti |
| L5 — `ibm_kingston`, 1 mérés, TREX | −4.0 **± 12.5** mHa | FCI-vel összeférhető, de a felbontás ≫ kémiai pontosság |

*(✅ = kémiai pontosságon belül, |Δ| < 1.6 mHa; ± = 50 seed szórása, ill. a
hardveres ensemble standard hiba)*

#### Fázis 1 — mért eredmény (H2, 0.735 Å, STO-3G, zajmentes)

| Szint | Energia (Ha) | Hiba |
|---|---|---|
| Hartree–Fock | −1.1169989968 | — |
| **L0 — PySCF Full CI** | **−1.1373060358** | referencia |
| **L1 — egzakt diagonalizáció** | **−1.1373060358** | leképezés: **+1.33 × 10⁻¹⁵ Ha** |
| **L2 — VQE** | **−1.1373060358** | ansatz: **+7.99 × 10⁻¹⁵ Ha** |

**Visszanyert korrelációs energia: 100.000000 %.** A hiba a kémiai pontosság
(1.59 × 10⁻³ Ha) nagyjából 10⁻¹²-szerese. Három leképezés (Jordan–Wigner,
paritás, Bravyi–Kitaev) egymástól függetlenül ugyanezt adja.

Részletek: [`docs/testing/TR-F01_vqe_mag.md`](docs/testing/TR-F01_vqe_mag.md).

### Fázis 1M — három platform, egyetlen eredmény

| Platform | Optimalizáló | E (Ha) | Eltérés a Qiskittől |
|---|---|---|---|
| `qiskit_statevector` | SLSQP | −1.137306035753 | referencia |
| `cirq_simulator` | SLSQP | −1.137306035753 | **4.4 × 10⁻¹⁶** |
| `qsim` | Powell | −1.137306006762 | **2.9 × 10⁻⁸** |

![Optimalizáló × platform mátrix](docs/figures/fig02_optimalizalo_matrix.png)

**A fázis legfontosabb felfedezése:** a **gradiens-alapú optimalizálók csendben
téves minimumot találnak** egyszeres pontosságú (`complex64`) platformon. A SciPy
véges-differencia lépésköze `1.49 × 10⁻⁸`, a qsim célfüggvény-zaja viszont
`1.13 × 10⁻⁷` — nagyobb a lépésköznél, ezért a becsült gradiens **8
nagyságrenddel** téved. Az `SLSQP` a qsimen `1.5 × 10⁻²` Ha hibát ad
(„sikeresen konvergált" állapotban), a `Powell` viszont `2.9 × 10⁻⁸`-at.

**Ez egyetlen platformon nem derülhetett volna ki** — Qiskiten és Cirqen mind a
nyolc optimalizáló hibátlan. Részletek és az ábrák:
[`docs/01m_multiplatform.md`](docs/01m_multiplatform.md).

### Fázis 1b — véges lövésszám és hardver-zajszimuláció

| Szint | Backend | Optimalizáló | E (Ha) | Hiba az L1-hez |
|---|---|---|---|---|
| **L3a** | `qiskit_aer_shot` (8192 shot) | COBYLA | −1.1105387727 | +26.8 mHa |
| **L3b** | `qiskit_aer_noisy` (FakeManilaV2) | COBYLA | −1.0954609696 | +41.9 mHa |

*`v0.7.1` értékek (`python -m vqebd --backend <b> --optimizer COBYLA`). A `v0.7.0`
L3a-értéke (+15.9 mHa) egy állandó mintavételi eltolás volt — TR-F01B 6. szakasz.*

A Fázis 1b szétválasztja a véges mintavételi (shot) zajt és az eszköz kalibrációs
zaját (kapuhiba, T1/T2 dekoherencia). **A kiolvasási hibát az Aer Estimator nem
modellezi** (mérve, ADR-0003 1. kiegészítés). **Fontos korlát:** a H₂ teljes
korrelációs energiája (20.3 mHa) csak ~1.8σ egyetlen 8192 lövéses kiértékelés
zajához képest, ezért egyetlen zajos VQE-futás ezt nem tudja megbízhatóan
feloldani. Ez a Fázis 5 több-seedes módszertanának oka.
Részletek: [`docs/01b_noisy_simulation.md`](docs/01b_noisy_simulation.md).

### Fázis 2 — valódi hardveres mérés (IBM Heron QPU)

| Szint | Backend | Mód | E (Ha) | Hiba az L0-hoz |
|---|---|---|---|---|
| **L5** | `ibm_kingston` (156 qubit Heron r2) | 1 kiértékelés θ*-nál, 8192 shot, **TREX** | **−1.1413** | **−3.96 ± 12.5 mHa** (ensemble SE) |

Job `dapq25kak42c73cj1hu0`, **15 QPU-másodperc**. A mérés **nem nyers**: a szerver
alapértelmezett mitigációja (`resilience_level=1`, TREX mérésmitigáció +
mérés-twirling) futott. A v0.7.1 óta ez explicit paraméter. A variációs határ
alatti érték 0.3σ-s statisztikus ingadozás. A mérés FCI-vel összeférhető, de
kémiai pontosságot sem igazolni, sem cáfolni nem tud (≈ 62× több lövés kellene).
Részletek: [`TR-F02 v1.1.0`](docs/testing/TR-F02_hardware_run.md).

### Fázis 3 — hibaenyhítés Zero-Noise Extrapolation-nel (ZNE)

| Mérés | Nyers | Richardson | Exponenciális | Lineáris |
|---|---|---|---|---|
| **Torzítás** — `zne_local` (ISA-hajtogatás) | +27.52 | **+0.23 ✅** | **+0.15 ✅** | +3.15 |
| **Torzítás** — `zne_mitiq` (logikai hajtogatás) | +37.57 | **+0.37 ✅** | **+0.17 ✅** | +5.43 |
| **1 futás RMSE** (50 seed, 8192 lövés/pont) | 28.6 | 26.5 | 77.7 | **12.3** |

*(mHa, a Full CI-hez; torzítás = egzakt zajos várható érték, `precision=0`)*

A ZNE **módszere helyes**: a torzítás a kémiai pontosságon belül van, és két
független implementáció 0.13 mHa-en belül ugyanoda jut. Egyetlen futás
szórását viszont az extrapoláció felnagyítja, ezért **8192 lövésnél a lineáris
extrapoláció adja a legkisebb teljes hibát**. Az extrapolátor választása tehát a
lövésszám függvénye.
Részletek: [`docs/03_mitigation_test.md`](docs/03_mitigation_test.md).

![Hibaenyhítés: ZNE torzítás és szórás](docs/figures/fig06_mitigacio.png)

### Fázis 4 — adatséma és perzisztens tárolás (SQLite & FAIR export)

A VQEBD a számítási eredményeket közvetlenül típusos, indexelt SQLite adatbázisba
menti (`data/db/vqebd.sqlite`), amelyből determinisztikusan reprodukálható CSV és
JSON exportok készülnek. A verziózott referencia-export:
[`docs/figures/data/results_v1.json`](docs/figures/data/results_v1.json) (`v0.7.1`).

| Tárolt futás | Backend | Mitigáció | E (Ha) | Hiba az L0-hoz |
|---|---|---|---|---|
| **L2** | `qiskit_statevector` / `cirq_simulator` | none | −1.1373060358 | < 10⁻¹⁴ Ha ✅ |
| **L2** | `qsim` (Powell) | none | −1.1373060068 | 2.9 × 10⁻⁸ Ha ✅ |
| **L3a** | `qiskit_aer_shot` (COBYLA, 50 it.) | none | −1.1421267225 | −4.8 mHa ¹ |
| **L3b** | `qiskit_aer_noisy` (COBYLA, 50 it.) | none | −1.1145306932 | +22.8 mHa |
| **L4** | `qiskit_aer_noisy` | zne_local (Rich.) | −1.1075860081 | +29.7 mHa |
| **L5** | `ibm_kingston` | ibm_resilience_1 (TREX) | −1.1412691258 | −4.0 mHa ² |

¹ a zajos minimum kiválasztási torzítása (TR-F01B 6.3) · ² 1σ-n belül (TR-F02)

Részletek: [`docs/04_data_schema.md`](docs/04_data_schema.md), [`TR-F04 v1.1.0`](docs/testing/TR-F04_storage.md).


### Gyors indítás

```bash
git clone https://github.com/aiasz/VQEBD.git
cd VQEBD
make build      # Docker-image építése
make test       # teljes tesztkészlet (455 teszt)
```

Az első kvantumszámítás futtatása:

```bash
docker run --rm vqebd:0.7.1 python -m vqebd
```

Make nélkül (pl. Windows PowerShell):

```powershell
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.7.1 .
docker run --rm vqebd:0.7.1 python -m vqebd
```

Részletes útmutató: **[`docs/00_setup.md`](docs/00_setup.md)**

### Dokumentáció

| Dokumentum | Tartalom |
|---|---|
| [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) | **Bővített mesterterv** — architektúra, referenciaszintek, politikák, kockázatok |
| [`docs/plan/phase_00.md`](docs/plan/phase_00.md) | A Fázis 0 részletes terve |
| [`docs/plan/phase_01.md`](docs/plan/phase_01.md) | A Fázis 1 részletes terve |
| [`docs/plan/phase_01m.md`](docs/plan/phase_01m.md) | A Fázis 1M részletes terve |
| [`docs/plan/phase_01b.md`](docs/plan/phase_01b.md) | A Fázis 1b részletes terve |
| [`docs/plan/phase_02.md`](docs/plan/phase_02.md) | A Fázis 2 részletes terve |
| [`docs/plan/phase_03.md`](docs/plan/phase_03.md) | A Fázis 3 részletes terve |
| [`docs/plan/phase_04.md`](docs/plan/phase_04.md) | A Fázis 4 részletes terve |
| [`docs/01m_multiplatform.md`](docs/01m_multiplatform.md) | **Többplatformos validáció: mit ad, és mit nem** |
| [`docs/01b_noisy_simulation.md`](docs/01b_noisy_simulation.md) | **Zajos és véges lövésszámú szimuláció (L3a / L3b)** |
| [`docs/02_hardware_run.md`](docs/02_hardware_run.md) | **Valódi hardveres futtatás IBM Heron QPU-n (L5)** |
| [`docs/03_mitigation_test.md`](docs/03_mitigation_test.md) | **Hibaenyhítés és Zero-Noise Extrapolation (L4)** |
| [`docs/04_data_schema.md`](docs/04_data_schema.md) | **Adatséma, SQLite adattárolás és FAIR exportálás** |
| [`docs/01_vqe_core.md`](docs/01_vqe_core.md) | **A VQE-mag: használat, architektúra, korlátok** |
| [`docs/00_setup.md`](docs/00_setup.md) | Telepítés, futtatás, hibaelhárítás |
| [`docs/references.md`](docs/references.md) | **37 hivatkozás, 35 gépileg DOI-validálva** |
| [`docs/adr/`](docs/adr/) | Architektúra-döntések (ADR-0001…0005) |
| [`docs/testing/`](docs/testing/) | Teszttervek és mérési jegyzőkönyvek |

#### Architektúra-döntések

| ADR | Döntés |
|---|---|
| [0001](docs/adr/ADR-0001-technologiai-stack.md) | A stack Qiskit **1.4.6**-ra rögzítve — a Mitiq 0.47.0 `numpy<2.0`-t követel, a Qiskit 2.x `numpy>=2.0`-t |
| [0002](docs/adr/ADR-0002-sajat-vqe-hurok.md) | Saját VQE-hurok **V2 primitívekkel**, `qiskit-algorithms` nélkül → Qiskit 2.x-re átvihető |
| [0003](docs/adr/ADR-0003-mitigacios-architektura.md) | Pluginalapú hibaenyhítés, **saját ISA-biztos ZNE** (a Mitiq ISA-áramkörön qubiteket veszít) |
| [0004](docs/adr/ADR-0004-adattarolas.md) | SQLite kanonikus tároló, sémaverziózással, FAIR-elvek szerint |
| [0005](docs/adr/ADR-0005-determinizmus.md) | Minden véletlenforrás explicit seedet kap, és rekordba kerül |
| [0006](docs/adr/ADR-0006-tobbplatformos-architektura.md) | **A platform önálló benchmark-dimenzió** — Qiskit ↔ Cirq ↔ qsim |

### Módszertani alapelvek

1. **Egyetlen fázis sem zárható le, amíg az elfogadási kritériuma dokumentáltan nem teljesül.**
2. **Minden fázis terve a megvalósítás előtt készül el**, és a mérési jegyzőkönyve utána — mindkettő verziózva.
3. **Három tesztkör fázisonként:** funkcionális → robusztussági → keresztvalidációs.
4. **Minden szám mért, nem becsült.** A dokumentációban szereplő értékek reprodukálható mérésekből származnak, a szkriptek a repóban vannak.
5. **A hivatkozások gépileg validáltak.** A `scripts/gen_references.py` a Crossref és DataCite API-ból oldja fel a bibliográfiai adatokat — a szerzőlistákat, címeket és évszámokat nem kézzel írjuk.

### Licenc és harmadik felek szoftverei

A VQEBD **MIT** licencű — lásd [`LICENSE`](LICENSE).

> **⚠️ Mitiq (GPL-3.0).** A Mitiq csomag GPL-3.0 licencű. A VQEBD **nem linkeli be
> és nem terjeszti újra**: opcionális, futásidőben betöltött komponensként
> használja, egyetlen modulba zárva (`src/vqebd/mitigation/mitiq_zne.py`).
> **Mitiq nélkül a rendszer teljes funkcionalitással működik.** Részletek:
> [ADR-0003](docs/adr/ADR-0003-mitigacios-architektura.md). Opcionális telepítés
> (a `zne_mitiq` keresztvalidációhoz): `pip install -r requirements-mitiq.txt`.

A felhasznált szoftverek teljes listája licencekkel és hivatkozásokkal:
[`docs/references.md`](docs/references.md).

### Biztonság

**Soha ne commitolj IBM API-tokent.** A védelem három rétegű, és automatikus teszt
őrzi (`tests/repo/test_secrets_hygiene.py`):

1. `.gitignore` — a titkok nem kerülnek verziókezelésbe;
2. `.dockerignore` — a titkok nem kerülnek az image rétegeibe;
3. tartalmi ellenőrzés — tokennek látszó string keresése a verziózott fájlokban.

A tokent a `.env` fájlba tedd (`cp .env.example .env`). A valódi hardverre küldést
külön biztonsági kapcsoló védi: `VQEBD_ALLOW_HARDWARE=false` az alapértelmezés.

### Hivatkozás

Ha a projektet használod, hivatkozz rá a [`CITATION.cff`](CITATION.cff) szerint.
A Zenodo DOI a Fázis 9-ben kerül ide.

### Közreműködés

A projekt jelenleg korai fázisban van. Hibajelzés és javaslat: GitHub Issues.
A commit-üzenetek a [Conventional Commits](https://www.conventionalcommits.org/)
konvenciót követik.

---

## English

> A reproducible, containerized benchmark for VQE-based ground-state energy
> calculations of small molecules, comparing error-mitigation strategies —
> on simulators and on real IBM quantum hardware.

**Authors:** Attila Kormos · Claude AI (Anthropic, Claude Opus 5)

### ⚠️ Project Status

This project is **under active development**, in staged phases.
Current status: **Phase 4 completed, correction round (`v0.7.1`)** — the VQE core
works across three platforms (Qiskit, Cirq, qsim), with finite-shot noise (L3a),
calibration device noise (L3b), physical hardware measurement on IBM's 156-qubit
Heron QPU (`ibm_kingston`, L5), ISA-level Zero-Noise Extrapolation error
mitigation (L4, cross-validated against Mitiq), and structured SQLite storage
(`vqebd.storage`).

> **v0.7.1 — correction round (2026-09-25).** The review before Phase 5 found and
> fixed three measurement defects: (1) Aer sampling applied the same offset to
> every evaluation, so the "shot noise" was a constant bias; (2) the transpiler
> partially cancelled the ZNE folding; (3) the hardware measurement's uncertainty
> and mitigation level (TREX) were not recorded. The previously published
> "ZNE → +0.35 mHa ✅" was a TR-000 spike number, not a result of the shipped
> code. **The values below are measured with the corrected code.** Details:
> [`CHANGELOG.md`](CHANGELOG.md), [TR-F03 v1.1.0](docs/testing/TR-F03_mitigation.md).

| Phase | Content | Status |
|---|---|---|
| 0 | Repo + Docker base infrastructure | ✅ **Completed** (`v0.1.0`) |
| 1 | H2-VQE on simulator | ✅ **Completed** (`v0.2.0`) |
| **1M** | **Multi-platform validation (Qiskit ↔ Cirq ↔ qsim)** *(ADR-0006)* | ✅ **Completed** (`v0.3.0`) |
| **1b** | **Noisy simulation on FakeBackend (L3a / L3b)** | ✅ **Completed** (`v0.4.0`) |
| **2** | **Single run on real IBM hardware (`ibm_kingston` Heron QPU, L5)** | ✅ **Completed** (`v0.5.0`) |
| **3** | **Error mitigation (ISA ZNE + Mitiq cross-validation, L4)** | ✅ **Completed** (`v0.6.0`) |
| **4** | **Data schema and persistent storage (SQLite / CSV / JSON)** | ✅ **Completed** (`v0.7.0`) |
| 5 | Batch runs, multiple molecules (LiH, BeH2) | ⏳ **Next** (`v0.8.0`) |
| 6 | Automation and scheduling | ⬜ Planned |
| 7 | Streamlit dashboard | ⬜ Planned |
| 8 | Full containerization | ⬜ Planned |
| 9 | Documentation and publication (Zenodo DOI) | ⬜ Planned |
| 10 | Community feedback | ⬜ Planned |

### What Does This Project Solve?

In the NISQ era, a single VQE result is meaningless on its own: if an energy
value deviates from the true value, **we don't know why** — the fermion-to-qubit
mapping, ansatz limitations, finite shot count, or hardware noise could all be
the cause.

VQEBD therefore runs the same calculation at **five reference levels**,
quantifying each source of error separately:

```
 L0  FCI (classical exact)
  │  ← mapping error
 L1  exact lowest eigenvalue of the qubit Hamiltonian
  │  ← ansatz error
 L2  VQE on noiseless statevector
  │  ← statistical (shot) noise
 L3a VQE with finite shot count
  │  ← hardware noise
 L3b VQE on noisy simulator / real QPU
  │  ← error mitigation
 E_mitigated
```

Measured example (H2, 0.735 Å, STO-3G, `FakeManilaV2` noise model, at the noiseless
optimum, `v0.7.1` — details: [TR-F03](docs/testing/TR-F03_mitigation.md)):

| Level | Error vs Full CI | What it shows |
|---|---|---|
| L1 — exact diagonalization | 1.3 × 10⁻¹⁵ Ha | mapping error |
| L2 — VQE (statevector) | ~10⁻¹⁴ Ha | ansatz error |
| L3b — noisy, raw (exact expectation value) | +27.5 mHa ❌ | gate noise |
| L4 — ZNE Richardson, **bias** | **+0.23 mHa ✅** | systematic error of the method |
| L4 — ZNE Richardson, **single run, 8192 shots** | −5.7 **± 26.2** mHa | amplifies shot noise 2.28× |
| L5 — `ibm_kingston`, single measurement, TREX | −4.0 **± 12.5** mHa | consistent with FCI, but resolution ≫ chemical accuracy |

*(✅ = within chemical accuracy, |Δ| < 1.6 mHa; ± = standard deviation over 50
seeds, or the hardware ensemble standard error)*

#### Phase 1 — Measured Result (H2, 0.735 Å, STO-3G, noiseless)

| Level | Energy (Ha) | Error |
|---|---|---|
| Hartree–Fock | −1.1169989968 | — |
| **L0 — PySCF Full CI** | **−1.1373060358** | reference |
| **L1 — exact diagonalization** | **−1.1373060358** | mapping: **+1.33 × 10⁻¹⁵ Ha** |
| **L2 — VQE** | **−1.1373060358** | ansatz: **+7.99 × 10⁻¹⁵ Ha** |

**Correlation energy recovered: 100.000000%.** The error is roughly 10⁻¹² times
the chemical accuracy threshold (1.59 × 10⁻³ Ha). Three mappings (Jordan–Wigner,
parity, Bravyi–Kitaev) independently give the same result.

Details: [`docs/testing/TR-F01_vqe_mag.md`](docs/testing/TR-F01_vqe_mag.md).

### Phase 1M — Three Platforms, One Result

| Platform | Optimizer | E (Ha) | Deviation from Qiskit |
|---|---|---|---|
| `qiskit_statevector` | SLSQP | −1.137306035753 | reference |
| `cirq_simulator` | SLSQP | −1.137306035753 | **4.4 × 10⁻¹⁶** |
| `qsim` | Powell | −1.137306006762 | **2.9 × 10⁻⁸** |

![Optimizer × platform matrix](docs/figures/fig02_optimalizalo_matrix.png)

**The key finding of this phase:** **gradient-based optimizers silently converge
to a wrong minimum** on single-precision (`complex64`) platforms. SciPy's
finite-difference step is `1.49 × 10⁻⁸`, but qsim's objective-function noise is
`1.13 × 10⁻⁷` — larger than the step, so the estimated gradient is off by **8
orders of magnitude**. On qsim, `SLSQP` yields a `1.5 × 10⁻²` Ha error while
reporting successful convergence; `Powell` yields `2.9 × 10⁻⁸`.

**This could not have been discovered on a single platform** — on Qiskit and Cirq
all eight optimizers work flawlessly. Details and figures:
[`docs/01m_multiplatform.md`](docs/01m_multiplatform.md).

### Phase 1b — Finite-Shot and Device Noise Simulation

| Level | Backend | Optimizer | E (Ha) | Error vs L1 |
|---|---|---|---|---|
| **L3a** | `qiskit_aer_shot` (8192 shots) | COBYLA | −1.1105387727 | +26.8 mHa |
| **L3b** | `qiskit_aer_noisy` (FakeManilaV2) | COBYLA | −1.0954609696 | +41.9 mHa |

*`v0.7.1` values (`python -m vqebd --backend <b> --optimizer COBYLA`). The `v0.7.0`
L3a value (+15.9 mHa) was a constant sampling offset — TR-F01B, section 6.*

Phase 1b isolates finite sampling (shot) noise and device calibration noise (gate
error, T1/T2 decoherence). **Readout error is not modelled by the Aer Estimator**
(measured, ADR-0003 addendum 1). **Key limitation:** the full H₂ correlation
energy (20.3 mHa) is only ~1.8σ of a single 8192-shot evaluation's noise, so a
single noisy VQE run cannot resolve it reliably. This motivates the multi-seed
methodology of Phase 5.
Details: [`docs/01b_noisy_simulation.md`](docs/01b_noisy_simulation.md).

### Phase 2 — Real Physical Hardware Execution (IBM Heron QPU)

| Level | Backend | Mode | E (Ha) | Error vs L0 |
|---|---|---|---|---|
| **L5** | `ibm_kingston` (156-qubit Heron r2) | single evaluation at θ*, 8192 shots, **TREX** | **−1.1413** | **−3.96 ± 12.5 mHa** (ensemble SE) |

Job `dapq25kak42c73cj1hu0`, **15 QPU seconds**. The measurement is **not raw**: the
server-default mitigation (`resilience_level=1`, TREX readout mitigation +
measurement twirling) was applied; since v0.7.1 this is an explicit parameter.
The value below the variational bound is a 0.3σ statistical fluctuation. The
measurement is consistent with FCI, but can neither confirm nor refute chemical
accuracy (≈ 62× more shots would be needed).
Details: [`TR-F02 v1.1.0`](docs/testing/TR-F02_hardware_run.md).

### Phase 3 — Error Mitigation with Zero-Noise Extrapolation (ZNE)

| Measurement | Raw | Richardson | Exponential | Linear |
|---|---|---|---|---|
| **Bias** — `zne_local` (ISA folding) | +27.52 | **+0.23 ✅** | **+0.15 ✅** | +3.15 |
| **Bias** — `zne_mitiq` (logical folding) | +37.57 | **+0.37 ✅** | **+0.17 ✅** | +5.43 |
| **Single-run RMSE** (50 seeds, 8192 shots/point) | 28.6 | 26.5 | 77.7 | **12.3** |

*(mHa vs Full CI; bias = exact noisy expectation value, `precision=0`)*

The ZNE **method is correct**: its bias is within chemical accuracy, and two
independent implementations agree to within 0.13 mHa. The extrapolation,
however, amplifies the noise of a single run, so **at 8192 shots the linear
extrapolator gives the smallest total error**. The choice of extrapolator
therefore depends on the shot budget.
Details: [`docs/03_mitigation_test.md`](docs/03_mitigation_test.md).

![Error mitigation: ZNE bias and variance](docs/figures/fig06_mitigacio.png)

### Phase 4 — Data Schema and Persistent Storage (SQLite & FAIR Export)

VQEBD persists all quantum computation records into a canonical, typed SQLite
database (`data/db/vqebd.sqlite`), with deterministic CSV and JSON exports. The
versioned reference export:
[`docs/figures/data/results_v1.json`](docs/figures/data/results_v1.json) (`v0.7.1`).

| Stored run | Backend | Mitigation | E (Ha) | Error vs L0 |
|---|---|---|---|---|
| **L2** | `qiskit_statevector` / `cirq_simulator` | none | −1.1373060358 | < 10⁻¹⁴ Ha ✅ |
| **L2** | `qsim` (Powell) | none | −1.1373060068 | 2.9 × 10⁻⁸ Ha ✅ |
| **L3a** | `qiskit_aer_shot` (COBYLA, 50 it.) | none | −1.1421267225 | −4.8 mHa ¹ |
| **L3b** | `qiskit_aer_noisy` (COBYLA, 50 it.) | none | −1.1145306932 | +22.8 mHa |
| **L4** | `qiskit_aer_noisy` | zne_local (Rich.) | −1.1075860081 | +29.7 mHa |
| **L5** | `ibm_kingston` | ibm_resilience_1 (TREX) | −1.1412691258 | −4.0 mHa ² |

¹ selection bias of the noisy minimum (TR-F01B 6.3) · ² within 1σ (TR-F02)

Details: [`docs/04_data_schema.md`](docs/04_data_schema.md), [`TR-F04 v1.1.0`](docs/testing/TR-F04_storage.md).


### Quick Start

```bash
git clone https://github.com/aiasz/VQEBD.git
cd VQEBD
make build      # build the Docker image
make test       # full test suite (455 tests)
```

Running the first quantum computation:

```bash
docker run --rm vqebd:0.7.1 python -m vqebd
```

Without Make (e.g. Windows PowerShell):

```powershell
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.7.1 .
docker run --rm vqebd:0.7.1 python -m vqebd
```

Detailed guide: **[`docs/00_setup.md`](docs/00_setup.md)**

### Documentation

| Document | Content |
|---|---|
| [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) | **Extended master plan** — architecture, reference levels, policies, risks |
| [`docs/plan/phase_00.md`](docs/plan/phase_00.md) | Detailed Phase 0 plan |
| [`docs/plan/phase_01.md`](docs/plan/phase_01.md) | Detailed Phase 1 plan |
| [`docs/plan/phase_01m.md`](docs/plan/phase_01m.md) | Detailed Phase 1M plan |
| [`docs/plan/phase_01b.md`](docs/plan/phase_01b.md) | Detailed Phase 1b plan |
| [`docs/plan/phase_02.md`](docs/plan/phase_02.md) | Detailed Phase 2 plan |
| [`docs/plan/phase_03.md`](docs/plan/phase_03.md) | Detailed Phase 3 plan |
| [`docs/plan/phase_04.md`](docs/plan/phase_04.md) | Detailed Phase 4 plan |
| [`docs/01m_multiplatform.md`](docs/01m_multiplatform.md) | **Multi-platform validation: what it buys, what it doesn't** |
| [`docs/01b_noisy_simulation.md`](docs/01b_noisy_simulation.md) | **Noisy and finite-shot simulation (L3a / L3b)** |
| [`docs/02_hardware_run.md`](docs/02_hardware_run.md) | **Real physical hardware execution on IBM Heron QPU (L5)** |
| [`docs/03_mitigation_test.md`](docs/03_mitigation_test.md) | **Error mitigation and Zero-Noise Extrapolation (L4)** |
| [`docs/04_data_schema.md`](docs/04_data_schema.md) | **Data schema, SQLite database and FAIR exports** |
| [`docs/01_vqe_core.md`](docs/01_vqe_core.md) | **The VQE core: usage, architecture, limits** |
| [`docs/00_setup.md`](docs/00_setup.md) | Installation, running, troubleshooting |
| [`docs/references.md`](docs/references.md) | **37 references, 35 machine DOI-validated** |
| [`docs/adr/`](docs/adr/) | Architecture decisions (ADR-0001…0005) |
| [`docs/testing/`](docs/testing/) | Test plans and measurement logs |

#### Architecture Decisions

| ADR | Decision |
|---|---|
| [0001](docs/adr/ADR-0001-technologiai-stack.md) | Stack pinned to Qiskit **1.4.6** — Mitiq 0.47.0 requires `numpy<2.0`, Qiskit 2.x requires `numpy>=2.0` |
| [0002](docs/adr/ADR-0002-sajat-vqe-hurok.md) | Custom VQE loop with **V2 primitives**, without `qiskit-algorithms` → portable to Qiskit 2.x |
| [0003](docs/adr/ADR-0003-mitigacios-architektura.md) | Plugin-based error mitigation, **custom ISA-safe ZNE** (Mitiq loses qubits on ISA circuits) |
| [0004](docs/adr/ADR-0004-adattarolas.md) | SQLite as canonical storage, with schema versioning, following FAIR principles |
| [0005](docs/adr/ADR-0005-determinizmus.md) | Every random source gets an explicit seed and is recorded |

### Methodological Principles

1. **No phase is closed until its acceptance criteria are documented as met.**
2. **Every phase's plan is written before implementation**, and its measurement log afterward — both versioned.
3. **Three test rounds per phase:** functional → robustness → cross-validation.
4. **Every number is measured, not estimated.** Values in the documentation come from reproducible measurements; the scripts are in the repo.
5. **References are machine-validated.** `scripts/gen_references.py` resolves bibliographic data from the Crossref and DataCite APIs — author lists, titles, and years are never entered manually.

### License and Third-Party Software

VQEBD is licensed under **MIT** — see [`LICENSE`](LICENSE).

> **⚠️ Mitiq (GPL-3.0).** The Mitiq package is GPL-3.0 licensed. VQEBD does
> **not link or redistribute** it: it is used as an optional, runtime-loaded
> component, isolated in a single module (`src/vqebd/mitigation/mitiq_zne.py`).
> **The system works with full functionality without Mitiq.** Details:
> [ADR-0003](docs/adr/ADR-0003-mitigacios-architektura.md). Optional install
> (for the `zne_mitiq` cross-validation): `pip install -r requirements-mitiq.txt`.

Full list of software used, with licenses and references:
[`docs/references.md`](docs/references.md).

### Security

**Never commit an IBM API token.** Protection is three-layered, and an automated
test enforces it (`tests/repo/test_secrets_hygiene.py`):

1. `.gitignore` — secrets are excluded from version control;
2. `.dockerignore` — secrets are excluded from image layers;
3. content scanning — searches for token-like strings in versioned files.

Put the token in a `.env` file (`cp .env.example .env`). Sending jobs to real
hardware is protected by a separate safety switch: `VQEBD_ALLOW_HARDWARE=false`
by default.

### Citation

If you use this project, please cite it according to [`CITATION.cff`](CITATION.cff).
The Zenodo DOI will be added in Phase 9.

### Contributing

The project is currently in an early phase. Bug reports and suggestions: GitHub
Issues. Commit messages follow the
[Conventional Commits](https://www.conventionalcommits.org/) convention.

---

*© 2026 Kormos Attila (Attila Kormos), Claude AI (Anthropic) — MIT license*
