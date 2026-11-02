# Fázis 7 — Dashboard (bemutatási réteg)

| | |
|---|---|
| **Fázis** | 7 |
| **Dokumentum-verzió** | 1.2.0 |
| **Dátum** | 2026-11-02 |
| **Státusz** | **Megvalósítva és lezárva (2026-11-02)** — mind a 12 elfogadási kritérium teljesült: [`TR-F07`](../testing/TR-F07_dashboard.md). A 7. fejezet döntései az alapértelmezésekkel jóváhagyva |
| **Célverzió** | `v0.10.0` |
| **Előzmény** | [`phase_06.md`](phase_06.md), [`00_master_plan.md`](00_master_plan.md) 7. fejezet, v0.9.0 ([`CHANGELOG`](../../CHANGELOG.md)) |
| **Új ADR** | [`ADR-0009`](../adr/ADR-0009-dashboard-architektura.md) — Streamlit + Plotly, tiszta adat- és ábraréteg, csak olvasás |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |

---

## 1. Miért most, és miért így

Az alapterv Fázis 7-je: „a Fázis 4-es tárolóból élő, interaktív vizualizáció”, **négy belső
lépésben, egyenként tesztelve**. A Fázis 5–6 után három tény alakítja a tartalmat:

1. **Az eredmények ma statikus PNG-k.** A `scripts/gen_report_figures.py` rögzített ábrákat
   készít; a felhasználó nem tud molekulát váltani, szűrni, és a hibákat (`run_failures`, v0.9.0)
   semmi nem mutatja.
2. **Az adat háromféle alakban él.** (a) SQLite adatbázis (helyi, gitignore-olt), (b) batch-export
   JSON (`{"rows": [...]}`, a `docs/figures/data/f5_*.json`), (c) a Fázis 4 teljes rekordlistája
   (`results_v1.json`, 8 rekord). Egy tiszta klónon **csak a JSON-ok vannak meg**, ezért a
   dashboardnak mindhárom forrást ismernie kell, különben a Fázis 8 elfogadási kritériuma („tiszta
   gépen megjeleníti a korábban gyűjtött adatokat”) nem teljesülhet.
3. **A függőségi stack rögzített**, és a Streamlit **rejtett ütközést** hoz (2. fejezet).

A Fázis 7 ezért öt dolgot szállít: (0) **reprodukálható build** (a lock betartatása), (A) az adat-
és ábrarétegek tiszta, tesztelhető függvényekként, (B) egy vékony Streamlit-felület, (C) a négy
belső lépés egyenként, (D) a hibák megjelenítése.

---

## 2. Előzetes mérés (2026-11-02, `vqebd:0.9.0`)

| # | Kérdés | Mérés | Következmény |
|---|---|---|---|
| M1 | Telepíthető-e a Streamlit a pinelt stack mellé? | `pip install --dry-run streamlit plotly -c requirements.lock`: 26 új csomag, **a numerikus stack (numpy, scipy, qiskit, pandas) érintetlen** | Telepíthető |
| M2 | Működik-e is? | **Nem:** a Streamlit a `pyarrow 26.0.0`-t húzza be, az **NumPy ≥ 2.0-t követel** (`ImportError`), így az `st.dataframe` a `numpy 1.26.4` mellett elbukik. A pip feloldója ezt **nem jelzi** (futásidejű hiba) | Új kényszer a `pyarrow` pinjére |
| M3 | Melyik `pyarrow` jó? | **Első (hibás) mérés:** 19.0.1 … 25.0.0 működik, mert csak táblát hoztam létre. **Javítva, lásd M9** | A pin végül **`pyarrow==24.0.0`**; ezzel a feloldó Streamlit **1.59.1**-et választ |
| M9 | Összeomlik-e valami szálváltás után? | **Igen, a `pyarrow 25.0.0`:** ha egy script-futásban `st.dataframe` fut, a következő futás (a Streamlit minden futást új szálban végez) első `pyarrow.compute`-hívása (a pandas `Series.unique()`-ja az új `str` oszloptípuson) **szegmentációs hibával** (exit 139) leáll. A 16.1.0 … 24.0.0 mind rendben van. Valószínű ok (nem bizonyított): az alapértelmezett `mimalloc` memóriakezelő; mérve: `ARROW_DEFAULT_MEMORY_POOL=mimalloc` összeomlik, `=system` és `=jemalloc` nem | Élesben a szerver leállna a felhasználó második kattintásánál. Védő teszt: `test_dashboard_pyarrow_guard.py` (alfolyamatban) |
| M4 | Tesztelhető-e fej nélkül? | `streamlit.testing.v1.AppTest`: widgetváltás (`selectbox`) újrafuttatja az appot, a `metric` és `dataframe` frissül; 0.23 s/futás | A belső lépések automatikusan tesztelhetők; a JS-ben renderelt Plotly-t **nem**, ezért az ábrákat adatszinten teszteljük |
| M5 | Betartatja-e a build a `requirements.lock`-ot? | **Nem.** A Dockerfile csak a `requirements.txt`-t (közvetlen pinek) telepíti; egy most épített image a 71 lockolt csomagból **21-ben eltér** (pl. `pillow` 12.3.0 ↔ 13.0.0, `certifi`, `pydantic`, `cryptography`). A numerikus stack (numpy, scipy, qiskit, aer, pyscf) azonos | A reprodukálhatósági ígéret (ADR-0001) nem teljesül a tranzitív rétegen; lásd 0. lépés |
| M6 | Hasonló-e a hiba a lockon kívüli telepítésnél? | A lockkal telepítve a pip figyelmeztet: `ibm-cloud-sdk-core 3.28.1` (az image-ben) `python_dateutil>=3.0.0`-t kér, a lock 2.9.0.post0-t pinel | Az eltérés konkrét következménye; a 0. lépés megszünteti |
| M7 | Tárolja-e az adatbázis a körméretet? | **Nem:** nincs `n_qubits` / `n_parameters` oszlop, a `metadata_json` üres. A hőtérképhez a körméret kell | A qubitszámot a dashboard **levezeti** (7. lépés, 4.3); séma-módosítás nincs |
| M8 | Mekkorák a rendszerek? | Mért (parity + kétqubites redukció): H₂ **2** qubit/3 paraméter · (2e,3o) **4**/8 · LiH (2e,5o) **8**/24 · BeH₂ (4e,6o) **10**/92 | Képlet: `2·pálya − 2`; a teszt az 5 mért rendszerrel igazol (AC-7.7) |

