# 01b — Véges-lövéses és zajos szimuláció (Fázis 1b)

| | |
|---|---|
| **Dokumentum** | `docs/01b_noisy_simulation.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Projektverzió** | 0.4.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1b — Véges lövésszám és zajmodellek |

---

## 1. Mit csinál ez a fázis

A Fázis 1b két új szimulációs szintet valósít meg a VQE referencialáncban,
amelyek elválasztják a **véges mintavételi (shot) zajt** és a **valódi hardvereszköz
kalibrációs zaját** anélkül, hogy valódi IBM QPU kvótát fogyasztanának:

1. **L3a (`qiskit_aer_shot`)**: Véges mintavételezés (8192 lövés), ideális
   kvantumkapukkal (nincs fizikai relaxáció és depolarizáció).
2. **L3b (`qiskit_aer_noisy`)**: Kalibrációs zajszimuláció `FakeManilaV2`
   5-qubites hardverprofil segítségével (T1/T2 relaxáció, termikus zaj, 1-qubites
   és 2-qubites kapuhibák, kiolvasási hibák).

```bash
# L3a futtatás (8192 lövés, COBYLA optimalizálóval)
docker run --rm vqebd:0.4.0 python -m vqebd --backend qiskit_aer_shot --optimizer COBYLA

# L3b futtatás (FakeManilaV2 zajmodell, COBYLA optimalizálóval)
docker run --rm vqebd:0.4.0 python -m vqebd --backend qiskit_aer_noisy --optimizer COBYLA
```

---

## 2. A kibővített referenciaszintek

```
L0  Full CI (PySCF, független számítás)
 └── L1  Egzakt diagonalizáció (Qiskit qubit-Hamiltoni)
      └── L2  VQE zajmentes állapotvektoron (qiskit_statevector, cirq_simulator, qsim)
           └── L3a VQE véges lövésszámmal (qiskit_aer_shot, 8192 shot)
                └── L3b VQE hardver-zajmodellel (qiskit_aer_noisy, FakeManilaV2)
                     └── L4  VQE hibaenyhítéssel (Fázis 3, Mitiq ZNE)
                          └── L5  Valódi IBM QPU futtatás (Fázis 2)
```

### Példa kimenet (L3a — véges mintavétel)

```
Molekula ............ H2 [sto3g]
Geometria ........... H 0 0 0; H 0 0 0.735000
Leképezés ........... parity (2-qubit redukcióval)
Áramkör ............. 2 qubit, 3 paraméter, 5 Pauli-tag
Backend ............. qiskit_aer_shot [qiskit, complex128]
Optimalizáló ........ COBYLA (0 iteráció, 116 kiértékelés)

Energiák (Hartree):
  Hartree–Fock ...... -1.1169989968
  L0  Full CI ....... -1.1373060358
  L1  egzakt diag. .. -1.1373060358
  L3a VQE (shot) .... -1.1213780162

Hibák:
  leképezés (L1−L0) . +1.332e-15 Ha
  ansatz+zaj (L3−L1)  +1.593e-02 Ha
  referenciához ..... +1.593e-02 Ha
  korreláció vissza . 21.5640 %

Kémiai pontosságon belül (|Δ| < 1.6 mHa): NEM
Variációs elv (E_VQE ≥ E_egzakt): teljesül
Konvergált: igen (Optimization terminated successfully.)
Futásidő: 5.315 s
Konfiguráció-ujjlenyomat: b10bff4dce6b
```

---

## 3. Fontos architekturális tanulságok

### 3.1 Véges differenciák és zajos célfüggvény (Gradiens-biztonság)

A gradiens-alapú optimalizálók (pl. `SLSQP`, `L-BFGS-B`) a gradiens vektort véges
differenciákkal közelítik:
$$g_i \approx \frac{E(\theta + h e_i) - E(\theta)}{h}$$
ahol a SciPy alapértelmezett lépésköze $h \approx \sqrt{\varepsilon_{64}} \approx 1.49 \times 10^{-8}$.

Ha a célfüggvény zaja $\sigma \sim 10^{-2}\ \text{Ha}$ (mintavételi vagy hardverzaj),
akkor a differencia számlálóját a zaj dominálja, a tört értéke pedig több nagyságrenddel
eltér a valódi gradienstől. A `vqebd.platforms` modul erre automatikusan
`RuntimeWarning` figyelmeztetést ad, és deriváltmentes algoritmust (pl. `COBYLA`, `Powell`)
javasol.

### 3.2 Transzpiláció és ISA Layout

Valódi backend vagy FakeBackend esetén az áramkört transzpilálni kell az eszköz
fizikai topológiájára (pl. `FakeManilaV2` esetén 5 fizikai qubit). Az eredeti
2-qubites Pauli-operátor nem értékelhető ki közvetlenül az 5-qubites transzpilált
áramkörön, ezért elengedhetetlen a layout illesztése:
```python
isa_observable = observable.apply_layout(isa_circuit.layout)
```

### 3.3 Determinizmus sztochasztikus környezetben

Az ADR-0005 elveinek megfelelően az összes véletlenforrás (transzpiláció, szimulátor
zaj-mintavételezés, kezdeti pont) determinisztikusan származtatott seedeket kap a
`SeedSet` objektumon keresztül. Azonos konfiguráció és seed mellett a futás bitre
azonos lebegőpontos számot eredményez.
