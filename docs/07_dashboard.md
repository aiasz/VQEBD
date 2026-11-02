# 07 — A dashboard (Fázis 7)

| | |
|---|---|
| **Dokumentum** | `docs/07_dashboard.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Projektverzió** | 0.10.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 7 — Dashboard |
| **Háttér** | [`phase_07.md`](plan/phase_07.md) · [`ADR-0009`](adr/ADR-0009-dashboard-architektura.md) · [`TR-F07`](testing/TR-F07_dashboard.md) |

---

## 1. Mit ad a Fázis 7?

Egy csak olvasó, interaktív felület (Streamlit + Plotly) a tárolt eredményekhez. **Négy nézet**, amelyek
egymás után, külön commitban készültek:

| Nézet | Mit mutat | Mire jó |
|---|---|---|
| **Táblázat** (7.1) | az eredmények táblázata, a *Hibák* fül (`run_failures`) | mi van az adatban, mi bukott el |
| **Disszociációs görbe** (7.2) | energia a kötéshossz függvényében, molekula-, aktívtér- és módszerválasztóval | a görbe alakja, a módszerek eltérése a Full CI-től |
| **Módszer-összehasonlítás** (7.3) | sávdiagram: referencia, nyers, mitigált | melyik módszer mennyit ront vagy javít |
| **Hőtérkép** (7.4) | körméret (qubit) × módszer; sikeresség vagy medián hiba | hol bukik el a módszer a méret növekedtével |

## 2. Indítás

**Docker** (a repó gyökeréből; Windows / Git Bash alatt `MSYS_NO_PATHCONV=1` előtaggal):

```bash
docker run --rm -p 8501:8501 -v "$PWD:/repo" -w /repo \
  -e PYTHONPATH=/repo/src -e VQEBD_DASHBOARD_ROOT=/repo vqebd:0.10.0 \
  python -m streamlit run dashboard/app.py --server.address 0.0.0.0
