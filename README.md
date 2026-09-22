# VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard

[![Licenc: MIT](https://img.shields.io/badge/licenc-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Verzió](https://img.shields.io/badge/verzió-0.2.0-orange.svg)](CHANGELOG.md)
[![Fázis](https://img.shields.io/badge/fázis-1%2F10%20lezárva-yellow.svg)](docs/plan/00_master_plan.md)
[![Tesztek](https://img.shields.io/badge/tesztek-248%20zöld-brightgreen.svg)](docs/testing/TR-F01_vqe_mag.md)

> Reprodukálható, konténerizált benchmark kis molekulák VQE-alapú
> alapállapoti-energia számítására, hibaenyhítési stratégiák összehasonlításával —
> szimulátoron és valódi IBM-kvantumhardveren.

**Készítők:** Kormos Attila · Claude AI (Anthropic, Claude Opus 5)

---

## ⚠️ A projekt állapota

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

---

## Mit old meg ez a projekt?

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

### Fázis 1 — mért eredmény (H2, 0.735 Å, STO-3G, zajmentes)

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

---

## Gyors indítás

```bash
git clone https://github.com/kormosattila/vqebd.git
cd vqebd
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

---

## Dokumentáció

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

### Architektúra-döntések

| ADR | Döntés |
|---|---|
| [0001](docs/adr/ADR-0001-technologiai-stack.md) | A stack Qiskit **1.4.6**-ra rögzítve — a Mitiq 0.47.0 `numpy<2.0`-t követel, a Qiskit 2.x `numpy>=2.0`-t |
| [0002](docs/adr/ADR-0002-sajat-vqe-hurok.md) | Saját VQE-hurok **V2 primitívekkel**, `qiskit-algorithms` nélkül → Qiskit 2.x-re átvihető |
| [0003](docs/adr/ADR-0003-mitigacios-architektura.md) | Pluginalapú hibaenyhítés, **saját ISA-biztos ZNE** (a Mitiq ISA-áramkörön qubiteket veszít) |
| [0004](docs/adr/ADR-0004-adattarolas.md) | SQLite kanonikus tároló, sémaverziózással, FAIR-elvek szerint |
| [0005](docs/adr/ADR-0005-determinizmus.md) | Minden véletlenforrás explicit seedet kap, és rekordba kerül |

---

## Módszertani alapelvek

1. **Egyetlen fázis sem zárható le, amíg az elfogadási kritériuma dokumentáltan
   nem teljesül.**
2. **Minden fázis terve a megvalósítás előtt készül el**, és a mérési jegyzőkönyve
   utána — mindkettő verziózva.
3. **Három tesztkör fázisonként:** funkcionális → robusztussági → keresztvalidációs.
4. **Minden szám mért, nem becsült.** A dokumentációban szereplő értékek
   reprodukálható mérésekből származnak, a szkriptek a repóban vannak.
5. **A hivatkozások gépileg validáltak.** A `scripts/gen_references.py` a Crossref
   és DataCite API-ból oldja fel a bibliográfiai adatokat — a szerzőlistákat,
   címeket és évszámokat nem kézzel írjuk.

---

## Licenc és harmadik felek szoftverei

A VQEBD **MIT** licencű — lásd [`LICENSE`](LICENSE).

> **⚠️ Mitiq (GPL-3.0).** A Mitiq csomag GPL-3.0 licencű. A VQEBD **nem linkeli be
> és nem terjeszti újra**: opcionális, futásidőben betöltött komponensként
> használja, egyetlen modulba zárva (`src/vqebd/mitigation/mitiq_zne.py`).
> **Mitiq nélkül a rendszer teljes funkcionalitással működik.** Részletek:
> [ADR-0003](docs/adr/ADR-0003-mitigacios-architektura.md).

A felhasznált szoftverek teljes listája licencekkel és hivatkozásokkal:
[`docs/references.md`](docs/references.md).

---

## Biztonság

**Soha ne commitolj IBM API-tokent.** A védelem három rétegű, és automatikus teszt
őrzi (`tests/repo/test_secrets_hygiene.py`):

1. `.gitignore` — a titkok nem kerülnek verziókezelésbe;
2. `.dockerignore` — a titkok nem kerülnek az image rétegeibe;
3. tartalmi ellenőrzés — tokennek látszó string keresése a verziózott fájlokban.

A tokent a `.env` fájlba tedd (`cp .env.example .env`). A valódi hardverre küldést
külön biztonsági kapcsoló védi: `VQEBD_ALLOW_HARDWARE=false` az alapértelmezés.

---

## Hivatkozás

Ha a projektet használod, hivatkozz rá a [`CITATION.cff`](CITATION.cff) szerint.
A Zenodo DOI a Fázis 9-ben kerül ide.

---

## Közreműködés

A projekt jelenleg korai fázisban van. Hibajelzés és javaslat: GitHub Issues.
A commit-üzenetek a [Conventional Commits](https://www.conventionalcommits.org/)
konvenciót követik.

---

*© 2026 Kormos Attila, Claude AI (Anthropic) — MIT licenc*
