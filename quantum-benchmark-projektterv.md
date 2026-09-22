# Kvantumkémiai VQE Benchmark & Dashboard — Projektterv

## 0. Cél és alapelv

**Cél:** Egy konténerizált Python-rendszer, ami VQE-alapú kvantumkémiai számításokat futtat kis molekulákra (H2, LiH, BeH2), különböző hibaenyhítési stratégiákkal, szimulátoron és valódi IBM-hardveren, az eredményeket strukturáltan tárolja, és egy dashboardon vizuálisan összehasonlítja — publikálható, reprodukálható közösségi benchmarkként.

**Alapelv:** Minden fázis egy önmagában futtatható, tesztelhető, dokumentálható egység. Egy fázis csak akkor zárható le, ha a hozzá tartozó elfogadási kritérium teljesül. Nem lépünk tovább "félig működő" alapokon.

**Architektúra három rétegben:**

```
[Végrehajtási réteg]  -->  [Adattárolási réteg]  -->  [Bemutatási réteg]
   Qiskit + Mitiq          CSV/SQLite + séma            Streamlit dashboard
   (a kvantumprogram)      (strukturált eredmények)     (vizuális összehasonlítás)
```

---

## Fázis 0 — Alapinfrastruktúra és repó-szerkezet

**Cél:** A projekt csontszerkezetének létrehozása, Docker-alapokkal, mielőtt egyetlen kvantumsor is lefutna.

**Feladatok:**
- Git repó létrehozása, MIT licenc, `.gitignore` (Python, Docker, adatfájlok).
- Mappaszerkezet kialakítása:
  ```
  /src            -> kvantumkód (végrehajtási réteg)
  /data           -> gyűjtött eredmények (séma szerint)
  /dashboard      -> Streamlit app
  /tests          -> automatikus tesztek
  /docker         -> Dockerfile-ok, docker-compose.yml
  /docs           -> dokumentáció, README részletek
  ```
- Egyetlen minimális `Dockerfile`, amely csak Python 3.11 + pip-et telepít, semmi kvantumkönyvtárat még.
- `requirements.txt` üres, csak `pytest` benne.

**Elfogadási kritérium (teszt):**
`docker build` sikeresen lefut, és a konténerben `python --version` helyes kimenetet ad.

**Dokumentáció:** Rövid `docs/00_setup.md` — hogyan épül fel és futtatható a konténer.

---

## Fázis 1 — Az egyetlen kvantumprogram: H2-VQE szimulátoron

**Cél:** Egy önálló, kézzel is futtatható és ellenőrizhető Python-modul, ami H2-re kiszámolja az alapállapoti energiát szimulátoron.

**Feladatok:**
- `src/vqe_runner.py` — egyetlen függvény: `run_vqe(molecule_config) -> float` (visszaadja az energiát Hartree-ban).
- `qiskit`, `qiskit-nature`, `qiskit-aer`, `pyscf` hozzáadása a `requirements.txt`-hez, Docker image frissítése.
- A H2 molekula fix konfigurációval (0.735 Å kötéshossz, STO-3G bázis) van bekódolva induló tesztesetként.

**Elfogadási kritérium (teszt):**
- `pytest tests/test_vqe_h2.py` — a kapott energia -1.137 Hartree körül van (±0.01 Hartree tolerancia).
- Ez egy **automatikus unit teszt**, nem csak vizuális ellenőrzés — ha a szám kicsúszik a tartományból, a teszt pirosat jelez.

**Dokumentáció:** `docs/01_vqe_core.md` — mit csinál a függvény, milyen paraméterei vannak, hogyan futtatható önállóan (`docker run ... python src/vqe_runner.py`).

**Miért itt állunk meg:** Ez az a pont, ahol már van egy kézzelfogható, saját kezűleg futtatott kvantumprogramod — a korábbi beszélgetésben leírt 1. lépés. Ne menj tovább, amíg ez nem megy stabilan, többször lefuttatva is ugyanazt az eredményt adja.

---

