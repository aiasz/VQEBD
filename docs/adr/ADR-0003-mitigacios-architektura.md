# ADR-0003 — Pluginalapú hibaenyhítés, saját ISA-biztos ZNE

| | |
|---|---|
| **Azonosító** | ADR-0003 |
| **Cím** | Pluginalapú hibaenyhítési architektúra, saját ISA-biztos ZNE-implementációval |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 3, 5, 6, 7 |
| **Függ** | [ADR-0001](ADR-0001-technologiai-stack.md), [ADR-0002](ADR-0002-sajat-vqe-hurok.md) |
| **Bizonyíték** | [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md), 2–3. kör |

---

## Kontextus

Az alapterv Fázis 3-a egyetlen hibaenyhítési módszert nevez meg: **Mitiq ZNE**.
A spike három olyan tényt tárt fel, amely ezt önmagában kivitelezhetetlenné, illetve
elégtelenné teszi.

### Tény 1 (M3) — a Mitiq-konverzió eldobja az inaktív qubiteket

A Mitiq belső áramkör-reprezentációja a **Cirq**. A `qiskit → cirq` konverzió
(`mitiq.interface.mitiq_qiskit.conversions.from_qiskit`) QASM-en keresztül történik,
és **csak azokat a qubiteket tartja meg, amelyeken művelet van**.

Mért eset: H2/UCCSD `FakeManilaV2`-re transzpilálva (`optimization_level=3`):

```
qiskit ISA áramkör : 5 qubit, mélység 12, {rz: 8, sx: 7, cx: 2}
   from_qiskit()   -> cirq: 17 művelet, 2 qubit      <-- 3 qubit elveszett
   to_qiskit()     -> qiskit: 2 qubit
```

Az observable ugyanakkor `apply_layout()` után **5 qubites**, így a kiértékelés elszáll:

```
ValueError: The number of qubits of the circuit (2) does not match
            the number of qubits of the ()-th observable (5).
```

Ez a hiba **pont a Fázis 3-ban, valódi hardveren, kvótát égetve** jelentkezne.

### Tény 2 (M4) — a saját folding és a Mitiq folding bitre egyezik

A ZNE zajskálázása [giurgicatiron2020] szerint **unitáris hajtogatás** (unitary
folding): `U → U (U† U)^n`, ahol a zajszorzó `λ = 2n + 1`. Ezt Qiskitben közvetlenül
is elvégezhetjük, a qubit-szám és a regiszterek megőrzésével. Kereszt-validáció
(H2/UCCSD, `rz, sx, x, cx` bázis):

| λ | Mitiq `fold_global` kapuszám | Saját `fold_global` kapuszám | Egyezés |
|---|---|---|---|
| 1 | 23 | 23 | ✅ |
| 3 | 69 | 69 | ✅ |
| 5 | 115 | 115 | ✅ |

### Tény 3 (M5) — a readout-hibát a ZNE nem javítja

A unitáris hajtogatás **nem skálázza** a mérési (readout) hibát, mert a mérés nem
unitáris művelet. Mért readout-hibák `FakeManilaV2`-n:
`[0.0353, 0.0219, 0.0964, 0.0144, 0.0186]`. Ez a ZNE után is szisztematikus
maradékhibaként jelentkezik ([nation2021]).

### Tény 4 — licenckonfliktus

A Mitiq **GPL-3.0** licencű, a VQEBD **MIT**. A Mitiq kötelező, beépített
függőségként való használata a származtatott mű licencelését érintené.

## Probléma

Hogyan építsük fel a hibaenyhítési réteget úgy, hogy

1. ISA-áramkörökön is működjön (M3),
2. a Mitiq mint független referencia megmaradjon (M4),
3. a readout-hiba külön kezelhető legyen (M5),
4. a licenc tiszta maradjon,
5. és a benchmark új módszerekkel bővíthető legyen (Fázis 10)?

## Döntés

