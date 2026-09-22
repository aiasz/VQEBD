# ADR-0006 — Többplatformos architektúra: Qiskit, Cirq és qsim

| | |
|---|---|
| **Azonosító** | ADR-0006 |
| **Cím** | A platform mint önálló benchmark-dimenzió: Qiskit ↔ Cirq ↔ qsim |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-22 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 1M (új), 1b, 2, 3, 4, 5, 7 |
| **Függ** | [ADR-0001](ADR-0001-technologiai-stack.md), [ADR-0002](ADR-0002-sajat-vqe-hurok.md) |
| **Bizonyíték** | [`TR-000`](../testing/TR-000_spike.md) 5–6. kör, [`TR-F01M`](../testing/TR-F01M_tobbplatform.md) |

---

## Kontextus

Az alapterv egyetlen kvantum-szoftverkörnyezetet feltételez (Qiskit). A projekt
célja azonban **benchmark**, és egy benchmark hitelessége azon áll, hogy az
eredményei **nem egyetlen implementáció sajátosságai**.

Két, egymást kiegészítő platform áll rendelkezésre:

| Platform | Mit ad | Korlát / kvóta |
|---|---|---|
| **IBM Quantum Platform** (Qiskit) | Valódi 100+ qubites QPU-k **és** lokális szimulátor (Aer) | Open Plan: 10 perc QPU-futásidő / 28 nap; 20 perc felhasználás után egyszeri +180 perc / 12 hónap |
| **Google Cirq + qsim** | Python-keretrendszer, saját gépen futó, C++-ban optimalizált szimulátor | Teljesen ingyenes, **nincs kvóta**. Cirq beépített szimulátora ~20 qubitig kényelmes, qsim jóval nagyobb rendszerekig |

### A probléma, amit ez megold

