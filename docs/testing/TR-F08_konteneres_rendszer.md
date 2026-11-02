# TR-F08 — Fázis 8 mérési jegyzőkönyve (konténeres rendszer, a dashboard egyparancsos indítása)

| | |
|---|---|
| **Azonosító** | TR-F08 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 8 — Konténerizáció összeszerelése |
| **Tesztterv** | [`TP-F08`](TP-F08_konteneres_rendszer.md) |
| **Terv** | [`phase_08.md`](../plan/phase_08.md) |
| **Kódállapot** | `vqebd` 0.11.0 |
| **Státusz** | **Lezárva — mind a 10 elfogadási kritérium teljesült** (az 5. pont korlátaival) |

---

## 1. Összefoglalás

A Compose-rendszer három szolgáltatást tartalmaz (`app`, `scheduler`, `dashboard`), egy image-ből és egy közös
`vqebd-data` volume-mal. A dashboard a **saját gépen**, egyetlen paranccsal indul, és csak a gazdagép hurokcímén
érhető el.

| | |
|---|---|
| Elfogadási kritériumok | **10 / 10 teljesült** |
| Tesztkészlet | **772 teszt: 771 sikeres, 1 kihagyott** (TC-302, `mitiq` nélkül) |
| Új tesztek a Fázis 8-ban | **9** (`tests/repo/test_compose.py`); a v0.10.0: 763 |
| Tiszta klónos build | gyorsítótár nélkül sikeres; `pip freeze` ↔ lock: **101 / 101, 0 eltérés** |
| Futó dashboard | ~66 MiB RAM, 0.6% CPU üresjáratban |

## 2. Elfogadási kritériumok

