# Fázis 0 — Alapinfrastruktúra és repó-szerkezet (bővített terv)

| | |
|---|---|
| **Fázis** | 0 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Státusz** | **Elfogadott — végrehajtás alatt** |
| **Célverzió** | `v0.1.0` |
| **Előzmény** | [`00_master_plan.md`](00_master_plan.md), [`TR-000_spike.md`](../testing/TR-000_spike.md) |

---

## 1. Az alapterv szövege és a bővítés viszonya

Az alapterv Fázis 0-ja:

> **Cél:** A projekt csontszerkezetének létrehozása, Docker-alapokkal, mielőtt
> egyetlen kvantumsor is lefutna.
> **Elfogadási kritérium:** `docker build` sikeresen lefut, és a konténerben
> `python --version` helyes kimenetet ad.

Ez a terv ezt **megtartja és kiegészíti**. Az alapterv egy szándékosan szigorú
elvet mond ki: *„Egyetlen minimális Dockerfile, amely csak Python 3.11 + pip-et
telepít, semmi kvantumkönyvtárat még. A `requirements.txt` üres, csak `pytest`
benne."*

**Ezt az elvet tiszteletben tartjuk**, noha a TR-000 spike-ból már ismerjük a teljes
stacket. Indok: a Fázis 0 célja annak igazolása, hogy a *konténer-infrastruktúra*
önmagában működik. Ha a kvantumkönyvtárakat is most telepítenénk, egy build-hiba
esetén nem tudnánk, hogy az infrastruktúra vagy a függőségek hibásak-e. A teljes
stack a **Fázis 1**-ben kerül be, a TR-000-ban már feloldott, rögzített verziókkal.

---

## 2. Célkitűzések

| # | Cél |
|---|---|
| C0.1 | Verziókezelt, licencelt, publikálásra alkalmas repó-váz. |
| C0.2 | Reprodukálható, minimális Docker-környezet Python 3.11-gyel. |
| C0.3 | Működő tesztfuttatás a konténerben (`pytest`). |
| C0.4 | Minőségi kapuk (lint, típusellenőrzés) helyben és CI-ben. |
| C0.5 | A dokumentációs és verziózási rendszer élesítése (nem a végén, hanem most). |
| C0.6 | Titokkezelési alapok — az IBM-token soha ne kerülhessen a repóba. |

---

## 3. Szállítandók

### 3.1 Repó-szerkezet

```
VQEBD/
├── .github/workflows/ci.yml        # CI: lint + típus + teszt konténerben
├── .dockerignore
├── .gitignore
├── .env.example                    # minta; a valódi .env SOHA nem kerül be
├── LICENSE                         # MIT — Kormos Attila, Claude AI
├── README.md
├── CHANGELOG.md                    # Keep a Changelog 1.1.0
├── CITATION.cff                    # Citation File Format 1.2.0
├── VERSION                         # egyetlen sor: 0.1.0
├── Makefile                        # make build / test / lint / check / shell
├── pyproject.toml                  # csomag-metaadat + ruff/mypy/pytest konfig
├── requirements.txt                # futásidejű függőségek (Fázis 0: üres)
├── requirements-dev.txt            # pytest, ruff, mypy
├── docker/
│   ├── Dockerfile                  # python:3.11-slim, digest-pinnelve
│   └── docker-compose.yml          # Fázis 0: csak az `app` szolgáltatás
├── src/vqebd/
│   ├── __init__.py                 # __version__ a VERSION fájlból
│   ├── py.typed                    # PEP 561 — típusinformáció szállítása
│   ├── backends/  chemistry/  mitigation/  storage/  vqe/   # üres csomagvázak
├── tests/
│   ├── conftest.py
│   ├── unit/                       # gyors, izolált
│   ├── integration/                # több modul, szimulátor
│   └── validation/                 # fizikai helyesség irodalmi értékkel
├── dashboard/                      # Fázis 7
├── data/{raw,db}/                  # futásidőben keletkezik, .gitignore-olt
├── scripts/
│   ├── gen_references.py           # kész (hivatkozásjegyzék-generátor)
│   └── spike/                      # TR-000 reprodukáló szkriptek
└── docs/
    ├── 00_setup.md                 # az alapterv által előírt fázis-dokumentum
    ├── references.md               # kész, 37 tétel, 35 DOI-validált
    ├── plan/     adr/     testing/     figures/
```

### 3.2 Docker-image specifikáció

| Jellemző | Érték | Indok |
|---|---|---|
| Alap | `python:3.11-slim`, **digest-tel rögzítve** | Reprodukálhatóság: a tag mozog, a digest nem. |
| Platform | `linux/amd64` | Lebegőpontos determinizmus (ADR-0005). |
| Felhasználó | nem-root (`vqebd`, uid 1000) | Biztonság; a bind-mountolt fájlok tulajdonjoga. |
| `PYTHONHASHSEED` | `0` | Determinizmus (ADR-0005, 5. véletlenforrás). |
| `PYTHONDONTWRITEBYTECODE` | `1` | Tiszta bind-mount, nincs `__pycache__` szemét. |
| `PYTHONUNBUFFERED` | `1` | A naplók azonnal láthatók. |
| Munkakönyvtár | `/app` | — |
| `PYTHONPATH` | `/app/src` | A `src/` layout importálhatósága telepítés nélkül. |
| Rétegsorrend | függőségek → forrás | Cache-hatékonyság: a kód változása nem építi újra a pipet. |

