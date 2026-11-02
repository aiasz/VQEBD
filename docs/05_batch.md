# 05 — Batch-futtatás, aktív tér és statisztika (Fázis 5)

| | |
|---|---|
| **Dokumentum** | `docs/05_batch.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Projektverzió** | 0.8.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 5 — Batch-futtatás, aktív tér, statisztikai módszertan |
| **Háttér** | [`phase_05.md`](plan/phase_05.md) · [`ADR-0007`](adr/ADR-0007-batch-statisztika.md) · [`TR-F05`](testing/TR-F05_batch.md) |

---

## 1. Mit ad a Fázis 5?

| Képesség | Modul | Mire jó |
|---|---|---|
| **Aktív tér** | `vqebd.config.ActiveSpaceSpec`, `vqebd.chemistry` | LiH és BeH₂ kezelhető qubitszámon (8–10), a frozen-core redukcióval |
| **Batch-motor** | `vqebd.batch` | sok futás egyetlen, folytatható, determinisztikus listából |
| **Statisztika** | `vqebd.stats` | konfidenciaintervallum, kémiai pontossági besorolás, hibaköltségvetés |
| **Újramintavételezés** | `VQEConfig.reestimate` | a zajos végső energia torzítatlan becslése |
| **Séma v2** | `vqebd.storage` | az új mezők tárolása, v1 → v2 automatikus migráció |

## 2. Aktív tér

Egy aktív tér két számmal adható meg: az aktív elektronok és az aktív térbeli
pályák száma. A többi betöltött pálya befagyasztott; energiájuk a Hamilton-operátor
**konstans eltolásaként** (`energy_offset`) jelenik meg.

```python
from vqebd.config import ActiveSpaceSpec, VQEConfig

config = VQEConfig(
    molecule=lih(1.595),  # lásd vqebd.batch.spec
    active_space=ActiveSpaceSpec(2, 5),  # LiH frozen core, 8 qubit
)
```

A teljes energia = a VQE által adott elektronos energia + `energy_offset`, ahol az
eltolás **magtaszítás + inaktív energia**. Aktív térben ez nem azonos a
`nuclear_repulsion_energy`-vel; teljes térben bitre azonos (TC-502).

### Melyik teret válasszuk?

| Tér | Qubit | Csonkolás (CASCI − FCI) | Megjegyzés |
|---|---|---|---|
| LiH (2e,3o) — minimális | 6 | 15.7–71.8 mHa | a korrelációs energia töredékét tartja meg |
| **LiH (2e,5o) — frozen core** | 8 | **0.23–0.34 mHa** | kémiai pontosságon belül |
| BeH₂ (2e,3o) — minimális | 6 | 25.3–67.6 mHa | |
| **BeH₂ (4e,6o) — frozen core** | 10 | **0.34 mHa** (1.33 Å) | |

A minimális tér modellhibája **determinisztikus**: ismétléssel nem csökken. A
választás mért indoklása: [`phase_05.md`](plan/phase_05.md) 2. fejezet, ábra:
`fig07_aktiv_ter.png`.

## 3. Batch-futtatás

```bash
python scripts/run_batch.py --preset f5-smoke        # 5 futás, gyors ellenőrzés
python scripts/run_batch.py --preset f5-deterministic \
       --db data/db/f5.sqlite --export docs/figures/data/f5_deterministic.json