| AC | Teszteset | Eredmény | Bizonyíték |
|---|---|---|---|
| AC-8.1 | TC-801 | ✅ három szolgáltatás, mind `vqebd:<VERSION>`; `docker compose config --services` = `app`, `scheduler`, `dashboard` | `test_compose.py`, végrehajtás |
| AC-8.2 | TC-802 | ✅ a klónból: a konténer `healthy` (4. ellenőrzésre, ~8 s), `/_stcore/health` = `ok`, a főoldal HTTP 200, 6602 bájt | végrehajtás |
| AC-8.3 | TC-803 | ✅ `docker compose build --no-cache dashboard` a klónból sikeres; 101 / 101 csomag, **0 eltérés** a lockkal | végrehajtás |
| AC-8.4 | TC-804 | ✅ `docker port vqebd-dashboard` → `8501/tcp -> 127.0.0.1:8501` | végrehajtás, `test_compose.py` |
| AC-8.5 | TC-805 | ✅ nincs `env_file`, token, `ibm_quantum`, `allow_hardware`, `.env` a dashboard-blokkban | `test_compose.py` |
| AC-8.6 | TC-806 | ✅ a konténerben 4 forrás: `scheduler.sqlite` (5 sor), `f5_deterministic.json` (50), `f5_statistical.json` (180), `results_v1.json` (8); az alapnézet és a három további nézet kivétel nélkül fut | végrehajtás |
| AC-8.7 | TC-807 | ✅ `/app/src`, `/app/dashboard`, `/app/docs/figures/data`: az írási kísérlet elbukik („csak olvasható") | végrehajtás |
| AC-8.8 | TC-808 | ✅ `docker compose down` után a `vqebd-data` volume megvan | végrehajtás |
| AC-8.9 | TC-809 | ✅ `make dashboard` / `dashboard-stop` / `dashboard-logs`; a 9 Compose-teszt zöld | `test_compose.py` |
| AC-8.10 | — | ✅ `docs/08_deployment.md`, TP-F08, TR-F08, README (HU/EN), az összes dokumentum átvilágítva, `v0.11.0` | commit, 3. pont |

## 3. Dokumentum-átvilágítás (a felhasználó kérésére)

Az átvilágítás a következőket találta és javította:

| Állomány | Észrevétel | Javítás |
|---|---|---|
| `README.md` (HU/EN) | a Fázis 8 „Tervezett", a `Gyors indítás` dashboard nélkül, régi verzió- és tesztszám | Fázis 8 lezárva, dashboard-indítás a `Gyors indítás`-ban, verzió `0.11.0`, tesztszám 772, új dokumentumsorok |
| `docs/07_dashboard.md` | az indítás nyers `docker run`; az L5 korlát („a Compose-szolgáltatás a Fázis 8 feladata") elavult; a „nem ír" túl egyszerű | indítás Compose-szal; L5 lezárva; a WAL-segédfájl pontosítása |
| `docs/06_automation.md` | nem említette, hogy az ütemező adatbázisát a dashboard megjeleníti | kiegészítve a közös volume-mal |
| `docs/00_setup.md` | a Fázis 0 állapotát írja (nincs jelölve, hogy történeti) | figyelmeztető fejléc a naprakész dokumentumokra |
| `docs/plan/phase_05_allapot.md` | a Fázis 5 folytatási jegyzete, a végrehajtás után is „folyamatban" hangzású | **archívként** jelölve |
| `docs/plan/00_master_plan.md` | a 8. fázis sora változatlan | 1.7.0, a fázis lezárva |
| `CHANGELOG.md` | — | `[0.11.0]` |

## 4. Mérés és megfigyelés

1. **Erőforrás:** a futó dashboard-konténer ~66 MiB RAM, 0.6% CPU üresjáratban (a konténer `docker stats`-a).
2. **Pontosítás a „csak olvas"-hoz:** a dashboard az adatbázist `read_only=True`-val nyitja, **az adatot nem
   módosítja**, de egy WAL módú adatbázis olvasásakor az SQLite `-shm` / `-wal` segédfájlt hozhat létre a
   `data/db/` mappában (megfigyelve a `scheduler.sqlite` mellett). Ezért a `vqebd-data` volume nem `:ro`. Az
   AC-7.9 („az adatbázisfájl bitre változatlan") a **főfájlra** igaz; a segédfájlokra nem vonatkozott, a korábbi
   dokumentumok („nem ír") ezzel a megkötéssel értendők.
3. **Az adatbetöltési utak** (a `08_deployment.md` 5. pontja) mind kipróbálva: `run_pipeline.py` a közös volume-ba
   (5 sor, a dashboard felderíti), `docker compose cp` a meglévő `f5.sqlite`-hoz (230 sor, a root tulajdonú
   másolat is olvasható).
4. A `scheduler`-tesztet a dashboard-szakasz miatt újra kellett határolni (a blokk addig tartott, amíg a fájl végéig).

## 5. Korlátok és nyitott pontok

| # | Korlát | Megjegyzés |
|---|---|---|
| L1 | **A „tiszta gép" nem volt valóban tiszta:** a klónt ugyanazon a gépen, ugyanazzal a Docker-démonnal, gyorsítótár nélküli építéssel próbáltuk; az alap-image (`python:3.11-slim`) már le volt töltve | másik gépen vagy VM-en nem próbáltuk |
| L2 | A fejlesztés Windows + Docker Desktop alatt történt; külön Linux- és macOS-teszt nincs | |
| L3 | Hosszú távú (napokig tartó) futást nem mértünk | a `restart: unless-stopped` viselkedését Docker-újraindítás után nem próbáltuk |
| L4 | Egy image mindhárom szolgáltatáshoz (2.19 GB) | külön, kisebb dashboard-image későbbi optimalizáció (`phase_08.md` D1) |
| L5 | Nincs hitelesítés; a védelem a hurokcím-kötés | a távoli használat követelményei: `08_deployment.md` 7. |

## 6. Reprodukálás

```bash
git clone https://github.com/aiasz/VQEBD.git && cd VQEBD
docker compose -f docker/docker-compose.yml build --no-cache dashboard      # AC-8.3
docker compose -f docker/docker-compose.yml up -d dashboard                 # AC-8.2
docker compose -f docker/docker-compose.yml ps                              # healthy
docker port vqebd-dashboard                                                 # AC-8.4: 127.0.0.1:8501
docker compose -f docker/docker-compose.yml down                            # AC-8.8: a volume megmarad
```

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
