# Fázis 6 — Automatizálás, strukturált hibatárolás, újrapróbálkozás

| | |
|---|---|
| **Fázis** | 6 |
| **Dokumentum-verzió** | 1.1.0 |
| **Dátum** | 2026-11-02 |
| **Státusz** | **Megvalósítva és lezárva (2026-11-02)** — mind a 11 elfogadási kritérium teljesült: [`TR-F06`](../testing/TR-F06_automatizalas.md). A 6. fejezet döntései az alapértelmezésekkel jóváhagyva |
| **Célverzió** | `v0.9.0` |
| **Előzmény** | [`phase_05.md`](phase_05.md), [`00_master_plan.md`](00_master_plan.md) 7. fejezet, v0.8.1 ([`CHANGELOG`](../../CHANGELOG.md)) |
| **Új ADR** | [`ADR-0008`](../adr/ADR-0008-hibakezeles-es-utemezes.md) — hibamodell, újrapróbálkozás, hardveres ütemezés |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Miért most, és miért így

Az alapterv Fázis 6-ja: „a gyűjtés emberi beavatkozás nélkül, rendszeresen fusson”;
a mesterterv ezt kiegészíti **strukturált hibatárolással** és **újrapróbálkozási
politikával**. A Fázis 5 után két tény alakítja a tartalmat:

1. **A hibák ma nem maradnak meg.** Mért (2026-11-02, `vqebd:0.8.1`): egy 3 futásos
   batchben a 2. futás hibás aktív térrel `ValueError`-ral elbukott, a batch
   folytatódott (2 futás lefutott, 2 sor a `results` táblában). A hiba azonban
   csak a `BatchReport` memóriabeli listájába és a naplóba került; az adatbázis
   táblái `meta` és `results`, **hibatábla nincs**. Egy megszakadt vagy felügyelet
   nélkül futó folyamat hibái elvesznek, és ez a „nem áll el csendben” követelmény
   (alapterv, Fázis 6) megsértése.
2. **A hardver ütemezése kvótakérdés, nem kényelmi kérdés.** Az Open Plan 600 QPU-s
   kerete 28 napos gördülő ablak. A K7 (v0.8.1) azt mutatta, hogy egy védelem
   nélküli útvonal egyetlen futással elfogyasztja a keretet. Egy cron-ra tett
   hardveres feladat ugyanezt ismétlődően tenné.

A Fázis 6 ezért négy dolgot szállít: (A) **hibatárolás** az adatbázisban, (B)
**újrapróbálkozási politika** hibaosztályozással, (C) egy **pipeline**, amely a
batch → export → jelentés láncot egyben, naplózva futtatja, (D) egy
**ütemező**, amely a szimulátoros láncot rendszeresen indítja, **a hardvert viszont
alapértelmezésben nem**.

---

## 2. Előzetes mérés — a jelenlegi hibakezelés (2026-11-02, `vqebd:0.8.1`)

| Kérdés | Mérés | Következmény |
|---|---|---|
| Hová jut egy futásidejű hiba? | `BatchReport.failed` (memória) + `progress` napló. Az adatbázisban nincs nyoma. | Kell hibatábla (G1) |
| Folytatódik-e a batch? | Igen: a 3 futásból a hibás kihagyva, a másik kettő tárolva. | A hibaizoláció marad |
| Hol bukik a rossz backendnév? | A `BatchCell` konstruktorában (`KeyError`, nem `ValueError`), **a batch futása előtt**. | A hibainjektáláshoz futásidejű hiba kell (pl. érvénytelen aktív tér); az alaptervi „rossz backendnév” példa a spec szintjén elfogott |
| Mit adtak az IBM-hibák? | Megfigyelt: `RequestsApiError` 403 (lejárt token), `InvalidAccountError` („Unable to retrieve instances”, hiányzó `crn`). Mindkettő **tartós**, nem átmeneti. | Az újrapróbálás nem segít rajtuk (G2) |
| Mennyi ideig áll sorban egy hardveres job? | Mért: 186 s és 331 s fali idő 24 és 33 QPU-s jobnál (5.H). | A hardveres időkorlát legalább percekben, nem másodpercekben értendő |

Mérendő a megvalósítás során (nem tudjuk még): az IBM Runtime tényleges kivételtípusai
átmeneti hálózati hibánál és `5xx` esetén. A `ConnectionError`/`Timeout`
osztályozása ezért **feltevés**, amíg szimulált hibával nem teszteltük (AC-6.2);
az ismeretlen kivétel konzervatívan **tartósnak** számít.

---

## 3. Célkitűzések

