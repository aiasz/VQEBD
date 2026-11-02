# TR-F06 — Fázis 6 mérési jegyzőkönyve (automatizálás, hibatárolás, ütemezés)

| | |
|---|---|
| **Azonosító** | TR-F06 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 6 — Automatizálás |
| **Tesztterv** | [`TP-F06`](TP-F06_automatizalas.md) |
| **Terv / döntés** | [`phase_06.md`](../plan/phase_06.md) · [`ADR-0008`](../adr/ADR-0008-hibakezeles-es-utemezes.md) |
| **Kódállapot** | `vqebd` 0.9.0 |
| **Státusz** | **Lezárva — mind a 11 elfogadási kritérium teljesült** (a 6. pont korlátaival) |

---

## 1. Összefoglalás

A Fázis 6 a sikertelen futásokat adatbázisban tárolja (séma v3), osztályozott és korlátos
újrapróbálkozást végez, egy naplózott pipeline-t futtat, és ezt egy átfedés elleni zárral védett
ütemezőből indítja. A valódi QPU **nincs ütemezve**.

| | |
|---|---|
| Elfogadási kritériumok | **11 / 11 teljesült** |
| Tesztkészlet | **642 teszt: 641 sikeres, 1 kihagyott** (TC-302, `mitiq` nélkül) |
| Új tesztek a Fázis 6-ban | **105** (a v0.8.1: 537) |
| Minőségi kapuk | ruff check, ruff format, mypy (strict): tiszta |
| Konténeres ellenőrzés | `docker compose run scheduler`: `f5-smoke` 5 új futás, kilépési kód 0, a volume-jogosultság rendben (uid 1000) |

## 2. Elfogadási kritériumok

| AC | Teszteset | Eredmény | Bizonyíték |
|---|---|---|---|
| AC-6.1 | TC-601 | ✅ a hibás futás sorként tárolódik (`ValueError`, `permanent`, attempt 1), a batch folytatódik (2 futás tárolva), az export `failed` listája 1 elemű | `test_failing_run_is_stored_logged_and_does_not_crash_the_pipeline` |
| AC-6.2 | TC-602 | ✅ 19 osztályozási eset + 7 titoktalanítási eset; visszalépés `[5, 10, 20, 30, 30]` s a 30 s-os korláttal | `test_pipeline_errors.py`, `test_retry.py` |
| AC-6.3 | TC-603 | ✅ tartós és kvótahiba 1 próbálkozás, várakozás nélkül; átmeneti hiba legfeljebb `max_attempts`, várakozások `[5, 10]` s | `test_retry.py` |
| AC-6.4 | TC-604 | ✅ a próbálkozásszám újraindítás után érvényes (2 + 1 = 3); a feladott futást a pipeline kihagyja, nem jön új hibasor; `--retry-abandoned` megbocsát (`forgiven = 1`), a történet megmarad | `test_retry.py`, `test_pipeline.py` |
| AC-6.5 | TC-605 | ✅ hardveren 1 próbálkozás, várakozás nélkül; a `hardware_evaluation_budget` helyes; a batch szintű kapu 16 kiértékelést × 1.2-es tartalékot kér | `test_pipeline.py`, `test_hardware_guard.py` |
| AC-6.6 | TC-606 | ✅ dry run: 9 naplóbejegyzés, 5 új futás, kilépési kód 0; a második indítás 5 kihagyás | `test_dry_run_runs_the_whole_chain_without_error` + konténeres futás |
| AC-6.7 | TC-607 | ✅ a hibás futás naplózódik, a kilépési kód 1, az összegzés `partial` | `test_pipeline.py` |
| AC-6.8 | TC-608 | ✅ a token és a `crn:v1:…` az adatbázisból, a naplóból, a jelentésből, az exportból és az üzenetből is hiányzik; a hiba típusa (`RuntimeError`) megmarad | `test_secrets_never_reach_the_database_the_log_or_the_report` |
| AC-6.9 | TC-609 | ✅ a v2 rekord bitre változatlan (valódi futásból készült), a második megnyitás nem migrál újra, a friss és migrált `results` és `run_failures` azonos | `test_storage_v3.py` |
| AC-6.10 | TC-610 | ✅ kizárólagos zár, a határon (3600 s) elavul, 3599 s-on még él, sérült zár átvehető, idegen zárat a `release` nem töröl, kivételnél is elengedődik | `test_scheduler.py` |
| AC-6.11 | TC-611 | ✅ a `scheduler` szolgáltatás érvényes (`docker compose config --services`: `app`, `scheduler`), titok és `--allow-hardware` nélkül; `--allow-hardware` + `--every` elutasított (2-es kód) | `test_scheduler.py`, `test_pipeline.py` |

### 2.1 Új tesztek fájlonként

| Fájl | Tesztek |
|---|---|
| `tests/unit/test_pipeline_errors.py` | 28 |
| `tests/unit/test_retry.py` | 18 |
| `tests/unit/test_storage_v3.py` | 12 |
| `tests/unit/test_scheduler.py` | 31 |
| `tests/integration/test_pipeline.py` | 14 |
| `tests/unit/test_hardware_guard.py` (+2 a kapuhoz) | 25 összesen |

