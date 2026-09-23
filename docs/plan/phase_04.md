# Fázis 4 — Adatséma és perzisztens tárolás

| | |
|---|---|
| **Fázis** | 4 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Státusz** | Tervezés alatt |
| **Célverzió** | `v0.7.0` |
| **Előzmény** | [`phase_03.md`](phase_03.md), [`ADR-0004`](../adr/ADR-0004-adattarolas.md) |

## 1. Cél

A Fázis 4 célja a korábbi szöveges mérési jegyzőkönyvek és izolált JSON fájlok
helyett egy **strukturált, perzisztens, FAIR-megfelelő adattárolási réteg**
kialakítása (ADR-0004):

1. **Kanonikus SQLite adatbázis (`data/db/vqebd.sqlite`):**
   - Sémaverziózott (`schema_version`), típusos táblák `CHECK` megszorításokkal.
   - WAL (Write-Ahead Logging) mód a párhuzamos olvasás (Dashboard) és írás (Runner) támogatására.
   - Append-only elv: korábbi rekordok nem módosulnak, megőrizve a teljes auditálhatóságot.
2. **Teljes reprodukálhatósági kontextus (Provenance):**
   - Minden rekord önmagában tartalmazza a fizikai problémát, a módszert, a platformot, a hibaenyhítést, a seedeket, a konfigurációs ujjlenyomatot (`config_hash`) és a csomagverziókat (`environment_fingerprint`).
3. **Determinisztikus exportálás (CSV & JSON):**
   - A tárolt eredmények determinisztikusan exportálhatók nyílt formátumokba (`data/exports/`), amelyek bekerülhetnek az archiválásba és a Zenodo adatcsomagba (Fázis 9).
4. **Történeti adatok betöltése:**
   - A Fázis 1–3 reprezentatív mérési eredményei (L0, L1, L2, L3a, L3b, L4 ZNE, L5 hardver) visszamenőleg betöltésre kerülnek az adatbázisba.

## 2. Architektúra (`src/vqebd/storage/`)

```
src/vqebd/storage/
├── __init__.py           — Publikus felület: Database, save_result, load_results, export_csv
├── schema.py             — SQL DDL definíciók és sémamigrációk (v1)
├── db.py                 — SQLite adatbáziskezelő (WAL mód, konverziók, lekérdezések)
└── export.py             — Determinisztikus CSV / JSON exportáló
```

## 3. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-4.1** | `Database` inicializálja az SQLite adatbázist WAL módban és ellenőrzi a sémaverziót | egységteszt |
| **AC-4.2** | `save_result(result)` lementi a `VQEResult` objektumot; `get_result(run_id)` bitpontosan visszaadja az értékeket | egységteszt |
| **AC-4.3** | `query_results()` szűrést tesz lehetővé molekula, backend, hibaenyhítés és konvergencia alapján | integrációs teszt |
| **AC-4.4** | A determinisztikus CSV export rögzített oszloprendben és sorrendben ment | egységteszt |
| **AC-4.5** | A Fázis 1–3 eredményei (L0, L1, L2, L3a, L3b, L4, L5) megtalálhatók és lekérdezhetők az adatbázisban | validációs teszt |
| **AC-4.6** | Érvénytelen séma vagy hiányzó kötelező mező esetén az adatbázis `sqlite3.IntegrityError` hibát dob | egységteszt |
| **AC-4.7** | A dokumentáció (`docs/04_data_schema.md`) mezőnként definiálja a típusokat, mértékegységeket és szemantikát | dokumentáció-audit |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