| # | Cél | Szállítandó |
|---|---|---|
| G1 | Strukturált hibatárolás | `run_failures` tábla (séma v3), `Database.record_failure` / `failure_history` |
| G2 | Hibaosztályozás | `classify(exc)` → `transient` / `permanent` / `quota`; titokmentes üzenet |
| G3 | Újrapróbálkozási politika | `RetryPolicy` (korlátos próbálkozás, exponenciális visszalépés), tartósított próbálkozásszám |
| G4 | Pipeline | `vqebd.pipeline` + `scripts/run_pipeline.py`: batch → export → összegzés, JSON-soros napló |
| G5 | Ütemezés | `scheduler` szolgáltatás a `docker-compose.yml`-ben; átfedés elleni zár; (opcionális) szimulátoros CI-ütemezés |
| G6 | Titokkezelés | az IBM-token csak környezeti változóból, naplóba és hibatáblába soha |
| G7 | Hardveres ütemezési politika | alapértelmezésben **nincs** automatikus QPU-futás; kvótakapu |

---

## 4. Architektúra

### 4.1 Hibamodell (G1, G2)

Minden sikertelen próbálkozás **egy sor** az új `run_failures` táblában (append-only,
mint a `results`):

| Oszlop | Jelentés |
|---|---|
| `run_id`, `batch_id` | melyik futás |
| `attempt` | a próbálkozás sorszáma (1-től), **az adatbázisban tartósítva** |
| `timestamp` | UTC, ISO-8601 |
| `error_type` | kivételtípus (`ValueError`, `RequestsApiError`, …) |
| `error_class` | `transient` / `permanent` / `quota` |
| `error_message` | **titoktalanított**, legfeljebb 2000 karakter |
| `wall_time_s` | a próbálkozás ideje |
| `will_retry` | 0/1: a politika szerint lesz-e újabb próbálkozás |

**Osztályozás (G2).** Szabálytábla, kivételtípus szerint, a megfigyelt és a feltételezett
esetekkel (a feltételezettek AC-6.2-ben tesztelendők):

| Osztály | Kivételek | Újrapróbálás |
|---|---|---|
| `quota` | `QuotaExhaustedError`, `EvaluationBudgetExceededError` | nem; a következő indítás a `time_available_at`-ra időzítve |
| `permanent` | `ValueError`, `KeyError`, `PermissionError`/`HardwareNotAllowedError`, `InvalidAccountError`, `RequestsApiError` 4xx, **minden ismeretlen** | nem |
| `transient` | `ConnectionError`, `TimeoutError`, `RequestsApiError` 429/5xx | igen, korlátosan |

Az „ismeretlen = tartós” szabály szándékos: egy rosszul osztályozott átmeneti hiba
egy elmaradt újrapróbálás, egy rosszul osztályozott tartós hiba viszont **fogyasztott
kvóta** hardveren.

### 4.2 Újrapróbálkozási politika (G3)

```python
RetryPolicy(max_attempts=3, base_delay_s=5.0, factor=2.0, max_delay_s=300.0)
```

- Visszalépés: `min(base · factor^(n−1), max)`; **jitter nincs**, hogy az ütemezés
  determinisztikus és tesztelhető legyen (ADR-0005 szellemében); az idő és az alvás
  injektálható.
- **A próbálkozásszám tartósított**: egy tartósan hibázó futás a `max_attempts`
  elérése után `abandoned` állapotú, és az újabb indítások nem próbálják újra
  (nincs végtelen ciklus egy ütemezett környezetben). Az `abandoned` futások a
  jelentésben külön szerepelnek, és kézzel visszaállíthatók (`--retry-abandoned`).
- **Hardveres futásra a `max_attempts` alapértelmezése 1.** Minden próbálkozás újra
  lefuttatja a `guard_hardware_vqe`-t (engedély + kvóta), tehát egy újrapróbálkozás
  sem kerülheti meg a K7 védelmét.

### 4.3 Pipeline (G4)

`run_pipeline(preset, db, …)` lépései, mindegyik JSON-soros naplóbejegyzéssel
(`data/logs/pipeline-YYYYMMDD.jsonl`; mezők: időbélyeg, lépés, `run_id`, próbálkozás,
állapot, időtartam, hibaosztály):

1. **Előellenőrzés** — preset, adatbázis, hardveres engedély/kvóta (ha kell).
2. **Batch** — `run_batch` újrapróbálással és hibatárolással (a Fázis 5 folytathatósága
   változatlan: a már tárolt futásokat kihagyja).