## Fázis 2 — Egyszeri futtatás valódi IBM-hardveren

**Cél:** Ugyanaz a VQE-kód, de most a szimulátor helyett egy valódi IBM QPU-ra küldve, egyetlen, manuálisan indított futtatással.

**Feladatok:**
- `src/backend_selector.py` — egy kapcsoló, amivel a `run_vqe()` függvény vagy `AerSimulator`-t, vagy valódi `QiskitRuntimeService` backendet használ.
- IBM API-token kezelése: Docker `secrets` vagy `.env` fájl (soha nem kerül a repóba).
- Egyszeri, manuális futtatás egy kis, elérhető backenden.

**Elfogadási kritérium (teszt):**
- A futás sikeresen visszaad egy energiaértéket (nem hibával áll el).
- Az eredményt kézzel összeveted a Fázis 1 szimulált értékkel — dokumentált eltérés (pl. "+0.08 Hartree a zaj miatt").
- Ez itt még **nem automatikus teszt**, hanem egy manuálisan validált, dokumentált mérési jegyzőkönyv (lásd alább).

**Dokumentáció:** `docs/02_hardware_run.md` — a pontos backend neve, futás időpontja, kapott érték, eltérés a referenciától. Ez lesz az első "mérési napló" bejegyzésed, ami később a `data/` réteg formátumát is meghatározza.

**Miért itt állunk meg:** Ez a korábbi 2. lépés. Itt láthatod először a saját szemeddel a zaj hatását — ha ez az érték irreálisan nagy (pl. teljesen véletlenszerű), előbb ezt kell megérteni, mielőtt hibaenyhítést adnál hozzá.

---

## Fázis 3 — Mitiq hibaenyhítés hozzáadása ugyanerre a futtatásra

**Cél:** A Fázis 2 futtatás megismétlése zero-noise extrapolációval (ZNE), és az eredmény összevetése.

**Feladatok:**
- `mitiq` hozzáadása a függőségekhez.
- `src/mitigation.py` — a `run_vqe()` kimenetét becsomagolja Mitiq ZNE-vel (több zajszinten futtatja, extrapolál).
- Ugyanazon backenden, ugyanabban az időablakban lefuttatva, hogy a kalibráció összehasonlítható legyen.

**Elfogadási kritérium (teszt):**
- Három érték egymás mellett dokumentálva: szimulált (referencia), nyers hardver, mitigált hardver.
- Manuális ellenőrzés: a mitigált érték **közelebb van-e** a referenciához, mint a nyers.
- Ha nem közelít — ez is érvényes, dokumentálandó eredmény, nem hiba (a valós kutatásban ez gyakori tanulság).

**Dokumentáció:** `docs/03_mitigation_test.md` — táblázat a három értékkel, és egy rövid `matplotlib` sávdiagram (ez az első vizuális elem, amit a projekt generál).

**Miért itt állunk meg:** Ez a korábbi 3. lépés. Ha ez a három elem (szimulátor, nyers hardver, mitigált hardver) egyetlen molekulára, egyetlen futtatásra stabilan és érthetően működik, a projekt "kvantum-magja" készen áll. Innentől már csak sokszorosítás és infrastruktúra következik — nem új kvantumfizika.

---

## Fázis 4 — Adatséma és perzisztens tárolás

**Cél:** A korábbi manuális "mérési naplók" helyett strukturált, gépileg feldolgozható tárolás.

**Feladatok:**
- Séma rögzítése (pl. SQLite tábla vagy CSV oszloplista):
  `molekula, kötéshossz, backend, szimulátor_e, hibaenyhítés_típusa, nyers_energia, mitigált_energia, referencia_energia, futás_időpontja, qiskit_verzió, mitiq_verzió, qpu_idő_mp, shot_szám`
- `src/storage.py` — egy `save_result(record)` és `load_results()` függvénypár.
- A Fázis 1-3 eredményeit visszamenőleg betöltöd ebbe a formátumba (kézzel, egyszer).

