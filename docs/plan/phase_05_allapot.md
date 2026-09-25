# Fázis 5 — állapotjegyzet és folytatási útmutató

| | |
|---|---|
| **Dokumentum** | `docs/plan/phase_05_allapot.md` |
| **Rögzítve** | 2026-09-25 |
| **Tervezett folytatás** | **2026-10-21** (az IBM-kvóta újra elérhető: `2026-10-21T11:27Z`) |
| **Kódállapot** | `VERSION` = `0.8.0` — **fejlesztés alatt, a Fázis 5 nincs lezárva** |
| **Utolsó lezárt kiadás** | `v0.7.1` (javítókör) |
| **Terv** | [`phase_05.md`](phase_05.md) · [`ADR-0007`](../adr/ADR-0007-batch-statisztika.md) · [`TP-F05`](../testing/TP-F05_batch.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

Ez a jegyzet azért készült, hogy a munka egy megszakítás után **kontextusvesztés
nélkül** folytatható legyen. Minden állítás mögött fájl, parancs vagy mérés áll.

---

## 1. Egy bekezdésben

A v0.7.1 javítókör lezárult (mintavételi hiba, ISA-ZNE, hardveres bizonytalanság).
A Fázis 5 kódja és tesztjei **elkészültek**: aktív tér, batch-motor, statisztika,
séma v2, hardveres védőkorlátok. A statisztikai batch **lefutott** (180/180), a
fig08 ábra **kész**. **Hátravan:**
- a determinisztikus batch befejezése (a commit idején 38/50);
- a fig07 és fig09 ábra;
- a TR-F05 jegyzőkönyv;
- a README és a CHANGELOG lezárása;
- a **hardveres H₂ disszociációs görbe (5.H)**, amelyet az IBM-kvóta kimerülése
  miatt a 2026-10-21 utánra halasztottunk.

---

## 2. Ami kész (és tesztelt)

### 2.1 Kód

| Elem | Fájl | Megjegyzés |
|---|---|---|
| Aktív tér | `src/vqebd/config.py` (`ActiveSpaceSpec`), `chemistry/problem.py` | `energy_offset` = magtaszítás + inaktív energia (LiH frozen core: −7.80 Ha) |
| L0′ CASCI-referencia | `chemistry/reference.py` (`casci_energy`) | L1 ↔ CASCI ≤ 4·10⁻¹⁴ Ha (AC-5.1) |
| Statisztika | `src/vqebd/stats.py` | t-CI, négyállapotú besorolás, blokkátlag, hibaköltségvetés |
| Batch-motor | `src/vqebd/batch/` | preset-ek: `f5-deterministic` (50), `f5-statistical` (180), `f5-smoke` (5) |
| Újramintavételezés | `VQEConfig.reestimate`, `vqe/runner.py`, `vqe/result.py` | végérték, előzmény-minimum, friss átlag ± SEM |
| Séma v2 + migráció | `storage/schema.py`, `storage/db.py` | 11 új nullázható oszlop; v1 → v2 automatikus |
| Hardveres védőkorlátok | `src/vqebd/hardware.py` | engedély (`VQEBD_ALLOW_HARDWARE`) + kvóta-előellenőrzés |
| Több PUB egy jobban | `IBMQpuEnergyEvaluator.evaluate_observables` | kvótatakarékos pásztázás |
| Szkriptek | `scripts/run_batch.py`, `scripts/run_hardware_pes.py` | folytatható batch; hardveres PES `--dry-run`-nal |
| Ábrák | `scripts/gen_report_figures.py` | `aktiv_ter`, `ismetles`, `hibakoltsegvetes` lépések; `--only`, `--replot` |
| Hivatkozások | `docs/references.md` v1.1.0 | +[student1908], +[wecker2015] (DOI-validált) |

### 2.2 Minőségi kapuk (2026-09-25, `vqebd:0.8.0`)

- ruff check, ruff format, mypy (strict): tiszta.
- Tesztek: lásd a commit üzenetét (a teljes készlet zöld, mitiq nélkül 1 kihagyott teszt: TC-302).
- Új tesztfájlok: `test_stats.py`, `test_batch.py`, `test_hardware_guard.py`,
  `test_active_space.py`, `test_batch_statistics.py`; kiegészítve: `test_storage.py`
  (migráció), `test_project_structure.py` (a `data/` teszt javítva).

### 2.3 Dokumentumok

`phase_05.md` (terv, a mért előfelderítéssel), `ADR-0007`, `TP-F05`,
`docs/04_data_schema.md` (séma v2), mesterterv 1.2.0 (R13–R16).

---

## 3. Mért eredmények eddig

### 3.1 Aktívtér-előmérés (`phase_05.md` 2. fejezet)

A „tisztességes” aktív tér a **frozen core**: LiH (2e,5o) 8 qubit, csonkolás
0.23 mHa; BeH₂ (4e,6o) 10 qubit, 0.34 mHa. A minimális (2e,3o) tér 19–34 mHa-t
veszít, és a korrelációs energia csak 1.6–5.2%-át tartja meg.

### 3.2 Statisztikai batch — `docs/figures/data/f5_statistical.json` (v0.8.0, 180/180)

Hiba a Full CI-hez, mHa; N seed, K = 16 friss kiértékelés futásonként.

| Konfiguráció | N | átlag | szórás | 95% CI | RMSE | kiválasztási torzítás¹ | besorolás |
|---|---|---|---|---|---|---|---|
| H₂ 0.735 · lövészaj | 20 | +11.59 | 8.27 | [+7.72, +15.46] | 14.12 | −25.47 | excluded |
| H₂ 0.735 · zajos | 20 | +38.15 | 8.38 | [+34.23, +42.07] | 39.02 | −25.51 | excluded |
| H₂ 0.735 · ZNE lineáris | 20 | +15.52 | 8.17 | [+11.70, +19.35] | 17.45 | — | excluded |
| H₂ 0.735 · ZNE Richardson | 20 | +11.54 | 10.03 | [+6.84, +16.23] | 15.12 | — | excluded |
| H₂ 1.5 · lövészaj | 20 | +15.23 | 8.56 | [+11.22, +19.24] | 17.37 | −25.64 | excluded |
| H₂ 1.5 · zajos | 20 | +29.63 | 9.02 | [+25.41, +33.85] | 30.91 | −25.77 | excluded |
| H₂ 1.5 · ZNE lineáris | 20 | +19.00 | 8.99 | [+14.79, +23.21] | 20.92 | — | excluded |
| H₂ 1.5 · ZNE Richardson | 20 | +17.24 | 8.63 | [+13.20, +21.28] | 19.19 | — | excluded |
| LiH (2e,3o) · lövészaj | 10 | +28.04 | 7.65 | [+22.57, +33.52] | 28.97 | −30.80 | excluded |
| LiH (2e,3o) · zajos | 10 | **+465.65** | 13.11 | [+456.27, +475.03] | 465.82 | −30.84 | excluded |

¹ Előzmény-minimum − friss átlag. Ennyit tévedne egy implementáció, amely a zajos
kiértékelések minimumát közölné. A VQEBD ezt nem teszi. Hibaenyhített cellában
nem értelmezett, mert az előzmény nyers, az átlag mitigált.

**Előzetes értelmezés** (a TR-F05-ben véglegesítendő):

- **Egyik zajos konfiguráció sem éri el a kémiai pontosságot**, és ezt a CI
  statisztikailag ki is zárja (`excluded`).
- **Lövészajnál is +11.6 mHa a hiba**, pedig a lövészaj rögzített θ-nál
  torzítatlan. A hiba tehát az *optimalizálásból* ered: a H₂ korrelációs
  energiája csak ~1.8σ, így a COBYLA nem θ*-ban áll meg. A fig09 ezt
  „optimalizálás zajban” és „eszközzaj θ_opt-ban” tagokra bontja; ez a
  determinisztikus batch után futtatható.
- **A ZNE csökkenti a hibát** (+38.2 → +11.5 mHa), de nem viszi a sávba. Itt a
  Richardson RMSE-je jobb a lineárisénál (15.1 vs. 17.5 mHa), fordítva, mint a
  TR-F03 θ*-beli, K = 1 elemzésében. Ez összhangban van a „lövésszámfüggő
  extrapolátor-választás” állítással: K = 16-nál a szórás kisebb, ezért a torzítás
  dominál.
- **LiH (2e,3o) zajosan: +466 mHa**, messze a HF fölött. Ez az UCCSD mélységi fala:
  ~170 CX a FakeManilaV2 ~1%-os CX-hibája mellett. A kvantumos jel elvész.
- **Nyitott kérdés:** az optimalizáló végértéke átlagosan **+2.51 ± 0.99 mHa**-val
  a friss átlag fölött van (100 futás, 2.5σ). Várhatóan egy COBYLA-leállási
  sajátosság; a TR-F05-ben kivizsgálandó.

### 3.3 fig08 — az ismétlés hatása (`docs/figures/data/ismetles.json`, 1024 minta)

| Sorozat | log-log meredekség (elmélet: −0.5) | átlag − padló | padló |
|---|---|---|---|
| lövészaj | −0.53 | +2.06 SEM | 0 |
| FakeManilaV2 nyers | −0.48 | −0.29 SEM | +27.52 mHa |
| FakeManilaV2 + ZNE Richardson | −0.55 | +0.32 SEM | +0.23 mHa |

**Az ismétlés a szórást N^−½ szerint csökkenti, a torzítást nem.** A torzítás
ellen a *módszer* (ZNE) hat. Ez a felhasználói kérdés („hozzájárul-e a több teszt
a pontossághoz?”) mért válasza, a `phase_05.md` 3. fejezetének táblázatával együtt.

---

## 4. Ami félkész vagy hátravan

| # | Teendő | Függ | Hogyan |
|---|---|---|---|
| T1 | **Determinisztikus batch befejezése** | — | 5.1 szakasz |
| T2 | fig07 (aktív tér PES) és fig09 (hibaköltségvetés) | T1 | `python scripts/gen_report_figures.py --only aktiv_ter`, majd `--only hibakoltsegvetes` |
| T3 | Ábra-ellenőrzés: feliratütközés, olvashatóság (a fig06/fig08-nál bevált módon) | T2 | szemrevételezés, szükség esetén `--replot` |
| T4 | **TR-F05** mérési jegyzőkönyv (AC-5.1 … 5.10), a 3.2 pont nyitott kérdésével együtt | T1–T3 | `docs/testing/TR-F05_batch.md` |
| T5 | `docs/05_batch.md` felhasználói dokumentum | T4 | a `docs/0x_*.md` mintájára |
| T6 | README (HU **és** EN): Fázis 5 szakasz, ábrák, tesztszám-jelvény | T4 | mindkét nyelvi rész szinkronban |
| T7 | CHANGELOG `[0.8.0]` lezárása, `v0.8.0` címke | T4–T6 | a kiadás a Fázis 5 lezárása (5.H nélkül is) |
| T8 | **5.H hardveres H₂ PES** | kvóta ≥ 120 s | 5.2 szakasz |

**Döntés a lezárásról:** az 5.H nem elfogadási kritérium (`phase_05.md` 6.4). A
Fázis 5 tehát T1–T7 után lezárható és `v0.8.0`-ként kiadható. Az 5.H eredménye
utána egy `v0.8.1` kiegészítés lehet. Alternatíva: a lezárást 2026-10-21-ig
elhalasztjuk, és az 5.H-val együtt adjuk ki. **Ez felhasználói döntés.**

---

## 5. Folytatás lépésről lépésre

Minden parancs a repó gyökeréből, a projekt Docker-image-ével. Windows / Git Bash
alatt a `MSYS_NO_PATHCONV=1` előtag kell.

```bash
docker build -f docker/Dockerfile -t vqebd:0.8.0 .
RUN="docker run --rm -v $PWD:/repo -w /repo -e PYTHONPATH=/repo/src \
     -e PYTHONHASHSEED=0 -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
     vqebd:0.8.0"
```

### 5.1 A determinisztikus batch befejezése (T1)

A batch **folytatható**: a már tárolt futásokat kihagyja, az eredmény bitre azonos
egy megszakítás nélküli futáséval (AC-5.5). Az adatbázis helyi és gitignore-olt:
`data/db/f5.sqlite`.

```bash
$RUN python -W ignore scripts/run_batch.py --preset f5-deterministic \
     --db data/db/f5.sqlite --export docs/figures/data/f5_deterministic.json
```

- Várható idő a nulláról: ~40 perc. A leghosszabb tagok: qsim LiH (2e,5o) ~8 perc
  (mérve: 486 s), Qiskit BeH₂ (4e,6o) ~4 perc (mérve: 220 s), Cirq BeH₂ (4e,6o)
  ~9 perc (becslés a Cirq/Qiskit ≈ 2.4× arányból).
- Ha a `data/db/f5.sqlite` elveszett, a statisztikai batch is újrafuttatható
  (~20 perc), és bitre ugyanazt adja: a v0.7.1-es és a v0.8.0-s futás is azonos
  energiákat adott.

### 5.2 Hardveres H₂ PES (5.H, T8) — 2026-10-21 után

1. **Kvóta és terv ellenőrzése, beküldés nélkül.** A szkript a klasszikus
   előkészítést elvégzi, a kvótát lekérdezi, és ha a keret kevés, `exit 2`-vel
   megáll:
   ```bash
   $RUN python -W ignore scripts/run_hardware_pes.py --dry-run
   ```
   Várt kimenet: `Dry run: a kvóta elegendő, beküldés nem történt.`
2. **A mérés** (2 job, 10 PUB, becslés ≤ 120 QPU-s):
   ```bash
   docker run --rm -v $PWD:/repo -w /repo -e PYTHONPATH=/repo/src \
     -e VQEBD_ALLOW_HARDWARE=true vqebd:0.8.0 \
     python -W ignore scripts/run_hardware_pes.py
   ```
   Kimenet: `docs/figures/data/hardware_h2_pes.json`. Tartalma: job-azonosítók,
   számlázott QPU-idő, `stds` és `ensemble_standard_error` PUB-onként, szerveroldali
   mitigációs metaadat, kvóta előtte és utána.
3. **Hiányzó adat utólagos pótlása** (kvóta nélkül): `scripts/fetch_ibm_job.py`
   mintájára a `service.job(id).result()` visszaolvasható.
4. **Még megírandó:** fig10 (hardveres PES, L0/L2 görbe és a két szint pontjai
   hibasávval, alul hiba vs. R), valamint a TR-F05 és a TR-F02 kiegészítése.

**Kvótahelyzet a jegyzet írásakor** (`service.usage()`, csak olvasás):
630 / 600 s felhasználva, `usage_limit_reached = true`,
`time_available_at = 2026-10-21T11:27:12.987Z`. A 630 s-ból a projekt Fázis 2-es
jobja 15 s volt. **A többi 615 s nem a projekt futásaiból származik.**
Figyelem: a keret gördülő 28 napos ablak. A 2026-10-21 utáni tényleges
hátralévő időt a `--dry-run` mutatja meg.

---

## 6. Ismert korlátok és nyitott kérdések (döntésre)

| # | Téma | Állapot | Javaslat |
|---|---|---|---|
| K1 | Az Aer Estimator nem modellezi a readout-hibát (ADR-0003, 1. kieg.) | dokumentálva | Sampler-alapú becslő (Fázis 6) |
| K2 | A `precision` → σ konvenció nem a Hamilton-operátor Pauli-varianciája | dokumentálva | K1-gyel együtt |
| K3 | Nincs Heron FakeBackend a rögzített `qiskit-ibm-runtime`-ban | mérve | zajmodell az `ibm_kingston` kalibrációjából, kvóta nélkül (Fázis 6) |
| K4 | UCCSD mélységi fal (LiH (2e,3o): +466 mHa zajosan) | mérve | hardverhatékony ansatz (Fázis 6+) |
| K5 | Az optimalizáló végértéke +2.5 ± 1.0 mHa-val a friss átlag fölött | nyitott | TR-F05-ben kivizsgálni |
| K6 | 5.H a lezárás előtt vagy után (4. fejezet) | **felhasználói döntés** | — |

---

## 7. Git-állapot a jegyzet írásakor

- `v0.7.1` javítókör: commitolva és címkézve.
- A Fázis 5 részállapota ebben a commitban (`VERSION` 0.8.0, fejlesztés alatt).
- A `docs/figures/data/f5_deterministic.json` **nincs** a commitban: a batch a
  commit idején még futott (38/50). Ha a helyi futás végigér, az export a
  munkakönyvtárban megjelenik, és a következő commitba kerül (T1 kész).

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
