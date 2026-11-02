# 06 — Automatizálás, hibatárolás és ütemezés (Fázis 6)

| | |
|---|---|
| **Dokumentum** | `docs/06_automation.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Projektverzió** | 1.0.0 |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Fázis** | 6 — Automatizálás |
| **Háttér** | [`phase_06.md`](plan/phase_06.md) · [`ADR-0008`](adr/ADR-0008-hibakezeles-es-utemezes.md) · [`TR-F06`](testing/TR-F06_automatizalas.md) |

---

## 1. Mit ad a Fázis 6?

| Képesség | Hol | Mire jó |
|---|---|---|
| **Hibatárolás** | `run_failures` tábla (séma v3) | a sikertelen futás nem tűnik el a folyamattal együtt |
| **Hibaosztályozás** | `vqebd.pipeline.errors` | eldönti, érdemes-e újrapróbálni |
| **Újrapróbálkozás** | `vqebd.pipeline.retry` | korlátos, exponenciális visszalépésű, adatbázisban tartósított próbálkozásszám |
| **Pipeline** | `scripts/run_pipeline.py` | előellenőrzés → batch → export → összegzés, JSON-soros naplóval |
| **Ütemező** | `python -m vqebd.scheduler`, `scheduler` compose-szolgáltatás | a pipeline rendszeres, átfedés nélküli indítása |

A hardver **alapértelmezésben nincs ütemezve** (lásd 6. pont): az ütemezett működés csak
szimulátort indít.

## 2. Egyszeri futtatás

```bash
python scripts/run_pipeline.py --preset f5-smoke \
       --db data/db/pipeline.sqlite --export data/exports/f5_smoke.json
```

| Kapcsoló | Jelentés |
|---|---|
| `--preset` | `f5-smoke` (5 futás), `f5-deterministic` (50), `f5-statistical` (180) |
| `--db` | az adatbázis (alapértelmezés: `data/db/vqebd.sqlite`) |
| `--export` | JSON-export (a Fázis 5 formátuma) |
| `--log-dir` | a napló mappája (alapértelmezés: `data/logs`) |
| `--max-attempts` | próbálkozások futásonként (alapértelmezés: 3) |
| `--base-delay` | az első visszalépés másodpercben (alapértelmezés: 5) |
| `--max-runs` | legfeljebb ennyi új futás |
| `--retry-abandoned` | a feladott futások hibáinak megbocsátása, majd újrapróbálás |
| `--allow-hardware` | valódi QPU engedélyezése (lásd 6. pont) |

**Kilépési kód:** `0` minden futás rendben · `1` részleges hiba (a hibák tárolva) ·
`2` végzetes (ismeretlen preset, hiányzó engedély, adatbázis-hiba).

A pipeline **folytatható**: a már tárolt futásokat kihagyja, így egy megszakadt vagy
részben hibás futás ugyanazzal a paranccsal folytatható.

## 3. A hibák tárolása

Minden sikertelen próbálkozás egy sor a `run_failures` táblában (append-only):

| Oszlop | Jelentés |
|---|---|
| `run_id`, `batch_id` | melyik futás |
| `attempt` | a próbálkozás sorszáma (1-től, folyamatos) |
| `timestamp` | UTC, ISO-8601 |
| `error_type` | kivételtípus (`ValueError`, `ConnectionError`, …) |
| `error_class` | `transient` / `permanent` / `quota` |
| `error_message` | **titoktalanított**, legfeljebb 2000 karakter |
| `wall_time_s` | a próbálkozás ideje |
| `will_retry` | 0/1: lesz-e újabb próbálkozás |
| `forgiven` | 0/1: megbocsátott (nem számít a korlátba), lásd 5. pont |

Lekérdezés:

```python
from vqebd.storage import Database

with Database("data/db/pipeline.sqlite", read_only=True) as db:
    for row in db.failures("f5-smoke"):
        print(row["run_id"], row["attempt"], row["error_class"], row["error_message"])
