# TR-F07 — Fázis 7 mérési jegyzőkönyve (dashboard)

| | |
|---|---|
| **Azonosító** | TR-F07 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Fázis** | 7 — Dashboard |
| **Tesztterv** | [`TP-F07`](TP-F07_dashboard.md) |
| **Terv / döntés** | [`phase_07.md`](../plan/phase_07.md) · [`ADR-0009`](../adr/ADR-0009-dashboard-architektura.md) |
| **Kódállapot** | `vqebd` 0.10.0 |
| **Státusz** | **Lezárva — mind a 12 elfogadási kritérium teljesült** (az 5. pont korlátaival; vizuális ellenőrzés nincs) |

---

## 1. Összefoglalás

A Fázis 7 egy csak olvasó Streamlit + Plotly felületet ad négy nézettel (táblázat, disszociációs görbe,
módszer-összehasonlítás, hőtérkép), három adatforrással (SQLite, batch-export, teljes rekordlista), és
**reprodukálható buildet**: a Docker-image mostantól betartatja a `requirements.lock`-ot.

| | |
|---|---|
| Elfogadási kritériumok | **12 / 12 teljesült** |
| Tesztkészlet | **763 teszt: 762 sikeres, 1 kihagyott** (TC-302, `mitiq` nélkül) |
| Új tesztek a Fázis 7-ben | **121** (a v0.9.0: 642) |
| Minőségi kapuk | ruff check, ruff format, mypy (strict): tiszta |
| Lock ↔ image | **101 / 101 csomag, 0 eltérés** |
| Szerver-füstteszt | a konténerben elindított Streamlit-szerver: `/_stcore/health` = `ok`, a főoldal 6602 bájt; a gazdagépről a közzétett porton is elérhető |

## 2. Elfogadási kritériumok

| AC | Teszteset | Eredmény | Bizonyíték |
|---|---|---|---|
| AC-7.1 | TC-701 | ✅ a frissen épített image `pip freeze`-e a lockkal **0 eltérés** (101 / 101); a 71 régi csomag bitre változatlan, +30 dashboard-csomag | végrehajtás (kétszer: a 0. lépés és a `pyarrow` javítása után) |
| AC-7.2 | TC-702 | ✅ numpy 1.26.4, scipy 1.13.1, qiskit 1.4.6, pandas 3.0.6 változatlan; az `st.dataframe` működik; a második script-futás nem omlik össze (`pyarrow 24.0.0`) | `test_requirements.py`, `test_dashboard_pyarrow_guard.py` |
| AC-7.3 | TC-703 | ✅ 15 `AppTest`: az app elindul, a táblázat pontosan a 3 fixture-rekordot mutatja, metrikák, Hibák fül | `test_dashboard_app.py` |
| AC-7.4 | TC-704 | ✅ SQLite, teljes lista és batch-export azonos `error_mha`, módszer, pontosság, qubitszám, aktív tér | `test_three_sources_give_identical_derived_columns` |
| AC-7.5 | TC-705 | ✅ molekulaváltásra a Full CI-görbe és a pontok változnak (BeH₂ 3, H₂ 6, LiH 4 geometria a valódi batchben) | `test_dashboard_figures.py`, `test_dashboard_app.py` |
| AC-7.6 | TC-706 | ✅ referencia 0, nyers +38.1, mitigált +1.0 mHa; a TR-F05 értékeivel egyezik (lásd 4. pont) | `test_dashboard_app.py` |
| AC-7.7 | TC-707 | ✅ qubitszám 2, 4, 8, 4, 10; az üres cellák üresek; a valódi batchen 2/4/8/10 qubit | `test_dashboard_data.py`, `test_dashboard_app.py` |
| AC-7.8 | TC-708 | ✅ külön commit lépésenként: `d237885` (0), `9cdbfbe` (7.1), `496c7ef` (7.2), `0dd3080` (7.3), `3555484` (7.4); a korábbi lépések tesztjei **módosítás nélkül** zöldek maradtak | commit-történet |
| AC-7.9 | TC-709 | ✅ az adatbázisfájl SHA-256-ja a betöltés és az app futtatása után változatlan; a betöltő nyitási módja csak olvasható | `test_dashboard_data.py`, `test_dashboard_app.py` |
| AC-7.10 | TC-710 | ✅ hiányzó fájl, ismeretlen típus, 5 hibás JSON-változat, nem adatbázis `.sqlite`, üres adatbázis, üres JSON: érthető üzenet | ugyanott |
| AC-7.11 | TC-711 | ✅ `f5_deterministic.json` 50, `f5_statistical.json` 180, `results_v1.json` 8 sor, kivétel nélkül | `test_the_versioned_exports_load_with_the_expected_row_count` |
| AC-7.12 | — | ✅ `docs/07_dashboard.md`, TP-F07, TR-F07, README (HU/EN), CHANGELOG, `v0.10.0` | commit |