python scripts/run_batch.py --preset f5-statistical  --db data/db/f5.sqlite
```

| Kapcsoló | Jelentés |
|---|---|
| `--preset` | `f5-smoke` (5), `f5-deterministic` (50), `f5-statistical` (180) |
| `--db` | cél-adatbázis (alapértelmezés: `data/db/vqebd.sqlite`) |
| `--max-runs N` | legfeljebb N *új* futás, utána leáll (folytatható) |
| `--export` | JSON-export a csoportosított statisztikákkal |
| `--quiet` | kevesebb kimenet |

**Tulajdonságok**

- **Determinisztikus.** Azonos spec → azonos futáslista és azonos `run_id`-k.
  Az ismétlések csak a seedben különböznek (`master_seed + ismétlés-index`).
- **Folytatható.** A már tárolt futásokat kihagyja; a megszakított és folytatott
  batch bitre azonos egy megszakítás nélküli futással (AC-5.5).
- **Hibaizolált.** Egy futás kivétele nem állítja le a batchet; a jelentés
  `failed` listája mutatja.
- **Hardverbiztos.** `ibm_qpu` cella `VQEBD_ALLOW_HARDWARE` nélkül
  `PermissionError`-t ad.

Futásidő (Docker, egy szál): `f5-deterministic` ≈ 42 perc (mérve: 2535 s),
`f5-statistical` ≈ 20 perc. A leghosszabb tagok a LiH (2e,5o) qsim (≈ 10 perc)
és a BeH₂ (4e,6o) Cirq (≈ 16 perc).

## 4. Statisztika

A zajos futás eredménye valószínűségi változó, ezért **N seed** és **K friss
kiértékelés** kell ahhoz, hogy a kémiai pontosságról állítani lehessen.

### 4.1 Újramintavételezés (`reestimate=K`)

Az optimalizáló végértéke egyetlen zajos minta, nem a θ_opt-beli energia
becslése. Ha `reestimate = K`, a futás θ_opt-ban **K független, friss
kiértékelést** végez, és ezek átlaga a végső energia (± SEM). A rekord a nyers
optimalizálói végértéket és az előzmény-minimumot is tárolja.

> **Soha ne közöljük az előzmény-minimumot.** Zajban a minimum a szerencsés
> húzás: 25–34 mHa-val a valódi érték alatt van (TR-F05, 4. pont). A VQEBD ezt
> nem teszi.

`K = 1` nem megengedett: egyetlen mintából nincs SEM.

### 4.2 `vqebd.stats`

| Függvény | Mit ad |
|---|---|
| `summarize(values)` | átlag, szórás, SEM, medián, t-CI |
| `classify_chemical_accuracy(...)` | `confirmed` / `consistent` / `excluded` / `undetermined` |
| `rmse(...)` | átlagos négyzetes hiba (torzítás és szórás együtt) |
| `block_mean_spread(...)`, `loglog_slope(...)` | SEM(N) skálázás; elmélet: −0.5 |
| `error_budget(...)` | a teljes hiba felbontása (lásd 4.4) |

### 4.3 Kémiai pontossági besorolás

A hiba 95%-os CI-jét a ±1.6 mHa sávhoz viszonyítjuk:

| Osztály | Jelentés |
|---|---|
| `confirmed` | a teljes CI a sávon belül |
| `consistent` | a CI metszi a sávot, de nincs teljesen benne |
| `excluded` | a CI teljesen a sávon kívül — a konfiguráció **nem** kémiailag pontos |
| `undetermined` | egyetlen *zajos* minta: a bizonytalanság nem becsülhető |

### 4.4 Hibaköltségvetés

A teljes hiba (átlag − Full CI) tagokra bomlik:

| Tag | Jelentése | Csökken-e ismétléssel? |
|---|---|---|
| csonkolás (CASCI − FCI) | az aktív tér modellhibája | nem |
| leképezés (L1 − CASCI) | Jordan–Wigner / Parity numerikus hibája | nem |
| ansatz (L2 − L1) | az UCCSD kifejezőképessége | nem |
| optimalizálás zajban | az optimalizáló nem θ*-ban áll meg | részben |
| eszközzaj θ_opt-ban | a zajmodell torzítása | **nem** (módszer kell: ZNE) |
| statisztikus (SEM) | lövészaj | **igen**, N^−½ szerint |

Ábra: `fig09_hibakoltsegvetes.png`.

### 4.5 Mit jelent ez a gyakorlatban?

**Az ismétlés a szórást csökkenti, a torzítást nem** (`fig08_ismetles.png`). A
nyers zajos H₂ esetben a padló +27.5 mHa; ZNE-vel +0.23 mHa. Több futás tehát
a *statisztikai* bizonytalanságot szűkíti, a *szisztematikus* hibához más módszer
kell.

## 5. Séma v2

A `results` tábla 11 új, nullázható oszlopot kapott (az újramintavételezés, az
aktív tér és a referenciák számára). A v1 adatbázis megnyitáskor **automatikusan
migrál**, a v1 rekordok bitre változatlanok maradnak, és a második megnyitás nem
migrál újra. Ismeretlen (újabb) sémaverzió hibát ad, nem próbál migrálni.
Mezőlista: [`04_data_schema.md`](04_data_schema.md).

## 6. Hardveres védőkorlátok (`vqebd.hardware`)

Két szint védi az IBM-kvótát:

1. **Engedély:** hardveres beküldés csak `VQEBD_ALLOW_HARDWARE=true` mellett.
2. **Kvóta-előellenőrzés:** beküldés előtt a becsült QPU-idő a hátralévő kerethez
   mérődik; ha kevés, a szkript `exit 2`-vel megáll.

`scripts/run_hardware_pes.py --dry-run` a klasszikus előkészítést és a kvótát
ellenőrzi, **beküldés nélkül**. A kvóta egy **gördülő 28 napos ablak**, nem naptári
hónap.

A VQE-útvonalra (`run_vqe`, `python -m vqebd --backend ibm_qpu`) ugyanez
érvényes, kiegészítve **kiértékelési kerettel** (K7, javítva):

1. engedély (`VQEBD_ALLOW_HARDWARE=true`), hálózati hívás előtt;
2. a legrosszabb eset — `maxiter` + a végső becslések (ZNE-nél × a zajszorzók
   száma) × **15 QPU-s** — a hátralévő kerethez mérve;
3. kemény keret: az optimalizáló a fedezett számnál több kiértékelést
   (jobot) nem indíthat (`EvaluationBudgetExceededError`).

> **Következmény:** az alapértelmezett `--maxiter 300` hardveren elutasításra
> kerül (300 × 15 s = 4500 s > 600 s). Hardveres VQE-hez kis iterációkorlát kell,
> pl. `--maxiter 20` (≈ 300 s). Az indoklás: a védelem nélküli útvonal 2026-09-23-án
> 42 jobbal fogyasztotta el a teljes keretet.

## 7. Ismert korlátok

| # | Korlát |
|---|---|
| K4 | UCCSD mélységi fal: LiH (2e,3o) zajos szimulációban +466 mHa |
| K7 | ~~A hardveres VQE-útvonal kvótavédelem nélkül~~ — **javítva** (6. pont) |
| K8 | A qsim (`complex64`) a LiH (2e,5o) 1.595 Å-nél 2.8·10⁻⁵ Ha-val tér el, a névleges tűrés (10⁻⁵ Ha) fölött; a kémiai pontosság 1.8%-a. Az ok megmérve: a `complex64` aritmetika, nem a Powell (a Powell `complex128`-on 9·10⁻¹² Ha-ra konvergál). A tűrés a (2e,3o) terekre igaz, 24 paraméteren nem ([TR-F05](testing/TR-F05_batch.md) 3.2) |
| 5.H | Hardveres H₂ görbe: lefutott (2026-11-02), a hardver nem éri el a kémiai pontosságot; pontonként egyetlen futás ([TR-F05](testing/TR-F05_batch.md) 7.) |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