3. **Export** — a Fázis 5 JSON-export.
4. **Összegzés** — `completed` / `skipped` / `failed` / `abandoned`, kilépési kód.

Kilépési kódok: `0` minden futás rendben · `1` részleges hiba (tárolva) · `2`
végzetes (konfiguráció, adatbázis, engedély).

### 4.4 Ütemező (G5)

- **Elsődleges:** a `docker-compose.yml`-be egy `scheduler` szolgáltatás, amely
  `python -m vqebd.scheduler --every 24h --preset f5-smoke` parancsot futtat. Nem
  cron-démon, mert a konténer nem-root felhasználóval fut; egy Python-hurok
  (`time.sleep`, injektálható órával) tesztelhető és platformfüggetlen.
- **Átfedés elleni zár:** zárfájl a `data/`-ban (PID + időbélyeg, elavulás-ellenőrzéssel).
  Egy még futó pipeline mellé nem indul második.
- **Opcionális:** GitHub Actions `schedule:` workflow, **csak szimulátorra**, titok
  nélkül. Ehhez a repót pusholni kell; ez a felhasználó döntése.

### 4.5 Titokkezelés (G6)

- A token csak `IBM_QUANTUM_TOKEN` (és `IBM_QUANTUM_INSTANCE`) környezeti változóból
  vagy a gitignore-olt `IBM.token` / `.env` fájlból jön (a Fázis 2 mechanizmusa).
  CI-ban a GitHub titkos változó (`secrets.IBM_QUANTUM_TOKEN`) környezeti változóként.
- A hibatárolás **titoktalanítja** az üzenetet: a betöltött token értékét és a CRN-t
  `***`-ra cseréli a mentés előtt. Teszt: egy szándékosan a tokent tartalmazó
  kivétel nem kerülhet a hibatáblába, a naplóba vagy a jelentésbe.

### 4.6 Hardveres ütemezési politika (G7)

**Alapértelmezés: az ütemező nem indít valódi QPU-futást.** Indok: 600 QPU-s keret /
28 nap, a K7 tapasztalata, és az, hogy egy hardveres mérés tudományos értéke a
tervezett, ismételt-rögzített méréseken van (pl. 5.H), nem a rendszeres
ismétlésen. Hardveres ütemezés csak akkor, ha **mind** teljesül: `--allow-hardware`
kapcsoló, `VQEBD_ALLOW_HARDWARE=true`, kvótakapu (a hátralévő idő ≥ a batch
becslése + 20% tartalék), és a futás **egyszeri**, nem ismétlődő.

---

## 5. Új és módosuló modulok

| Modul | Változás |
|---|---|
| `src/vqebd/pipeline/errors.py` | **új** — `classify`, `scrub_secrets` |
| `src/vqebd/pipeline/retry.py` | **új** — `RetryPolicy`, `run_with_retry` (injektálható `sleep`/`clock`) |
| `src/vqebd/pipeline/runner.py` | **új** — `run_pipeline`, napló, kilépési kódok |
| `src/vqebd/scheduler.py` | **új** — intervallum-hurok, zár |
| `src/vqebd/batch/run.py` | `retry` paraméter; hibák a `db.record_failure`-be; `abandoned` állapot |
| `src/vqebd/storage/schema.py`, `db.py` | séma **v3**: `run_failures` tábla + v2 → v3 migráció |
| `scripts/run_pipeline.py` | **új** — CLI |
| `docker/docker-compose.yml` | `scheduler` szolgáltatás |
| `.github/workflows/scheduled-sim.yml` | **új, opcionális** — szimulátoros ütemezés |

A séma v3 **csak hozzáad** (új tábla); a `results` oszlopai és rekordjai változatlanok,
így a v1/v2 → v3 migráció a Fázis 5 mintáját követi.

---

## 6. Döntések, amelyek a felhasználóra várnak

| # | Kérdés | Javaslat | Következmény, ha mást választ |
|---|---|---|---|
| D1 | Ütemező: konténeres Python-hurok vagy GitHub Actions | **Konténeres hurok** (nem igényel push-t, a helyi adatbázissal dolgozik) | GitHub Actions: nincs tartós adatbázis a futások között (artefaktum-kezelés kell) |
| D2 | Automatikus hardveres futás | **Nem** (4.6) | Ismétlődő hardveres ütemezés: kvótakapu + egyedi jóváhagyás nélkül nem javasolt |
| D3 | Szimulátoros CI-ütemezés (GitHub Actions) | **Később**, a push után | — |
| D4 | Alapértelmezett `max_attempts` szimulátoron | **3** | 1: nincs újrapróbálás (tisztább, de egy átmeneti hiba végleges) |

