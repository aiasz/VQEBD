# Változásnapló

A projekt minden lényeges változása ebben a fájlban szerepel.

A formátum a [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) ajánlást
követi, a verziózás a [Semantic Versioning 2.0.0](https://semver.org/) szerint történik.
A `MINOR` verzió minden lezárt projektfázisnál lép
(lásd [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md), 8.1).

---

## [Unreleased] — Nem kiadott

### Tervezett
- **Fázis 1b** — zajos szimuláció FakeBackend-en, kvótamentesen (`v0.3.0`).

---

## [0.2.0] — 2026-09-22

**Fázis 1 lezárva — H2-VQE szimulátoron.**

Az első valódi kvantumszámítás. A modul kiszámolja a H2 alapállapoti energiáját,
és — ami módszertanilag legalább ennyire fontos — **igazolja, hogy a kapott szám
helyes**, három egymástól független referenciához mérve.

### Hozzáadva

#### A VQE-mag
- `vqebd.config` — fagyasztott, hash-elhető konfiguráció stabil SHA-256
  ujjlenyomattal (`config_hash` a Fázis 4 adatsémájához).
- `vqebd.seeds` — determinisztikus, BLAKE2b-alapú seed-származtatás egyetlen
  mester-seedből, öt komponensre (ADR-0005).
- `vqebd.versions` — környezet-ujjlenyomat: csomagverziók + platform.
- `vqebd.chemistry` — molekula-definíciók (H2, LiH, BeH2), PySCF-meghajtó típusos
  burkolata, három fermion→qubit leképezés, L0/L1 referenciaenergiák.
- `vqebd.vqe` — UCCSD ansatz Hartree–Fock kezdőállapottal, saját SciPy-alapú
  optimalizáló-hurok konvergencia-naplóval, strukturált `VQEResult`.
- `vqebd.backends` — backend-független energiakiértékelő interfész
  (Fázis 1: `statevector`; a Fázis 1b/2 változatlan interfésszel bővíti).
- `vqebd.cli` + `python -m vqebd` — önállóan futtatható parancssori felület.

#### Függőségek
- A teljes kvantum-stack bekerült a `requirements.txt`-be, `==` pinnekkel:
  numpy 1.26.4 · scipy 1.13.1 · qiskit 1.4.6 · qiskit-aer 0.17.2 ·
  qiskit-nature 0.7.2 · qiskit-ibm-runtime 0.41.1 · pyscf 2.14.0 · ply 3.11.
- **Új:** `requirements.lock` — a teljes tranzitív fa (53 csomag) a megépült
  image-ből, `pip freeze --all`-lal.
- Dockerfile: `libgomp1` (a PySCF OpenMP-futásideje) és `*_NUM_THREADS=1`
  a lebegőpontos determinizmushoz.

#### Tesztelés
- **+108 automatikus teszt** (összesen 216): validációs, integrációs és egységszint.
- `tests/validation/test_h2_vqe.py` — a fizikai helyesség 23 tesztje.
- `tests/integration/test_cli.py` — a teljes lánc a parancssoron keresztül.
- `tests/unit/` — konfiguráció, seedek, verziók, optimalizáló (analitikus
  célfüggvényen, kvantumszimuláció nélkül).
- `tests/repo/test_requirements.py` — a pin ↔ lock konzisztencia és a GPL-licenc
  elkülönítés ellenőrzése.
- A negatív harness **8 → 11** esetre bővült (TC-N9…N11).

#### Dokumentáció
- `docs/plan/phase_01.md` — a Fázis 1 bővített terve.
- `docs/01_vqe_core.md` — a VQE-mag használata, architektúrája és korlátai.
- `docs/testing/TP-F01` + `TR-F01` — tesztterv és mérési jegyzőkönyv.

### Mért eredmények (H2, 0.735 Å, STO-3G)

| Szint | Energia (Ha) | Eltérés |
|---|---|---|
| Hartree–Fock | −1.1169989968 | — |
| **L0 — PySCF Full CI** | **−1.1373060358** | referencia |
| **L1 — egzakt diagonalizáció** | **−1.1373060358** | +1.33 × 10⁻¹⁵ Ha |
| **L2 — VQE** | **−1.1373060358** | +9.33 × 10⁻¹⁵ Ha |

Visszanyert korrelációs energia: **100.0000 %**. A hiba a kémiai pontosság
(1.59 × 10⁻³ Ha) körülbelül 10⁻¹²-szerese.

Mindhárom leképezés (Jordan–Wigner, paritás, Bravyi–Kitaev) ugyanazt az energiát
adja; a paritás-leképezés kétqubites redukcióval 4 helyett **2 qubitet** és 15
helyett **5 Pauli-tagot** igényel.

### Szigorítva az alaptervhez képest
- Az elfogadási tolerancia ±0.01 Ha helyett **±1.6 mHa** (kémiai pontosság),
  és **két független referenciához** mérve, nem egy irodalmi számhoz.
- A „többször lefuttatva ugyanaz" elvárásból **automatikus, bitre azonosságot
  követelő teszt** lett (AC-1.6).
- A `run_vqe()` `float` helyett strukturált `VQEResult`-ot ad vissza; az
  alapterv által kért szám ennek az `energy` mezője.

### Javítva
- A `scipy.optimize` `TNC` metódusa `maxfun`-t vár `maxiter` helyett; a rossz
  opciókulcsot a SciPy **csendben eldobta**, így az iterációs korlát nem
  érvényesült. Az ismeretlen opciókulcs mostantól hibát ad, nem figyelmeztetést.
- A `qiskit-nature` több mezője (`num_particles`, `num_spatial_orbitals`,
  `nuclear_repulsion_energy`) lehet `None`; ezt explicit ellenőrzés kezeli
  beszédes hibaüzenettel.
- A CLI külön modulba (`vqebd.cli`) került, hogy a `runner` ne fusson egyszerre
  csomagimportként és `__main__`-ként (`runpy` figyelmeztetés).

### Ismert korlát
- A `qiskit-nature 0.7.2` UCCSD-je a Qiskit 1.4 `NLocal` osztályát használja,
  ami `PendingDeprecationWarning`-ot ad. Külső csomag, a helyességet nem érinti.

---

## [0.1.0] — 2026-09-22

**Fázis 0 lezárva — Alapinfrastruktúra és repó-szerkezet.**

### Hozzáadva

#### Infrastruktúra
- Git-repó, MIT licenc (Kormos Attila, Claude AI), `.gitignore`, `.gitattributes`,
  `.dockerignore`.
- Mappaszerkezet: `src/vqebd/` (5 alcsomag), `tests/` (unit, integration, validation,
  repo), `docker/`, `docs/` (plan, adr, testing, figures), `dashboard/`, `data/`,
  `scripts/`.
- `docker/Dockerfile` — `python:3.11-slim`, **digest-tel rögzítve**
  (`sha256:da047cb8…95ba9`, Python 3.11.16), nem-root felhasználó (uid 1000),
  `PYTHONHASHSEED=0`, OCI-címkék, `HEALTHCHECK`.
- `docker/docker-compose.yml` — egyetlen `app` szolgáltatás, nevesített `data` volume,
  opcionális `.env` betöltés.
- `Makefile` — `build`, `test`, `verify`, `lint`, `format`, `typecheck`, `check`, `shell`.
- `.github/workflows/ci.yml` — lint, típusellenőrzés és teszt konténerben.
- `.env.example` — titokkezelési minta, valódi token nélkül.

#### Csomagváz
- `vqebd` csomag `__version__`, `AUTHORS`, `LICENSE` attribútumokkal; a verzió
  igazságforrása a `VERSION` fájl.
- `py.typed` jelölő (PEP 561).
- Öt dokumentált alcsomag-váz: `backends`, `chemistry`, `mitigation`, `storage`, `vqe`.

#### Tesztelés
- 9 tesztmodulnyi automatikus ellenőrzés a Fázis 0 tíz elfogadási kritériumára.
- `tests/repo/` — repó-hatókörű tesztek (szerkezet, verzióegyezés, titokhigiénia),
  amelyek a szállított image-ben automatikusan kihagyásra kerülnek.
- `tests/unit/` — kódtesztek, amelyek mindenhol futnak.
- ADR-0002 betartatása automatikus teszttel: a `qiskit_algorithms` importja tilos
  a `src/vqebd/` alatt.

#### Dokumentáció
- [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) — bővített mesterterv:
  öt referenciaszint (L0–L3b), technológiai stack, verziózási és tesztelési politika,
  kockázatnyilvántartás.
- [`docs/plan/phase_00.md`](docs/plan/phase_00.md) — a Fázis 0 bővített terve.
- [`docs/00_setup.md`](docs/00_setup.md) — telepítési és futtatási útmutató.
- [`docs/references.md`](docs/references.md) — **37 hivatkozás, ebből 35 gépileg
  DOI-validált** a Crossref/DataCite API-val (`scripts/gen_references.py`).
- Öt architektúra-döntés (ADR-0001…0005).
- [`docs/testing/TR-000_spike.md`](docs/testing/TR-000_spike.md) — négykörös előzetes
  műszaki felderítés mérési jegyzőkönyve, 9 megállapítással.
- [`docs/testing/TP-F00_alapinfrastruktura.md`](docs/testing/TP-F00_alapinfrastruktura.md)
  és [`TR-F00`](docs/testing/TR-F00_alapinfrastruktura.md) — a Fázis 0 tesztterve és
  jegyzőkönyve.

### Fontos megállapítások (TR-000)

Ezek a mérések a projekt műszaki irányát határozták meg:

- **M1** — A Mitiq 0.47.0 (`numpy<2.0`) és a Qiskit 2.x (`numpy>=2.0`) **nem
  telepíthető egy környezetbe**. A stack ezért Qiskit **1.4.6**-ra rögzítve (ADR-0001).
- **M2** — A `ply==3.11` a Mitiq qiskit-interfészének **rejtett függősége**;
  közvetlen függőségként kezeljük.
- **M3** — A Mitiq `qiskit↔cirq` konverziója **eldobja az inaktív qubiteket**
  (5 qubites ISA-áramkörből 2 qubites lesz), így ISA-szinten nem használható (ADR-0003).
- **M4** — A saját unitáris hajtogatás és a Mitiq `fold_global` **bitre azonos**
  kapuszámot ad (23 / 69 / 115 λ=1/3/5-nél).
- **M5** — A ZNE **nem javítja a readout-hibát**; a mérési hibaenyhítés önálló
  sémadimenzió.
- **M6** — A `FakeBackend`-ek realisztikus zajmodellt adnak **IBM-kvóta nélkül** →
  új **Fázis 1b** iktatódik be a tervbe.

### Megjegyzés a függőségekről
A `requirements.txt` ebben a fázisban **szándékosan üres** — az alapterv előírása
szerint a Fázis 0 image nem tartalmazhat kvantumkönyvtárat. A teljes, már feloldott
stack a Fázis 1-ben kerül be.

[Unreleased]: https://github.com/kormosattila/vqebd/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kormosattila/vqebd/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kormosattila/vqebd/releases/tag/v0.1.0
