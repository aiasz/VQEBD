# Változásnapló

A projekt minden lényeges változása ebben a fájlban szerepel.

A formátum a [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) ajánlást
követi, a verziózás a [Semantic Versioning 2.0.0](https://semver.org/) szerint történik.
A `MINOR` verzió minden lezárt projektfázisnál lép
(lásd [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md), 8.1).

---

## [Unreleased] — Nem kiadott

### Hozzáadva
- **Zenodo DOI** a `v1.0.0` kiadáshoz: koncepció-DOI [`10.5281/zenodo.23886002`](https://doi.org/10.5281/zenodo.23886002) (a projekt minden verziójára), verzió-DOI [`10.5281/zenodo.23886003`](https://doi.org/10.5281/zenodo.23886003) (a `v1.0.0` pillanatképe). A `CITATION.cff` (`doi`, `identifiers`) és a README (jelvény, hivatkozási blokk, HU és EN) tartalmazza. A Zenodo-rekord szerzője: Kormos, Attila; licenc: MIT.

- **MI-felhasználási nyilatkozat** ([`AI_DISCLOSURE.md`](AI_DISCLOSURE.md), HU/EN): pontosan rögzíti, hogy a projekt MI-vel készített kísérlet, ki mit végzett, mely modellek (a commitok `Co-Authored-By` sorai alapján), mi **nem** ellenőrzött (nincs független lektorálás és replikáció), a dokumentált MI-hibákat, és cikkbe szánt szövegjavaslatot. Jelölve: README (HU/EN banner és szakasz), `CITATION.cff` (`message`, `abstract`), `docs/09_publishing.md` (kötelező ellenőrzőpont).
- **Szakirodalmi pozicionálás** ([`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)): a hasonló VQE- és hibaenyhítési benchmarkok áttekintése, nyíltan **nem szisztematikus** (S1–S6 korlátok), kivonat- és metaadat-szinten. Megállapítás: a VQEBD módszerei ismertek; a kiválasztási torzítás, a lövésszám-függő optimalizáló-sorrend és a kiolvasási hibaenyhítés haszna független forrásokkal egyező; nyitott kérdésnek *látszik* a kalibrációból épített Heron-zajmodell validálása VQE-energián.
- **`docs/references.md` 1.2.0**: +20 gépileg DOI-validált tétel (összesen 59, ebből 57 DOI-validált); a `scripts/gen_references.py` bővítve.

- **Fázis 11 terve** ([`docs/plan/phase_11.md`](docs/plan/phase_11.md)): a kalibrációból épített Heron-zajmodell validálása; előzetes (felderítő) mérés kvóta nélkül (a kiolvasást modellező becslő mind az 5 meglévő hardveres nyers ponttal \|z\| < 2 egyezést ad); előre kimondott hipotézisek és döntési szabályok; a hardveres mérések blokkokra darabolva a 600 s / 28 napos keretbe (az 1. ablakban ~388 s ≤ 480 s). **Jóváhagyásra vár, hardveres futtatás nem történt.**

### Módosítva
- A **GitHub Release `v1.0.0` jegyzete** (2026-11-02) az MI-jelölést a legelső bekezdésben tartalmazza (HU/EN, az `AI_DISCLOSURE.md`-re hivatkozva). A **Zenodo-rekord (`10.5281/zenodo.23886003`) leírását** a szerző ugyanezzel a jelöléssel egészítette ki (2026-11-02; a leírás elején HU/EN, a régi szöveg változatlan; a rekord szerzőlistája változatlanul csak Kormos Attila). Új verzió-DOI nem készült.

### Tervezett
- **K8** — a qsim platformtűrés méret-függő pontosítása (több mérési pont után).
- **D3** — szimulátoros GitHub Actions ütemezés.
- Külön, kisebb dashboard-image; a körméret (és CX-szám) tárolása (séma v4); platformonkénti bontás a dashboardon;
  böngészős képernyőképek; telepítés másik gépen vagy VM-en; valódi, független külső telepítési próba.
- **Fázis 10** — közösségi visszacsatolás (bejelentések, Metriq-beküldés, új ciklusok).

---

## [1.0.0] — 2026-11-02

**Fázis 9 — dokumentáció, validálás, publikálás: az első publikált kiadás.**

A Fázis 0–9 lezárult. A rendszer háromplatformos VQE-mag, öt referenciaszinttel (egzakt, véges lövésszám, zajmodell,
valódi IBM QPU, ISA-szintű ZNE), sémaverziózott tárolással, batch-motorral és statisztikával, hibatárolással és
ütemezővel, böngészős dashboarddal és konténeres rendszerrel. Terv: [`phase_09.md`](docs/plan/phase_09.md);
útmutató a kiadáshoz: [`docs/09_publishing.md`](docs/09_publishing.md); jegyzőkönyv:
[`TR-F09`](docs/testing/TR-F09_publikalas.md).

**Mit jelent az 1.0?** A rendszer reprodukálható és dokumentált; nem azt, hogy minden fizikai kérdés lezárult. Az ismert
korlátok nyíltan szerepelnek a jegyzőkönyvekben: zajos szimulációban egyik konfiguráció sem éri el a kémiai pontosságot
(`TR-F05`); a hardveres görbén csak egy pont egyeztethető vele (`TR-F05` 7.); a dashboardhoz nincs böngészős vizuális
ellenőrzés (`TR-F07`).

### Hozzáadva
- **Szabványos MIT `LICENSE`** és külön **`NOTICE`** a harmadik felekről és a Mitiq (GPL-3.0) megjegyzésről.
- **`CONTRIBUTING.md`**, **`SECURITY.md`**, GitHub issue-sablonok (hiba, javaslat).
- **README:** „Röviden" / „In short" bejárat (probléma, háromparancsos gyors indítás, példa kimenet), CI-jelvény,
  a kulcsverziók táblázata (a lockkal teszttel egyeztetve), hivatkozási blokk BibTeX-szel, a licenc/biztonság/
  közreműködés szakaszok frissítve.
- **`CITATION.cff`:** kétnyelvű (angol és magyar) leírás; egyetlen szerző (Kormos Attila), ez lesz a Zenodo-rekord szerzői
  listája (felhasználói döntés). A BibTeX-bejegyzés ezzel egyezik.
- **`docs/09_publishing.md`:** kiadási ellenőrzőlista, a Zenodo-integráció és a DOI beírásának lépései.
- **`tests/repo/test_publication.py`** (védőtesztek): a licenc a szabványos MIT, a `NOTICE` tartalma, a közösségi fájlok,
  a README bejárata és a verziótáblázat↔lock egyezése, minden relatív Markdown-hivatkozás létezik, a `CITATION.cff`
  és a BibTeX a `VERSION`-nel és a `CHANGELOG` dátumával konzisztens.

### Javítva
- **A GitHub CI a v0.9.0 óta piros volt.** Az ok a Fázis 6-ban írt `test_compose_defines_a_simulator_only_scheduler_service`,
  amely a `docker-compose.yml`-t a fájl helyéből számolt útvonalon olvasta; a szállított image-ben (mount nélkül) nincs
  `docker/` mappa. Helyben mindig bind-mountolt repóval futottam, ezért nem tűnt fel. A teszt a `repo_root` fixture-t
  használja (a szállított image-ben kihagyódik); mindkét CI-tesztlépés helyben reprodukálva és zöld.
- **A GitHub nem ismerte fel a licencet** (`other`), mert a `LICENSE` a szabványos MIT-szöveg után harmadik-fél-függeléket
  is tartalmazott. A függelék a `NOTICE`-ba költözött; a `LICENSE` szabványos MIT.

### Mért
- A `CITATION.cff` érvényes (`cffconvert --validate`, CFF 1.2.0).
- A tiszta klónból, a README parancsait szó szerint követve a build, a példafuttatás és a dashboard működik (`TR-F09` 3.).

### Ismert korlátok
- A README-alapú telepítést az asszisztens próbálta egy tiszta klónon, **ugyanazon a gépen**; független külső személy
  próbája nem volt.
- A Zenodo-integrációt a felhasználónak kell bekapcsolnia a release előtt; a DOI a release után kerül a `CITATION.cff`-be
  és a README-ba (`docs/09_publishing.md` 5.).

---

## [0.11.0] — 2026-11-02

**Fázis 8 — konténeres rendszer, a dashboard egyparancsos indítása a saját gépen.**

A fázis lezárult: mind a 10 elfogadási kritérium teljesült ([`TR-F08`](docs/testing/TR-F08_konteneres_rendszer.md));
772 teszt, ebből 771 sikeres és 1 kihagyott (TC-302, `mitiq` nélkül). Terv: [`phase_08.md`](docs/plan/phase_08.md).

### Hozzáadva
- **`dashboard` Compose-szolgáltatás:** `docker compose -f docker/docker-compose.yml up -d --build dashboard`
  (vagy `make dashboard`), utána <http://localhost:8501>. A port **csak a gazdagép hurokcímére** (`127.0.0.1`) kötött,
  mert a dashboardnak nincs hitelesítése (`VQEBD_DASHBOARD_PORT`-tal módosítható); healthcheck; csak olvasható kód- és
  export-mount; token, `env_file` és hardverengedély nélkül.
- `make dashboard`, `make dashboard-stop`, `make dashboard-logs`.
- `tests/repo/test_compose.py` (9 teszt): a Compose-fájl épsége, loopback-port, titok- és hardvermentesség, csak olvasó mountok.
- Dokumentumok: `phase_08.md`, `TP-F08`, `TR-F08`, `docs/08_deployment.md` (indítás, adatbetöltés, biztonság, eltávolítás,
  hibaelhárítás, a távoli hoszt követelményei).

### Változott
- **Minden README és dokumentum átvilágítva** (TR-F08 3.): Fázis 8 állapot, `Gyors indítás`, dokumentumtáblák, verziók,
  tesztszámok; a `00_setup.md` és a `phase_05_allapot.md` történetiként/archívként jelölve; a `07_dashboard.md` indítása
  Compose-szal; a `06_automation.md` kiegészítve a közös volume-mal.
- Mindhárom Compose-szolgáltatás image-címkéje `vqebd:0.11.0`.

### Mért
- **Tiszta klónból, gyorsítótár nélkül** épített image `pip freeze`-e a lockkal **0 eltérés** (101 / 101).
- A futó dashboard-konténer **~66 MiB RAM**, 0.6% CPU üresjáratban; az image 2.19 GB.
- A konténerben a dashboard 4 adatforrást talál (az ütemező adatbázisa és a verziózott exportok: 5 / 50 / 180 / 8 sor), mind a
  négy nézet kivétel nélkül fut; a kód- és export-mountok csak olvashatók.
- **Pontosítás:** a dashboard az adatot nem módosítja, de egy WAL módú adatbázis olvasásakor az SQLite `-shm` / `-wal`
  segédfájlt hozhat létre; ezért a `vqebd-data` volume nem `:ro`. A korábbi „nem ír" ezzel a megkötéssel értendő.

### Ismert korlátok
- A „tiszta gép" ugyanaz a gép volt (másik gépen vagy VM-en nem próbáltuk); külön Linux/macOS-teszt nincs.
- Hosszú távú futást és a `restart: unless-stopped` Docker-újraindítás utáni viselkedését nem mértük.
- Egy image mindhárom szolgáltatáshoz (2.19 GB); nincs hitelesítés, a védelem a hurokcím-kötés.

---

## [0.10.0] — 2026-11-02

**Fázis 7 — dashboard, és a `requirements.lock` betartatása a buildben.**

A fázis lezárult: mind a 12 elfogadási kritérium teljesült ([`TR-F07`](docs/testing/TR-F07_dashboard.md));
763 teszt, ebből 762 sikeres és 1 kihagyott (TC-302, `mitiq` nélkül). Terv: [`phase_07.md`](docs/plan/phase_07.md),
döntés: ADR-0009.

### Hozzáadva
- **`vqebd.dashboard`:** `data` (három forrás — SQLite, batch-export, teljes rekordlista — egy normalizált
  táblába; levezetett `error_mha`, `method`, `chemically_accurate`, `active_space`, `n_qubits`;
  `method_comparison_table`, `size_success_table`), `figures` (`dissociation_figure`,
  `method_comparison_figure`, `heatmap_figure`), `app` (Streamlit, vékony) és a `dashboard/app.py` belépő.
- **Négy nézet:** táblázat és hibák (7.1), disszociációs görbe molekulaválasztóval (7.2), módszer-
  összehasonlító sávdiagram (7.3), körméret × módszer hőtérkép (7.4); mindegyik külön commit.
- `requirements-dashboard.txt`: `streamlit` 1.59.1, `plotly` 7.1.0, `pyarrow` 24.0.0.
- 121 új teszt (köztük a TR-F05 közölt értékeivel való keresztvalidáció és a `pyarrow`-őr).
- Dokumentumok: `phase_07.md`, `ADR-0009`, `TP-F07`, `TR-F07`, `docs/07_dashboard.md`.

### Változott
- **A Docker-build a `requirements.lock`-ot kényszerként használja** (`pip install … -c requirements.lock`,
  a `pip`/`setuptools`/`wheel` is a lockból). Mért: a korábbi build a 71 lockolt csomagból 21-ben eltért;
  mostantól 101 / 101, 0 eltérés. A 71 régi csomag bitre változatlan, +30 dashboard-csomag.
- `docker/Dockerfile`: a `dashboard/` mappa is bekerül az image-be.
- `mypy`: a `pandas` és a `plotly` hiányzó típusstubját a konfiguráció kezeli.

### Mért
- **Rejtett függőségi ütközés:** a Streamlit `pyarrow 26.0.0`-t húz, amely NumPy ≥ 2-t követel; az
  `st.dataframe` a `numpy 1.26.4` mellett futásidőben elbukik, a pip feloldója nem jelzi.
- **A `pyarrow 25.0.0` szegmentációs hibával omlik össze** (exit 139), ha egy script-futásban `st.dataframe`
  fut, és a következő futás `pyarrow.compute`-ot hív (a Streamlit minden futást új szálban végez). A 16.1.0 …
  24.0.0 rendben van; a pin 24.0.0. Valószínű ok (nem bizonyított): a `mimalloc` memóriakezelő.
- A (2e,3o) terek **4 qubitesek** (H₂ 2, LiH (2e,5o) 8, BeH₂ (4e,6o) 10; parity, kétqubites redukció).
- Az adatbázis **nem tárolja a körméretet** (`metadata_json` üres); a dashboard levezeti.

### Javítva
- **A `pyarrow==25.0.0` pin (d237885) hibás volt:** az első próba csak táblát hozott létre, a szálváltást nem
  tesztelte. A 7.2 lépés `AppTest`-je tárta fel; javítva 24.0.0-ra (`55b6f87`), negatív kontrollal igazolt
  védőtesztel (`test_dashboard_pyarrow_guard.py`: 25.0.0 mellett elbukik, 24.0.0 mellett átmegy).
- `docs/05_batch.md`: a minimális (2e,3o) terek qubitszáma **4**, nem 6 (a pályaszám kétszerese szerepelt).

### Ismert korlátok
- **Nincs vizuális ellenőrzés:** az `AppTest` a JS-ben renderelt Plotly-t nem futtatja; képernyőkép nincs.
- A három egzakt platform (Qiskit, Cirq, qsim) a dashboardon egy `egzakt` címke alatt átlagolódik.
- A batch-exportokon a körméret mindig feltételezett (nincs `mapper`/`basis`), ezt a felület jelzi.
- A `dashboard` Compose-szolgáltatás a Fázis 8 feladata.

---

## [0.9.0] — 2026-11-02

**Fázis 6 — automatizálás, strukturált hibatárolás, újrapróbálkozás, ütemezés.**

A fázis lezárult: mind a 11 elfogadási kritérium teljesült
([`TR-F06`](docs/testing/TR-F06_automatizalas.md)); 642 teszt, ebből 641 sikeres és 1 kihagyott
(TC-302, `mitiq` nélkül). Terv: [`phase_06.md`](docs/plan/phase_06.md), döntés: ADR-0008.

### Hozzáadva
- **Séma v3:** `run_failures` tábla (append-only), v1 → v2 → v3 automatikus migráció; a `results` tábla
  nem változik.
- **`vqebd.pipeline`:** `classify` (kvóta / átmeneti / tartós, ismeretlen = tartós), `scrub_secrets`
  (token, CRN, API-kulcs alakú sorozatok), `RetryPolicy` és `run_with_retry` (korlátos, exponenciális,
  jitter nélküli visszalépés; a próbálkozásszám az adatbázisban tartósított), `run_pipeline`
  (előellenőrzés → batch → export → összegzés, JSON-soros napló, kilépési kódok 0/1/2).
- **`vqebd.scheduler`:** intervallum-hurok és átfedés elleni zárfájl (időalapú elavulással; PID-ellenőrzés
  nélkül, mert Windowson az `os.kill(pid, 0)` megszüntetné a folyamatot).
- **`scheduler` compose-szolgáltatás:** csak szimulátor, token nélkül.
- **`scripts/run_pipeline.py`** (`--retry-abandoned`, `--max-attempts`, `--allow-hardware`);
  **`vqebd.batch.export`** (a `run_batch.py` és a pipeline közös exportja, a formátum változatlan).
- **Hardveres védelem:** `hardware_evaluation_budget`; batch szintű kvótakapu (+20% tartalék) a
  pipeline előellenőrzésében.
- Dokumentumok: `phase_06.md`, `ADR-0008`, `TP-F06`, `TR-F06`, `docs/06_automation.md`, séma v3 a
  `docs/04_data_schema.md`-ben.

### Változott
- `run_batch`: új `retry`, `hardware_max_attempts`, `sleep` paraméter; a hibák a `run_failures`-be
  kerülnek; a `BatchReport` új `abandoned` mezője. `retry` nélkül a viselkedés a Fázis 5-tel azonos.
- `scripts/run_batch.py`: az exportot a közös `vqebd.batch.export` írja.

### Mért
- **A Fázis 5 batch hibái nem maradtak meg** (előmérés): a hiba csak a memóriában és a naplóban élt.
- **A rossz backendnév már a `BatchCell` konstruktorában elbukik** (`KeyError`), a batch futása előtt.
- **Konténeres futás** (`docker compose run scheduler`): `f5-smoke` 5 új futás, kilépési kód 0; a volume
  jogosultsága rendben.

### Ismert korlátok
- Az `transient` szabályok **feltevések**: valódi IBM-hibával nem erősítettük meg (TR-F06, L1).
- Az ütemezési hurkot valós alvással, hosszan nem futtattuk; az `--every` logikát injektált órával
  teszteltük (TR-F06, L3).
- Nincs értesítés hibáról.

---

## [0.8.1] — 2026-11-02

**Kvótavédelem a hardveres VQE-útvonalon (K7) és a hardveres H₂ görbe (5.H).**
Nincs séma- vagy API-törés; a szimulátoros útvonal számítása nem változott. Tesztkészlet: 537 teszt, 536 sikeres, 1 kihagyott (TC-302, `mitiq` nélkül).

### Hozzáadva
- **Fázis 5.H — H₂ disszociációs görbe valódi QPU-n** (`ibm_kingston`, 5 geometria,
  8192 lövés, θ* a zajmentes optimumból; 2 job, **57 QPU-s** a 600 s-ból).
  Nyers hiba +12 … +28 mHa; TREX-szel +5 … +18 mHa, az R = 1.5 Å pontban
  −0.68 ± 2.52 mHa. A hardver a görbén nem éri el a kémiai pontosságot.
  Pontonként egyetlen futás; a hibasáv drift nélküli. Adat:
  `docs/figures/data/hardware_h2_pes.json`; ábra: `fig10_hardver_pes.png`;
  jegyzőkönyv: TR-F05 7. pont, TR-F02 2. kiegészítés.

### Mért
- **K8 — a qsim-eltérés oka (LiH (2e,5o), 1.595 Å):** a Powell `complex128`
  Qiskit-en 4309 kiértékelés után 9·10⁻¹² Ha-ra konvergál, a qsim (`complex64`)
  7178 kiértékelés után 2.8·10⁻⁵ Ha-nál áll meg. Az ok tehát a `complex64`
  aritmetika, nem az optimalizáló. Egyetlen mérési pont: a 10⁻⁵ Ha tűrést nem
  módosítottuk (TR-F05 3.2).

### Javítva
- **K7 — kvótavédelem a hardveres VQE-útvonalon.** A `run_vqe` (és a
  `python -m vqebd --backend ibm_qpu`) korábban engedély és kvótaellenőrzés nélkül,
  korlátlan számú jobot küldhetett be; ez fogyasztotta el a 2026-09-23-i keretet
  (42 job × 15 QPU-s). Mostantól: (1) `VQEBD_ALLOW_HARDWARE=true` kell, hálózati
  hívás előtt; (2) a kvóta lekérdezése, és megtagadás, ha a legrosszabb eset
  (`maxiter` + végső becslések, ZNE-nél a zajszorzókkal szorozva, × 15 s) nem fér
  bele; (3) kemény kiértékelési keret (`EnergyEvaluator.max_calls`): az
  optimalizáló a fedezett számnál több jobot nem indíthat
  (`EvaluationBudgetExceededError`). Új: `vqebd.hardware.guard_hardware_vqe`.
  A CLI a `PermissionError`-t is `HIBA:` üzenetként, 2-es kilépési kóddal adja.
  **Következmény:** az alapértelmezett `--maxiter 300` hardveren elutasításra kerül
  (300 × 15 s > 600 s); a hardveres futáshoz kis `--maxiter` kell.
  Tesztek: `tests/unit/test_hardware_guard.py` (7 új).

---

## [0.8.0] — 2026-11-02

**Fázis 5 — batch-futtatás, aktív tér, ismétlésen alapuló statisztika.**

A fázis lezárult: mind a 10 elfogadási kritérium teljesült
([`TR-F05`](docs/testing/TR-F05_batch.md)); 529 teszt, ebből 528 sikeres és 1
kihagyott (TC-302, a `mitiq` nélkül). A hardveres H₂ PES (5.H) **nem** része a
kiadásnak; a v0.8.1-ben pótolva.

### Hozzáadva
- **Aktív tér:** `ActiveSpaceSpec`, `energy_offset` (magtaszítás + inaktív energia),
  L0′ CASCI-referencia (PySCF). L1 ↔ CASCI ≤ 4·10⁻¹⁴ Ha. A mért választás a
  frozen core: LiH (2e,5o) 0.23 mHa, BeH₂ (4e,6o) 0.34 mHa csonkolással
  (`phase_05.md` 2.).
- **`vqebd.stats`:** Student-t alapú CI, négyállapotú kémiai pontossági
  besorolás (`confirmed` / `consistent` / `excluded` / `undetermined`),
  blokkátlag-alapú SEM(N), hibaköltségvetés (ADR-0007).
- **`vqebd.batch`:** konfigurációs mátrix (preset-ek), determinisztikus `run_id`,
  folytatható és hibaizolált végrehajtás, csoportos aggregálás. CLI:
  `scripts/run_batch.py`.
- **Újramintavételezés** (`VQEConfig.reestimate`): K friss kiértékelés θ_opt-ban;
  a rekord tárolja az optimalizáló végértékét és az előzmény-minimumot is.
- **Adatséma v2** 11 új oszloppal, automatikus v1 → v2 migrációval.
- **Hardveres védőkorlátok** (`vqebd.hardware`): explicit engedély és
  **kvóta-előellenőrzés beküldés előtt**. `IBMQpuEnergyEvaluator.evaluate_observables`:
  több PUB egy jobban. `scripts/run_hardware_pes.py` (H₂ PES, `--dry-run`).
- **Ábrák:** `fig07_aktiv_ter`, `fig08_ismetles`, `fig09_hibakoltsegvetes`. A
  generátor új kapcsolója: `--replot`.
- `ADR-0007`, `phase_05.md`, `TP-F05`, **`TR-F05`**, **`docs/05_batch.md`**,
  `phase_05_allapot.md`; hivatkozásjegyzék 1.1.0 (+[student1908], +[wecker2015]).

### Mért
- **Statisztikai batch** (180 futás, `f5_statistical.json`): egyik zajos
  konfiguráció sem kémiailag pontos (mind `excluded`). A lövészajos H₂ hibája
  +11.6 ± 1.9 mHa, ez **optimalizálási** eredetű. A ZNE +38.2 → +11.5 mHa-re
  javít. A LiH (2e,3o) zajosan +466 mHa: az UCCSD mélységi fala.
- **Ismétlés (fig08):** SEM ∝ N^−½ (mért meredekség −0.48 … −0.55); a torzítás
  N-től független.
- **Valódi kiválasztási torzítás** (előzmény-minimum − friss átlag):
  −25.5 mHa (H₂), −30.8 mHa (LiH).
- **Determinisztikus batch** (50 futás, `f5_deterministic.json`): minden futás
  konvergált; a Qiskit és a Cirq frozen-core térben is 10⁻¹⁰–10⁻¹¹ Ha-ra egyezik.
  BeH₂ (4e,6o): L2 − CASCI = +0.371 mHa (UCCSD ansatz-hiba), a Full CI-hez
  +0.71 mHa, kémiai pontosságon belül.
- **K5 lezárva:** az optimalizáló végértéke az utolsó kiértékelés, torzítatlan
  minta θ_opt-ban. Független seeden a végérték − friss átlag −0.79 ± 0.62 mHa
  (lövészaj, 300 seed) és −1.05 ± 1.02 mHa (zajos, 100 seed). A batch +2.51 ±
  0.99 mHa-ja nem optimalizálói sajátosság; a cellák azonos seedkészletet
  használnak, így a 100 futás nem független.

### Változott
- `within_backend_tolerance` és `satisfies_variational_principle`: az L1-hez mér
  (`method_error`). Teljes térben ez numerikusan azonos a korábbival; aktív térben
  a csonkolás nem torzítja.
- `tests/repo/test_project_structure.py`: a `data/` teszt a git-követést és a
  `.gitignore`-szabályokat ellenőrzi, nem a futásidejű fájlok puszta létezését.

### Javítva
- **A v0.7.1 „kiválasztási torzítás” magyarázata téves volt** (TR-F01B 6.3,
  TR-F04, mesterterv R14, README). A SciPy COBYLA a végponti utolsó értéket adja
  vissza, nem az előzmény-minimumot. A −4.82 mHa-es L3a-érték ezért egyetlen
  zajos húzás (statisztikus), nem kiválasztás. A dokumentumok javítva, a mező
  neve `optimizer_final_ha` lett.
- `scripts/gen_references.py`: álnévnél (Student) nincs „Student, .” alak; a
  változásnapló és az online források ellenőrzési dátuma nem íródik felül.

### Ismert korlátok (nyitott)
- **K8 — qsim platformtűrés:** a LiH (2e,5o) 1.595 Å-nél a qsim (`complex64` +
  Powell) 2.8·10⁻⁵ Ha-val tér el a CASCI-tól, a névleges 10⁻⁵ Ha tűrés fölött
  (a kémiai pontosság 1.8%-a). Egyik teszt sem fedi; a TC-503 csak a (2e,3o)
  teret. Az ok (precízió vagy Powell-leállás) nincs szétmérve.
- **K7 — kvótavédelem hiánya** a `run_vqe` hardveres útvonalán (ez fogyasztotta el
  a 2026-09-23-i keretet).

### Elhalasztva
- **5.H — hardveres H₂ PES:** az IBM-kvóta kimerült (630/600 s), a kvóta-előellenőrzés
  megtagadta a beküldést, **job nem keletkezett**. A mérés a v0.8.1-ben futott le.

---

## [0.7.1] — 2026-09-25

**Javítókör a Fázis 5 előtt: a Fázis 1b–4 mérési láncának átvizsgálása.**

A v0.3.0 → v0.7.0 haladás átvizsgálása több olyan hibát tárt fel, amely a
korábban közölt számokat érinti. A **mérések (job, adatfájlok) nem változtak**, csak a
kiértékelésük és azok a kódrészek, amelyek hibásan mértek. A korábbi
CHANGELOG-bejegyzések történeti rögzítések, ezeket nem írtuk át. A javított
számok a TR-F01B 6., a TR-F02 v1.1.0, a TR-F03 v1.1.0 és a TR-F04 v1.1.0
dokumentumokban vannak.

### Javítva — mérési hibák

- **Aer-mintavétel (L3a/L3b):** az Aer `EstimatorV2` minden `run()`-nál
  `default_rng(seed_simulator)`-ból húzott, így rögzített seed mellett **minden
  kiértékelés ugyanazt a z·σ eltolást** kapta (+15.9 mHa). A „lövészaj” állandó
  torzítás volt, a VQE zajmentes felületet optimalizált. Most egzakt várható
  érték + saját, hívásonként továbblépő RNG (`_AerIsaEnergyEvaluator`); a futás
  továbbra is determinisztikus. Regressziós tesztek: TC-1B10 (×6).
- **ZNE hajtogatás (`zne_local`):** a logikai áramkör hajtogatását az
  `optimization_level=3` részben kiejtette (4/10/16 CX a 4/12/20 helyett). Most
  ISA-szintű hajtogatás, `level=0` fordítás, új `IsaEnergyEvaluator` alaposztály;
  `effective_scale_factors` metaadat. Regressziós teszt: TC-301b.
- **`zne_mitiq`:** sosem futott le (kötetlen paraméterek, `level=3` executor,
  annotációs típusfelismerés `from __future__ import annotations` mellett), és a
  `scaled_energies` mezőbe a nyers értéket ismételte. Mindhárom javítva; a
  keresztvalidáció (TC-302) most **CI-ben is fut**.
- **Hardveres kiértékelő (L5):** a `stds` eldobódott, a `resilience_level` implicit
  volt. Most a `last_std`, `last_ensemble_standard_error` és `last_metadata`
  rögzített, a `resilience_level` explicit (alapértelmezés 1 = a mért szerver-viselkedés).
- **Exponenciális extrapoláció:** hiba esetén csendben másodfokúra váltott
  „exponential” címkével. Most `RuntimeWarning` jelzi.
- **Export (L5-rekord):** `mitigation_strategy` `none` helyett `ibm_resilience_1`;
  a `satisfies_variational_principle` és a `correlation_recovered` számított (a
  v0.7.0 kézzel 1-et és 1.20-at írt).

### Javítva — dokumentáció

- **TR-F03 v1.1.0:** az 1.0.0 számai (+15.75 → +0.35 mHa ✅) a TR-000 spike-ból
  származtak. Újramérve: ZNE **torzítás** +0.23 mHa ✅ (Mitiq: +0.37 mHa), de egy
  8192 lövéses futás **szórása** 26 mHa. AC-3.4 indokoltan újrafogalmazva.
- **TR-F02 v1.1.0:** az L5 nem „nyers” (TREX); bizonytalanság ±12.5 mHa (ensemble
  SE) / ±53.3 mHa (`stds`); a −3.96 mHa 0.3σ-s ingadozás, nem a hardver
  hibaszintje. Adatútvonal javítva; kvóta: 15 QPU-s. A kalibráció a mérés
  időpontjára visszakérve.
- **TR-F01B, TR-F04, ADR-0003 (1. kiegészítés), `docs/01b`, `docs/02`, `docs/03`,
  mesterterv, `phase_03`:** javító jegyzetek.
- **README (HU/EN):** a két nyelvi rész újra szinkronban (az angol még a v0.6.0
  állapotot mutatta).

### Hozzáadva

- `requirements-mitiq.txt` (mitiq 0.47.0 + tabulate 0.10.0; mért hatás: `pip check` tiszta).
- `scripts/fetch_ibm_job.py` — tárolt IBM job visszaolvasása **QPU-kvóta nélkül**;
  konzisztencia-ellenőrzéssel pótolta a Fázis 2 hiányzó bizonytalansági adatait.
- `scripts/gen_report_figures.py --only <név>`; új `fig06_mitigacio` (torzítás +
  50 seedes szórás + L5 hibasávval).
- A `precision` paraméter az Aer-kiértékelőkön (`0.0` = egzakt zajos várható érték).
- A rekordok `versions_json` mezője a `vqebd` saját verzióját is tartalmazza.
- `pytest` `filterwarnings`: ~600 000 ismert külső elavulási figyelmeztetés
  célzott szűrése (üzenet + kibocsátó modul szerint).

### Mért, új modellezési korlátok (dokumentálva, nyitott tétel)

- Az Aer `EstimatorV2` a zajmodell **readout-hibáját nem alkalmazza**: csak
  readout-hibát tartalmazó modellel ⟨Z⟩ = 1.000, a Sampler-kontroll 20.3%.
- A zajos VQE végső energiája a zajos minimum **kiválasztási torzítását**
  hordozza: független újramintavételezés kell (Fázis 5).

### Tesztek

- **455 passed** (mitiq-kel) / **454 passed + 1 skipped** (nélküle), 3 figyelmeztetés;
  ruff, ruff format, mypy (strict) tiszta.

---

## [0.7.0] — 2026-09-23

**Fázis 4 lezárva — Adatséma és perzisztens tárolás (SQLite & FAIR export).**

A korábbi szöveges jegyzőkönyvek és adatszigetek helyett strukturált, FAIR-megfelelő
adattárolási réteg jött létre (ADR-0004):

### Hozzáadva

#### Adattárolási réteg (`vqebd.storage`)
- `Database` — SQLite adatbáziskezelő WAL móddal, típusos `CHECK` megszorításokkal, indexeléssel és sémaverziózással (`schema_version = 1`).
- `export_to_csv`, `export_to_json` — determinisztikusan rendezett CSV és JSON exportáló modul.
- `scripts/export_results.py` — történeti adatok automatikus migrációja és betöltése (8 reprezentatív futtatás: L0, L1, L2 Qiskit/Cirq/qsim, L3a, L3b, L4 ZNE Richardson/Exp, L5 IBM Heron QPU).
- `tests/unit/test_storage.py` — 8 új egység- és integrációs teszt (séma, WAL, beszúrás, szűrés, CSV determinizmus, megszorítások).

#### Dokumentáció
- `docs/04_data_schema.md`, `docs/plan/phase_04.md`, `TP-F04` és `TR-F04`.
- Exportált referenciaállományok: `docs/figures/data/results_v1.csv` és `results_v1.json`.

---

## [0.6.0] — 2026-09-23

**Fázis 3 lezárva — Hibaenyhítési stratégiák (ZNE & Mitiq) (L4).**

A VQEBD pluginalapú hibaenyhítési réteggel bővült (ADR-0003), amely Zero-Noise
Extrapolation (ZNE) segítségével sikeresen csökkenti a zajt és helyreállítja a
kémiai pontosságot:

### Hozzáadva

#### Hibaenyhítési réteg (`vqebd.mitigation`)
- `MitigationStrategy` protokoll és `MitigationResult` rekord.
- `ZneLocalMitigation` — saját, **ISA- és layout-biztos** globális unitáris áramkör-hajtogatás (`fold_global_unitary`, $\lambda \in \{1, 3, 5\}$).
- Extrapolációs modellek (`extrapolation.py`): Richardson (Lagrange $\lambda \to 0$), lineáris, másodfokú/polinomiális és exponenciális.
- `MitiqZneMitigation` — opcionális Mitiq ZNE referencia (GPL-3.0 izolált).
- `NoMitigation` — nyers referencia.
- CLI és konfiguráció: `--mitigation none | zne_local | zne_mitiq`, `--extrapolator richardson | linear | quadratic | exponential`.
- L4 szintű jelentés és szerializáció a `VQEResult` rekordokban.

#### Dokumentáció és tesztek
- `docs/03_mitigation_test.md`, `docs/plan/phase_03.md`, `TP-F03` és `TR-F03`.
- Új egység- és validációs tesztek: `test_folding.py`, `test_extrapolation.py`, `test_mitigation_strategies.py`, `test_mitigation_validation.py`.

### Mért eredmények (H2, STO-3G, FakeManilaV2)

| Módszer | Extrapolátor | Energia (Ha) | Hiba az L1-hez (mHa) | Kémiai pontosság |
|---|---|---|---|---|
| Referencia (L0/L1/L2) | — | −1.137306 | 0.00 | ✅ |
| **Nyers (L3b)** | — | −1.121556 | +15.75 | ❌ |
| **`zne_local` (L4)** | **Richardson** | **−1.136959** | **+0.35** | **✅ IGEN** |
| **`zne_local` (L4)** | **Exponenciális** | **−1.136965** | **+0.34** | **✅ IGEN** |
| **`zne_mitiq` (L4)** | **Richardson** | **−1.137885** | **−0.58** | **✅ IGEN** |

---

## [0.5.0] — 2026-09-23

**Fázis 2 lezárva — Valódi hardveres futtatás IBM Heron QPU-n (L5).**

Megtörtént az első éles fizikai kvantumprocesszoros mérés az IBM Quantum felhőben
üzemelő, 156-qubites `ibm_kingston` Heron QPU-n:

### Hozzáadva

#### Hardveres backend
- `vqebd.backends.estimators.IBMQpuEnergyEvaluator` — valódi IBM Quantum Heron QPU kiértékelő (L5 szint), 156-qubites ISA transzpilációval és `observable.apply_layout()` illesztéssel.
- Új backend azonosító: `ibm_qpu` a `vqebd.config.BackendKind` és `vqebd.platforms.PLATFORMS` nyilvántartásban (`requires_quota=True`).
- `scripts/run_hardware_vqe.py` — automatizált hardveres mérési szkript az L2-n megtalált optimális $\theta^*$ pont kiértékelésére és a nyers adatok mentésére.
- `tests/unit/test_hardware_evaluator.py` — kvótavédett egység- és mocktesztek (`@pytest.mark.hardware`).

#### Dokumentáció és tesztek
- `docs/02_hardware_run.md`, `docs/plan/phase_02.md`, `TP-F02` és `TR-F02`.
- Nyers hardveres mérési adatok: `data/raw/hardware_h2_kingston.json` (Job ID: `dapq25kak42c73cj1hu0`).

### Mért eredmények (H2, 0.735 Å, STO-3G, ibm_kingston Heron QPU)

| Szint | Backend | Mód | Energia (Ha) | Hiba az L0-hoz (Ha) |
|---|---|---|---|---|
| **L0** | PySCF Full CI | — | −1.1373060358 | 0.0 |
| **L1** | Egzakt diag. | — | −1.1373060358 | $+1.33 \times 10^{-15}$ |
| **L2** | `qiskit_statevector` | SLSQP | −1.1373060358 | $+1.49 \times 10^{-15}$ |
| **L3a** | `qiskit_aer_shot` | COBYLA (8192 shot) | −1.1213780162 | $+1.59 \times 10^{-2}$ |
| **L3b** | `qiskit_aer_noisy` | COBYLA (FakeManila) | −1.0938632143 | $+4.34 \times 10^{-2}$ |
| **L5** | **`ibm_kingston` (Heron QPU)** | **8192 shot (Job: dapq25...)** | **−1.1412691258** | **−3.963 × 10⁻³ (−3.96 mHa)** |

---

## [0.4.0] — 2026-09-23

**Fázis 1b lezárva — Véges lövésszámú és zajos szimuláció (L3a / L3b).**

A VQE referencialánc két új szimulációs szinttel bővült, amelyek elkülönítik a
véges mintavételi (shot) zajt és a valódi eszköz kalibrációs zaját
kvótamentes szimulációban:

### Hozzáadva

#### Zajos és véges mintavételi szimuláció
- `vqebd.backends.estimators.AerShotEnergyEvaluator` — L3a szint (Qiskit Aer, 8192 shot).
- `vqebd.backends.estimators.AerNoisyEnergyEvaluator` — L3b szint (`FakeManilaV2` 5-qubites kalibrációs zajmodell, T1/T2 relaxáció, kapu- és kiolvasási hibák).
- Automatikus ISA transzpiláció és `observable.apply_layout()` illesztés az 5-qubites eszköztopológiára.
- CLI: `--backend qiskit_aer_shot | qiskit_aer_noisy`.
- L3a / L3b címkék és ansatz+zaj hibabontás a `VQEResult.report()` kimenetben.

#### Platform- és optimalizáló-biztonság
- Új bejegyzések a `vqebd.platforms.PLATFORMS` nyilvántartásban `qiskit_aer_shot` és `qiskit_aer_noisy` backendekre.
- Gradiens-alapú optimalizálókra (pl. `SLSQP`) futásidejű `RuntimeWarning` figyelmeztetés lép életbe zajos célfüggvény esetén.

#### Dokumentáció és tesztek
- `docs/01b_noisy_simulation.md`, `docs/plan/phase_01b.md`, `TP-F01B` és `TR-F01B`.
- `tests/validation/test_noisy_simulation.py` — 19 új automatikus teszteset (TC-1B01–TC-1B09).

### Mért eredmények (H2, 0.735 Å, STO-3G)

| Szint | Backend | Optimalizáló | Energia (Ha) | Hiba az L1-hez (Ha) |
|---|---|---|---|---|
| **L0** | PySCF Full CI | — | −1.1373060358 | 0.0 |
| **L1** | Egzakt diag. | — | −1.1373060358 | $1.33 \times 10^{-15}$ |
| **L2** | `qiskit_statevector` | SLSQP | −1.1373060358 | $1.49 \times 10^{-15}$ |
| **L3a** | `qiskit_aer_shot` | COBYLA (8192 shot) | −1.1213780162 | $+1.59 \times 10^{-2}$ |
| **L3b** | `qiskit_aer_noisy` | COBYLA (FakeManila) | −1.0938632143 | $+4.34 \times 10^{-2}$ |

---

## [0.3.0] — 2026-09-22

**Fázis 1M lezárva — Többplatformos validáció (Qiskit ↔ Cirq ↔ qsim).**

Az alaptervhez képest **új fázis**. Indoka: egy benchmark, amelynek eredménye
egyetlen könyvtár sajátossága lehet, nem benchmark. A platform önálló
benchmark-dimenzióvá vált (ADR-0006).

### Hozzáadva

#### Második platform
- `cirq-core 1.4.1` és `qsimcirq 0.22.1` a stackben. Az újabb Cirq-ágak
  `numpy>=1.25`, illetve `numpy~=2.1` korlátja miatt kizárva; az 1.4.1 egyúttal
  a Mitiq `cirq-core<1.5.0` pinjével is kompatibilis (Fázis 3).
- `vqebd.platforms` — platform-metaadatok: számábrázolás, **mért zajszint**,
  tolerancia, gradiens-biztonság, ajánlott optimalizáló.
- `vqebd.backends.conversion` — Qiskit → Cirq konverzió (Hamilton-operátor és
  áramkör), **mátrixszinten validálva**.
- `vqebd.backends.cirq_estimators` — `CirqEnergyEvaluator`, `QsimEnergyEvaluator`.
- CLI: `--backend qiskit_statevector | cirq_simulator | qsim`.

#### IBM-hitelesítés (a Fázis 2 előkészítése)
- `vqebd.credentials` — token betöltése három forrásból (környezeti változó →
  `.env` → `IBM.token` JSON), **maszkolt `repr()`-rel**; a titok csak explicit
  `reveal()` hívással érhető el.
- `scripts/check_ibm_access.py` — **kvótamentes** hozzáférés-ellenőrzés
  (csak olvasás), fiókdiagnosztikával.

#### Vizualizáció
- `scripts/gen_report_figures.py` — 5 ábra a **tényleges mérési adatokból**,
  CVD-validált palettával. A nyers adatok `docs/figures/data/*.json`.

#### Dokumentáció
- `docs/01m_multiplatform.md` — **„Hozzájárul-e a több platform a pontossághoz?"**
  — a mért, őszinte válasz, azzal együtt, hogy mit **nem** ad.
- `docs/plan/phase_01m.md`, `docs/adr/ADR-0006`, `TP-F01M` + `TR-F01M`.

### Mért eredmények (H2, 0.735 Å, STO-3G)

| Platform | Optimalizáló | E (Ha) | Eltérés a Qiskittől |
|---|---|---|---|
| `qiskit_statevector` | SLSQP | −1.137306035753 | referencia |
| `cirq_simulator` | SLSQP | −1.137306035753 | **4.4 × 10⁻¹⁶** |
| `qsim` | Powell | −1.137306006762 | **2.9 × 10⁻⁸** |

Qubit-sorrend (endianness) mátrixszintű igazolása:
fordított sorrenddel `max|ΔM| = 0.00`, egyenessel **1.59**.

### A fázis legfontosabb felfedezése

**A gradiens-alapú optimalizálók csendben téves minimumot találnak egyszeres
pontosságú platformon.** A SciPy véges-differencia lépésköze
`√ε₆₄ ≈ 1.49 × 10⁻⁸`, a qsim célfüggvény-zaja viszont `1.13 × 10⁻⁷` — nagyobb a
lépésköznél, ezért a becsült gradiens zajból származik (**8 nagyságrend** hiba).

| Optimalizáló | Qiskit | Cirq | qsim |
|---|---|---|---|
| SLSQP (gradiens) | 9 × 10⁻¹⁵ | 9 × 10⁻¹⁵ | **1.5 × 10⁻² ✗** |
| TNC (gradiens) | 1 × 10⁻¹³ | 4 × 10⁻¹⁵ | **2.0 × 10⁻² ✗** |
| Powell (deriváltmentes) | 1 × 10⁻¹⁵ | 0 | **2.9 × 10⁻⁸ ✅** |

**Ez egyetlen platformon nem derülhetett volna ki**: Qiskiten és Cirqen mind a
nyolc optimalizáló hibátlan. A hibamód a Fázis 1b-ben vagy 2-ben bukkant volna
elő — ott viszont már IBM-kvótát égetve, „sikeresen konvergált" futásnak álcázva.

Beépítve: a `run_vqe()` futásidejű `RuntimeWarning`-ot ad a veszélyes
kombinációkra, és minden platformnak van **mért** ajánlott optimalizálója.

### Változott (törő)
- **`BackendKind` átnevezés:** `"statevector"` → `"qiskit_statevector"`.
  Indok: a platform nélküli név három egzakt szimulátor mellett félreérthető.
- A `VQEResult` új mezői: `platform`, `precision`, `backend_tolerance_ha`,
  és a `within_backend_tolerance` tulajdonság.

### Javítva
- **Commitolt merge-konfliktusok** a `.gitignore` és a `LICENSE` fájlokban (a
  távoli repó csatolása után). A titokvédelem sértetlen maradt — ellenőrizve:
  a token egyetlen commitban sem szerepel.
- **Nem reprodukálható teljesítmény-állítás:** egy korábbi, egyszeri mérés 24
  qubiten 22-szeres qsim-gyorsulást közölt. Ismételt méréssel (min-of-3) a valós
  tartomány **3.6–9.1×**. Minden dokumentum javítva.
- `mypy`: a Cirq implicit re-exportjaihoz célzott override — a saját kód
  ellenőrzése változatlanul szigorú.

### Megjegyzés
A `matplotlib` explicit pint kapott: tranzitívan amúgy is települne, de az
ábrák közvetlen függősége, és egy csendes verzióváltás megváltoztathatná a
generált ábrákat.

---

## [0.2.0] — 2026-09-22

**Fázis 1 lezárva — H2-VQE szimulátoron.**

Az első valódi kvantumszámítás. A modul kiszámolja a H2 alapállapoti energiáját,
és — ami módszertanilag legalább ennyire fontos — **igazolja, hogy a kapott szám
helyes**, három egymástól független referenciához mérve.

### Hozzáadva

#### A VQE-mag
- `vqebd.config` — fagyasztott, hash-elhető konfiguráció stabil SHA-256
  ujjlenyomattal (`config_hash` a Fázis 4 adatsémájához).
- `vqebd.seeds` — determinisztikus, BLAKE2b-alapú seed-származtatás egyetlen
  mester-seedből, öt komponensre (ADR-0005).
- `vqebd.versions` — környezet-ujjlenyomat: csomagverziók + platform.
- `vqebd.chemistry` — molekula-definíciók (H2, LiH, BeH2), PySCF-meghajtó típusos
  burkolata, három fermion→qubit leképezés, L0/L1 referenciaenergiák.
- `vqebd.vqe` — UCCSD ansatz Hartree–Fock kezdőállapottal, saját SciPy-alapú
  optimalizáló-hurok konvergencia-naplóval, strukturált `VQEResult`.
- `vqebd.backends` — backend-független energiakiértékelő interfész
  (Fázis 1: `statevector`; a Fázis 1b/2 változatlan interfésszel bővíti).
- `vqebd.cli` + `python -m vqebd` — önállóan futtatható parancssori felület.

#### Függőségek
- A teljes kvantum-stack bekerült a `requirements.txt`-be, `==` pinnekkel:
  numpy 1.26.4 · scipy 1.13.1 · qiskit 1.4.6 · qiskit-aer 0.17.2 ·
  qiskit-nature 0.7.2 · qiskit-ibm-runtime 0.41.1 · pyscf 2.14.0 · ply 3.11.
- **Új:** `requirements.lock` — a teljes tranzitív fa (53 csomag) a megépült
  image-ből, `pip freeze --all`-lal.
- Dockerfile: `libgomp1` (a PySCF OpenMP-futásideje) és `*_NUM_THREADS=1`
  a lebegőpontos determinizmushoz.

#### Tesztelés
- **+108 automatikus teszt** (összesen 216): validációs, integrációs és egységszint.
- `tests/validation/test_h2_vqe.py` — a fizikai helyesség 23 tesztje.
- `tests/integration/test_cli.py` — a teljes lánc a parancssoron keresztül.
- `tests/unit/` — konfiguráció, seedek, verziók, optimalizáló (analitikus
  célfüggvényen, kvantumszimuláció nélkül).
- `tests/repo/test_requirements.py` — a pin ↔ lock konzisztencia és a GPL-licenc
  elkülönítés ellenőrzése.
- A negatív harness **8 → 11** esetre bővült (TC-N9…N11).

#### Dokumentáció
- `docs/plan/phase_01.md` — a Fázis 1 bővített terve.
- `docs/01_vqe_core.md` — a VQE-mag használata, architektúrája és korlátai.
- `docs/testing/TP-F01` + `TR-F01` — tesztterv és mérési jegyzőkönyv.

### Mért eredmények (H2, 0.735 Å, STO-3G)

| Szint | Energia (Ha) | Eltérés |
|---|---|---|
| Hartree–Fock | −1.1169989968 | — |
| **L0 — PySCF Full CI** | **−1.1373060358** | referencia |
| **L1 — egzakt diagonalizáció** | **−1.1373060358** | +1.33 × 10⁻¹⁵ Ha |
| **L2 — VQE** | **−1.1373060358** | +9.33 × 10⁻¹⁵ Ha |

Visszanyert korrelációs energia: **100.0000 %**. A hiba a kémiai pontosság
(1.59 × 10⁻³ Ha) körülbelül 10⁻¹²-szerese.

Mindhárom leképezés (Jordan–Wigner, paritás, Bravyi–Kitaev) ugyanazt az energiát
adja; a paritás-leképezés kétqubites redukcióval 4 helyett **2 qubitet** és 15
helyett **5 Pauli-tagot** igényel.

### Szigorítva az alaptervhez képest
- Az elfogadási tolerancia ±0.01 Ha helyett **±1.6 mHa** (kémiai pontosság),
  és **két független referenciához** mérve, nem egy irodalmi számhoz.
- A „többször lefuttatva ugyanaz" elvárásból **automatikus, bitre azonosságot
  követelő teszt** lett (AC-1.6).
- A `run_vqe()` `float` helyett strukturált `VQEResult`-ot ad vissza; az
  alapterv által kért szám ennek az `energy` mezője.

### Javítva
- A `scipy.optimize` `TNC` metódusa `maxfun`-t vár `maxiter` helyett; a rossz
  opciókulcsot a SciPy **csendben eldobta**, így az iterációs korlát nem
  érvényesült. Az ismeretlen opciókulcs mostantól hibát ad, nem figyelmeztetést.
- A `qiskit-nature` több mezője (`num_particles`, `num_spatial_orbitals`,
  `nuclear_repulsion_energy`) lehet `None`; ezt explicit ellenőrzés kezeli
  beszédes hibaüzenettel.
- A CLI külön modulba (`vqebd.cli`) került, hogy a `runner` ne fusson egyszerre
  csomagimportként és `__main__`-ként (`runpy` figyelmeztetés).

### Ismert korlát
- A `qiskit-nature 0.7.2` UCCSD-je a Qiskit 1.4 `NLocal` osztályát használja,
  ami `PendingDeprecationWarning`-ot ad. Külső csomag, a helyességet nem érinti.

---

## [0.1.0] — 2026-09-22

**Fázis 0 lezárva — Alapinfrastruktúra és repó-szerkezet.**

### Hozzáadva

#### Infrastruktúra
- Git-repó, MIT licenc (Kormos Attila, Claude AI), `.gitignore`, `.gitattributes`,
  `.dockerignore`.
- Mappaszerkezet: `src/vqebd/` (5 alcsomag), `tests/` (unit, integration, validation,
  repo), `docker/`, `docs/` (plan, adr, testing, figures), `dashboard/`, `data/`,
  `scripts/`.
- `docker/Dockerfile` — `python:3.11-slim`, **digest-tel rögzítve**
  (`sha256:da047cb8…95ba9`, Python 3.11.16), nem-root felhasználó (uid 1000),
  `PYTHONHASHSEED=0`, OCI-címkék, `HEALTHCHECK`.
- `docker/docker-compose.yml` — egyetlen `app` szolgáltatás, nevesített `data` volume,
  opcionális `.env` betöltés.
- `Makefile` — `build`, `test`, `verify`, `lint`, `format`, `typecheck`, `check`, `shell`.
- `.github/workflows/ci.yml` — lint, típusellenőrzés és teszt konténerben.
- `.env.example` — titokkezelési minta, valódi token nélkül.

#### Csomagváz
- `vqebd` csomag `__version__`, `AUTHORS`, `LICENSE` attribútumokkal; a verzió
  igazságforrása a `VERSION` fájl.
- `py.typed` jelölő (PEP 561).
- Öt dokumentált alcsomag-váz: `backends`, `chemistry`, `mitigation`, `storage`, `vqe`.

#### Tesztelés
- 9 tesztmodulnyi automatikus ellenőrzés a Fázis 0 tíz elfogadási kritériumára.
- `tests/repo/` — repó-hatókörű tesztek (szerkezet, verzióegyezés, titokhigiénia),
  amelyek a szállított image-ben automatikusan kihagyásra kerülnek.
- `tests/unit/` — kódtesztek, amelyek mindenhol futnak.
- ADR-0002 betartatása automatikus teszttel: a `qiskit_algorithms` importja tilos
  a `src/vqebd/` alatt.

#### Dokumentáció
- [`docs/plan/00_master_plan.md`](docs/plan/00_master_plan.md) — bővített mesterterv:
  öt referenciaszint (L0–L3b), technológiai stack, verziózási és tesztelési politika,
  kockázatnyilvántartás.
- [`docs/plan/phase_00.md`](docs/plan/phase_00.md) — a Fázis 0 bővített terve.
- [`docs/00_setup.md`](docs/00_setup.md) — telepítési és futtatási útmutató.
- [`docs/references.md`](docs/references.md) — **37 hivatkozás, ebből 35 gépileg
  DOI-validált** a Crossref/DataCite API-val (`scripts/gen_references.py`).
- Öt architektúra-döntés (ADR-0001…0005).
- [`docs/testing/TR-000_spike.md`](docs/testing/TR-000_spike.md) — négykörös előzetes
  műszaki felderítés mérési jegyzőkönyve, 9 megállapítással.
- [`docs/testing/TP-F00_alapinfrastruktura.md`](docs/testing/TP-F00_alapinfrastruktura.md)
  és [`TR-F00`](docs/testing/TR-F00_alapinfrastruktura.md) — a Fázis 0 tesztterve és
  jegyzőkönyve.

### Fontos megállapítások (TR-000)

Ezek a mérések a projekt műszaki irányát határozták meg:

- **M1** — A Mitiq 0.47.0 (`numpy<2.0`) és a Qiskit 2.x (`numpy>=2.0`) **nem
  telepíthető egy környezetbe**. A stack ezért Qiskit **1.4.6**-ra rögzítve (ADR-0001).
- **M2** — A `ply==3.11` a Mitiq qiskit-interfészének **rejtett függősége**;
  közvetlen függőségként kezeljük.
- **M3** — A Mitiq `qiskit↔cirq` konverziója **eldobja az inaktív qubiteket**
  (5 qubites ISA-áramkörből 2 qubites lesz), így ISA-szinten nem használható (ADR-0003).
- **M4** — A saját unitáris hajtogatás és a Mitiq `fold_global` **bitre azonos**
  kapuszámot ad (23 / 69 / 115 λ=1/3/5-nél).
- **M5** — A ZNE **nem javítja a readout-hibát**; a mérési hibaenyhítés önálló
  sémadimenzió.
- **M6** — A `FakeBackend`-ek realisztikus zajmodellt adnak **IBM-kvóta nélkül** →
  új **Fázis 1b** iktatódik be a tervbe.

### Megjegyzés a függőségekről
A `requirements.txt` ebben a fázisban **szándékosan üres** — az alapterv előírása
szerint a Fázis 0 image nem tartalmazhat kvantumkönyvtárat. A teljes, már feloldott
stack a Fázis 1-ben kerül be.

[Unreleased]: https://github.com/aiasz/VQEBD/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/aiasz/VQEBD/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aiasz/VQEBD/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/aiasz/VQEBD/releases/tag/v0.1.0
