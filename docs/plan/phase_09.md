# Fázis 9 — Dokumentáció, validálás, publikálás (`v1.0.0`)

| | |
|---|---|
| **Fázis** | 9 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Státusz** | **Kiadásra kész (2026-11-02)** — a helyi munka a `v1.0.0`-ig kész: [`TR-F09`](../testing/TR-F09_publikalas.md). **Az AC-9.1 (zöld CI a GitHubon) a push után, az AC-9.10 (release, DOI) a felhasználó jóváhagyása és a Zenodo-kapcsoló után zár** (5. fejezet) |
| **Célverzió** | `v1.0.0` (a mesterterv 8.1: „Fázis 9 lezárva = első publikált release, DOI") |
| **Előzmény** | [`phase_08.md`](phase_08.md), [`00_master_plan.md`](00_master_plan.md) 7–8. fejezet, v0.11.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Miért most, és mi a különlegessége ennek a fázisnak

Az alapterv Fázis 9-e: a projekt „közösségi szintre emelése”: teljes README, Zenodo-integráció, első GitHub Release és DOI,
rögzített verziók. Az elfogadási kritérium: **egy külső személy a README alapján, segítség nélkül** fel tudja telepíteni és
futtatni a rendszert.

Ez a fázis az eddigiektől két ponton tér el:

1. **Kifelé ható, nem visszavonható lépéseket tartalmaz.** Egy GitHub Release és főleg a Zenodo-archívum **állandó és
   nyilvános** (a DOI nem törölhető). Ezért a helyi előkészítés és az ellenőrzés elválik a kiadástól, és a kiadást **a
   felhasználó külön jóváhagyja** (5. fejezet).
2. **Egy lépést csak a felhasználó tud megtenni:** a Zenodo-integrációt a **saját Zenodo-fiókjában** kell bekapcsolni a
   repóhoz, **a release előtt**. Ezt az asszisztens nem végezheti el.

---

## 2. Előzetes mérés (2026-11-02, `v0.11.0`)

| # | Kérdés | Mérés | Következmény |
|---|---|---|---|
| M1 | Zöld-e a GitHub CI? | **Nem: a v0.9.0 óta piros.** A hibás lépés: *„AC-0.3 — a szállított image beépített tesztjei (mount nélkül)”*; az ok a Fázis 6-ban írt `test_compose_defines_a_simulator_only_scheduler_service`, amely a `docker-compose.yml`-t a fájl helyéből számolt útvonalon olvasta (`parents[2]`), a szállított image-ben viszont nincs `docker/` mappa. Helyben mindig bind-mountolt repóval futtattam, ezért nem tűnt fel | Javítva (`c9794db`); mindkét CI-tesztlépés helyben reprodukálva és zöld (mount nélkül 575 sikeres, mounttal 770); **a GitHubon a push után igazolandó** (AC-9.1) |
| M2 | Felismeri-e a GitHub a licencet? | **Nem:** a `licenseInfo.key` = `other`, mert a `LICENSE` a szabványos MIT-szöveg után egy harmadik-fél-függeléket is tartalmaz (Mitiq/GPL megjegyzés) | A függelék a `NOTICE`-ba költözik, a `LICENSE` szabványos MIT lesz (AC-9.2) |
| M3 | Érvényes-e a `CITATION.cff`? | **Igen** (`cffconvert --validate`: CFF 1.2.0). A belőle generált Zenodo-metaadat: 2 szerző (Kormos, Attila; „Claude Opus 5”), MIT, 9 kulcsszó, **magyar leírás** | A leírás kétnyelvű legyen; az AI mint Zenodo-szerző a felhasználó döntése (D4) |
| M4 | Mi van a GitHub-oldalon? | Nyilvános repó, leírás van; **nincs release, nincsenek témakörök (topics)**, nincs `CONTRIBUTING`, `SECURITY`, CI-jelvény | Pótlandó (G2–G4); a topics a felhasználó jóváhagyásával (D3) |
| M5 | Mekkora a README? | ~800 sor (HU+EN), a Fázis 0–8 összes szakaszával | A bejárat legyen rövid „Röviden” blokk: 3 parancs, mielőtt a részletek jönnek |
| M6 | Védi-e valami a hivatkozásokat? | Eddig csak egyszeri kézi ellenőrzés (60 fájl, 385 hivatkozás, 0 hibás) | Automata teszt a jövőbeli törések ellen (G5) |
| M7 | Reprodukálhatósági állítás | A lock 101 csomagot rögzít (a build betartatja, 0 eltérés); a README-ban nincs rövid verziótáblázat | Táblázat a kulcscsomagokról, teszttel a lockhoz kötve (G6) |

---

## 3. Célkitűzések

| # | Cél | Szállítandó |
|---|---|---|
| G1 | Zöld CI | a hibás teszt javítása; a push utáni futás igazolása |
| G2 | Szabványos licenc | `LICENSE` = MIT; `NOTICE` a harmadik felekről és a Mitiq/GPL-ről; teszt |
| G3 | Közösségi fájlok | `CONTRIBUTING.md`, `SECURITY.md`, issue-sablonok |
| G4 | A README bejárata | „Röviden” blokk (HU/EN), CI-jelvény, hivatkozási blokk (BibTeX), kétnyelvű `CITATION.cff`-leírás |
| G5 | Védőtesztek | hivatkozás-ellenőrző teszt, licenc-teszt, CFF-érvényesség (ha elérhető), README↔lock verziótáblázat |
| G6 | Reprodukálhatósági állítás | kulcsverziók táblázata a README-ban, a lockhoz kötve |
| G7 | README-alapú telepítés igazolása | tiszta klón + a README parancsai **szó szerint**; jegyzőkönyv a súrlódásokkal |
| G8 | Kiadási folyamat | `docs/09_publishing.md` (Zenodo-lépések, kiadás, a DOI beírása), kiadási jegyzet a `CHANGELOG`-ból |
| G9 | A kiadás | `v1.0.0` címke, GitHub Release, Zenodo-DOI (**jóváhagyással**) |

---

## 4. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-9.1** | A GitHub CI **minden jobja zöld** a kiadási commiton | `gh run list` a push után |
| **AC-9.2** | A GitHub a licencet MIT-ként ismeri fel; a `NOTICE` tartalmazza a Mitiq/GPL megjegyzést | `gh repo view` + teszt |
| **AC-9.3** | A `CITATION.cff` érvényes (CFF 1.2.0), a `version` és a `date-released` a `VERSION`-nel és a `CHANGELOG`-gal egyezik | `cffconvert --validate` + teszt |
| **AC-9.4** | `CONTRIBUTING.md`, `SECURITY.md`, issue-sablonok léteznek, a README hivatkozik rájuk | teszt |
| **AC-9.5** | A README bejáratán a probléma, a gyors indítás (3 parancs), a licenc, a hivatkozás és a CI-jelvény megvan, HU és EN is | teszt + átvizsgálás |
| **AC-9.6** | Az összes Markdown-fájl minden relatív hivatkozása létező fájlra mutat | automata teszt |
| **AC-9.7** | A README kulcsverzió-táblázata egyezik a `requirements.lock`-kal | teszt |
| **AC-9.8** | **README-alapú telepítés:** tiszta klónból, a README parancsait szó szerint követve a build, a példafuttatás és a dashboard működik | végrehajtás + TR-F09 |
| **AC-9.9** | `docs/09_publishing.md`, TP-F09, TR-F09, `CHANGELOG`, `v1.0.0` konzisztens (`VERSION`, `CITATION.cff`, Compose, dokumentumok) | `test_version_consistency` + végrehajtás |
| **AC-9.10** | **A kiadás:** GitHub Release `v1.0.0`; a Zenodo-DOI kiosztva és beírva a `CITATION.cff`-be és a README-ba | **jóváhagyással**; a DOI a felhasználó Zenodo-beállításától függ |

> **Az AC-9.8 korlátja:** a „külső személy” szerepét az asszisztens játssza egy tiszta klónon, **ugyanazon a gépen**.
> Ez nem egyenértékű egy független személy próbájával; a TR-F09 ezt nyíltan rögzíti, és a Fázis 10 első lépése lehet egy
> valódi külső próba.

---

## 5. A kiadás és a Zenodo: ki mit tesz

| Lépés | Ki | Mikor |
|---|---|---|
| Helyi előkészítés, tesztek, `v1.0.0` címke | asszisztens | a fázis elején |
| Push a GitHubra, a CI zöldjének igazolása | asszisztens (**jóváhagyással**) | a helyi munka után |
| GitHub-témakörök (topics) beállítása | asszisztens (**jóváhagyással**, D3) | a kiadás előtt |
| **Zenodo-integráció bekapcsolása:** zenodo.org → belépés GitHubbal → *GitHub* → a `aiasz/VQEBD` kapcsolójának átbillentése | **felhasználó** | **a release előtt** |
| GitHub Release `v1.0.0` létrehozása | asszisztens (**jóváhagyással**) | a Zenodo-kapcsoló után |
| A Zenodo a release-t archiválja, DOI-t ad (koncepció- és verzió-DOI) | automatikus | a release után |
| A DOI beírása a `CITATION.cff`-be és a README-ba | asszisztens (a felhasználó által megadott DOI-val) | a DOI után |

---

## 6. Döntések, amelyek a felhasználóra várnak

| # | Kérdés | Javaslat | Következmény |
|---|---|---|---|
| D1 | A kiadás verziója | **`v1.0.0`** (a mesterterv 8.1 szerint) | `v0.12.0`: a „1.0” később; de az eltérés a saját tervtől |
| D2 | Zenodo-integráció | a felhasználó kapcsolja be, **mielőtt** a release elkészül | a DOI utólag is kérhető, de egy release-t a Zenodo csak a kapcsoló bekapcsolása **után** archivál |
| D3 | GitHub-témakörök (topics) és repóleírás | beállítás: `quantum-computing`, `vqe`, `quantum-chemistry`, `error-mitigation`, `qiskit`, `benchmark`, `reproducibility`, `streamlit` | a repó láthatósága javul; bármikor visszavonható |
| D4 | „Claude Opus 5” mint **Zenodo-szerző** | **Eldöntve (2026-11-02): csak Kormos Attila** a `CITATION.cff` szerzői között; az AI a README/dokumentumok „Készítők” soraiban és a `LICENSE` szerzői sorában marad | a Zenodo-rekord szerzői listáján csak Kormos Attila; **utólag nehezen javítható**, ezért kellett a döntés a kiadás előtt |
| D5 | ORCID a szerzőhöz | a felhasználó megadja, ha van | nélküle a rekord ORCID-azonosító nélkül készül |
| D6 | `CODE_OF_CONDUCT.md` | **kimarad** most (a Contributor Covenant szövege hosszú és külső); a `CONTRIBUTING.md` rövid viselkedési elvet ad | a Fázis 10-ben pótolható |

---

## 7. Amit ez a fázis NEM tartalmaz

- A közösségi bejelentések (QOSF, Unitary Fund, r/QuantumComputing) és a Metriq-beküldés — Fázis 10.
- Valódi, független külső személy telepítési próbája (lásd az AC-9.8 korlátját).
- Böngészős képernyőképek a README-ban (a vizuális ellenőrzés hiánya: TR-F07 L1).
- Új funkció vagy új tudományos mérés.

---

## 8. Kilépési feltétel

AC-9.1 … AC-9.10 teljesül; TP-F09 és TR-F09 elkészült; `v1.0.0`; a DOI beírva. **Ha a DOI a felhasználó
Zenodo-beállítására vár, a fázis „kiadva, DOI függőben” állapotban van**, és az AC-9.10 második fele a DOI beérkezésekor zár.

---

## 9. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-11-02 | Első változat; az előmérés (2. fejezet) és a kiadás kifelé ható jellege alapján |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
