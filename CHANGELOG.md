# Változásnapló

A projekt minden lényeges változása ebben a fájlban szerepel.

A formátum a [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) ajánlást
követi, a verziózás a [Semantic Versioning 2.0.0](https://semver.org/) szerint történik.
A `MINOR` verzió minden lezárt projektfázisnál lép
(lásd [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md), 8.1).

---

## [Unreleased] — Nem kiadott

### Tervezett
- **Fázis 1** — H2-VQE szimulátoron, L0/L1/L2 keresztvalidációval (`v0.2.0`).

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

[Unreleased]: https://github.com/kormosattila/vqebd/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kormosattila/vqebd/releases/tag/v0.1.0
