# ADR-0004 — SQLite mint kanonikus tároló, sémaverziózással

| | |
|---|---|
| **Azonosító** | ADR-0004 |
| **Cím** | SQLite kanonikus tároló, CSV/Parquet export, sémaverziózás |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 4, 5, 6, 7, 8, 9 |

---

## Kontextus

Az alapterv Fázis 4-e „SQLite tábla **vagy** CSV oszloplista" formában hagyja nyitva a
tárolást, és 13 mezőt sorol fel. A Fázis 7 (dashboard), a Fázis 8 (több konténer közös
volume-on) és a Fázis 9 (publikálás, FAIR) mind erre a rétegre épül, ezért a döntést
itt kell meghozni.

## Megfontolt alternatívák

| | CSV | SQLite | PostgreSQL |
|---|---|---|---|
| Függőség | nincs | **Python stdlib** | külön konténer |
| Egyidejű írás | nincs védelem | fájlzár, WAL | teljes |
| Séma kikényszerítése | nincs | van (`CHECK`, típusok) | van |
| Lekérdezés a dashboardból | teljes betöltés | **SQL, indexelt** | SQL |
| Emberi olvashatóság | ✅ | ❌ (de exportálható) | ❌ |
| Git-barát | részben | ❌ (bináris) | ❌ |
| Zenodo-archiválás | ✅ | ✅ (egy fájl) | ❌ |

## Döntés

**SQLite a kanonikus tároló, CSV és Parquet az export.**

1. **Kanonikus:** `data/db/vqebd.sqlite` — ez az igazság forrása. Típusos, `CHECK`
   megszorításokkal, indexelve, `WAL` módban (a Fázis 6 ütemező és a Fázis 7 dashboard
   egyidejű hozzáférése miatt).
2. **Export:** `data/exports/results_vN.csv` és `.parquet` — ez kerül a Git LFS-be
   illetve a Zenodo-ra. Az exportot `scripts/export_results.py` generálja,
   **determinisztikusan** (rögzített sorrend), hogy a diff értelmes legyen.
3. **Append-only:** az eredményrekordok nem módosulnak és nem törlődnek. Javítás =
   új rekord + `supersedes` hivatkozás. Ez a reprodukálhatóság és az auditálhatóság
   feltétele.

### Sémaverziózás

- Minden rekord hordoz egy `schema_version` egész mezőt.
- A séma DDL-je: `src/vqebd/storage/schema/vNNN.sql`.
- Migrációk: `src/vqebd/storage/migrations/` — előre irányú, idempotens szkriptek.
- A `meta` tábla tárolja az adatbázis aktuális sémaverzióját; a `storage` réteg
  indításkor ellenőrzi, és **eltérés esetén hibával leáll** (nem próbál automatikusan
  migrálni).

### Környezet-ujjlenyomat minden rekordban

Az alapterv 13 mezője kiegészül a teljes reprodukálhatósági kontextussal. A séma
végleges mezőlistája a Fázis 4 tervdokumentumában kerül rögzítésre; az itt eldöntött
**elv**: minden rekord önmagában elegendő a futás rekonstruálásához —

- a fizikai feladat (molekula, geometria, bázis, töltés, spin, aktív tér),
- a módszer (leképezés, ansatz, optimalizáló, kezdőpont),
- a végrehajtás (backend, lövésszám, `optimization_level`, seedek),
- a hibaenyhítés (stratégia, paraméterek, skálázási pontok),
- az eredmény (energia + minden referenciaszint + bizonytalanság),
- a környezet (csomagverziók, konténer-digest, futás időbélyege, `run_id`),
- a provenance (`git_commit`, `config_hash`, `supersedes`).

### FAIR-megfelelés [wilkinson2016]

| Elv | Megvalósítás |
|---|---|
| **F**indable | Zenodo DOI (Fázis 9), `run_id` mint stabil azonosító. |
| **A**ccessible | Nyílt CSV/Parquet export, MIT licenc, publikus repó. |
| **I**nteroperable | Szabványos oszlopnevek, SI/atomi egységek dokumentálva, `docs/04_data_schema.md`. |
| **R**eusable | Teljes környezet-ujjlenyomat + licenc + provenance minden soron. |

## Következmények

- **Pozitív:** nulla extra futásidejű függőség (a `sqlite3` a Python stdlib része);
  egyetlen fájl archiválható; a dashboard SQL-lel szűr, nem tölt be mindent.
- **Pozitív:** a Fázis 8 „opcionálisan `db` szolgáltatás" pontja nyitva marad — ha
  később PostgreSQL kell, a `storage` réteg interfésze változatlan.
- **Negatív:** az SQLite bináris, így Gitben nem diffelhető. **Kezelés:** a
  `data/db/*.sqlite` a `.gitignore`-ban van; a verziózott műtermék a determinisztikus
  CSV-export.
- **Negatív:** az SQLite egyidejű írása korlátozott. **Kezelés:** WAL mód + az írás
  egyetlen folyamatra (a runner) korlátozása; a dashboard **csak olvas**
  (`file:...?mode=ro` URI).

## Hivatkozások

- [wilkinson2016] — FAIR alapelvek
- SQLite WAL: <https://www.sqlite.org/wal.html> (ellenőrizve: 2026-09-22)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
