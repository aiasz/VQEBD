# 00 — Telepítés és futtatás (Fázis 0)

| | |
|---|---|
| **Dokumentum** | `docs/00_setup.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Projektverzió** | 0.1.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 0 — Alapinfrastruktúra |

---

## 1. Mit tartalmaz ez a fázis

A Fázis 0 terméke a **konténer-infrastruktúra**, kvantumkönyvtárak nélkül. Ez
szándékos: ha a kvantum-stack is most kerülne be, egy build-hiba esetén nem
lehetne szétválasztani az infrastruktúra és a függőségek hibáját. A teljes stack
a Fázis 1-ben kerül be, a [`TR-000`](testing/TR-000_spike.md)-ban már feloldott,
rögzített verziókkal.

---

## 2. Előfeltételek

| Szoftver | Minimum | Ellenőrzés | Megjegyzés |
|---|---|---|---|
| Docker Engine | 24.0 | `docker --version` | **Linux konténerek** módban |
| Docker Compose | v2.20 | `docker compose version` | a `docker compose` (nem `docker-compose`) |
| Git | 2.30 | `git --version` | |
| GNU Make | 4.0 | `make --version` | *opcionális* — lásd a 4.3 szakaszt |

**Fejlesztett és tesztelt környezet (2026-09-22):**
Windows 11 Pro 10.0.26200 · Docker 29.1.3 (szerver: linux/amd64, 8 GB) ·
Docker Compose v5.0.0-desktop.1 · Git 2.50.1

> **Fontos.** A gazdagépre **nem kell Pythont telepíteni**. Minden számítás
> konténerben fut — egyrészt a reprodukálhatóság miatt, másrészt mert a PySCF
> (a Fázis 1-től használt kvantumkémiai motor) **nem támogatja natívan a
> Windowst**. Lásd R8 kockázat, [`00_master_plan.md`](plan/00_master_plan.md).

---

## 3. Telepítés

```bash
git clone https://github.com/aiasz/VQEBD.git
cd vqebd
```

A Fázis 0 nem igényel titkokat. (Az IBM-token csak a Fázis 2-től kell; a minta
fájl már most rendelkezésre áll: `.env.example`.)

---

## 4. Az image építése és futtatása

### 4.1 Make-kel (ajánlott)

```bash
make build      # image építése          -> AC-0.1
make verify     # a SZÁLLÍTOTT image önellenőrzése -> AC-0.2, AC-0.3, AC-0.4, AC-0.5
make test       # teljes tesztkészlet a bind-mountolt repóval
make check      # lint + típusellenőrzés + teszt -> AC-0.9
make help       # minden elérhető parancs
```

### 4.2 Docker compose-zal

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml run --rm app python --version
```

### 4.3 Nyers Docker-parancsokkal (Make nélkül, pl. Windows PowerShell)

```powershell
# Építés
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.3.0 .

# AC-0.2 — Python-verzió
docker run --rm vqebd:0.3.0 python --version

# AC-0.4 — nem-root futás (a várt kimenet 1000, NEM 0)
docker run --rm vqebd:0.3.0 id -u

# AC-0.5 — determinizmus
docker run --rm vqebd:0.3.0 printenv PYTHONHASHSEED

# AC-0.3 — a szállított image beépített tesztjei
docker run --rm -e VQEBD_IN_CONTAINER=1 vqebd:0.3.0 python -m pytest tests -ra

# Teljes tesztkészlet a repóval (a repó-hatókörű tesztek is futnak)
docker run --rm -v "${PWD}:/repo:ro" -e VQEBD_REPO_ROOT=/repo `
  -e PYTHONPATH=/repo/src -e VQEBD_IN_CONTAINER=1 -w /repo `
  vqebd:0.3.0 python -m pytest tests -ra -p no:cacheprovider
```

### 4.4 Várt kimenetek

| Parancs | Várt kimenet |
|---|---|
| `python --version` | `Python 3.11.16` |
| `id -u` | `1000` |
| `printenv PYTHONHASHSEED` | `0` |
| `python -m pytest tests` | minden teszt zöld; a repó-hatókörűek `skipped` |

---

## 5. Az image felépítése

```
python:3.11-slim@sha256:da047cb8…95ba9     <- DIGEST-tel rögzítve
  └─ nem-root felhasználó: vqebd (uid 1000, gid 1000)
     └─ ENV: PYTHONHASHSEED=0, PYTHONPATH=/app/src,
             PYTHONDONTWRITEBYTECODE=1, PYTHONUNBUFFERED=1
        └─ pip: requirements.txt (Fázis 0-ban üres) + requirements-dev.txt
           └─ /app/{VERSION, pyproject.toml, src/, tests/, scripts/}
              └─ /app/data/{db,raw,exports}   <- ide csatol a compose volume
```

### Miért digest és nem tag?

