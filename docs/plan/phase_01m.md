# Fázis 1M — Többplatformos validáció (bővített terv)

| | |
|---|---|
| **Fázis** | 1M (új — nem szerepel az alaptervben) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Státusz** | **Elfogadott — végrehajtás alatt** |
| **Célverzió** | `v0.3.0` |
| **Előzmény** | [`phase_01.md`](phase_01.md), [`TR-F01`](../testing/TR-F01_vqe_mag.md), [ADR-0006](../adr/ADR-0006-tobbplatformos-architektura.md) |

---

## 1. Miért van szükség erre a fázisra

Az alapterv egyetlen kvantum-szoftverkörnyezetet (Qiskit) feltételez. A Fázis 1
lezárásakor a hibaforrások láncát (L0 → L1 → L2) **egyetlen implementációval**
mértük.

A hiányzó biztosíték: egy **szisztematikus, minden szinten azonos irányban ható**
hiba rejtve maradna. A legjellemzőbb ilyen a **qubit-sorrend (endianness)**
elrontása — szimmetrikus Hamilton-operátoron akár helyes energiát is adhat, és
csak egy aszimmetrikus rendszernél (LiH, BeH2 — Fázis 5) bukna ki, amikor már a
teljes batch-infrastruktúra rá épül.

Emellett három gyakorlati haszon:

| Haszon | Miért számít |
|---|---|
| **Kvótavédelem** | Az IBM Open Plan **10 perc QPU-idő / 28 nap**. A Fázis 2 kódja két kvótamentes platformon próbálható ki előbb. |
| **Skálázás** | A qsim **4–9× gyorsabb** a Cirqnél (mért, 12–24 qubit) — a Fázis 5 nagyobb rendszereihez lényeges. |
| **Publikációs érték** | A platformok pontosság–sebesség kompromisszuma **önálló benchmark-eredmény**. |

---

## 2. Célkitűzések

| # | Cél |
|---|---|
| C1M.1 | A `platform` önálló benchmark-dimenzióvá tétele, az adatsémáig átvezetve. |
| C1M.2 | Qiskit → Cirq konverzió a **Hamilton-operátorra** és az **áramkörre**, mátrixszinten validálva. |
| C1M.3 | A Fázis 1 összes elfogadási kritériumának teljesítése **mindhárom platformon**. |
| C1M.4 | A platformok közti eltérés **számszerűsítése és megmagyarázása** — nem elrejtése. |
| C1M.5 | A `VQEResult` platformfüggetlen: a Fázis 4 adatsémája már ezzel készül. |

---

## 3. Architektúra

### 3.1 Egyetlen forrás, három kiértékelő

```
   PySCF + Qiskit Nature  (a fizikai feladat EGYETLEN definíciója)
            │
     ┌──────┴────────────────────────────┐
     │ SparsePauliOp                     │ QuantumCircuit (UCCSD)
     │                                   │
     │  to_cirq_pauli_sum()              │  to_cirq_circuit()
     │  (ADR-0006, reversed qubit order) │  (explicit kapu-leképezés)
     ▼                                   ▼
  cirq.PauliSum                      cirq.Circuit
     │                                   │
     └──────────────┬────────────────────┘
                    │
   ┌────────────────┼────────────────┐
   ▼                ▼                ▼
qiskit_statevector  cirq_simulator   qsim
 complex128          complex128      complex64
```

### 3.2 Új és módosuló modulok

```
src/vqebd/
├── platforms.py                      ÚJ  — platform-metaadatok, tolerancia, képességek
├── backends/
│   ├── estimators.py                 MÓD — a gyár bővül; BackendKind átnevezve
│   ├── conversion.py                 ÚJ  — Qiskit → Cirq konverzió
│   └── cirq_estimators.py            ÚJ  — CirqEnergyEvaluator, QsimEnergyEvaluator
├── config.py                         MÓD — BackendKind bővítése
└── vqe/result.py                     MÓD — platform + pontosság a rekordba
```

### 3.3 Törő változás: a `BackendKind` átnevezése

| Régi | Új |
|---|---|
| `"statevector"` | `"qiskit_statevector"` |

Indok: a platform nélküli név a három egzakt szimulátor bevezetésével
félreérthetővé vált. A projekt `0.x` szakaszában van; a `CHANGELOG` rögzíti.

---

## 4. A konverzió specifikációja

### 4.1 Hamilton-operátor: `SparsePauliOp` → `cirq.PauliSum`

**Qubit-sorrend.** A Qiskit Pauli-címke little-endian: a **jobb szélső** karakter
a 0. qubit. A `SparsePauliOp.to_matrix()` a 0. qubitet tekinti a legkisebb
helyiértéknek. A Cirq a `qubit_order` lista **elején** álló qubitet tekinti a
legnagyobb helyiértékűnek.

→ A mátrixegyezéshez a Cirq oldalán **`reversed(qubits)`** sorrend kell.
Mért bizonyíték: ADR-0006, „A konverzió két kritikus pontja".