**Elfogadási kritérium (teszt):**
- `pytest tests/test_storage.py` — egy teszt-rekord mentése és visszaolvasása bit-pontosan egyezik.
- A Fázis 3 három mérési eredménye visszakeresve megjelenik a táblában.

**Dokumentáció:** `docs/04_data_schema.md` — a séma pontos leírása, mezőnkénti magyarázat, egy minta-sor.

---

## Fázis 5 — Sokszorosítás: több molekula, több paraméter

**Cél:** A Fázis 1-3 logikáját általánosítani, hogy több molekulára és kötéshosszra automatikusan lefusson.

**Feladatok:**
- `src/experiment_runner.py` — egy konfigurációs lista (molekula + kötéshossz-tartomány + backend-lista + hibaenyhítési módszer-lista) alapján sorban lefuttatja az összes kombinációt, és menti az eredményeket a Fázis 4 tárolóba.
- Kezdetben csak szimulátoron, kis kombinációs mátrixon (pl. H2, 5 kötéshossz-érték) — ez még nem terheli az IBM-kvótát.

**Elfogadási kritérium (teszt):**
- A futás után a tárolt adatbázisban pontosan N sor van (ahol N a kombinációk száma), mindegyik érvényes energiaértékkel.
- Egy gyors `matplotlib` disszociációs görbe (energia vs. kötéshossz) generálódik, és vizuálisan U-alakot mutat (a helyes kémiai viselkedés).

**Dokumentáció:** `docs/05_batch_runs.md` — hogyan kell egy új konfigurációt hozzáadni, mennyi ideig tart egy batch futás.

---

## Fázis 6 — Automatizálás és ütemezés

**Cél:** A gyűjtés emberi beavatkozás nélkül, rendszeresen fusson.

**Feladatok:**
- `docker/docker-compose.yml` egy `scheduler` szolgáltatással (pl. `cron` a konténerben, vagy GitHub Actions, ha a hardveres futtatás oda kerül).
- IBM API-token biztonságos kezelése CI-titkosításban.
- Hibakezelés: ha egy backend nem elérhető vagy a job hibára fut, a rendszer ezt is elmenti (nem áll el csendben).

**Elfogadási kritérium (teszt):**
- Egy manuálisan indított "dry run" a teljes automatizált pipeline-t végigfuttatja hiba nélkül, egy szimulált backenden.
- Egy szimulált hibás eset (pl. rossz backend név) esetén a rendszer naplózza a hibát, és nem omlik össze.

**Dokumentáció:** `docs/06_automation.md` — az ütemezés logikája, hibakezelési stratégia.

---

## Fázis 7 — Dashboard (bemutatási réteg)

**Cél:** A Fázis 4-es tárolóból élő, interaktív vizualizáció.

**Feladatok (belső lépésekre bontva, egyenként tesztelve):**
1. Statikus adatbeolvasás Streamlitben — csak egy táblázat megjelenítése. *(Teszt: az app elindul, a táblázat helyesen jelenik meg.)*
2. Disszociációs görbe interaktív megjelenítése molekula-választóval. *(Teszt: molekulát váltva a grafikon frissül.)*
3. Módszer-összehasonlító sávdiagram (nyers vs. mitigált vs. referencia). *(Teszt: a három sáv helyes értékeket mutat egy ismert teszt-rekordra.)*
4. Volumetrikus/hőtérkép nézet a körméret vs. sikeresség összefüggésre. *(Teszt: legalább egy backend, egy molekula adatával helyesen színez.)*

**Elfogadási kritérium (teszt):**
Mind a négy belső lépés önállóan, egymást követően fut és validálható — a dashboard fázis nem "egyben" készül el, hanem inkrementálisan.

**Dokumentáció:** `docs/07_dashboard.md` — képernyőképek, a nézetek magyarázata.

---

## Fázis 8 — Teljes konténerizáció összeszerelése

**Cél:** Minden korábbi darab egyetlen `docker-compose` rendszerben, egymástól elszigetelt szolgáltatásokként.