**Következmény a korábbi dokumentumra:** az M8 mérés kimutatta, hogy a `docs/05_batch.md` a
minimális (2e,3o) terekre 6 qubitet írt; ez **hibás** volt (4 a helyes). Javítva (`CHANGELOG`,
Unreleased).

---

## 3. Célkitűzések

| # | Cél | Szállítandó |
|---|---|---|
| G0 | Reprodukálható build | a Docker-build a `requirements.lock`-ot **kényszerként** használja (`-c`); a lock újragenerálva a dashboard-függőségekkel |
| G1 | Függőségek | `requirements-dashboard.txt`: `streamlit`, `plotly`, `pyarrow==24.0.0` (indok a fájlban); a numerikus stack változatlan |
| G2 | Adatréteg | `vqebd.dashboard.data`: három forrás egységes `DataFrame`-be; levezetett oszlopok (hiba mHa-ban, módszer-címke, kémiai pontosság, qubitszám) |
| G3 | Ábrarétegek | `vqebd.dashboard.figures`: tiszta függvények, amelyek Plotly-ábrát adnak, az UI-tól függetlenül tesztelhetők |
| G4 | UI | `dashboard/app.py` (vékony belépő) + `vqebd.dashboard.app`: oldalsáv (adatforrás, szűrők), négy nézet |
| G5 | Négy belső lépés | 7.1 táblázat · 7.2 disszociációs görbe · 7.3 módszer-összehasonlítás · 7.4 hőtérkép; **mindegyik külön commit és teszt** |
| G6 | Hibanézet | a `run_failures` tábla megjelenítése (a 7.1 lépés része) |
| G7 | Dokumentáció | `docs/07_dashboard.md`, TP-F07, TR-F07, README (HU/EN), CHANGELOG |

---

## 4. Architektúra

### 4.1 Rétegek (ADR-0009)

```
 adatforrás ──►  vqebd.dashboard.data    (tiszta, pandas)   ──►  vqebd.dashboard.figures (tiszta, plotly)
 SQLite / JSON        load_results, load_failures                    dissociation_figure, method_comparison_figure,
                      derive_columns                                 heatmap_figure
                                              └────────────►  vqebd.dashboard.app (Streamlit, vékony)
                                                                    ▲
                                              dashboard/app.py ─────┘   (streamlit run dashboard/app.py)
```

- **A logika a `src`-ben él** (mypy strict, a Fázis 0 kapuival), a Streamlit-fájl csak widgetet és
  hívást tartalmaz. Így az adat- és ábrarétegek a UI nélkül, gyorsan tesztelhetők.
- **Csak olvasás:** az adatbázist `read_only=True`-val nyitja; a dashboard semmit nem ír, hálózatot
  és QPU-t nem ér el.

