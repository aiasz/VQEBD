# TR-F09 — Fázis 9 mérési jegyzőkönyve (dokumentáció, validálás, publikálás)

| | |
|---|---|
| **Azonosító** | TR-F09 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Fázis** | 9 — Dokumentáció, validálás, publikálás |
| **Tesztterv** | [`TP-F09`](TP-F09_publikalas.md) |
| **Terv** | [`phase_09.md`](../plan/phase_09.md) · [`docs/09_publishing.md`](../09_publishing.md) |
| **Kódállapot** | `vqebd` 1.0.0 |
| **Státusz** | **Lezárva — mind a 10 elfogadási kritérium teljesült.** A `v1.0.0` GitHub Release és a Zenodo-archívum létrejött; DOI: `10.5281/zenodo.23886002` (koncepció), `10.5281/zenodo.23886003` (verzió) |

---

## 1. Összefoglalás

| | |
|---|---|
| Elfogadási kritériumok | **10 / 10 teljesült** |
| Kiadás | GitHub Release `v1.0.0` (a `d0c22ce` commiton); Zenodo-rekord: <https://zenodo.org/records/23886003>; szerzők: Kormos, Attila; licenc: MIT |
| DOI | koncepció: `10.5281/zenodo.23886002`; verzió: `10.5281/zenodo.23886003`; mindkettő feloldódik (HTTP 302 a `doi.org`-ról) |
| GitHub CI a kiadási commiton (`d0c22ce`) | **zöld:** mindkét job sikeres (build–lint–típus–teszt; DOI-validálás); futás: 41450527321 |
| GitHub licenc-felismerés | `licenseInfo.key` = **`mit`** |
| Tesztkészlet | **792 teszt: 791 sikeres, 1 kihagyott** (TC-302, `mitiq` nélkül) |
| Új tesztek a Fázis 9-ben | **20** (`tests/repo/test_publication.py`); a v0.11.0: 772 |
| Minőségi kapuk | ruff check, ruff format, mypy (strict): tiszta |
| CI-tesztlépések helyben | szállított image mount nélkül: **575 sikeres, 0 hibás**; repó `:ro` mounttal: **770 sikeres, 0 hibás** (a CI `-m "not hardware"` szűrőjével) |
| `CITATION.cff` | érvényes (CFF 1.2.0, `cffconvert --validate`) |
| README-alapú telepítés | tiszta klónból szó szerint sikeres (3. pont) |

## 2. Elfogadási kritériumok

| AC | Teszteset | Eredmény | Bizonyíték |
|---|---|---|---|
| AC-9.1 | TC-901 | ✅ a hiba javítva (`c9794db`); a GitHub CI **minden jobja zöld** a `d0c22ce` kiadási commiton (futás: 41450527321) | `gh run list`, `gh run view` |
| AC-9.2 | TC-902 | ✅ helyben: a `LICENSE` a kanonikus MIT-törzs, nincs benne GPL/Mitiq/függelék; a `NOTICE` a Mitiq/GPL megjegyzést, a modulútvonalat, a lockot és az ADR-0003-at tartalmazza. ✅ a GitHub `licenseInfo.key` = `mit` felismerése igazolva | `test_publication.py` |
| AC-9.3 | TC-903 | ✅ `cffconvert --validate`: „valid according to schema version 1.2.0"; a Zenodo-metaadat: verzió 1.0.0, dátum 2026-11-02, licenc MIT; a `version`/`date-released` a `VERSION`-nel és a `CHANGELOG`-gal egyezik | végrehajtás, `test_publication.py` |
| AC-9.4 | TC-904 | ✅ `CONTRIBUTING.md`, `SECURITY.md`, 3 issue-sablon-fájl; a README mindkét nyelven hivatkozik rájuk | `test_publication.py` |
| AC-9.5 | TC-905 | ✅ „Röviden" / „In short" blokk, háromparancsos gyors indítás HU és EN, példa kimenet, CI-jelvény | `test_publication.py` |
| AC-9.6 | TC-906 | ✅ minden Markdown-fájl minden relatív hivatkozása (> 100) létező fájlra mutat | `test_publication.py` |
| AC-9.7 | TC-907 | ✅ a README két kulcsverzió-táblázata (14 csomag) azonos egymással és a lockkal | `test_publication.py` |
| AC-9.8 | TC-908 | ✅ tiszta klónból a README parancsai szó szerint (3. pont) | végrehajtás |
| AC-9.9 | TC-909 | ✅ a `VERSION`, a `CITATION.cff`, a Compose-címkék (3), a BibTeX (HU és EN) és a dokumentumok verziója 1.0.0; a `docs/09_publishing.md` megvan | `test_version_consistency.py`, `test_publication.py` |
| AC-9.10 | TC-910 | ✅ a GitHub Release `v1.0.0` létrejött; a Zenodo a release-t archiválta; a DOI-k (`10.5281/zenodo.23886002`, `10.5281/zenodo.23886003`) beírva a `CITATION.cff`-be és a README-ba (HU és EN, jelvénnyel) | `gh release view`, Zenodo API, `docs/09_publishing.md` |