---

## 7. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-6.1** | Egy sikertelen futás **sorként tárolódik** a `run_failures` táblában (típus, osztály, titoktalanított üzenet, próbálkozásszám); a batch folytatódik | integrációs teszt (érvénytelen aktív tér, a Fázis 5 előmérésének esete) |
| **AC-6.2** | A hibaosztályozás a szabálytábla szerint működik; ismeretlen kivétel `permanent`; `transient` hibánál a visszalépés a képlet szerinti (injektált órával, valós várakozás nélkül) | egységteszt |
| **AC-6.3** | `permanent` és `quota` hibát a rendszer **nem** próbál újra; `transient` hibát legfeljebb `max_attempts`-szor | egységteszt |
| **AC-6.4** | A próbálkozásszám **újraindítás után is** érvényes: a `max_attempts`-et elérő futás `abandoned`, a következő indítás nem futtatja; `--retry-abandoned` visszaállítja | integrációs teszt |
| **AC-6.5** | Hardveres futásra a `max_attempts` alapértelmezése 1, és minden próbálkozás meghívja a `guard_hardware_vqe`-t | egységteszt (mockolt Runtime) |
| **AC-6.6** | **Dry run:** a teljes pipeline (előellenőrzés → batch → export → összegzés) hiba nélkül lefut `f5-smoke`-on, szimulált backenden, `0` kilépési kóddal, naplóval | integrációs teszt |
| **AC-6.7** | **Hibainjektálás:** egy szándékosan hibás futás naplózódik és tárolódik, a pipeline nem omlik össze, a kilépési kód `1` | integrációs teszt |
| **AC-6.8** | A token értéke sem a hibatáblában, sem a naplóban, sem a jelentésben nem szerepel (szándékosan a tokent tartalmazó kivétellel) | egységteszt |
| **AC-6.9** | Séma v2 → v3 migráció: a v2 rekordok bitre változatlanok; a második megnyitás nem migrál újra; friss és migrált séma azonos | egységteszt |
| **AC-6.10** | Az ütemező nem indít második pipeline-t, ha a zárfájl él; elavult zárat felold; az intervallum-hurok injektált órával tesztelhető | egységteszt |
| **AC-6.11** | A `docker compose config` a `scheduler` szolgáltatást érvényesnek jelzi; az ütemező alapértelmezésben nem enged `ibm_qpu` cellát | teszt + végrehajtás |

---

## 8. Tesztelési terv (összefoglaló; részletesen: TP-F06)

- **1. kör — funkcionális:** hibatárolás, osztályozás, újrapróbálkozás, pipeline dry run.
- **2. kör — negatív és robusztussági:** sérült zárfájl; adatbázis zárolva; az
  újrapróbálkozás közbeni megszakítás; `max_attempts = 0` vagy negatív;
  titkot tartalmazó hibaüzenet; ismeretlen preset; hardveres cella engedély nélkül.
- **3. kör — keresztvalidáció:** a v3 migráció ↔ friss v3 adatbázis; a pipeline
  eredménye ↔ a Fázis 5 `run_batch` eredménye bitre (azonos `config_hash` és energia).

---

## 9. Amit ez a fázis NEM tartalmaz

- **Heron-zajmodell** az `ibm_kingston` kalibrációjából (K3) és **Sampler-alapú
  becslő** a readout-hibához (K1, K2). Tudományos bővítés, nem automatizálás; a
  Fázis 5 „Fázis 6 jelölt”-ként nevezte meg. **Javaslat:** külön, a dashboard (7.
  fázis) utáni „6b” vagy 10. fázis előtti kör, a felhasználó döntésével.
- **Hardverhatékony ansatz** (K4) — Fázis 6+.
- **Dashboard** — Fázis 7.
- **Értesítések** (e-mail, chat) hibákról — nem része az alaptervnek; a hibatábla és a
  napló erre alapot ad.

---

## 10. Kilépési feltétel

AC-6.1 … AC-6.11 teljesül; TP-F06 és TR-F06 elkészült; `docs/06_automation.md`;
README (HU/EN), CHANGELOG, `v0.9.0`; minőségi kapuk (ruff, mypy strict, teljes
tesztkészlet) zöldek.

---

## 11. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-11-02 | Első változat, a jelenlegi hibakezelés előmérése (2. fejezet) alapján |
| 1.1.0 | 2026-11-02 | Megvalósítva; a D1–D4 jóváhagyva az alapértelmezésekkel. A batch szintű kvótakapu (4.6) a megvalósítás során pótolva (TR-F06 3.) |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