### 4.2 Adatforrások (G2)

| Forrás | Felismerés | Megjegyzés |
|---|---|---|
| SQLite | `.sqlite` / `.db` | teljes rekord, + `run_failures` |
| Batch-export | `.json`, szótár `"rows"` kulccsal | részhalmaz-oszlopok (nincs `mapper`, `basis`) |
| Teljes rekordlista | `.json`, lista | a `results_v1.json` alakja |

Az egységesítés **levezetett** oszlopokat ad: `error_mha` (`energia − Full CI`, mHa), `method`
(pl. „lövészaj", „zajos", „ZNE Richardson", „QPU TREX"), `chemically_accurate`
(`|error| < 1.6 mHa`), `n_qubits` (4.3). Hiányzó `mapper` / `basis` esetén a VQEBD alapértelmezése
(parity, kétqubites redukció, STO-3G) érvényes, és az oszlop **`size_assumed = True`**-val jelöli.

### 4.3 A körméret levezetése (M7, M8)

`n_qubits = 2 · pályák − 2` (parity + kétqubites redukció), egyébként `2 · pályák`. A pályaszám az
aktív térből jön, teljes térben a bázisból (STO-3G: H₂ 2, LiH 6, BeH₂ 7). Ismeretlen bázisnál
`NaN`: a hőtérkép kihagyja, **nem találgat**. A képletet az 5 mért rendszer igazolja (AC-7.7). A
valódi tárolás (`n_qubits`, `n_parameters`, CX-szám a rekordban, séma v4) **nincs a Fázis 7-ben**;
ez a hőtérkép x-tengelyét a CX-számra cserélhetné, és külön döntés.

### 4.4 A négy belső lépés (G5)

| Lépés | Nézet | Tartalom | Önálló teszt |
|---|---|---|---|
| **7.1** | Táblázat | a rekordok táblázata (+ „Hibák” fül a `run_failures`-ből) | az app elindul, a táblázat pontosan a fixture rekordjait mutatja |
| **7.2** | Disszociációs görbe | energia vs. kötéshossz, **molekulaválasztóval**; Full CI, HF és a futások pontjai | molekulát váltva a görbe pontjai a kiválasztott molekuláé |
| **7.3** | Módszer-összehasonlítás | sávdiagram: nyers vs. mitigált vs. referencia | a három sáv értéke egy ismert fixture-rekordra helyes |
| **7.4** | Hőtérkép | körméret (qubit) × módszer, szín = medián hiba vagy a kémiailag pontos futások aránya | legalább egy backend és molekula adatával helyesen színez |

Minden lépés **külön commit**; a következő lépés az előző összes tesztjét változatlanul átengedi.

---

## 5. Új és módosuló fájlok

| Fájl | Változás |
|---|---|
| `docker/Dockerfile` | `pip install -r … -c requirements.lock`; a dashboard-függőségek telepítése |
| `requirements-dashboard.txt` | **új** |
| `requirements.lock` | újragenerálva |
| `src/vqebd/dashboard/data.py`, `figures.py`, `app.py` | **új** |
| `dashboard/app.py` | **új**, vékony belépő (a mappa ma üres) |
| `tests/unit/test_dashboard_data.py`, `test_dashboard_figures.py`, `tests/integration/test_dashboard_app.py` | **új** |

---

## 6. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-7.1** | A Docker-build a lockot betartatja: egy frissen épített image `pip freeze`-e a lockkal **0 eltérést** mutat | végrehajtás |
| **AC-7.2** | A dashboard-függőségekkel a numerikus stack változatlan (numpy, scipy, qiskit, pandas), az `st.dataframe` működik, és a **második script-futás nem omlik össze** (`pyarrow 24.0.0`, M9) | teszt + végrehajtás |
| **AC-7.3** | **7.1:** az app elindul (`AppTest`, kivétel nélkül), a táblázat és a Hibák fül pontosan a fixture rekordjait mutatja | integrációs teszt |
| **AC-7.4** | Az adatréteg ugyanarra a rekordra azonos levezetett oszlopokat ad mindhárom forrásból (SQLite, batch-export, teljes lista) | keresztvalidáció |
| **AC-7.5** | **7.2:** molekulaváltásra az ábra pontjai a kiválasztott molekuláéra változnak (a Full CI-görbével együtt) | egység- + integrációs teszt |
| **AC-7.6** | **7.3:** egy ismert fixture-rekordra a három sáv értéke (nyers, mitigált, referencia) pontosan egyezik a vártakkal | egységteszt |
| **AC-7.7** | **7.4:** a qubitszám-levezetés az 5 mért rendszeren helyes (2, 4, 8, 4, 10); a hőtérkép cellaszíne az ismert fixture-re a várt | egységteszt |
| **AC-7.8** | A négy lépés egymás után, külön commitban készül; minden lépés után az összes korábbi lépés tesztje zöld | commit-történet + CI |
| **AC-7.9** | A dashboard az adatbázist csak olvasásra nyitja: a futás után az adatbázisfájl bitre változatlan | teszt |
| **AC-7.10** | Hiányzó/üres/sérült adat (nem létező útvonal, üres DB, hibás JSON) **érthető üzenet**, nem kivétel | negatív teszt |
| **AC-7.11** | Valódi adat: a `f5_deterministic.json` (50), `f5_statistical.json` (180) és `results_v1.json` (8) kivétel nélkül betöltődik, a sorszámok egyeznek | integrációs teszt |
| **AC-7.12** | `docs/07_dashboard.md`, TP-F07, TR-F07, README (HU/EN), CHANGELOG, `v0.10.0`; a minőségi kapuk zöldek | végrehajtás |