### 2.1 Új tesztek fájlonként

| Fájl | Tesztek |
|---|---|
| `tests/unit/test_dashboard_data.py` | 44 |
| `tests/unit/test_dashboard_figures.py` | 37 |
| `tests/integration/test_dashboard_app.py` | 36 (7.1: 15, 7.2: 7, 7.3: 7, 7.4: 7) |
| `tests/integration/test_dashboard_pyarrow_guard.py` | 1 (alfolyamatban) |
| `tests/repo/test_requirements.py` (+3) | dashboard-pinek a lockban, `pyarrow`-őr, a Dockerfile a lockot használja |

## 3. Amit a mérés megmutatott

1. **A `requirements.lock` nem volt betartatva** (előmérés, M5): a Dockerfile csak a közvetlen pineket telepítette,
   a tranzitív réteg lebegett, és egy újraépített image a 71 lockolt csomagból **21-ben** eltért (`pillow` 12.3.0 ↔
   13.0.0, `certifi`, `pydantic`, `cryptography`, …). A numerikus stack (numpy, scipy, qiskit, aer, pyscf) azonos
   volt, ezért a korábbi fázisok eredményeit ez **nem érinti**. A javítás után a 71 régi csomag bitre változatlan.
2. **Rejtett függőségi ütközés (M2):** a Streamlit `pyarrow 26.0.0`-t húz, amely NumPy ≥ 2-t követel; az `st.dataframe`
   futásidőben elbukik, a pip feloldója nem jelzi.
3. **A saját hibám: a `pyarrow==25.0.0` pin hibás volt (M9).** Az első mérésem (M3) csak táblát hozott létre, és ezt
   „működik"-nek könyveltem el. A 7.2 lépés `AppTest`-je tárta fel: ha egy script-futásban `st.dataframe` fut, a
   *következő* futás (a Streamlit minden futást új szálban végez) első `pyarrow.compute`-hívása szegmentációs hibával
   (exit 139) leáll. Élesben a szerver a felhasználó második kattintásánál állt volna le. A 16.1.0 … 24.0.0 rendben
   van; a pin **24.0.0** (`55b6f87`). Valószínű ok (nem bizonyított): a 25.0.0 `mimalloc` memóriakezelője
   (`ARROW_DEFAULT_MEMORY_POOL=mimalloc` összeomlik, `=system` és `=jemalloc` nem).
4. **A védőteszt negatív kontrollja:** a `test_dashboard_pyarrow_guard.py` `pyarrow 25.0.0` mellett **elbukik** (kilépési
   kód −11, SIGSEGV), 24.0.0 mellett átmegy, tehát tényleg véd.
5. **A saját dokumentációs hibám:** a `docs/05_batch.md` a minimális (2e,3o) terekre 6 qubitet írt; a mérés szerint **4**
   (a pályaszám kétszeresét írtam, a redukciót nem vettem figyelembe). Javítva.
