# ADR-0002 — Saját VQE-hurok a `qiskit-algorithms` helyett

| | |
|---|---|
| **Azonosító** | ADR-0002 |
| **Cím** | A VQE optimalizáló-hurok saját implementációja V2 primitívekkel |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 1, 1b, 2, 3, 5 |
| **Függ** | [ADR-0001](ADR-0001-technologiai-stack.md) |
| **Bizonyíték** | [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md), 1. kör / 7. lépés |

---

## Kontextus

A VQE két részből áll: egy **kvantumos** részből (paraméterezett áramkör kiértékelése
egy Hamilton-operátorra) és egy **klasszikus** részből (a paraméterek optimalizálása).
A klasszikus hurokra két út áll rendelkezésre:

1. `qiskit_algorithms.VQE` — kész implementáció;
2. `scipy.optimize.minimize` + saját kiértékelő-függvény.

### A primitívek V1 → V2 váltása

A Qiskit 1.2-ben elavultnak jelölték, a **2.0-ban pedig eltávolították** a V1
primitíveket (`qiskit.primitives.Estimator`, `BaseEstimator`). A helyükre a V2
primitívek léptek (`StatevectorEstimator`, `BackendEstimatorV2`,
`qiskit_aer.primitives.EstimatorV2`, `qiskit_ibm_runtime.EstimatorV2`).

A `qiskit_algorithms.VQE` konstruktora **V1 `BaseEstimator`-t vár**. Az ADR-0001
szerinti Qiskit 1.4.6-on ez még működik (elavultsági figyelmeztetésekkel), de:

- a kód **nem vihető át** Qiskit 2.x-re a `qiskit-algorithms` kicserélése nélkül;
- a V1 primitívek elavultsági figyelmeztetései elfedik a valódi problémákat;
- a `qiskit-algorithms` nálunk egyébként is csak a `qiskit-nature` **tranzitív**
  függősége — nem szándékos választás.

## Probléma

Melyik úton írjuk a Fázis 1 magját úgy, hogy

- a Fázis 1 elfogadási kritériuma (±1.6 mHa a referenciától) teljesüljön,
- a kód **determinisztikus és tesztelhető** legyen (Mesterterv 10. fejezet),
- a stack elavulása (R4 kockázat) ne tegye írásra a teljes kódbázist,
- és a kiértékelés ugyanazzal a kóddal fusson egzakt, zajos és QPU-backenden?

## Megfontolt alternatívák

### A) `qiskit_algorithms.VQE` V1 primitívekkel
- ➕ Kevesebb saját kód; bevált, tesztelt implementáció.
- ➖ V1 primitív → **Qiskit 2.x-ben nem létezik** → R4 kockázat nem csökken.
- ➖ A callback/logolás és a lövésszám-vezérlés nehezebben illeszthető a saját
  adatsémánkhoz (Fázis 4).
- ➖ A `qiskit-nature` 0.7.2 + `qiskit-algorithms` 0.3.1 párosítás egy 2024-es API,
  amelynek jövője a Qiskit-ökoszisztémában bizonytalan.

### B) Saját hurok V2 primitívekkel + SciPy ✅
- ➕ **V2 primitív → a Qiskit 2.x-ben változatlanul létezik** → a kód előre-hordozható.
- ➕ A backend-váltás (egzakt → Aer zajos → QPU) csak az estimator-objektum cseréje,
  ugyanaz a hurok fut mindhármon → az L0–L3b referencialánc egyetlen kódúton mérhető.
- ➕ Teljes kontroll: iterációnkénti naplózás, lövésszám-ütemezés, konvergencia-kritérium,
  determinizmus.
- ➕ Az optimalizálók irodalmi hivatkozással azonosíthatók ([nelder1965], [powell1994],
  [kraft1988], [spall1992]).
- ➖ Saját kód → saját tesztelési felelősség.