```

Utána: <http://localhost:8501>. A `--server.address 0.0.0.0` a konténeren kívüli eléréshez kell.

**Helyben** (ha a rögzített stack telepítve van): `streamlit run dashboard/app.py`.

| Környezeti változó | Jelentés |
|---|---|
| `VQEBD_DASHBOARD_SOURCE` | az alapértelmezett adatforrás útvonala (felülírja a felderítést) |
| `VQEBD_DASHBOARD_ROOT` | a felderítés gyökere (alapértelmezés: az aktuális könyvtár) |

A dashboard **csak olvas**: az adatbázist `read_only=True`-val nyitja, nem ír, hálózatot és QPU-t nem ér el.

## 3. Adatforrások

| Forrás | Felismerés | Megjegyzés |
|---|---|---|
| SQLite | `.sqlite`, `.sqlite3`, `.db` | teljes rekord; **csak itt van** a *Hibák* fül |
| Batch-export | `.json`, szótár `"rows"` kulccsal | pl. `docs/figures/data/f5_deterministic.json` |
| Teljes rekordlista | `.json`, lista | a `results_v1.json` alakja |

Az oldalsáv automatikusan felderíti a `data/db/*.sqlite`, `data/db/*.db`,
`docs/figures/data/f5_*.json` és `docs/figures/data/results_v*.json` fájlokat. **Egy tiszta klónon csak
a verziózott JSON-ok vannak meg** (az adatbázis helyi és gitignore-olt), ezért a dashboard ezekből is
megjeleníti az adatot. Az *Egyéni útvonal* mező felülírja a felderített forrást.

Hiányzó fájl, üres adatbázis, hibás vagy ismeretlen szerkezetű JSON: **érthető üzenet**, nem kivétel.

## 4. A nézetek olvasása

### 4.1 Hiba a Full CI-hez

Minden hiba **energia − Full CI**, mHa-ban (`error_mha`). A **kémiai pontosság** ±1.5936 mHa. A
*kémiailag pontos* futás: `|hiba| < 1.5936 mHa`.

> **Aktív térben a Full CI-hez mért hiba tartalmazza a csonkolást is.** A minimális (2e,3o) terek
> 15–72 mHa-t veszítenek, ezért az *egzakt* futás is „pontatlan" a Full CI-hez mérve: ez a tér modellhibája,
> nem a módszeré ([`TR-F05`](testing/TR-F05_batch.md) 3., fig09).

### 4.2 Módszercímkék

| Címke | Jelentés |
|---|---|
| `egzakt` | zajmentes szimuláció (Qiskit, Cirq vagy qsim — **a három platform egy címke alatt**, lásd 6. pont) |
| `lövészaj` | véges lövésszám, zajmentes eszköz |
| `zajos (nyers)` | zajmodell, hibaenyhítés nélkül |
| `ZNE lineáris` / `Richardson` / `exponenciális` | Zero-Noise Extrapolation a megnevezett extrapolátorral |
| `QPU (nyers)` / `QPU (TREX)` / `QPU (resilience 2)` | valódi hardver, a szerveroldali hibaenyhítés szintje szerint |

Minden módszer **minden nézetben ugyanazt a színt** kapja (Okabe–Ito, színtévesztés-biztos).

### 4.3 Disszociációs görbe

A szaggatott vonal a **Full CI**, a pontozott a **Hartree–Fock**; a jelölők az egyes futások
(átlátszó jelölőkkel, hogy az ismétlések látsszanak). A súgószöveg a `run_id`-t és a hibát mutatja.
Aktív térrel rendelkező molekulánál (LiH, BeH₂) az *Aktív tér* választó szűri a futásokat. A módszerválasztás
**molekula- vagy aktívtér-váltáskor visszaáll az alapértelmezettre** (minden módszer).

### 4.4 Módszer-összehasonlítás

Egy (molekula, aktív tér, kötéshossz) pontra módszerenként az **átlagos hiba** sávja, a hibasáv a
mintaszórás (több futásnál). Az első sáv a **referencia** (Full CI, hibája definíció szerint 0), a zöld
sáv a kémiai pontosság. Az alapértelmezett kötéshossz az, ahol a legtöbb módszer szerepel. Az ábra alatti
táblázat a számokat adja (`n`, átlag, szórás, SEM, kémiai pontosság az *átlagra*).

### 4.5 Hőtérkép

Az x tengely a **körméret** (qubit), az y a módszer. Két mérőszám: a **kémiailag pontos futások aránya**
(0–1, zöld a jó) és a **medián |hiba|** (mHa, a skála fordított, így a zöld itt is a jó). A hiányzó
(qubit, módszer) cellák **üresek**, nem nullák. Példa a valódi adatból: az egzakt futások sikeressége
2 qubiten 100%, 4 qubiten 0% (a minimális tér csonkolása), 8 és 10 qubiten 100% (frozen core).

> **A körméret nincs eltárolva a rekordban**, hanem levezetett: `2 · pálya − 2` (parity leképezés,
> kétqubites redukció), egyébként `2 · pálya`. A batch-exportok nem hordozzák a `mapper`-t és a `basis`-t,
> ezért ott a VQEBD alapértelmezése (parity, redukció, STO-3G) érvényes, és a nézet ezt **jelzi**.
> Ismeretlen bázisnál a futás kimarad (nem találgat).

## 5. Függőségek

A dashboard-csomagok a `requirements-dashboard.txt`-ben vannak, és a Docker-build a `requirements.lock`-ot
kényszerként használja (101 csomag). **Két mért kényszer** a `pyarrow` verziójára:

| `pyarrow` | Eredmény a `numpy 1.26.4` mellett |
|---|---|
| 16.1.0 … **24.0.0** | működik (a pin: **24.0.0**) |
| 25.0.0 | **szegmentációs hiba** a második script-futásban (`st.dataframe` után egy `pyarrow.compute`-hívás) |
| 26.0.0 | `ImportError`: NumPy ≥ 2-t követel |

A pin emelésekor a `tests/integration/test_dashboard_pyarrow_guard.py` jelzi az összeomlást. Részletek:
[`requirements-dashboard.txt`](../requirements-dashboard.txt), [`phase_07.md`](plan/phase_07.md) 2. (M2, M9).

## 6. Ismert korlátok

| # | Korlát |
|---|---|
| L1 | **Nincs vizuális ellenőrzés:** az `AppTest` a JS-ben renderelt Plotly-t nem futtatja; az ábrákat adatszinten (`x`/`y`/`z`) teszteltük, böngészős képernyőkép nincs |
| L2 | **A három egzakt platform egy címke** (`egzakt`): a Qiskit, Cirq és qsim futásai együtt átlagolódnak, a platformdimenzió nem látszik |
| L3 | A körméret levezetett, nem tárolt (4.5); a batch-exportokon mindig feltételezett |
| L4 | Nincs hitelesítés, többfelhasználós működés és élő frissítés; az adat a betöltéskor, a fájl módosítási idejével kulcsolt gyorsítótárból jön |
| L5 | A `dashboard` Compose-szolgáltatás és az egyparancsos indítás a Fázis 8 feladata |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