A `python:3.11-slim` **tag mozog**: ma 3.11.16-ra mutat, holnap 3.11.17-re, és a
mögöttes Debian-csomagok is frissülnek. Egy benchmark-projektben, amelynek a
terméke maga a reprodukálhatóság, ez elfogadhatatlan. A digest az image
tartalmának kriptográfiai ujjlenyomata — **soha nem változik**.

Ha a digestet frissíteni kell (pl. biztonsági javítás miatt):

```bash
docker pull python:3.11-slim
docker inspect python:3.11-slim --format '{{index .RepoDigests 0}}'
# az új digestet írd be a docker/Dockerfile FROM sorába, és rögzítsd a CHANGELOG-ban
```

### Miért `slim` és nem `alpine`?

Az Alpine a **musl** libc-t használja. A `numpy`, `scipy`, `pyscf` és `qiskit-aer`
bináris wheel-jei viszont **manylinux** (glibc) alapúak, így Alpine-on forrásból
fordulnának: hosszú build, és — ami súlyosabb — potenciálisan **eltérő numerikus
eredmények**. A `slim` (Debian, glibc) a helyes választás.

---

## 6. Tesztelési modell

A tesztek két hatókörben futnak. Ez a megkülönböztetés szándékos:

| Hatókör | Könyvtár | Mit vizsgál | Hol fut |
|---|---|---|---|
| **Kód** | `tests/unit/`, `tests/integration/`, `tests/validation/` | A csomag viselkedését. | mindenhol — a szállított image-ben is |
| **Repó** | `tests/repo/` | A checkout szerkezetét, verzióegyezést, titokhigiéniát. | gazdagépen és bind-mountolt repóval |

A `tests/repo/` tesztjei a szállított image-ben **automatikusan kihagyásra
kerülnek**, mert ott nincs teljes checkout (a `docs/` és a `LICENSE` szándékosan
nem kerül az image-be). A kihagyás indoklása megjelenik a `pytest -ra` kimenetben —
nem néma.

A repó-gyökér felismerése: `VQEBD_REPO_ROOT` környezeti változó, vagy a
`pyproject.toml` + `VERSION` + `LICENSE` + `docs` + `src` jelölők együttes megléte.

---

## 7. Hibaelhárítás

| Tünet | Ok | Megoldás |
|---|---|---|
| `docker: command not found` | Docker nincs telepítve vagy nem fut. | Indítsd el a Docker Desktopot. |
| `failed to solve: python:3.11-slim@sha256:…: not found` | A digest elavult a registryben. | Frissítsd a digestet az 5. szakasz szerint. |
| `exec /usr/local/bin/python: exec format error` | ARM gazdagép, amd64 image. | `--platform linux/amd64` (emulációval lassú, de működik). |
| A repó-tesztek `skipped` státuszúak | Hiányzik a teljes checkout. | `-v "$PWD:/repo:ro" -e VQEBD_REPO_ROOT=/repo` |
| `permission denied` bind-mountolt fájlon | uid-eltérés a gazdagép és a konténer között. | `docker build --build-arg APP_UID=$(id -u) --build-arg APP_GID=$(id -g) …` |
| CRLF-hiba shell-szkriptben | Windows sorvégek. | A `.gitattributes` `eol=lf`-et kényszerít; klónozz újra. |
| `make: command not found` (Windows) | Nincs GNU Make. | Használd a 4.3 szakasz nyers parancsait. |

---

## 8. A Fázis 0 elfogadási kritériumai

A teljes lista és a mérési eredmények:
[`docs/testing/TR-F00_alapinfrastruktura.md`](testing/TR-F00_alapinfrastruktura.md).

| # | Kritérium | Hogyan ellenőrizd |
|---|---|---|
| AC-0.1 | `docker build` hiba nélkül lefut | `make build` |
| AC-0.2 | `python --version` → `Python 3.11.x` | `make verify` |
| AC-0.3 | `pytest` zölden lefut a konténerben | `make verify` |
| AC-0.4 | A konténer nem root-ként fut | `make verify` |
| AC-0.5 | `PYTHONHASHSEED=0` | `make verify` |
| AC-0.6 | A repó-szerkezet megfelel a tervnek | `make test` |
| AC-0.7 | A verziószám mindenhol egyezik | `make test` |
| AC-0.8 | A `.gitignore` kizárja a titkokat | `make test` |
| AC-0.9 | `ruff` és `mypy` hiba nélkül fut | `make check` |
| AC-0.10 | Kétszeri build ugyanazt adja | `make rebuild && make verify` |

---

## 9. Következő lépés

**Fázis 1** — H2-VQE szimulátoron. A kvantum-stack ekkor kerül be, a
[`TR-000`](testing/TR-000_spike.md)-ban rögzített verziókkal. Terv:
`docs/plan/phase_01.md`, dokumentáció: `docs/01_vqe_core.md`.

---

## 10. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás (Fázis 0). |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