### C) Mindkettő, `qiskit-algorithms` referenciaként
- ➕ Keresztvalidáció.
- ➖ V1 primitívek behozatala pont azt a függőséget cementezi be, amitől szabadulni akarunk.
- **Részlegesen átvesszük:** a keresztvalidációt nem a `qiskit-algorithms`-szal, hanem
  a **PySCF FCI** és az **egzakt diagonalizáció** ellenében végezzük — ez erősebb
  referencia, mert *független implementáció, független elmélet*.

## Döntés

**A (B) alternatívát választjuk**, a (C) keresztvalidációs elvével kiegészítve.

### Implementációs kontraktus

```python
# src/vqebd/vqe/runner.py  (vázlat, a részletes API a Fázis 1 tervben)
def run_vqe(problem, ansatz, estimator, optimizer_cfg, x0=None, seed=None) -> VQEResult
```

- **Kiértékelés:** `estimator.run([(ansatz, observable, params)])` — V2 PUB-formátum.
- **Optimalizálás:** `scipy.optimize.minimize`, konfigurálható `method`-dal.
- **Kezdőpont:** alapértelmezés `x0 = 0` vektor. UCCSD-nél ez **pontosan a
  Hartree–Fock állapot**, azaz fizikailag értelmes, determinisztikus kiindulás
  (nem véletlen), ami egyúttal a barren-plateau kockázatot is csökkenti (R7).
- **Nincs `qiskit_algorithms` import** a `src/vqebd/` alatt. Ezt statikus teszt
  kényszeríti ki (`tests/unit/test_no_forbidden_imports.py`).

### Mért igazolás (TR-000, 1. kör / 7. lépés)

H2 / 0.735 Å / STO-3G, parity-leképezés 2 qubites redukcióval, UCCSD (3 paraméter),
`StatevectorEstimator` + SciPy `SLSQP`, `x0 = 0`:

| Mennyiség | Érték |
|---|---|
| PySCF FCI (L0) | −1.13730604 Ha |
| Egzakt diagonalizáció (L1) | −1.13730604 Ha (eltérés 1.3 × 10⁻¹⁵) |
| **Saját VQE (L2)** | **−1.13730604 Ha (eltérés 7.6 × 10⁻¹⁵)** |
| Iterációk | 4 |
| Célfüggvény-kiértékelések | 17 |

Azaz a saját hurok **gépi pontossággal** eltalálja a referenciát — nagyságrendekkel
a kémiai pontosság (1.6 mHa) alatt.

## Következmények

### Pozitív
- Egy kódút mind az öt referenciaszintre (L0–L3b).
- A Qiskit 2.x-re való átállás a `requirements.lock` és a `qiskit-nature` cseréjére
  korlátozódik; a VQE-mag változatlan marad.
- Az optimalizáló-választás a benchmark **dimenziójává** válik (Fázis 5): ugyanazon
  molekulára több optimalizáló összehasonlítható.

### Negatív és kezelés
- **Saját kód → saját hibalehetőség.** Kezelés: a Fázis 1 három tesztkört ír elő
  (funkcionális / robusztussági / keresztvalidációs, Mesterterv 9.3), és a
  keresztvalidáció két **független** referenciához mér (PySCF FCI, egzakt diagonalizáció).
- **A `qiskit-algorithms` telepítve marad** (a `qiskit-nature` függősége). Ez elfogadott:
  telepítve van, de nem hívjuk; a tiltást automatikus teszt őrzi.

## Felülvizsgálati feltétel

- Ha a `qiskit-nature` olyan verzióra vált, amely nem igényli a `qiskit-algorithms`-t,
  a függőség eltávolítható.
- Ha a saját hurok bármely fázisban nem éri el a kémiai pontosságot ott, ahol a
  `qiskit-algorithms` elérné, a döntést újra kell tárgyalni.

## Hivatkozások

- [peruzzo2014], [mcclean2016], [tilly2022] — VQE elmélet
- [romero2019] — UCCSD ansatz és a HF kezdőállapot indoklása
- [virtanen2020] — SciPy; [nelder1965], [powell1994], [kraft1988], [spall1992] — optimalizálók
- Mérési jegyzőkönyv: [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