```

## 4. Hibaosztályok és újrapróbálkozás

| Osztály | Kivételek | Újrapróbálás |
|---|---|---|
| `quota` | `QuotaExhaustedError`, `EvaluationBudgetExceededError` | nem |
| `permanent` | `ValueError`, `KeyError`, `PermissionError`, `InvalidAccountError`, HTTP 4xx, **minden ismeretlen** | nem |
| `transient` | `ConnectionError`, `TimeoutError`, `Timeout`, HTTP 408/425/429/500/502/503/504 | igen, legfeljebb `--max-attempts`-szor |

A visszalépés `min(base · 2^(n−1), 300 s)`, jitter nélkül: 5 s, 10 s, 20 s, … Az ismeretlen kivétel
szándékosan **tartós**: egy ki nem hagyott újrapróbálás pótolható, egy fölöslegesen megismételt
hardveres job viszont kvótát éget el.

> **Figyelem:** az `transient` szabályok **feltevések**. Nem mértük, hogy az IBM Runtime pontosan
> milyen kivételtípust ad átmeneti hálózati hibánál; a megfigyelt IBM-hibák (403 lejárt token,
> `InvalidAccountError`) mindkettő tartós volt. Új típus a `_TRANSIENT_NAMES` / `_RETRYABLE_HTTP`
> táblában vehető fel (`src/vqebd/pipeline/errors.py`).

## 5. Feladott futások

Egy futás **feladott** (`abandoned`), ha nincs eredménye, és az utolsó aktív hibája nem
újrapróbálható (`will_retry = 0`): tartós vagy kvótahiba, vagy a próbálkozási korlát elfogyott. A
pipeline az ilyen futásokat **kihagyja**, ezért egy ütemezett környezetben nincs végtelen ciklus. A
feladott futás miatt a pipeline kilépési kódja `1`, amíg valaki nem foglalkozik vele.

Visszaállítás (a hibatörténet megmarad, csak a korlátba nem számít):

```bash
python scripts/run_pipeline.py --preset f5-smoke --db data/db/pipeline.sqlite --retry-abandoned
```

## 6. Hardver: miért nincs ütemezve

A valódi QPU keret 600 s / 28 nap, és a v0.8.1 előtti védelem nélküli útvonal egyetlen futással
elfogyasztotta (K7). Ezért:

- az **ütemező** (`--every`) sosem indít `ibm_qpu` cellát, és a `--allow-hardware` kapcsolót
  `--every` mellett elutasítja;
- a `scheduler` compose-szolgáltatás **nem kap tokent** (nincs `env_file`);
- a pipeline csak **egyszeri, kézi** futásnál indít hardvert, és ehhez **két kulcs** kell:
  `--allow-hardware` **és** `VQEBD_ALLOW_HARDWARE=true`;
- engedélyezett hardveres futásnál a pipeline **batch szintű kvótakaput** futtat (a teljes batch
  legrosszabb esete +20% tartalékkal), és minden futás külön is átmegy a `run_vqe` védelmén;
- hardveres futásra a próbálkozások száma **1**, mert egy újrapróbálás kvótát fogyasztana.

## 7. Ütemező

```bash
python -m vqebd.scheduler --preset f5-smoke --every 24h --db data/db/scheduler.sqlite
```

| Kapcsoló | Jelentés |
|---|---|
| `--every` | ismétlési periódus (`30s`, `15m`, `6h`, `1d`); nélküle egyszeri futás |
| `--lock` | a zárfájl (alapértelmezés: `data/scheduler.lock`) |
| `--max-attempts` | próbálkozások futásonként |

**Átfedés elleni zár.** Egy még futó pipeline mellé nem indul második: a zárfájl `O_CREAT | O_EXCL`
-lel jön létre. Az **elavult** zár (12 óránál régebbi, vagy sérült) átvehető. A zár *kizárólag időalapú*:
nincs PID-ellenőrzés, mert Windowson az `os.kill(pid, 0)` a folyamatot megszüntetné.

**Docker Compose.**

```bash
docker compose -f docker/docker-compose.yml up -d scheduler     # indítás
docker compose -f docker/docker-compose.yml logs -f scheduler   # napló
docker compose -f docker/docker-compose.yml stop scheduler      # leállítás
```

A napló és az adatbázis a `vqebd-data` volume-ban él (`logs/`, `db/scheduler.sqlite`). A `dashboard`
szolgáltatás ugyanezt a volume-ot csak olvasásra nyitja, ezért az ütemező eredményei a böngészőben
(<http://localhost:8501>) is megjelennek ([`08_deployment.md`](08_deployment.md)). A forrást
(`src`, `scripts`) a szolgáltatás a gazdagépről csatolja, ezért kódváltozás újraépítés nélkül
érvényesül; verzióváltás (`VERSION`, `pyproject.toml`) után `docker compose build` kell.

## 8. Naplózás és titkok

A pipeline soronként egy JSON-objektumot ír (`data/logs/pipeline-ÉÉÉÉHHNN.jsonl`):

```json
{"ts": "2026-11-02T10:14:34Z", "step": "preflight", "status": "ok", "batch_id": "f5-smoke", "planned_runs": 5, "max_attempts": 3}
{"ts": "2026-11-02T10:14:38Z", "step": "batch", "status": "progress", "message": "[1/5] H2 R=0.735 ... E=-1.1373060358 (3.0 s)"}
```

Lépések: `preflight`, `retry_abandoned`, `batch`, `export`, `summary`. Állapot: `ok` / `progress` /
`done` / `partial` / `fatal`.

**Titoktalanítás.** A hibaüzenetek tárolás és naplózás előtt három rétegben tisztulnak: (1) a betöltött
token és CRN szó szerint; (2) minden `crn:v1:…` minta; (3) minden 40+ karakteres, betű-számjegy-kötőjel
-aláhúzás sorozat (API-kulcs alakú). A (3) szándékosan agresszív: egy hosszú azonosító is maszkolódhat.
A token csak `IBM_QUANTUM_TOKEN` környezeti változóból, vagy a gitignore-olt `IBM.token` / `.env`
fájlból jön, **soha** nem kerül a repóba.

## 9. Ismert korlátok

| # | Korlát |
|---|---|
| L1 | Az `transient` szabályok feltevések; valódi IBM-hibával nincs megerősítve (4. pont) |
| L2 | A zár időalapú: egy összeomlott pipeline zárja legfeljebb 12 óráig tartja a helyet |
| L3 | Nincs értesítés (e-mail, chat) hibáról; a `run_failures` tábla és a napló erre alapot ad |
| L4 | Nincs GitHub Actions ütemezés (D3, a push utánra halasztva) |
| L5 | A `scrub_secrets` 3. rétege a 40+ karakteres azonosítókat is maszkolja |

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
