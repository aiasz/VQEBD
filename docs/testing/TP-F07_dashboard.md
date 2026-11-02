# TP-F07 — Fázis 7 tesztterv (dashboard)

| | |
|---|---|
| **Azonosító** | TP-F07 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 7 — Dashboard |
| **Terv** | [`phase_07.md`](../plan/phase_07.md) |
| **Döntés** | [`ADR-0009`](../adr/ADR-0009-dashboard-architektura.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Mit kell igazolni

1. **A build reprodukálható:** a Docker-image a `requirements.lock`-ot betartatja, és a dashboard-függőségek a
   numerikus stack változtatása nélkül, összeomlás nélkül működnek.
2. **Az adatréteg helyes:** három forrás ugyanarra a rekordra azonos levezetett oszlopokat ad; a körméret a mért
   építéssel egyezik; a dashboard nem ír.
3. **A négy nézet önállóan helyes:** ismert tesztadatra a kirajzolt értékek a vártak, és a közölt (TR-F05) számokkal
   egyeznek.

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl |
|---|---|---|---|
| **TC-701** | AC-7.1 | `pip freeze` ↔ `requirements.lock`: 0 eltérés; a Dockerfile `-c requirements.lock`-ot használ | végrehajtás, `tests/repo/test_requirements.py` |
| **TC-702** | AC-7.2 | a dashboard-pinek a lockban azonos verzióval; a `pyarrow` a mért tartományban (≤ 24.0); a kétfutásos `AppTest` alfolyamatban nem omlik össze | `tests/repo/test_requirements.py`, `tests/integration/test_dashboard_pyarrow_guard.py` |
| **TC-703** | AC-7.3 | 7.1: az app elindul; a táblázat pontosan a fixture rekordjait mutatja, a megadott oszlopokkal; metrikák; Hibák fül; egyéni útvonal; JSON-export | `tests/integration/test_dashboard_app.py` |
| **TC-704** | AC-7.4 | SQLite ↔ batch-export ↔ teljes lista: azonos `error_mha`, módszer, pontosság, qubitszám, aktív tér | `tests/unit/test_dashboard_data.py` |
| **TC-705** | AC-7.5 | 7.2: molekulaváltásra a Full CI-görbe és a pontok a másik molekuláéra változnak; aktív tér és módszer szűrő; valódi batch-adaton három molekula | `tests/unit/test_dashboard_figures.py`, `tests/integration/test_dashboard_app.py` |
| **TC-706** | AC-7.6 | 7.3: referencia 0, nyers +38.1, mitigált +1.0 mHa; a számtábla (n, átlag, szórás, SEM); keresztvalidáció a TR-F05 értékeivel | ugyanott |
| **TC-707** | AC-7.7 | 7.4: a qubitszám 2, 4, 8, 4, 10 az 5 mért rendszerre; a cellák ismert értéke, az üres cellák; valódi batch-adat (2/4/8/10 qubit) | ugyanott |
| **TC-708** | AC-7.8 | a négy lépés külön commit, mindegyik után az előző lépések tesztjei zöldek | commit-történet |
| **TC-709** | AC-7.9 | a betöltés és az app futtatása után az adatbázisfájl bitre változatlan; a betöltő nyitási módja valóban csak olvasható | `tests/unit/test_dashboard_data.py`, `tests/integration/test_dashboard_app.py` |
| **TC-710** | AC-7.10 | hiányzó fájl, ismeretlen típus, hibás JSON (5 változat), nem adatbázis `.sqlite`, üres adatbázis és üres JSON: érthető üzenet | ugyanott |
| **TC-711** | AC-7.11 | `f5_deterministic.json` (50), `f5_statistical.json` (180), `results_v1.json` (8) kivétel nélkül betöltődik | `tests/integration/test_dashboard_app.py` |

## 3. Negatív és robusztussági ellenőrzések

- Ismeretlen bázis: a qubitszám `NaN`, a futás kimarad a hőtérképről.
- Hiányzó Hartree–Fock-adat: a HF-trace elmarad.
- Üres kijelölés (ismeretlen molekula, aktív tér, módszer; üres módszerlista): magyarázott üres ábra.
- Egyetlen futásból nincs szórás (`NaN`), a hibasáv 0.
- Kötéshossz-egyezés lebegőpontos tűréssel; a kémiai pontosság küszöbe az átlagon, a határ két oldalán.
- Hiányzó `run_failures` tábla régi adatbázisban: üres hibatörténet, nem hiba.
- Ismeretlen mérőszám a hőtérképen: `ValueError`.
- A `mapper`/`basis` hiánya: a `size_assumed` jelzi, és a felület megjegyzést ír.

## 4. Keresztvalidációk

| Mit | Mivel | Várt |
|---|---|---|
| Módszer-összehasonlítás (H₂ 0.735 Å, N = 20) | TR-F05 4. pont | +11.59, +38.15, +15.52, +11.54 mHa (±0.01) |
| LiH (2e,3o) zajosan | TR-F05 4. pont | +465.65 mHa |
| Egzakt sikeresség qubitszámonként | TR-F05 / fig09 csonkolás | 2: 100%, 4: 0%, 8: 100%, 10: 100% |
| Levezetett qubitszám | a mért építés | 2, 4, 8, 4, 10 |
| Három adatforrás | egymás | azonos levezetett oszlopok |

## 5. Amit a terv nem fed

Vizuális megjelenés (böngésző, képernyőkép): az `AppTest` a JS-ben renderelt Plotly-t nem futtatja (TR-F07 5., L1).

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