**Validálási követelmény:** a konverzió helyességét **mátrixszinten** kell
igazolni (`max|M_cirq − M_qiskit| < 1e-12`), **nem** energiaszinten. Egy
szimmetrikus Hamilton-operátoron a rossz sorrend véletlenül helyes energiát adhat.

### 4.2 Áramkör: `QuantumCircuit` → `cirq.Circuit`

- **Kapukészlet:** `rz, ry, rx, h, x, sx, cx, cz` — a Qiskit-áramkört előbb erre
  a bázisra transzpiláljuk.
- **Szélességmegőrzés:** minden qubitre `cirq.I` kerül, így az inaktív qubitek
  sem vesznek el. *(A Mitiq QASM-alapú konverziója pont ezt rontja el — TR-000, M3.)*
- **Átugrott utasítások:** `barrier`, `id`, `delay` — nincs fizikai hatásuk a
  zajmentes szimulációban.
- **Ismeretlen kapu:** azonnali `ValueError`, a kapu nevével. **Soha nem néma
  kihagyás.**

### 4.3 Globális fázis

A `QuantumCircuit.global_phase` az energiát nem befolyásolja (`⟨ψ|H|ψ⟩`
fázisinvariáns), ezért nem visszük át. Az állapotvektor-összehasonlítás emiatt
**abszolút átfedéssel** (`|⟨ψ₁|ψ₂⟩| = 1`) történik, nem elemenkénti egyenlőséggel.

---

## 5. Platformonkénti toleranciák

A toleranciát **a platform számábrázolása** határozza meg, nem az, „ami éppen
átmegy":

| Platform | Aritmetika | Gépi epszilon | Elfogadási tolerancia | Indok |
|---|---|---|---|---|
| `qiskit_statevector` | `complex128` | 2.2 × 10⁻¹⁶ | **1 × 10⁻⁹ Ha** | ~10⁷ × gépi epszilon, bőven a halmozódó hiba fölött |
| `cirq_simulator` | `complex128` | 2.2 × 10⁻¹⁶ | **1 × 10⁻⁹ Ha** | ugyanaz |
| `qsim` | **`complex64`** | 1.2 × 10⁻⁷ | **1 × 10⁻⁵ Ha** | ~10² × gépi epszilon; még így is **159×** a kémiai pontosság alatt |

Mindhárom tolerancia **nagyságrendekkel** a kémiai pontosság (1.59 × 10⁻³ Ha)
alatt van, tehát a fizikai következtetéseket egyik platform sem befolyásolja.

---

## 6. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-1M.1** | A `cirq-core 1.4.1` + `qsimcirq 0.22.1` a meglévő stackkel együtt települ | build + `requirements.lock` |
| **AC-1M.2** | **Hamilton-konverzió mátrixszinten egzakt:** `max\|M_cirq − M_qiskit\| < 1e-12` | automatikus teszt |
| **AC-1M.3** | **A rossz qubit-sorrend kimutathatóan hibás:** az egyenes sorrend mátrixa **eltér** | automatikus teszt (negatív irányú állítás) |
| **AC-1M.4** | Áramkör-konverzió: `\|⟨ψ_cirq\|ψ_qiskit⟩\| = 1` (1e-9-ig), **és** a qubit-szám megegyezik | automatikus teszt |
| **AC-1M.5** | Ismeretlen kapu `ValueError`-t dob a kapu nevével | automatikus teszt |
| **AC-1M.6** | `cirq_simulator` energiája a Qiskittől < **1e-9 Ha**-ra | automatikus teszt |
| **AC-1M.7** | `qsim` energiája a Qiskittől < **1e-5 Ha**-ra | automatikus teszt |
| **AC-1M.8** | Mindhárom platform **kémiai pontosságon belül** van a Full CI-hez képest | automatikus teszt |
| **AC-1M.9** | Mindhárom platform **determinisztikus**: kétszeri futtatás bitre azonos | automatikus teszt |
| **AC-1M.10** | Mindhárom platformon teljesül a **variációs elv** | automatikus teszt |
| **AC-1M.11** | A `qsim` egyszeres pontossága **mérve és dokumentálva** (dtype + hibanagyságrend) | automatikus teszt + jegyzőkönyv |
| **AC-1M.12** | A `VQEResult` tárolja a `platform` és `precision` mezőket | automatikus teszt |
| **AC-1M.13** | A CLI `--backend` kapcsolóval mindhárom platform futtatható | integrációs teszt |
| **AC-1M.14** | `ruff`, `mypy --strict`, teljes tesztkészlet zöld | CI |
| **AC-1M.15** | Az IBM-hitelesítő adatok **biztonságosan** betölthetők, és a token nem szivárog | automatikus teszt |

---

## 7. Tesztelési terv (összefoglaló)

Részletek: [`TP-F01M`](../testing/TP-F01M_tobbplatform.md).

