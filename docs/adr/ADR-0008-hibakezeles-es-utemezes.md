# ADR-0008 — Hibamodell, újrapróbálkozás és hardveres ütemezési politika

| | |
|---|---|
| **Azonosító** | ADR-0008 |
| **Cím** | A hiba is adat: tárolt hibák, osztályozott újrapróbálkozás, nem ütemezett hardver |
| **Státusz** | **Elfogadott** (2026-11-02, a D1–D4 alapértelmezések jóváhagyásával; megvalósítva a v0.9.0-ban) |
| **Dátum** | 2026-11-02 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 6, 7 (dashboard: hibák megjelenítése), 8 (konténerizáció) |
| **Függ** | [ADR-0004](ADR-0004-adattarolas.md), [ADR-0005](ADR-0005-determinizmus.md), [`phase_06.md`](../plan/phase_06.md) |
| **Bizonyíték** | [`phase_06.md`](../plan/phase_06.md) 2. fejezet (előmérés), K7 ([CHANGELOG 0.8.1](../../CHANGELOG.md)), TR-F05 7. |

---

## Kontextus

A Fázis 5 batch-motorja hibaizolált: egy futás hibája után a batch folytatódik.
A hiba azonban csak a memóriában (`BatchReport.failed`) és a naplóban él; az
adatbázisban nincs hibatábla. Felügyelet nélküli, ütemezett működésnél ez azt
jelenti, hogy a hibák a folyamat végével elvesznek, és az alaptervi követelmény
(„ha egy backend nem elérhető vagy a job hibára fut, a rendszer ezt is elmenti”)
nem teljesül.

Az automatizálás emellett új kockázatot hoz: az ismétlődő futás ismétlődően fogyaszt.
A K7 (2026-09-23) egy védelem nélküli útvonallal 42 jobot, 630 QPU-s-ot égetett el
a 600 s-os keretből.

## Döntések

### 1. A hiba adat (append-only `run_failures` tábla)

Minden sikertelen próbálkozás egy sor (futás, próbálkozás sorszáma, típus, osztály,
titoktalanított üzenet, idő). A tábla **hozzáad** a sémához (v3), a `results`
változatlan. *Elvetve:* hibaoszlopok a `results`-ban — a sikertelen futásnak nincs
eredménye, és a `results` sorai az append-only elv szerint nem módosulnak.

### 2. Osztályozott, korlátos, tartósított újrapróbálás

`transient` / `permanent` / `quota` osztályok; **ismeretlen kivétel = `permanent`**;
korlátos próbálkozás exponenciális visszalépéssel, jitter nélkül (determinizmus,
tesztelhetőség). A próbálkozásszám az adatbázisban él, így egy újraindított
ütemező nem ismétel végtelenül (`abandoned` állapot).

*Indok az „ismeretlen = tartós” szabályra:* aszimmetrikus költség. Egy kihagyott
újrapróbálás egy későbbi indításban pótolható; egy fölöslegesen megismételt
hardveres job kvótát éget el. A megfigyelt IBM-hibák (403 lejárt token,
`InvalidAccountError` hiányzó `crn`) mindkettő tartós volt, tehát az
újrapróbálás rajtuk nem segít.

### 3. A valódi QPU alapértelmezésben nincs ütemezve

Az ütemező nem indít `ibm_qpu` cellát. Hardveres futás csak `--allow-hardware` +
`VQEBD_ALLOW_HARDWARE=true` + kvótakapu (hátralévő idő ≥ becslés + 20%) mellett, és
egyszeri, nem ismétlődő. A hardveres futás `max_attempts` alapértelmezése 1, és minden
próbálkozás újra átmegy a `guard_hardware_vqe`-n (K7).

*Elvetve:* rendszeres hardveres cron. A 600 QPU-s / 28 napos keret mellett egy
ismétlődő mérés a keretet szisztematikusan elfogyasztaná, és a tudományos érték a
tervezett, rögzített mérésekben van (5.H), nem az ismétlésben.

## Következmények

- **Pozitív:** a hibák megmaradnak és lekérdezhetők (dashboard alapja); az ütemezett
  futás nem fogyaszthat kvótát engedély nélkül; a viselkedés injektált órával
  determinisztikusan tesztelhető.
- **Negatív:** az „ismeretlen = tartós” szabály egy ritka átmeneti hibát véglegesít
  (amíg a kivételtípus nem kerül a szabálytáblába); séma v3 migráció.
- **Kockázat:** az IBM Runtime átmeneti hibáinak tényleges kivételtípusait nem mértük;
  a `transient` szabályok **feltevések**: szimulált hibával tesztelték (AC-6.2, TR-F06), valódi
  esetből nem erősítették meg (TR-F06 6., L1).
- **Megvalósítási kiegészítés:** a 3. döntés batch szintű kvótakapuja (+20% tartalék) a
  pipeline előellenőrzésében él; a futásonkénti védelem (K7) ettől függetlenül minden futásnál
  lefut (TR-F06 3.).

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
