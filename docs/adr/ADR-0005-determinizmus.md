# ADR-0005 — Determinizmus- és seed-politika

| | |
|---|---|
| **Azonosító** | ADR-0005 |
| **Cím** | Determinizmus- és seed-politika a reprodukálhatóság biztosítására |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 1–9 |

---

## Kontextus

Az alapterv Fázis 1-e kimondja: *„Ne menj tovább, amíg ez nem megy stabilan, többször
lefuttatva is ugyanazt az eredményt adja."* Ez a projekt egyik alapkövetelménye, de a
VQE-ben **öt** független véletlenforrás van, és ezek közül három rejtett.

## A véletlenforrások leltára

| # | Forrás | Rejtett? | Hatás, ha nincs kezelve |
|---|---|---|---|
| 1 | Szimulátor-lövések mintavétele | nem | Futásonként eltérő energia. |
| 2 | Transzpiláció (layout, routing, SABRE) | **igen** | Más fizikai áramkör → más zaj → más energia. |
| 3 | Optimalizáló kezdőpont | részben | Más lokális minimum. |
| 4 | Sztochasztikus optimalizálók (SPSA, COBYLA perturbációk) | **igen** | Más konvergencia-út. |
| 5 | Python `hash()` randomizáció (halmaz-/szótár-bejárás) | **igen** | Ritkán, de eltérő kapusorrend. |
| 6 | Mitiq véletlen folding (`fold_gates_at_random`) | nem | Más skálázott áramkör. |

A 2-es a legalattomosabb: a Qiskit transzpilere alapértelmezetten **sztochasztikus**
(SABRE-alapú layout és routing), így `seed_transpiler` nélkül *ugyanaz a kód,
ugyanazon a gépen, ugyanabban a percben* más fizikai áramkört adhat.

## Döntés

### Alapelv

> **Minden véletlenforrás explicit seedet kap, és minden seed bekerül az
> eredményrekordba.** Seed nélküli futtatás nem megengedett a `src/vqebd/` kódútban.

### Megvalósítás

| Forrás | Mechanizmus | Séma-mező |
|---|---|---|
| 1 | `seed_simulator` az Aer backend-opciókban | `seed_simulator` |
| 2 | `seed_transpiler` a `transpile()` hívásban | `seed_transpiler` |
| 3 | Explicit `x0`; alapértelmezés a nullvektor (= Hartree–Fock állapot, UCCSD-nél) | `initial_point_kind`, `initial_point_seed` |
| 4 | Az optimalizáló `seed`/`rng` paramétere | `optimizer_seed` |
| 5 | `PYTHONHASHSEED=0` a Dockerfile-ban | — (a konténer-digest rögzíti) |
| 6 | A Mitiq skálázó `seed` paramétere | `mitigation_params` (JSON) |

### Egyetlen belépési pont

```python
# src/vqebd/seeds.py  (vázlat)
@dataclass(frozen=True)
class SeedSet:
    master: int
    simulator: int
    transpiler: int
    optimizer: int
    mitigation: int

    @classmethod
    def derive(cls, master: int) -> "SeedSet": ...
```

Egyetlen `master` seedből **determinisztikusan származtatjuk** a többit (stabil
hash-alapú derivációval), így a felhasználó egy számot ad meg, a rendszer viszont
minden komponenst külön, ütközésmentesen seedel. A `SeedSet` teljes egészében a
rekordba kerül — nem csak a `master`.

### Determinizmus-szintek

Nem minden szinten várható bitre azonosság; ezt őszintén el kell különíteni:

| Szint | Elvárás | Teszt |
|---|---|---|
| **D1 — egzakt (statevector)** | **Bitre azonos** energia futásonként. | automatikus, minden CI-futásban |
| **D2 — véges lövésszám, zaj nélkül** | Bitre azonos **azonos seed mellett**. | automatikus |
| **D3 — zajos szimulátor** | Bitre azonos **azonos seed és azonos zajmodell mellett**. | automatikus |
| **D4 — valódi QPU** | **Nem determinisztikus** — a kalibráció időben változik. | manuális jegyzőkönyv (TR-002) |

A **D4 nem hiba, hanem fizikai tény.** A QPU-rekordok ezért rögzítik a
`calibration_timestamp` és `backend_properties_hash` mezőket, hogy két futás
összehasonlíthatósága *utólag megítélhető* legyen.

### Lebegőpontos determinizmus — ismert korlát

Bitre azonosság csak **azonos** processzorarchitektúrán, azonos BLAS-implementációval
és azonos csomagverziókkal garantálható. Egy másik gépen a `numpy`/`scipy` eltérő
SIMD-útja miatt az utolsó néhány bit eltérhet. Ezért:

- A **CI-ben** (rögzített image, `linux/amd64`) a bitre azonosság kikényszerített.
- A **validációs tesztek** toleranciája ezzel szemben fizikai (kémiai pontosság,
  1.6 mHa), nem bitszintű — így a teszt más gépen is értelmes marad.
- A Docker image `platform: linux/amd64` rögzítéssel épül.

## Következmények

- **Pozitív:** a Fázis 1 „többször lefuttatva is ugyanaz" kritériuma **automatikusan
  tesztelhetővé** válik, nem kézi megfigyelés kérdése.
- **Pozitív:** egy adatbázisbeli sorból a futás **egzaktul újrajátszható**
  (`scripts/replay_run.py`, Fázis 5).
- **Negatív:** minden hívási láncon át kell vezetni a seedet — több boilerplate.
  **Kezelés:** a `SeedSet` egyetlen objektumként utazik, nem öt külön paraméterként.
- **Negatív:** a rögzített seed **elfedheti** a statisztikus ingadozást.
  **Kezelés:** a Fázis 5 batch futtatások `n_repeats > 1` beállítással, **különböző,
  de rögzített** seedekkel futnak, és a séma tárolja a szórást
  (`energy_std`, `n_repeats`).

## Hivatkozások

- Qiskit `transpile()` és `seed_transpiler`: <https://quantum.cloud.ibm.com/docs>
  (ellenőrizve: 2026-09-22)
- Mesterterv 10. fejezet: [`docs/plan/00_master_plan.md`](../plan/00_master_plan.md)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