### Kör 1 — funkcionális
AC-1M.1 … AC-1M.15.

### Kör 2 — robusztussági és **negatív**

| Eset | Rontás | Elvárt bukás |
|---|---|---|
| **TC-N12** | A konverter qubit-sorrendjének megfordítása (`reversed` → egyenes) | `test_hamiltonian_conversion_matches_matrix` |
| **TC-N13** | Egy kapu kihagyása a konverter leképezéséből | `test_unknown_gate_raises` |
| **TC-N14** | A `qsim` toleranciájának 1e-12-re szigorítása | `test_qsim_agrees_with_qiskit` |

A **TC-N12 a legfontosabb**: ez bizonyítja, hogy a mátrixszintű teszt valóban
kiszúrja az endianness-hibát — azt a hibát, amely energiaszinten rejtve maradna.

### Kör 3 — keresztvalidáció

| Eset | Mit vizsgál |
|---|---|
| **TC-X1M1** | Qiskit ↔ Cirq ↔ qsim energia, mindhárom leképezéssel (3 × 3 = 9 kombináció) |
| **TC-X1M2** | Mindhárom platform ↔ PySCF Full CI (L0) |
| **TC-X1M3** | Cirq sajátérték-diagonalizáció ↔ Qiskit sajátérték-diagonalizáció (L1 két úton) |
| **TC-X1M4** | Disszociációs görbe mindhárom platformon (aszimmetrikus teszt: a Hamilton-operátor r-függő) |
| **TC-X1M5** | `cirq.Simulator(complex64)` ↔ `qsim` — a pontossági hipotézis igazolása |

A **TC-X1M4** külön fontos: a 0.735 Å-ös H2 Hamilton-operátora viszonylag
szimmetrikus. A disszociációs görbe **több, eltérő szerkezetű** Hamilton-operátort
vizsgál, így az esetleges sorrendhiba nagyobb eséllyel bukik ki.

---

## 8. IBM-hitelesítő adatok kezelése

A projekt gyökerében megjelent egy `IBM.token` fájl (IBM Cloud API-kulcs, JSON).

### 8.1 Már meglévő védelem (Fázis 0) — **ellenőrizve**

| Réteg | Állapot |
|---|---|
| `.gitignore:11: *.token` | ✅ kizárja |
| Bármely commitban? | ✅ **nincs** |
| `.dockerignore:9: *.token` | ✅ az image-be sem kerül |

### 8.2 Ebben a fázisban készül

- `src/vqebd/credentials.py` — hitelesítő adatok betöltése **három forrásból**,
  prioritási sorrendben: környezeti változó → `.env` → `IBM.token`.
- A token **soha nem kerül** naplóba, kivételüzenetbe, `repr()`-be vagy
  eredményrekordba. A betöltött objektum maszkolt `__repr__`-t kap.
- Automatikus teszt a maszkolásra és a szivárgás-ellenőrzésre.
- **A tényleges QPU-futtatás továbbra is a Fázis 2.** Itt csak a hitelesítés
  előkészítése történik; a `VQEBD_ALLOW_HARDWARE=false` alapértelmezés marad.

---

## 9. Vizualizáció

A felhasználói igény: legyen látható, **mi az elvárt, mi az igazolt, és mi valódi
mérés**.

Szállítandó:

1. `scripts/gen_report_figures.py` — **reprodukálható** ábrák generálása
   (matplotlib) a `docs/figures/` mappába, a tényleges mérési adatokból.
2. Egy **állapot-mátrix**: minden elfogadási kritériumhoz az elvárt érték, a mért
   érték, az ellenőrzés módja (automatikus / manuális / még nincs) és az állapot.
3. A Fázis 7 Streamlit-dashboardja ezt később átveszi; ez most statikus,
   verziózott műtermék.

**Alapelv:** az ábrák **generáltak**, nem kézzel rajzoltak. A bemenetük a
tényleges mérési eredmény, így nem csúszhatnak el a valóságtól.

---

## 10. Amit ez a fázis **nem** tartalmaz

- Zaj (→ Fázis 1b), valódi QPU-futtatás (→ Fázis 2), hibaenyhítés (→ Fázis 3).
- OpenFermion-alapú független kémiai út (ADR-0006 szerint kizárva a
  `numpy` ütközés miatt; Fázis 10 lehetőség).
- Cirq-alapú *hardver* (Google QPU nem elérhető ebben a projektben).

---

## 11. Kilépési feltétel

1. Mind a 15 elfogadási kritérium dokumentáltan teljesül a
   [`TR-F01M`](../testing/TR-F01M_tobbplatform.md) jegyzőkönyvben;
2. a három tesztkör lefutott, a negatív esetek a várt módon buktak;
3. `docs/01m_multiplatform.md` elkészült;
4. a vizualizációs műtermékek generálva és verziózva;
5. `CHANGELOG.md` `0.3.0` bejegyzése kész;
6. `v0.3.0` annotált Git-tag létrehozva.

---

## 12. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
