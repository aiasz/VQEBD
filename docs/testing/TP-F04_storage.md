# TP-F04 — Fázis 4 tesztterv (Adattárolás és séma)

| | |
|---|---|
| **Azonosító** | TP-F04 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Fázis** | 4 — Adatséma és tárolás |
| **Terv** | [`phase_04.md`](../plan/phase_04.md) |

## 1. Tesztelési cél

Annak igazolása, hogy a VQEBD perzisztens tárolási rétege (`src/vqebd/storage`)
megbízhatóan, veszteségmentesen és FAIR-elveknek megfelelően tárolja a
kvantumszámítások eredményeit, támogatja az indexelt lekérdezéseket és a
determinisztikus exportot.

## 2. Tesztesetek

| Eset | AC | Ellenőrzés |
|---|---|---|
| **TC-401** | AC-4.1 | SQLite adatbázis inicializálása, WAL mód, sémaverzió ellenőrzése. |
| **TC-402** | AC-4.2 | `insert_result` és `get_result` bitpontos visszaolvasása lebegőpontos számokra és beágyazott mezőkre. |
| **TC-403** | AC-4.3 | `query_results` szűrés molekula, backend, mitigáció, konvergencia alapján. |
| **TC-404** | AC-4.4 | Determinisztikus CSV export: azonos adathalmaz azonos CSV kimenetet ad. |
| **TC-405** | AC-4.5 | Történeti adatok betöltése: L0, L1, L2, L3a, L3b, L4, L5 rekordok elérhetősége. |
| **TC-406** | AC-4.6 | Sémaintegritás: hibás típusok, megszorítás-sértések (`IntegrityError`) kezelése. |
| **TC-407** | AC-4.7 | Dokumentáció (`docs/04_data_schema.md`) és meződefiníciók ellenőrzése. |

## 3. Negatív ellenőrzések

- Duplikált `run_id` beszúrása `sqlite3.IntegrityError` kivételt vált ki.
- Érvénytelen sémaverziójú adatbázis megnyitása `ValueError` hibával leáll.
- Sérült vagy hiányzó SQLite fájl esetén a réteg automatikusan és tisztán inicializálja az új adatbázist.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