**Feladatok:**
- `app` (kvantumfuttató), `scheduler` (automatizálás), `dashboard` (Streamlit), opcionálisan `db` (ha SQLite helyett valódi adatbázisra váltasz) — külön konténerek, közös volume a `data/` mappához.
- `docker-compose up` egyetlen paranccsal elindítja az egész rendszert.

**Elfogadási kritérium (teszt):**
Tiszta gépen (vagy tiszta VM-en) `git clone` + `docker-compose up` után a dashboard elérhető a böngészőből, és megjeleníti a korábban gyűjtött adatokat.

**Dokumentáció:** `docs/08_deployment.md` — telepítési útmutató lépésről lépésre, ez lesz a README fő telepítési szakasza is.

---

## Fázis 9 — Dokumentáció, validálás, publikálás

**Cél:** A projekt közösségi szintre emelése.

**Feladatok:**
- Teljes `README.md`: probléma leírása, gyors indítás, példa kimenet/screenshot, licenc, hivatkozás.
- Zenodo-integráció bekapcsolása, első GitHub Release kiadása → DOI generálása.
- Verzióinformációk (Qiskit, Mitiq, Python) rögzítve a `requirements.txt`-ben és a dokumentációban a reprodukálhatóság miatt.

**Elfogadási kritérium (teszt):**
Egy külső személy (vagy te, egy másik gépen) kizárólag a README alapján, segítség nélkül fel tudja telepíteni és futtatni a rendszert.

**Dokumentáció:** Ez maga a fázis eredménye — a végleges README és a Zenodo DOI.

---

## Fázis 10 — Közösségi visszacsatolás és iteráció

**Cél:** A projekt nyílt beágyazása a meglévő ökoszisztémába.

**Feladatok:**
- Bejelentés QOSF/Unitary Fund/r-QuantumComputing közösségekben.
- Esetleges beküldés a Metriq platformra automatizált pipeline-nal.
- Visszajelzések alapján új fázis-ciklus indítása (pl. új molekula, új hibaenyhítési módszer) — ugyanazzal a lépcsőzetes, tesztelt logikával, mint Fázis 1-9.

---

## Összefoglaló táblázat — fázisok és elfogadási kritériumok

| Fázis | Fő kimenet | Elfogadási kritérium |
|---|---|---|
| 0 | Repó + Docker alap | `docker build` sikeres |
| 1 | H2-VQE szimulátoron | Automatikus teszt: energia ≈ -1.137 Hartree |
| 2 | Egyszeri valódi hardver futás | Dokumentált, kézzel validált eltérés |
| 3 | Mitiq hibaenyhítés | Dokumentált három-érték összehasonlítás |
| 4 | Adatséma + tárolás | Automatikus teszt: mentés/visszaolvasás egyezik |
| 5 | Batch futtatás | N sor a tárolóban, helyes disszociációs görbe |
| 6 | Automatizálás | Dry run hiba nélkül, hibakezelés tesztelve |
| 7 | Dashboard | 4 belső lépés egyenként validálva |
| 8 | Teljes konténerizáció | Tiszta gépen egy paranccsal elindul |
| 9 | Dokumentáció + publikálás | Külső fél README alapján telepíti |
| 10 | Közösségi iteráció | Visszajelzés alapján új ciklus |

## Alapelvek, amikre minden fázisnál figyelni kell

- Soha ne lépj a következő fázisra, amíg az aktuális elfogadási kritérium nem teljesül dokumentáltan.
- Minden fázis végén legyen egy rövid `.md` fájl a `docs/` mappában — ez folyamatosan épül, nem a végén egyszerre.
- A valódi IBM-hardvert csak a Fázis 2-3-ban és a Fázis 6 "dry run" utáni éles futtatásoknál használd — a kvóta védelme érdekében minden más fázis szimulátoron fejlesztendő és tesztelendő.
- Verziószámokat (Qiskit, Mitiq, Python) rögzítsd minden fázis dokumentációjában, mert a kvantum-szoftverstack gyorsan változik, és ez a reprodukálhatóság alapja.