6. **Téves tesztfeltevések a fejlesztés közben** (a kód helyes volt): a `Hartree–Fock` trace a fixture miatt jelen
   van; a Streamlit a nem kirajzolt widget állapotát eldobja, ezért a módszerválasztás molekulaváltáskor
   visszaáll az alapértelmezettre (a dokumentált szándék, tesztben rögzítve).
7. **A körméret nincs tárolva** az adatbázisban (`metadata_json` üres): a dashboard levezeti (`2·pálya − 2`), és a
   batch-exportokon (nincs `mapper`/`basis`) mindig feltételezi, ami a felületen jelezve van.

## 4. Keresztvalidáció a korábbi fázisokkal

| Mit | A dashboard | Közölt érték | |
|---|---|---|---|
| H₂ 0.735 Å lövészaj, N = 20 | +11.59 | +11.59 mHa (TR-F05 4.) | ✅ |
| H₂ 0.735 Å zajos | +38.15 | +38.15 mHa | ✅ |
| H₂ 0.735 Å ZNE lineáris | +15.52 | +15.52 mHa | ✅ |
| H₂ 0.735 Å ZNE Richardson | +11.54 | +11.54 mHa | ✅ |
| LiH (2e,3o) zajosan | +465.65 | +465.65 mHa | ✅ |
| LiH (2e,3o) lövészaj | +28.04 | +28.04 mHa | ✅ |
| Egzakt sikeresség 4 qubiten | 0% | csonkolás 15–72 mHa (fig09) | ✅ |
| Egzakt sikeresség 8 és 10 qubiten | 100% | csonkolás 0.23 / 0.34 mHa (fig09) | ✅ |

## 5. Korlátok és nyitott pontok

| # | Korlát | Megjegyzés |
|---|---|---|
| L1 | **Nincs vizuális ellenőrzés:** az `AppTest` a JS-ben renderelt Plotly-t nem futtatja; az ábrákat adatszinten teszteltük, és a szerver indulását füsttesztelte | böngészős képernyőkép nincs (D4); a `docs/07_dashboard.md` ezért képernyőképek nélkül, szöveges leírással készült |
| L2 | A három egzakt platform (Qiskit, Cirq, qsim) egy `egzakt` címke alatt átlagolódik | a platformdimenzió a nézetekben nem látszik |
| L3 | A körméret levezetett; a batch-exportokon mindig feltételezett | a séma v4 (tárolás) külön döntés |
| L4 | Valódi böngészős munkamenetet (WebSocket) nem futtattunk; a szálváltás-összeomlást az `AppTest` reprodukálja | az első valódi használat az éles bizonyíték |
| L5 | A betöltés gyorsítótára (`st.cache_data`) a fájl módosítási idejével kulcsolt; nagy adatbázis betöltési idejét nem mértük | a verziózott exportokon (≤ 180 sor) nem észlelhető |
| L6 | A `dashboard` Compose-szolgáltatás nincs (Fázis 8) | **megoldva a Fázis 8-ban** ([`TR-F08`](TR-F08_konteneres_rendszer.md)); az akkori jegyzőkönyv állapota változatlan |

## 6. Reprodukálás

```bash
docker build -f docker/Dockerfile -t vqebd:0.10.0 .
docker run --rm -v "$PWD:/repo" -w /repo -e PYTHONPATH=/repo/src -e VQEBD_REPO_ROOT=/repo \
    vqebd:0.10.0 python -W ignore -m pytest -q
docker run --rm -p 8501:8501 -v "$PWD:/repo" -w /repo -e PYTHONPATH=/repo/src \
    -e VQEBD_DASHBOARD_ROOT=/repo vqebd:0.10.0 \
    python -m streamlit run dashboard/app.py --server.address 0.0.0.0
```

Windows / Git Bash alatt a `MSYS_NO_PATHCONV=1` előtag kell. A `VQEBD_REPO_ROOT` a repó-hatókörű és a valódi
adatot használó dashboard-tesztekhez kell (a szállított image nem tartalmazza a `docs/` mappát).

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