> **Miért nem `python:3.11-alpine`?** Az Alpine a musl libc-t használja; a `numpy`,
> `scipy`, `pyscf` és `qiskit-aer` bináris wheel-jei manylinux-alapúak, így Alpine-on
> forrásból fordulnának (hosszú build, eltérő numerika). A `slim` (Debian, glibc)
> a helyes választás — ezt a Fázis 1 igazolja majd, de a döntés már most születik.

### 3.3 Minőségi kapuk

| Eszköz | Konfiguráció | Szigor |
|---|---|---|
| `ruff check` | `pyproject.toml` | E, F, I, N, UP, B, SIM, RUF szabálycsoportok |
| `ruff format --check` | 100 karakteres sorhossz | kötelező |
| `mypy` | `src/vqebd/` felett, `strict = true` | kötelező |
| `pytest` | `tests/`, `--strict-markers`, `-q` | kötelező |

---

## 4. Elfogadási kritériumok

Az alapterv egyetlen kritériuma (AC-0.1, AC-0.2) alatt van, a többi bővítés.
**Mind a 10 teljesülése szükséges a fázis lezárásához.**

| # | Kritérium | Ellenőrzés módja |
|---|---|---|
| **AC-0.1** | `docker build` hiba nélkül lefut. | manuális + CI |
| **AC-0.2** | A konténerben `python --version` → `Python 3.11.x`. | automatikus (`make verify`) |
| **AC-0.3** | A konténerben `pytest` lefut, minden teszt zöld, 0 hiba. | automatikus |
| **AC-0.4** | A konténer **nem root**-ként fut (`id -u` ≠ 0). | automatikus |
| **AC-0.5** | `PYTHONHASHSEED=0` a konténerben. | automatikus |
| **AC-0.6** | A repó-szerkezet megfelel a 3.1 specifikációnak. | automatikus teszt |
| **AC-0.7** | `VERSION` == `pyproject.toml` verzió == `src/vqebd.__version__` == `CHANGELOG` legfelső bejegyzés. | automatikus teszt |
| **AC-0.8** | A `.gitignore` kizárja: `.env`, `*.sqlite`, `data/`, titkok. | automatikus teszt |
| **AC-0.9** | `ruff check` és `mypy` hiba nélkül fut. | automatikus |
| **AC-0.10** | Az image kétszeri építése ugyanazt a Python-verziót adja (digest-pin működik). | manuális, TR-F00-ban rögzítve |

---

## 5. Tesztelési terv (összefoglaló)

A részletes tesztterv: [`docs/testing/TP-F00_alapinfrastruktura.md`](../testing/TP-F00_alapinfrastruktura.md).
A Mesterterv 9.3 szerinti **három kör**:

| Kör | Tartalom |
|---|---|
| **1 — funkcionális** | AC-0.1…AC-0.5: épül-e, fut-e, jó verzió-e. |
| **2 — robusztussági** | Újraépítés cache nélkül; teszt hibás `VERSION`-nel (a teszt *elbukik-e*, amikor kell); bind-mount jogosultságok; `.env` szivárgás-ellenőrzés. |
| **3 — keresztvalidáció** | A konténerben és a gazdagépen futtatott `pytest` ugyanazt adja; a `docker compose run` és a `docker run` ekvivalens. |

### Negatív tesztek (a „a teszt tényleg fog-e?" ellenőrzése)

Egy zöld teszt csak akkor ér valamit, ha piros is tud lenni. A 2. körben
szándékosan elrontunk három dolgot, és **elvárjuk a hibát**:

1. `VERSION` átírása → az AC-0.7 tesztnek buknia kell.
2. `.gitignore`-ból a `.env` törlése → az AC-0.8 tesztnek buknia kell.
3. Egy kötelező könyvtár törlése → az AC-0.6 tesztnek buknia kell.

---

## 6. Kockázatok ebben a fázisban

| # | Kockázat | Ellenintézkedés |
|---|---|---|
| R0.1 | A digest-pin elavul (az image törlődik a registryből). | A digest mellett a tag is szerepel kommentben; a CI hetente ellenőrzi. |
| R0.2 | Windows↔Linux sorvégek (CRLF) elrontják a shell-szkripteket. | `.gitattributes` `* text=auto eol=lf`; a Dockerfile nem használ host-szkriptet. |
| R0.3 | A bind-mountolt fájlok root tulajdonba kerülnek. | Nem-root konténerfelhasználó, uid 1000. |
| R0.4 | Titok (IBM-token) véletlen commitolása. | `.gitignore` + `.env.example` + automatikus teszt + a README figyelmeztetése. |

---

## 7. Amit ez a fázis **nem** tartalmaz

- Semmilyen kvantumkönyvtárat (→ Fázis 1).
- Semmilyen VQE-kódot (→ Fázis 1).
- IBM-hitelesítést (→ Fázis 2).
- Adatbázist (→ Fázis 4).
- Dashboardot (→ Fázis 7).
- Többszolgáltatásos compose-t (→ Fázis 8). A Fázis 0 compose-ában **csak** az
  `app` szolgáltatás van, hogy a `docker compose` útvonal már most teszteltessen.

---

## 8. Kilépési feltétel

A fázis akkor **zárható le**, ha:

1. mind a 10 elfogadási kritérium dokumentáltan teljesül a
   [`TR-F00`](../testing/TR-F00_alapinfrastruktura.md) jegyzőkönyvben;
2. a három tesztkör lefutott, a negatív tesztek is a várt módon buktak;
3. a `CHANGELOG.md` `0.1.0` bejegyzése kész;
4. a `v0.1.0` annotált Git-tag létrejött.

---

## 9. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