A Fázis 1 lezárásakor a hibaforrások láncát (L0 → L1 → L2) egyetlen
implementációval mértük. Ha a Qiskit `StatevectorEstimator`-ában lenne hiba, azt
a PySCF Full CI kiszúrná — de **csak addig, amíg a hiba az energiában
jelentkezik**. Egy szisztematikus, minden szinten azonos irányban ható hiba
(pl. rossz qubit-sorrend, ami szimmetrikus Hamilton-operátoron „kioltja
magát") rejtve maradna.

Egy **független implementáció** ezt a maradék kockázatot szünteti meg.

### A kvótakérdés

A Fázis 2-től a valódi hardver kvótás. Egyetlen hibás áramkör-konstrukció, amely
csak QPU-n derül ki, elégetheti a 10 perces keretet. Egy **kvótamentes, de
független** második szimulátor-platform ezt a kockázatot is csökkenti.

---

## Döntés

**A platform önálló benchmark-dimenzióvá válik**, a molekula, a leképezés, az
ansatz és az optimalizáló mellett.

### A platform-backend azonosítók

A konfiguráció egyetlen `backend` mezőt hordoz, amely **platformot és
végrehajtási módot együtt** azonosít. Ez kizárja az érvénytelen kombinációkat
(pl. „Cirq + IBM QPU").

| `backend` | Platform | Végrehajtás | Pontosság | Fázis |
|---|---|---|---|---|
| `qiskit_statevector` | Qiskit | egzakt állapotvektor | `complex128` | **1M** ✅ |
| `cirq_simulator` | Cirq | egzakt állapotvektor | `complex128` | **1M** ✅ |
| `qsim` | Cirq/qsim | egzakt állapotvektor, C++ | **`complex64`** | **1M** ✅ |
| `qiskit_aer_shot` | Qiskit | véges lövésszám | — | 1b |
| `qiskit_aer_noisy` | Qiskit | zajos szimuláció | — | 1b |
| `qsim_noisy` | Cirq/qsim | zajos szimuláció (csatorna-mintavétel) | — | 1b |
| `ibm_qpu` | IBM Quantum | valódi hardver | — | 2 |

> **Elnevezési változás.** A Fázis 1 `"statevector"` azonosítója
> `"qiskit_statevector"`-ra változik. Ez törő változás, de a projekt `0.x`
> szakaszában van, és az egyértelműség itt fontosabb a visszafelé
> kompatibilitásnál. A `CHANGELOG` rögzíti.

### Az architektúra: egyetlen forrás, több kiértékelő

A kulcsdöntés, hogy a **fizikai feladat definíciója egyetlen helyen születik**
(PySCF + Qiskit Nature), és onnan **konvertálódik** a másik platformra:

```
        PySCF + Qiskit Nature
                 │
        SparsePauliOp (qubit-Hamiltoni)      QuantumCircuit (UCCSD ansatz)
                 │                                    │
        ┌────────┴────────┐                  ┌────────┴────────┐
        │                 │                  │                 │
   Qiskit natív     cirq.PauliSum       Qiskit natív      cirq.Circuit
        │                 │                  │                 │
        └──────► qiskit_statevector ◄────────┘                 │
                          │                                    │
                  cirq_simulator ◄──────────────────────────────┤
                          │                                    │
                        qsim ◄────────────────────────────────── ┘
```

**Miért így, és nem független kémiával (OpenFermion) mindkét oldalon?**

| | Közös Hamiltoni (**választott**) | Független Hamiltoni (OpenFermion) |
|---|---|---|
| Mit izolál | **a szimulátort** — a fizikai feladat bizonyítottan azonos | a teljes láncot, de nem mondja meg, **hol** az eltérés |
| Függőségi kockázat | a konverzió a mi kódunk, tesztelhető | az `openfermion 1.8.1` `cirq-core>=1.6.0`-t követel → `numpy~=2.1` → **ütközik az ADR-0001 stackkel** |
| Kémiai keresztvalidáció | már megvan: PySCF FCI (L0) ↔ Qiskit leképezés (L1), 1.33 × 10⁻¹⁵ Ha | ugyanaz, más úton |

A kémiai réteget tehát **már validáltuk** egy független implementációval
(PySCF Full CI). A platform-dimenzió célja ezért a **szimulátor-réteg**
független ellenőrzése — és ehhez az azonos bemenet a helyes kísérleti elrendezés,
nem hiányosság.

*(Az OpenFermion-alapú, teljesen független kémiai út a Fázis 10 lehetséges
bővítése, ha a numpy-korlát feloldódik.)*

---

## A konverzió két kritikus pontja

### 1. Qubit-sorrend (endianness) — **mért, nem feltételezett**

A Qiskit **little-endian**: a Pauli-címke jobb szélső karaktere a 0. qubit, és a
`to_matrix()` a 0. qubitet tekinti a legkisebb helyiértéknek. A Cirq a
`qubit_order` listában **elöl álló** qubitet tekinti a legnagyobb helyiértékűnek.

Mért bizonyíték (H2, 2 qubit, 5 Pauli-tag — TR-000 5. kör):

| Qubit-sorrend a `PauliSum.matrix()` hívásban | `max\|M_cirq − M_qiskit\|` |
|---|---|
| `[q0, q1]` (egyenes) | **1.59** ❌ |
| `[q1, q0]` (**fordított**) | **0.00 × 10⁰** ✅ |

Ugyanez az állapotvektorra:

| Qubit-sorrend | `\|⟨ψ_cirq\|ψ_qiskit⟩\|` |
|---|---|
| egyenes | 0.2217 ❌ |
| **fordított** | **1.000000000000** ✅ |

> Ez a projekt egyik legveszélyesebb rejtett hibaforrása lett volna. Szimmetrikus
> Hamilton-operátoron a rossz sorrend **véletlenül helyes energiát is adhat**, és
> csak egy aszimmetrikus rendszernél (LiH, BeH2 — Fázis 5) bukna ki. Ezért a
> konverziót **mátrixszinten** validáljuk, nem energiaszinten.

### 2. Áramkör-konverzió qubit-vesztés nélkül

A Mitiq QASM-alapú konverziója **eldobja az inaktív qubiteket** (TR-000, M3).
Ezt a hibát itt nem ismételjük meg: a konverter **explicit kapu-leképezést**
használ (`rz, ry, rx, h, x, sx, cx, cz` → cirq megfelelők), és minden qubitre
`cirq.I` azonosságot helyez, így a szélesség megmarad.

Ismeretlen kapu esetén **azonnali `ValueError`**, nem néma kihagyás.

---

## Mért eredmények (H2, 0.735 Å, STO-3G)

### Energia-egyezés

| Platform | E (Ha) | Eltérés a Qiskittől |
|---|---|---|
| `qiskit_statevector` | −1.137306035753 | referencia |
| `cirq_simulator` | −1.137306035753 | **−2.22 × 10⁻¹⁵** |
| `qsim` | −1.137305744285 | **+2.91 × 10⁻⁷** |

### A qsim eltérésének oka — **egyszeres pontosság**

Nem hiba, hanem tervezési döntés a qsim oldalán:

| Mérés | Eredmény |
|---|---|
| `cirq.Simulator` állapotvektor dtype | `complex128` |
| **`qsimcirq` állapotvektor dtype** | **`complex64`** |
| `QSimOptions` pontosság-kapcsoló | **nincs** (mezők: `max_fused_gate_size`, `cpu_threads`, `ev_noisy_repetitions`, `use_gpu`, `gpu_mode`, `gpu_state_threads`, `gpu_data_blocks`, `verbosity`, `denormals_are_zeros`) |
| `cirq.Simulator(dtype=complex64)` hibája | +1.93 × 10⁻⁸ |
| `qsimcirq` hibája ugyanazon áramkörön | +1.21 × 10⁻⁸ |

A két utolsó sor **azonos nagyságrendje** bizonyítja, hogy az eltérés forrása a
32 bites lebegőpontos aritmetika, nem implementációs hiba.

**Ez a benchmark szempontjából kifejezetten értékes információ**, nem probléma:
a qsim hibája (~10⁻⁷ Ha) **négy nagyságrenddel** a kémiai pontosság
(1.59 × 10⁻³ Ha) alatt van.

### Teljesítmény (GHZ-lánc + forgatások, egy szálon)

| Qubit | `cirq.Simulator` | `qsim` | Gyorsulás |
|---|---|---|---|
| 12 | 0.003 s | 0.001 s | 4.5× |
| 16 | 0.010 s | 0.001 s | 6.8× |
| 20 | 0.119 s | 0.010 s | 11.9× |
| **24** | **17.380 s** | **0.791 s** | **22.0×** |

A `qsim` alapértelmezett `cpu_threads = 1`. Több szál gyorsítana, de a
lebegőpontos összegzés sorrendje szálszám-függő lenne — ez sértené az
[ADR-0005](ADR-0005-determinizmus.md) bitre azonossági követelményét. **A
determinizmus elsőbbséget élvez a sebességgel szemben**; a szálszám
konfigurálható, de az alapértelmezés 1 marad, és a rekord tárolja.

Mért determinizmus: a `qsim` háromszori futtatása **bitre azonos** eredményt ad.

---

## Következmények

### Pozitív

- A szimulátor-réteg **független implementációval** validált.
- A Fázis 2 hardveres kódja kvótamentesen, **két** platformon próbálható.
- A qsim a Fázis 5 nagyobb rendszereihez (LiH 10–12 qubit, BeH2 12–14 qubit)
  nagyságrendi gyorsulást ad.
- A pontosság–sebesség kompromisszum **mért, dokumentált benchmark-eredmény**,
  amely önmagában is publikációs érték.

### Negatív és kezelés

| Kockázat | Kezelés |
|---|---|
| A `cirq-core` 1.5.0-tól `numpy>=1.25`-öt, 1.7.0-tól `numpy~=2.1`-et követel → az ADR-0001 stackkel ütközne | **`cirq-core==1.4.1`** rögzítve; ez egyúttal a Mitiq `cirq-core<1.5.0` pinjével is kompatibilis (Fázis 3) |
| Az `openfermion` nem illeszthető a stackbe | Nem is szükséges — a kémiai keresztvalidációt a PySCF Full CI adja |
| A saját konverter karbantartási teher | Szűk, explicit kapukészlet; ismeretlen kapura azonnali hiba; mátrixszintű tesztek |
| A qsim `complex64` pontossága félrevezetheti az összehasonlítást | A rekord tárolja a platform pontosságát; a toleranciák platformonként külön definiáltak |

---

## Felülvizsgálati feltétel

Ezt az ADR-t újra kell tárgyalni, ha:

1. a Mitiq feloldja a `numpy<2` és a `cirq-core<1.5.0` korlátot — ekkor újabb
   `cirq-core` ág használható;
2. megjelenik kétszeres pontosságú qsim-változat;
3. az `openfermion` illeszthetővé válik a stackbe (független kémiai út).

## Hivatkozások

- Cirq: <https://quantumai.google/cirq> (ellenőrizve: 2026-09-22)
- qsim: <https://quantumai.google/qsim> (ellenőrizve: 2026-09-22)
- IBM Quantum Platform: <https://quantum.cloud.ibm.com/> (ellenőrizve: 2026-09-22)
- [jordan1928], [bravyi2002] — leképezések; [peruzzo2014], [tilly2022] — VQE
- Mérési jegyzőkönyvek: [`TR-000`](../testing/TR-000_spike.md),
  [`TR-F01M`](../testing/TR-F01M_tobbplatform.md)

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