**Pluginalapú `MitigationStrategy` architektúra**, négy induló stratégiával.

### Közös interfész

```python
# src/vqebd/mitigation/base.py  (vázlat)
class MitigationStrategy(Protocol):
    name: str  # az adatsémába kerülő azonosító

    def describe(self) -> dict: ...  # a rekordba mentendő paraméterek
    def estimate(self, circuit, observable, estimator) -> MitigationResult: ...
```

A `MitigationResult` tartalmazza a mitigált értéket, a nyers (λ=1) értéket, a
skálázási pontokat és az illesztés diagnosztikáját — így a dashboard (Fázis 7)
az extrapolációt is meg tudja rajzolni, nem csak a végeredményt.

### A négy induló stratégia

| `name` | Modul | Mit csinál | Hol fut |
|---|---|---|---|
| `none` | `none.py` | Nyers érték, referencia. | mindenhol |
| `zne_local` | `zne.py` | **Saját, ISA-biztos** unitáris hajtogatás + extrapoláció. | mindenhol |
| `zne_mitiq` | `mitiq_zne.py` | Mitiq `execute_with_zne`, **logikai szinten**. | szimulátor, QPU |
| `zne_runtime` | `runtime_zne.py` | IBM Runtime beépített ZNE-je (`ResilienceOptionsV2`). | csak QPU |

Kiegészítő, **ortogonális** dimenzió (nem ZNE-variáns):

| `measurement_mitigation` | `true` / `false` | A readout-hiba külön kezelése (M5). |

Ez az adatsémában (Fázis 4) **önálló oszlop**, nem a `mitigation_type` értéke — így
a `zne_local × measurement_mitigation` kombinációk is mérhetők.

### `zne_local` — a saját implementáció specifikációja

- **Skálázás:** globális unitáris hajtogatás, `λ ∈ {1, 3, 5, …}` (páratlan egészek).
  A qubit-szám, a regiszterek és a `layout` változatlan marad → az observable illeszkedik.
- **Bázis-visszafordítás:** a hajtogatás `sxdg`-t hoz létre, amely nincs a backend
  bázisában. A folded áramkörre **`optimization_level=0`** transzpilálás fut
  (csak bázisfordítás, layout/routing nélkül, gate-összevonás nélkül) — különben az
  optimalizáló kioltaná a `U† U` párokat, és a hajtogatás értelmét vesztené.
- **Ismert korlát (dokumentálandó):** a bázis-visszafordítás nem lineárisan növeli a
  kapuszámot (mért: λ=1 → 19 kapu, λ=3 → 85, λ=5 → 151), mert az `sxdg` három kapura
  bomlik. A **kétqubites** kapuk száma viszont **pontosan lineáris** (2 / 6 / 10), és
  a hiba ezekben dominál. A rekord ezért eltárolja a tényleges `two_qubit_gate_count`
  értéket is, hogy a λ *mért* skálája utólag ellenőrizhető legyen.
- **Extrapolátorok:** `richardson` (Lagrange λ=0-ra), `linear`, `polynomial(deg)`,
  `exponential`. Mindegyik eltárolja az illesztés reziduumát.

### `zne_mitiq` — logikai szintű alkalmazás

Az M3 megkerülése: a Mitiq a **transzpilálás előtti, logikai** áramkört kapja, és a
fizikai leképezés az executorba kerül:

```python
def executor(cirq_circuit):
    qc = to_qiskit(cirq_circuit)  # logikai, 2 qubit
    isa = transpile(qc, backend, optimization_level=0)  # itt lesz fizikai
    obs = logical_observable.apply_layout(isa.layout)  # az observable követi
    return estimator.run([(isa, obs)]).result()[0].data.evs
```

### Mért eredmény (TR-000, 3. kör)

H2/UCCSD, `AerSimulator.from_backend(FakeManilaV2)`, λ ∈ {1, 3, 5}:

| Módszer | Energia (Ha) | Eltérés a referenciától |
|---|---|---|
| Referencia (L2, zajmentes) | −1.137306 | — |
| **Nyers, ISA (L3b)** | −1.121556 | **+15.75 mHa** |
| `zne_local` / richardson | −1.136959 | **+0.35 mHa** ✅ |
| `zne_local` / exponential | −1.136965 | **+0.34 mHa** ✅ |
| `zne_local` / quadratic | −1.136959 | +0.35 mHa ✅ |
| `zne_local` / linear | −1.136357 | +0.95 mHa ✅ |
| Nyers, logikai (`opt_level=0`) | −1.100236 | +37.07 mHa |
| `zne_mitiq` / richardson | −1.137885 | **−0.58 mHa** ✅ |
| `zne_mitiq` / linear | −1.132967 | +4.34 mHa |

*(✅ = kémiai pontosságon belül, |Δ| < 1.6 mHa)*

**Mellékes, de fontos megfigyelés:** a nyers hiba az `optimization_level=3`-mal
transzpilált ISA-áramkörön +15.75 mHa, a `optimization_level=0`-val transzpilált
logikai áramkörön +37.07 mHa. **A transzpilálási szint tehát maga is zajcsökkentő
tényező**, és önálló benchmark-dimenzióként kerül a sémába (`optimization_level`).

## Következmények

### Pozitív
- Az M3 hiba a fejlesztés első napján, kvóta nélkül elhárítva.
- A `zne_local` és a `zne_mitiq` **kölcsönös keresztvalidációja** a benchmark
  hitelességének erős érve (M4).
- A `measurement_mitigation` külön dimenzióként lefedi az M5-öt.
- A séma bővíthető: PEC, PEA, Clifford-data regression későbbi ciklusban (Fázis 10).

### Licenckezelés
- A `mitiq` a `requirements.txt`-ben **`# opcionális` jelöléssel**, külön
  `requirements-mitiq.txt` fájlban szerepel.
- A `src/vqebd/mitigation/mitiq_zne.py` a **csak függvényen belül** importálja a
  `mitiq`-et; hiánya esetén a stratégia nem regisztrálódik, és a rendszer
  a maradék három stratégiával **teljes értékűen működik**.
- Ezt automatikus teszt őrzi (`tests/unit/test_mitiq_optional.py`).
- A licencviszonyt a [`docs/references.md`](../references.md) „Licencfigyelem"
  szakasza és a `README.md` is rögzíti.

### Negatív és kezelés
- **Saját ZNE-implementáció karbantartási terhe.** Kezelés: a `zne_local` és a
  `zne_mitiq` egyezését integrációs teszt ellenőrzi, rögzített seeddel, minden CI-futásban.
- **A `zne_runtime` csak QPU-n tesztelhető.** Kezelés: az opciók összeállítását
  (`EstimatorOptions`) unit teszt ellenőrzi QPU nélkül; a tényleges futás
  a Fázis 2–3 manuális mérési jegyzőkönyvébe kerül.

## Felülvizsgálati feltétel

- Ha a Mitiq megoldja a qubit-vesztést (M3), a `zne_mitiq` ISA-szinten is futtatható lesz.
- Ha a `zne_local` és a `zne_mitiq` bármikor statisztikailag szignifikánsan eltér,
  a projekt **leáll**, és a hiba felderítése elsőbbséget élvez.

## Hivatkozások

- [temme2017], [li2017] — a ZNE elméleti alapja
- [giurgicatiron2020] — digitális ZNE, unitáris hajtogatás (a `zne_local` alapja)
- [larose2022] — Mitiq
- [nation2021] — skálázható mérési hibaenyhítés (M5 válasza)
- [endo2018], [vandenberg2023] — PEC (későbbi bővítés)
- [cai2023] — hibaenyhítés review
- [kim2023] — a ZNE gyakorlati határai nagy skálán
- Mérési jegyzőkönyv: [`docs/testing/TR-000_spike.md`](../testing/TR-000_spike.md)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