---

## 7. Döntések, amelyek a felhasználóra várnak

| # | Kérdés | Javaslat | Következmény, ha mást választ |
|---|---|---|---|
| D1 | Egy image vagy külön dashboard-image | **Egy image** (a Fázis 8 szétválaszthatja) | Külön image: két Dockerfile, két lock |
| D2 | Plotly vagy Altair/matplotlib | **Plotly** (interaktív, hover, a Streamlit natívan támogatja) | Altair: a Streamlit alapértelmezett, de a hőtérképhez több kód; matplotlib: statikus |
| D3 | A 0. lépés (lock betartatása) a Fázis 7 része legyen | **Igen** (M5 miatt a dashboard-függőségek nélküle sem reprodukálhatók) | Elhagyva: a dashboard-csomagok tranzitív rétege is lebeg |
| D4 | Képernyőképek a dokumentációban | **Később**, ha lesz böngészős eszköz; addig az ábrák adatszintű leírása | A TR-F07 jelölje, hogy nincs vizuális ellenőrzés |

---

## 8. Tesztelési terv (összefoglaló; részletesen: TP-F07)

- **1. kör — funkcionális:** adatréteg (három forrás), ábrarétegek (adatszint), `AppTest` a négy
  lépésre.
- **2. kör — negatív és robusztussági:** hiányzó fájl, üres adatbázis, hibás JSON, ismeretlen
  bázis (`NaN`, nem találgat), csak egy módszer az adatban (a hőtérkép nem omlik össze), nulla
  sor szűrés után.
- **3. kör — keresztvalidáció:** SQLite ↔ export ↔ teljes lista; a dashboard `error_mha` ↔ a
  `vqebd.stats` / a Fázis 5 export `error_vs_fci`; a levezetett qubitszám ↔ a mért építés.

**Ismert korlát:** az `AppTest` a JS-ben renderelt Plotly-t nem futtatja. A vizuális megjelenés
ezért **nincs automatikusan ellenőrizve**, csak az ábra adatai (a trace-ek `x`/`y`/`z` értékei).

---

## 9. Amit ez a fázis NEM tartalmaz

- A `dashboard` **compose-szolgáltatás** és az egyparancsos indítás — Fázis 8.
- Hitelesítés, többfelhasználós működés, élő frissítés (websocket / automatikus újratöltés).
- Séma v4 (a körméret tárolása) és a CX-szám alapú hőtérkép.
- Heron-zajmodell, Sampler-alapú becslő, hardverhatékony ansatz (K1–K4): tudományos bővítés.
- Értesítések hibákról.

---

## 10. Kilépési feltétel

AC-7.1 … AC-7.12 teljesül; TP-F07 és TR-F07 elkészült; `docs/07_dashboard.md`; README (HU/EN),
CHANGELOG, `v0.10.0`; minőségi kapuk (ruff, mypy strict, teljes tesztkészlet) zöldek.

---

## 11. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-11-02 | Első változat, a függőségi és adatelőmérés (2. fejezet) alapján |
| 1.2.0 | 2026-11-02 | Megvalósítva és lezárva; D1–D4 jóváhagyva az alapértelmezésekkel |
| 1.1.0 | 2026-11-02 | **Javítás (M9):** a `pyarrow==25.0.0` pin hibás volt; a 25.0.0 szálváltás után szegmentációs hibával omlik össze, a helyes pin 24.0.0. Az első mérés (M3) csak táblát hozott létre, a `pyarrow.compute`-ot és a szálváltást nem tesztelte |

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
