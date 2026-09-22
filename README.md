# VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard

[![Licenc: MIT](https://img.shields.io/badge/licenc-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Verzió](https://img.shields.io/badge/verzió-0.2.0-orange.svg)](CHANGELOG.md)
[![Fázis](https://img.shields.io/badge/fázis-1%2F10%20lezárva-yellow.svg)](docs/plan/00_master_plan.md)
[![Tesztek](https://img.shields.io/badge/tesztek-248%20zöld-brightgreen.svg)](docs/testing/TR-F01_vqe_mag.md)

**🇭🇺 [Magyar](#magyar) | 🇬🇧 [English](#english)**

---

## Magyar

> Reprodukálható, konténerizált benchmark kis molekulák VQE-alapú
> alapállapoti-energia számítására, hibaenyhítési stratégiák összehasonlításával —
> szimulátoron és valódi IBM-kvantumhardveren.

**Készítők:** Kormos Attila · Claude AI (Anthropic, Claude Opus 5)

### ⚠️ A projekt állapota

Ez a projekt **fejlesztés alatt áll**, lépcsőzetes fázisokban.
Jelenlegi állapot: **Fázis 1 lezárva (`v0.2.0`)** — a VQE-mag működik és
validált. A zajos szimuláció a Fázis 1b-től, a valódi hardver a Fázis 2-től jön.

| Fázis | Tartalom | Állapot |
|---|---|---|
| 0 | Repó + Docker alapinfrastruktúra | ✅ **Lezárva** (`v0.1.0`) |
| 1 | H2-VQE szimulátoron | ✅ **Lezárva** (`v0.2.0`) |
| 1b | Zajos szimuláció FakeBackend-en *(új, a TR-000 alapján)* | ⏳ Következő |
| 2 | Egyszeri futás valódi IBM-hardveren | ⬜ Tervezett |
| 3 | Hibaenyhítés (ZNE + mérési hibaenyhítés) | ⬜ Tervezett |
| 4 | Adatséma és perzisztens tárolás | ⬜ Tervezett |
| 5 | Batch futtatás, több molekula | ⬜ Tervezett |
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

Mért példa (H2, 0.735 Å, STO-3G, `FakeManilaV2` zajmodell — részletek:
[`TR-000`](docs/testing/TR-000_spike.md)):

| Szint | Energia (Ha) | Eltérés az L2-től |
|---|---|---|
| L0 — PySCF FCI | −1.13730604 | — |
| L1 — egzakt diagonalizáció | −1.13730604 | 1.3 × 10⁻¹⁵ |
| L2 — VQE (állapotvektor) | −1.13730604 | 7.6 × 10⁻¹⁵ |
| L3b — zajos, nyers | −1.121556 | **+15.75 mHa** |
| L3b + ZNE (Richardson) | −1.136959 | **+0.35 mHa** ✅ |

*(✅ = kémiai pontosságon belül, |Δ| < 1.6 mHa)*

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

### Gyors indítás

```bash
git clone https://github.com/aiasz/VQEBD.git
cd VQEBD
make build      # Docker-image építése
make test       # teljes tesztkészlet (248 teszt)
```

Az első kvantumszámítás futtatása:

```bash
docker run --rm vqebd:0.2.0 python -m vqebd
```

Make nélkül (pl. Windows PowerShell):

```powershell
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.2.0 .
docker run --rm vqebd:0.2.0 python -m vqebd
```

Részletes útmutató: **[`docs/00_setup.md`](docs/00_setup.md)**

### Dokumentáció

| Dokumentum | Tartalom |
|---|---|
| [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) | **Bővített mesterterv** — architektúra, referenciaszintek, politikák, kockázatok |
| [`docs/plan/phase_00.md`](docs/plan/phase_00.md) | A Fázis 0 részletes terve |
| [`docs/plan/phase_01.md`](docs/plan/phase_01.md) | A Fázis 1 részletes terve |
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
> [ADR-0003](docs/adr/ADR-0003-mitigacios-architektura.md).

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
Current status: **Phase 1 completed (`v0.2.0`)** — the VQE core is working and
validated. Noisy simulation starts at Phase 1b, real hardware at Phase 2.

| Phase | Content | Status |
|---|---|---|
| 0 | Repo + Docker base infrastructure | ✅ **Completed** (`v0.1.0`) |
| 1 | H2-VQE on simulator | ✅ **Completed** (`v0.2.0`) |
| 1b | Noisy simulation on FakeBackend *(new, based on TR-000)* | ⏳ Next |
| 2 | Single run on real IBM hardware | ⬜ Planned |
| 3 | Error mitigation (ZNE + measurement error mitigation) | ⬜ Planned |
| 4 | Data schema and persistent storage | ⬜ Planned |
| 5 | Batch runs, multiple molecules | ⬜ Planned |
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

Measured example (H2, 0.735 Å, STO-3G, `FakeManilaV2` noise model — details:
[`TR-000`](docs/testing/TR-000_spike.md)):

| Level | Energy (Ha) | Deviation from L2 |
|---|---|---|
| L0 — PySCF FCI | −1.13730604 | — |
| L1 — exact diagonalization | −1.13730604 | 1.3 × 10⁻¹⁵ |
| L2 — VQE (statevector) | −1.13730604 | 7.6 × 10⁻¹⁵ |
| L3b — noisy, raw | −1.121556 | **+15.75 mHa** |
| L3b + ZNE (Richardson) | −1.136959 | **+0.35 mHa** ✅ |

*(✅ = within chemical accuracy, |Δ| < 1.6 mHa)*

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

### Quick Start

```bash
git clone https://github.com/aiasz/VQEBD.git
cd VQEBD
make build      # build the Docker image
make test       # full test suite (248 tests)
```

Running the first quantum computation:

```bash
docker run --rm vqebd:0.2.0 python -m vqebd
```

Without Make (e.g. Windows PowerShell):

```powershell
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.2.0 .
docker run --rm vqebd:0.2.0 python -m vqebd
```

Detailed guide: **[`docs/00_setup.md`](docs/00_setup.md)**

### Documentation

| Document | Content |
|---|---|
| [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) | **Extended master plan** — architecture, reference levels, policies, risks |
| [`docs/plan/phase_00.md`](docs/plan/phase_00.md) | Detailed Phase 0 plan |
| [`docs/plan/phase_01.md`](docs/plan/phase_01.md) | Detailed Phase 1 plan |
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
> [ADR-0003](docs/adr/ADR-0003-mitigacios-architektura.md).

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
