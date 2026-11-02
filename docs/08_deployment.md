# 08 — Konténeres rendszer és a dashboard indítása (Fázis 8)

| | |
|---|---|
| **Dokumentum** | `docs/08_deployment.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Projektverzió** | 0.11.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 8 — Konténerizáció összeszerelése |
| **Háttér** | [`phase_08.md`](plan/phase_08.md) · [`TR-F08`](testing/TR-F08_konteneres_rendszer.md) |

---

## 1. Mit ad a Fázis 8?

Egy Compose-rendszer három, egymástól elszigetelt szolgáltatással, **egy image-ből** és egy közös adat-volume-mal:

| Szolgáltatás | Mire való | Ír? |
|---|---|---|
| `dashboard` | az eredmények böngészős nézegetője ([`07_dashboard.md`](07_dashboard.md)) | nem (csak olvas) |
| `scheduler` | a szimulátoros pipeline rendszeres futtatása ([`06_automation.md`](06_automation.md)) | igen (`data/db`, `data/logs`) |
| `app` | egyszeri parancsok (batch, pipeline, export) konténerben | igen, ha futtatod |

**A dashboard a saját gépeden fut, egyetlen paranccsal.** Nincs szükség külön hostra.

## 2. Előfeltételek

| Mi | Megjegyzés |
|---|---|
| **Docker** (Docker Desktop Windowson/macOS-en, Docker Engine Linuxon) | a `docker compose` (v2) parancs kell |
| **Git** | a klónozáshoz |
| **~3 GB szabad lemez** | az image 2.19 GB (a kvantumstack miatt) |
| **x86-64 (amd64) gép** | a build a lebegőpontos determinizmus miatt `linux/amd64`-re rögzített |
| **RAM** | a dashboardnak ~65 MiB üresjáratban, ~170 MB egy munkamenet csúcsán |

A `make` **nem kötelező** (Windowson ritkán van): minden parancsnak megvan a nyers `docker compose` alakja.

## 3. Első indítás

```bash
git clone https://github.com/aiasz/VQEBD.git
cd VQEBD
docker compose -f docker/docker-compose.yml up -d --build dashboard
```

Make-kel ugyanez: `make dashboard`. Utána nyisd meg: **<http://localhost:8501>**.

Az első építés (az alap-image letöltése és a függőségek telepítése) több percig tart; a következő indítások a
gyorsítótárból másodpercek alatt megvannak. Az állapot ellenőrzése: `docker compose -f docker/docker-compose.yml ps`
(a `dashboard` sora `healthy`).

> **Windows / Git Bash:** ha a `-v` mount útvonalait egyedi `docker run` parancsokban adod meg, az
> `MSYS_NO_PATHCONV=1` előtag kell. A Compose-parancsokhoz nem.

## 4. Mindennapi használat

| Mit | Parancs | Make |
|---|---|---|
| Indítás | `docker compose -f docker/docker-compose.yml up -d dashboard` | `make dashboard` |
| Leállítás | `docker compose -f docker/docker-compose.yml stop dashboard` | `make dashboard-stop` |
| Napló | `docker compose -f docker/docker-compose.yml logs -f dashboard` | `make dashboard-logs` |
| Állapot | `docker compose -f docker/docker-compose.yml ps` | — |
| Frissítés | `git pull`, majd `docker compose -f docker/docker-compose.yml up -d --build dashboard` | `make dashboard` |
| Másik port | `VQEBD_DASHBOARD_PORT=8600 docker compose -f docker/docker-compose.yml up -d dashboard` | — |

A szolgáltatás `restart: unless-stopped`: a Docker újraindulása után visszajön, amíg ki nem kapcsolod
(`stop`). Az ütemező indítása: `docker compose -f docker/docker-compose.yml up -d scheduler`.

## 5. Honnan jön az adat?

A dashboard az alábbiakat **automatikusan felderíti** a konténerben:

| Forrás | Hol | Hogyan kerül oda |
|---|---|---|
| A verziózott exportok | `docs/figures/data/f5_*.json`, `results_v*.json` | a repóból, csak olvasható mountként; **tiszta klónon is megvannak** (50 + 180 + 8 sor) |
| Az ütemező adatbázisa | `data/db/scheduler.sqlite` | a `scheduler` szolgáltatás írja a `vqebd-data` volume-ba |
| Saját pipeline-/batch-futás | `data/db/*.sqlite` | lásd lent |
| Meglévő helyi adatbázis | `data/db/*.sqlite` | lásd lent |

**Saját futás a közös volume-ba** (a dashboardon az oldal újratöltése után megjelenik):

```bash
docker compose -f docker/docker-compose.yml run --rm app python scripts/run_pipeline.py \
    --preset f5-smoke --db /app/data/db/pipeline.sqlite --log-dir /app/data/logs
```

**Meglévő helyi adatbázis megtekintése** (pl. az `f5.sqlite` a `data/db/` mappából):

```bash
docker compose -f docker/docker-compose.yml cp data/db/f5.sqlite dashboard:/app/data/db/f5.sqlite
```

A másolat a `vqebd-data` volume-ba kerül, ezért megmarad a konténer újraindítása után is.

## 6. Biztonság

- **A dashboardnak nincs hitelesítése.** A Compose ezért a portot csak a gazdagép hurokcímére kötötte:
  `127.0.0.1:8501`. A hálózaton kívülről **nem érhető el**; ellenőrzés: `docker port vqebd-dashboard`
  (`8501/tcp -> 127.0.0.1:8501`).
- **Ne állítsd át a kötést `0.0.0.0`-ra** hitelesítő reverse proxy vagy VPN nélkül.
- A dashboard-szolgáltatás **nem kap tokent**, `env_file`-t és hardverengedélyt, és nem ér el hálózatot vagy QPU-t.
  A kód- és export-mountok csak olvashatók (a konténerben megerősítve).
- **„Csak olvas" pontosan:** a dashboard az adatbázist `read_only=True`-val nyitja, **az adatot nem módosítja**.
  Egy WAL módú adatbázis olvasásához az SQLite azonban `-shm` / `-wal` **segédfájlt** hozhat létre a mappában
  (ezért a `vqebd-data` volume nem `:ro`, `phase_08.md` D3).

## 7. Ha mégis távoli hoston futna

Nem szükséges (a dashboard a saját gépen fut), de a követelmények:

| Mi | Érték |
|---|---|
| Architektúra | **x86-64 (amd64)**; ARM-en nem javasolt |
| Dashboard önmagában | 1 vCPU, 512 MB–1 GB RAM elég |
| Dashboard + ütemező | 2 vagy több vCPU; az ütemező CPU-igényes (az `f5-statistical` ≈ 20 perc, az `f5-deterministic` ≈ 40 perc) |
| Hálózat | **hitelesítő reverse proxy vagy VPN kötelező** a dashboard elé |
| IBM-token | **nem kell** a hostra: az ütemező csak szimulátort indít, a hardver szándékosan nincs ütemezve |

## 8. Eltávolítás

| Mit | Parancs | Adat |
|---|---|---|
| A konténerek leállítása és eltávolítása | `docker compose -f docker/docker-compose.yml down` | **megmarad** (`vqebd-data`) |
| A konténerek **és az adat** törlése | `docker compose -f docker/docker-compose.yml down -v` | **TÖRLŐDIK** az ütemező adatbázisa és naplója |
| Az image törlése | `docker rmi vqebd:0.11.0` | — |

## 9. Hibaelhárítás

| Tünet | Ok és megoldás |
|---|---|
| `port is already allocated` | a 8501 foglalt: `VQEBD_DASHBOARD_PORT=8600 docker compose … up -d dashboard` |
| A `dashboard` `unhealthy` vagy nem indul | `docker compose … logs dashboard`; az első indításnál a `start_period` 20 s |
| „Nincs megnyitható adatforrás" | nincs sem adatbázis, sem export: futtasd a pipeline-t (5. pont), vagy ellenőrizd, hogy a repó `docs/figures/data/` mappája megvan |
| A böngésző nem éri el a `localhost:8501`-et | a Docker fut-e (`docker ps`); távoli gépről a hurokcím miatt szándékosan nem érhető el |
| `make: command not found` (Windows) | használd a nyers `docker compose` parancsokat (4. pont) |
| Lassú első indulás | az image 2.19 GB; az építés és a letöltés egyszeri |

## 10. Ismert korlátok

| # | Korlát |
|---|---|
| L1 | A tiszta klónos igazolás ugyanazon a gépen, gyorsítótár nélküli építéssel történt; **másik gépen vagy VM-en nem próbáltuk** (TR-F08 5.) |
| L2 | A `dashboard` és az `app` ugyanazt a 2.19 GB-os image-et használja; külön, kisebb dashboard-image későbbi optimalizáció |
| L3 | A konténer frissítéséhez újra kell építeni (`--build`); automatikus frissítés nincs |
| L4 | Nincs hitelesítés, TLS és többfelhasználós működés; a hurokcím-kötés a védelem |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