## 3. A README-alapú telepítés (AC-9.8)

A README „Gyors kipróbálás" parancsait **szó szerint** futtattuk egy tiszta klónban:

| Lépés | Parancs | Eredmény | Idő |
|---|---|---|---|
| 1 | `git clone … && cd VQEBD` | a commitolt állapot (v1.0.0) ¹ | 3 s |
| 2 | `docker compose -f docker/docker-compose.yml build app` | kilépési kód 0, `vqebd:1.0.0` ² | 4 s |
| 3 | `docker compose … run --rm app python -m vqebd` | kilépési kód 0; a README példa kimenetének **mind az 5 sora egyezik** | 5 s |
| 4 | `docker compose … up -d dashboard` | `healthy`, `/_stcore/health` = `ok`, főoldal HTTP 200, `8501/tcp -> 127.0.0.1:8501` | 11 s |

¹ A távoli URL helyett a **helyi, commitolt** állapotot klónoztuk, mert a v1.0.0 még nincs pusholva.
² A Docker-gyorsítótár **meleg** volt (ugyanazon a gépen épült korábban); egy valódi első építés több percig tart. Az
**ugyanezt gyorsítótár nélkül** a Fázis 8-ban igazoltuk (a `pip freeze` a lockkal 0 eltérés).

## 4. Amit a mérés megmutatott

1. **A GitHub CI hibás volt** az első, a v0.9.0-t tartalmazó push (`578a49d`) óta. Az ok: a Fázis 6-ban írt
   `test_compose_defines_a_simulator_only_scheduler_service` a `docker-compose.yml`-t a fájl helyéből számolt útvonalon olvasta
   (`parents[2]`), a szállított image-ben (mount nélkül) viszont nincs `docker/` mappa. **A saját hibám:** helyben mindig
   bind-mountolt repóval futtattam, ezért a mount nélküli CI-lépés bukása nem tűnt fel. A lekérdezett hat futás között
   négy hibás volt: a `578a49d` és három 2026-09-23-i futás; **ez utóbbiakat nem vizsgáltam**, a köztes `891b01f` zöld volt.
2. **A GitHub a licencet nem ismerte fel** (`licenseInfo.key` = `other`): a `LICENSE` a szabványos MIT-szöveg után egy
   harmadik-fél-függeléket is tartalmazott. A függelék a `NOTICE`-ba költözött.
3. **A védőtesztek működnek:** a hivatkozás-ellenőrző a hiányzó `TR-F09`-et pontosan megnevezte, mielőtt létezett.
4. **A kiadási verzió a saját tervünkből következik:** a mesterterv 8.1 szerint a Fázis 9 lezárása a `1.0.0`.

## 5. Korlátok és nyitott pontok

| # | Korlát | Megjegyzés |
|---|---|---|
| L1 | **A „külső személy" az asszisztens volt, ugyanazon a gépen** (TC-908) | független személy próbája nem volt; a Fázis 10 első lépése lehet |
| L2 | A Zenodo felülete és a DOI-kiosztás nem volt ellenőrizhető | a `09_publishing.md` 2. pontja emlékezetből készült, ezt jelöli |
| L3 | ~~A GitHub-oldali licenc-felismerés és a zöld CI csak a push után igazolható~~ | **igazolva** a push után (AC-9.1, AC-9.2) |
| L4 | **Eldöntve (D4):** a Zenodo-rekord szerzője csak Kormos Attila; az AI a README/dokumentumok „Készítők" soraiban és a `LICENSE` szerzői sorában marad | a `LICENSE` szerzői sorának egységesítése külön döntés |
| L5 | A README példa kimenete a program magyar nyelvű kimenete | az angol szakasz ezt jelzi |
| L6 | Nincs böngészős képernyőkép a README-ban | TR-F07 L1 |

## 6. Reprodukálás

```bash
git clone https://github.com/aiasz/VQEBD.git && cd VQEBD
docker compose -f docker/docker-compose.yml build app
docker compose -f docker/docker-compose.yml run --rm app python -m vqebd
docker compose -f docker/docker-compose.yml up -d dashboard      # http://localhost:8501
# a CI két tesztlépése
docker run --rm -e VQEBD_IN_CONTAINER=1 vqebd:1.0.0 python -m pytest tests -ra -m "not hardware" -p no:cacheprovider
docker run --rm -v "$PWD:/repo:ro" -e VQEBD_REPO_ROOT=/repo -e PYTHONPATH=/repo/src -e VQEBD_IN_CONTAINER=1 \
    -w /repo vqebd:1.0.0 python -m pytest tests -ra -m "not hardware" -p no:cacheprovider
```

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