## 3. Elővizsgálat és megvalósítás: amit a mérés megmutatott

1. **A hibák ma nem maradtak meg** (előmérés, `phase_06.md` 2.): a Fázis 5 batch-ben egy hibás futás
   hibája csak a memóriában élt, hibatábla nem volt. A Fázis 6 ezt a `run_failures` táblával zárja.
2. **A „rossz backendnév" hibainjektálás nem működik batch szinten:** a `BatchCell` már a
   konstruktorában elutasítja (`KeyError`), a batch futása előtt. A hibainjektáláshoz futásidejű
   hibát használtunk (érvénytelen aktív tér: (2e,50o) LiH-ra).
3. **Hiányt találtunk a saját tervünkben:** a `phase_06.md` 4.6 pontja batch szintű kvótakaput
   ír elő, de az első megvalósítás csak a futásonkénti védelmet (`run_vqe`) használta. A kaput a
   tesztelés közben pótoltuk (`guard_hardware_vqe(…, reserve=1.2)` a pipeline előellenőrzésében,
   2 új teszt); a `hardware_evaluation_budget` közös függvény lett, hogy a runner és a pipeline
   ugyanazt a képletet használja.
4. **Windows-veszély:** a PID-alapú zárelavulás `os.kill(pid, 0)`-t igényelne, ami Windowson a
   folyamatot megszüntetné. Ezért a zár **kizárólag időalapú** (12 óra), ennek ára a 6. pont L2
   korlátja.
5. **Az `abandoned` állapot levezetett,** nem tárolt oszlop: az utolsó aktív hiba `will_retry = 0`
   jelzője adja. A `--retry-abandoned` a sorokat nem törli, csak `forgiven = 1`-re állítja, így a
   hibatörténet auditálható marad.

## 4. Konténeres ellenőrzés

`docker compose -f docker/docker-compose.yml run --rm scheduler python -m vqebd.scheduler --preset
f5-smoke …` (egyszeri mód, a `vqebd-data` volume-mal):

- kimenet: `f5-smoke: 5 új, 0 kihagyva, 0 hibás, 0 feladott`, `[ütemező] iteráció 1: kilépési kód 0`;
- a volume `db/`, `exports/`, `logs/` mappái `vqebd:vqebd` (uid 1000) tulajdonúak, az adatbázis és a
  napló létrejött, a zárfájl elengedve (nincs a mappában).

## 5. Keresztvalidáció

- A pipeline `f5-smoke` eredménye a Fázis 5 `run_batch`-ével **bitre egyezik** (`run_id`,
  `energy_ha`, `config_hash`, `optimal_parameters_json`).
- A `scripts/run_batch.py` exportja a közös `vqebd.batch.export` modulra épül; a kulcsok és sorrendjük
  megegyeznek a `docs/figures/data/f5_*.json` fájlokéval.

## 6. Korlátok és nyitott pontok

| # | Korlát | Megjegyzés |
|---|---|---|
| L1 | Az `transient` szabályok **feltevések**: valódi IBM-hibával nem erősítettük meg | A megfigyelt IBM-hibák tartósak voltak; a szabálytábla bővíthető |
| L2 | A zár időalapú; egy összeomlott pipeline legfeljebb 12 óráig tartja a helyet | PID-ellenőrzés Windowson veszélyes |
| L3 | **Az ütemezési hurkot valós alvással, hosszú ideig nem futtattuk:** az `--every` logikát injektált órával teszteltük, a konténeres futás egyszeri módban történt | A 24 órás ciklus éles bizonyítéka az első valódi ütemezett futás után lesz |
| L4 | Nincs értesítés hibáról; nincs GitHub Actions ütemezés (D3, a push utánra halasztva) | |
| L5 | A `scrub_secrets` 3. rétege a 40+ karakteres azonosítókat (pl. 64 hexa `config_hash`) is maszkolja | Elfogadott ár a titokszivárgás ellen |
| L6 | A feladott futás miatt a pipeline kilépési kódja `1`, amíg nem oldják meg | Az ismétlődő ütemezés így hibajelzést tart fenn |

## 7. Reprodukálás

```bash
docker build -f docker/Dockerfile -t vqebd:0.9.0 .
docker run --rm -v "$PWD:/repo" -w /repo -e PYTHONPATH=/repo/src vqebd:0.9.0 python -W ignore -m pytest -q
docker run --rm -v "$PWD:/repo" -w /repo -e PYTHONPATH=/repo/src vqebd:0.9.0 \
    python -W ignore scripts/run_pipeline.py --preset f5-smoke --db /tmp/p.sqlite --log-dir /tmp/logs
docker compose -f docker/docker-compose.yml run --rm scheduler python -W ignore -m vqebd.scheduler \
    --preset f5-smoke --db /app/data/db/scheduler.sqlite --log-dir /app/data/logs
```

Windows / Git Bash alatt a `MSYS_NO_PATHCONV=1` előtag kell.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
