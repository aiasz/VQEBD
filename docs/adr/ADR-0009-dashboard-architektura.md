# ADR-0009 — Dashboard-architektúra: Streamlit + Plotly, tiszta rétegek, csak olvasás

| | |
|---|---|
| **Azonosító** | ADR-0009 |
| **Cím** | A bemutatási réteg: a logika a `src`-ben, a UI vékony, az adat csak olvasható |
| **Státusz** | **Javasolt** — a D1–D4 kérdések jóváhagyásra várnak |
| **Dátum** | 2026-11-02 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 7, 8 (konténerizáció), 9 (publikálás) |
| **Függ** | [ADR-0001](ADR-0001-technologiai-stack.md), [ADR-0004](ADR-0004-adattarolas.md), [ADR-0007](ADR-0007-batch-statisztika.md), [`phase_07.md`](../plan/phase_07.md) |
| **Bizonyíték** | [`phase_07.md`](../plan/phase_07.md) 2. fejezet (M1–M8) |

---

## Kontextus

A dashboardnak három olyan korlátja van, amelyet a mérés tárt fel:

1. **Rögzített numerikus stack.** `numpy 1.26.4` (a Mitiq miatt, ADR-0001). A Streamlit a `pyarrow
   26.0.0`-t húzza be, amely NumPy ≥ 2-t követel; a hiba **futásidejű**, a pip feloldója nem jelzi
   (M2). Ugyanaz a hibatípus, mint a Mitiq/`ply` eset. Ráadásul a `pyarrow 25.0.0` **szegmentációs
   hibával** omlik össze szálváltás után (M9), tehát a „legfrissebb numpy 1.x-szel induló" verzió
   sem jó.
2. **Az adat nem mindig adatbázis.** Egy tiszta klónon csak a verziózott JSON-exportok vannak meg
   (M7 és `phase_07.md` 1.); a körméret pedig sehol nincs tárolva.
3. **A Streamlit-appot nehéz tesztelni**, ha a logika benne él; az `AppTest` fej nélkül fut, de a JS
   renderelést nem látja (M4).

## Döntések

### 1. A logika a `src`-ben, a Streamlit-fájl vékony

`vqebd.dashboard.data` (pandas) és `vqebd.dashboard.figures` (Plotly) **tiszta függvények**; a
Streamlit-belépő (`dashboard/app.py`) csak widgetet és hívást tartalmaz. Így mypy strict alatt van, és
egység-szinten tesztelhető. *Elvetve:* a logika az `app.py`-ban — csak `AppTest`-tel tesztelhető,
lassú és törékeny.

### 2. Plotly

Interaktív (hover, zoom), a Streamlit natívan jeleníti meg, a hőtérkép és a hibasávos sávdiagram
kevés kóddal készül. A teszt az ábra **adatait** (`trace.x/y/z`) vizsgálja, a képet nem.
*Elvetve:* matplotlib (statikus), Altair (a hőtérképhez több kód).

### 3. Három adatforrás, egy normalizált tábla

SQLite, batch-export és teljes rekordlista ugyanazokat a **levezetett** oszlopokat adja. A hiányzó
`mapper`/`basis` értéket a VQEBD alapértelmezése pótolja, és a `size_assumed` oszlop jelzi. A
körméretet a rendszer **levezeti** (`2·pálya − 2`), nem tárolja; ismeretlen bázisnál `NaN`, nem
találgat.

### 4. Csak olvasás

Az adatbázis `read_only=True`-val nyílik; a dashboard nem ír, nem ér el hálózatot vagy QPU-t. Ezt
teszt őrzi (az adatbázisfájl bitre változatlan).

### 5. A függőségek a lockkal együtt, a `pyarrow` pinelve

`requirements-dashboard.txt`: `streamlit`, `plotly`, **`pyarrow==24.0.0`** (a legfrissebb, amely
NumPy 1.x-szel **és** szálváltás után is működik; mérve 16.1.0…24.0.0 rendben, a 25.0.0 összeomlik,
a 26.0.0 NumPy ≥ 2-t követel). A Docker-build a `requirements.lock`-ot
**kényszerként** használja (`-c`), mert a lock jelenleg nincs betartatva: egy frissen épített image a
71 lockolt csomagból 21-ben eltér (M5).

## Következmények

- **Pozitív:** a dashboard logikája gyorsan és mypy-védetten tesztelhető; egy tiszta klónon is van
  megjeleníthető adat; a build reprodukálható; a dashboard nem rongálhat adatot.
- **Negatív:** a `pyarrow` pin nem szokványos (a hiba okát az `requirements-dashboard.txt`
  magyarázza; a védelem egy alfolyamatban futó teszt); a lock újragenerálása minden függőségváltásnál kell; a vizuális megjelenés nincs
  automatikusan ellenőrizve.
- **Kockázat:** a `pyarrow==24.0.0` pin idővel ütközhet egy újabb Streamlit-tel; a Streamlit 1.59.1 a
  mért feloldás. **Az első mérésem (25.0.0 „működik") hibás volt**, mert csak táblát hozott létre;
  a szálváltás utáni `pyarrow.compute`-hívás (M9) csak a 7.2 lépés `AppTest`-jében bukott ki. A körméret levezetése a VQEBD alapértelmezett leképezésére épül; más leképezésű
  rekordnál (ha az export nem hordozza a `mapper`-t) a `size_assumed` jelzi a feltevést.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
