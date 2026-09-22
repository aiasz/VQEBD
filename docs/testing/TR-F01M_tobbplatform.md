# TR-F01M — Fázis 1M mérési jegyzőkönyve (Többplatformos validáció)

| | |
|---|---|
| **Azonosító** | TR-F01M |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1M — Többplatformos validáció (Qiskit ↔ Cirq ↔ qsim) |
| **Vizsgált verzió** | `0.3.0` |
| **Tesztterv** | [`TP-F01M`](TP-F01M_tobbplatform.md) |
| **Státusz** | **Lezárva — mind a 15 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

| | |
|---|---|
| Elfogadási kritériumok | **15 / 15 teljesült** |
| Automatikus tesztek | **345 futott, 345 zöld, 0 hiba** — 34.8 s |
| Negatív tesztek | 11 / 11 az elvárt módon elbukott |
| Lint / formázás / típus | 0 / 0 / 0 hiba (68 fájl, mypy 41 forrásfájl) |
| **Qiskit ↔ Cirq egyezés** | **4.4 × 10⁻¹⁶ Ha** |
| **qsim eltérés** (Powell) | **2.9 × 10⁻⁸ Ha** |
| **Felderített csendes hibamód** | **1** (gradiens × egyszeres pontosság) |
| IBM Quantum hozzáférés | ✅ **működik** — 3 db 156 qubites Heron QPU |

---

## 2. Tesztkörnyezet

| | |
|---|---|
| Image | `vqebd:0.3.0` (`python:3.11-slim@sha256:da047cb8…95ba9`) |
| Új csomagok | **`cirq-core 1.4.1`**, **`qsimcirq 0.22.1`** |
| Tranzitív fa | 71 csomag (`requirements.lock`) |
| Determinizmus | `PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `qsim cpu_threads=1` |

### 2.1 Miért `cirq-core 1.4.1`, és nem újabb

Mért függőségfeloldás (`pip install --dry-run`, `python:3.11-slim`):

| Kombináció | Eredmény |
|---|---|
| `cirq-core 1.4.1` + `qsimcirq 0.22.1` + teljes stack | ✅ **feloldódik** |
| `cirq-core 1.6.1` + `mitiq 0.47.0` | ❌ **`ResolutionImpossible`** |

A `cirq-core` 1.5.0-tól `numpy>=1.25`-öt, az 1.7.0-tól `numpy~=2.1`-et követel;
utóbbi ütközik az ADR-0001 szerinti `numpy<2.0` kötöttséggel. Az 1.4.1 egyúttal a
Mitiq `cirq-core<1.5.0` pinjével is kompatibilis (Fázis 3 előkészítése).

---

## 3. Kör 1 — funkcionális tesztek

### 3.1 AC-1M.2 / AC-1M.3 — A Hamilton-konverzió mátrixszinten egzakt ✅

Ez a fázis **központi állítása**. Energiaszintű összehasonlítás nem lenne elég:
szimmetrikus operátoron a hibás qubit-sorrend is helyes energiát adhat.

| `PauliSum.matrix()` qubit-sorrendje | `max\|M_cirq − M_qiskit\|` | Ítélet |
|---|---|---|
| `[q0, q1]` (egyenes) | **1.59** | ❌ kimutathatóan hibás |
| `[q1, q0]` (**fordított**) | **0.00 × 10⁰** | ✅ **bitre egyezik** |

A teszt **kétirányú**: igazolja a helyes sorrend egyezését *és* azt, hogy a
helytelen kimutathatóan eltér. Enélkül az első állítás triviálisan teljesülne.

Mindhárom leképezésre (Jordan–Wigner 4q, paritás 2q, Bravyi–Kitaev 4q) egzakt.

### 3.2 AC-1M.4 / AC-1M.5 — Áramkör-konverzió ✅

| Ellenőrzés | Eredmény |
|---|---|
| `\|⟨ψ_cirq\|ψ_qiskit⟩\|` | **1.000000000000** (fordított sorrenddel) |
| ugyanez egyenes sorrenddel | 0.2217 ❌ |
| Szélességmegőrzés (4q áramkör, 2 aktív qubit) | **4 qubit megmaradt** ✅ |
| Ismeretlen kapu (`swap`) | `ValueError` a kapu nevével ✅ |

A szélességmegőrzés külön fontos: a Mitiq QASM-alapú konverziója pont ezt rontja
el (TR-000, M3). Ezt a hibát nem ismételtük meg.

### 3.3 AC-1M.6 … AC-1M.8 — Energia-egyezés ✅

Referencia-eset: H2, 0.735 Å, STO-3G, paritás-leképezés, platformonként a **mért**
ajánlott optimalizálóval.

| Platform | Optimalizáló | E (Ha) | Leképezési hiba | Ansatz-hiba | Teljes hiba | Kiért. |
|---|---|---|---|---|---|---|
| `qiskit_statevector` | SLSQP | −1.137306035753 | 1.33 × 10⁻¹⁵ | 7.99 × 10⁻¹⁵ | **9.33 × 10⁻¹⁵** | 14 |
| `cirq_simulator` | SLSQP | −1.137306035753 | 1.33 × 10⁻¹⁵ | 7.55 × 10⁻¹⁵ | **8.88 × 10⁻¹⁵** | 14 |
| `qsim` | Powell | −1.137306006762 | 1.33 × 10⁻¹⁵ | 2.90 × 10⁻⁸ | **2.90 × 10⁻⁸** | 409 |

![A hibalánc szétbontása platformonként](../figures/fig01_hibalanc.png)

**Qiskit ↔ Cirq eltérés: 4.4 × 10⁻¹⁶ Ha** — két teljesen különböző kódbázis
(IBM és Google) gépi pontossággal egyezik.

### 3.4 AC-1M.9 — Determinizmus platformonként ✅

Mindhárom platform **bitre azonos** eredményt ad kétszeri futtatásra. A qsim
esetében ez a `cpu_threads = 1` beállításnak köszönhető: több szálon a
lebegőpontos összegzés sorrendje futásonként változna.

### 3.5 AC-1M.11 — A qsim egyszeres pontossága ✅

| Mérés | Eredmény |
|---|---|
| `cirq.Simulator` állapotvektor dtype | `complex128` |
| **`qsimcirq` állapotvektor dtype** | **`complex64`** |
| `QSimOptions` pontosság-kapcsoló | **nincs** |
| `cirq.Simulator(dtype=complex64)` hibája ugyanazon áramkörön | +1.93 × 10⁻⁸ |
| `qsimcirq` hibája | +1.21 × 10⁻⁸ |

Az utolsó két sor **azonos nagyságrendje** bizonyítja, hogy az eltérés forrása a
32 bites aritmetika, nem implementációs hiba.

### 3.6 AC-1M.15 — Titokkezelés ✅

| Ellenőrzés | Eredmény |
|---|---|
| `IBM.token` a `.gitignore`-ban | ✅ `*.token` (15. sor) |
| Bármely commitban? | ✅ **nincs** |
| `.dockerignore`-ban | ✅ `*.token` |
| `repr()` tartalmazza-e a tokent | ✅ **nem** (maszkolt) |
| Hibaüzenet tartalmazza-e | ✅ **nem** |
| CRN maszkolása a kimenetben | ✅ `quantum-computing / us-east / <maszkolva>` |

---

## 4. Kör 2 — negatív tesztek ✅

A [`scripts/negative_test_harness.py`](../../scripts/negative_test_harness.py)
izolált repó-másolaton ront el dolgokat.

```
Eredmény: 11/11 negatív eset bukott el az elvárt módon.
Minden védelmi teszt bizonyítottan képes hibát jelezni.
```

---

## 5. Kör 3 — keresztvalidáció

### 5.1 Optimalizáló × platform mátrix — **a fázis legfontosabb eredménye**

![Optimalizáló × platform mátrix](../figures/fig02_optimalizalo_matrix.png)

Hiba a Full CI-hez képest (Ha):

| Optimalizáló | Típus | Qiskit | Cirq | **qsim** |
|---|---|---|---|---|
| SLSQP | gradiens | 9.33 × 10⁻¹⁵ | 8.88 × 10⁻¹⁵ | **1.46 × 10⁻² ✗** |
| L-BFGS-B | gradiens | 4.44 × 10⁻¹⁵ | 8.88 × 10⁻¹⁶ | 1.27 × 10⁻⁴ |
| BFGS | gradiens | 2.22 × 10⁻¹⁵ | 1.33 × 10⁻¹⁵ | 3.24 × 10⁻⁴ |
| CG | gradiens | 1.78 × 10⁻¹⁵ | 1.33 × 10⁻¹⁵ | 3.24 × 10⁻⁴ |
| TNC | gradiens | 9.64 × 10⁻¹⁴ | 4.44 × 10⁻¹⁵ | **2.03 × 10⁻² ✗** |
| COBYLA | deriváltmentes | 3.55 × 10⁻¹⁵ | 8.88 × 10⁻¹⁶ | 4.14 × 10⁻⁷ ✅ |
| Powell | deriváltmentes | 1.33 × 10⁻¹⁵ | **0.00** | **2.90 × 10⁻⁸ ✅** |
| Nelder-Mead | deriváltmentes | 1.33 × 10⁻¹⁵ | 4.44 × 10⁻¹⁶ | **9.87 × 10⁻⁹ ✅** |

*(✗ = kémiai pontosság fölött)*

**Összegzés:** Qiskit 8/8 OK, Cirq 8/8 OK, **qsim 6/8** — a két bukás mindkettő
gradiens-alapú.

### 5.2 A magyarázat: zajszint vs véges-differencia lépésköz

![Gradiens-biztonság](../figures/fig03_gradiens_biztonsag.png)

| Platform | `f(x+h) − f(x)`, h = 1.49 × 10⁻⁸ | Becsült gradiens |
|---|---|---|
| `qiskit_statevector` | +6.66 × 10⁻¹⁶ | +4.47 × 10⁻⁸ ✅ |
| `cirq_simulator` | +2.22 × 10⁻¹⁶ | +1.49 × 10⁻⁸ ✅ |
| **`qsim`** | **−1.13 × 10⁻⁷** | **−7.61** ❌ |

A qsim becsült gradiense **nyolc nagyságrenddel** téves. A `complex64` gépi
epszilonja (1.19 × 10⁻⁷) **nagyobb** a lépésköznél (1.49 × 10⁻⁸).

> **Ez egyetlen platformon nem derülhetett volna ki.** Qiskiten és Cirqen mind a
> nyolc optimalizáló hibátlan. A hibamód a Fázis 1b-ben (lövészaj) vagy a
> Fázis 2-ben (hardverzaj) bukkant volna elő — ott viszont már **IBM-kvótát
> égetve**, és „sikeresen konvergált" futásnak álcázva.

### 5.3 Disszociációs görbe — eltérő geometriák ✅

![Disszociációs görbe](../figures/fig04_disszociacio.png)

A 0.735 Å-ös H2 Hamilton-operátora viszonylag szimmetrikus; a görbe **eltérő
szerkezetű** operátorokat vizsgál. Eltérés a Full CI-től (Ha):

| r (Å) | Qiskit | Cirq | qsim |
|---|---|---|---|
| 0.4 | 1.17 × 10⁻¹¹ | 1.15 × 10⁻¹¹ | 2.14 × 10⁻⁷ |
| 0.7 | 4.44 × 10⁻¹⁵ | 2.22 × 10⁻¹⁴ | 9.00 × 10⁻⁸ |
| 0.735 | 9.33 × 10⁻¹⁵ | 8.88 × 10⁻¹⁵ | 2.90 × 10⁻⁸ |
| 1.0 | 5.05 × 10⁻¹² | 5.01 × 10⁻¹² | 4.72 × 10⁻⁸ |
| 1.5 | 1.78 × 10⁻¹⁵ | 8.88 × 10⁻¹⁶ | 2.14 × 10⁻⁸ |
| 2.5 | 5.89 × 10⁻¹³ | 5.32 × 10⁻¹³ | 6.72 × 10⁻⁹ |

**Minden pont minden platformon kémiai pontosságon belül.** A legnagyobb qsim-hiba
(2.14 × 10⁻⁷ Ha) is **7 400-szor** a kémiai pontosság alatt van.

### 5.4 Skálázás ✅

![Skálázás](../figures/fig05_skalazas.png)

**3 ismétlésből a legrövidebb** (az időmérés zaja csak hozzáadni tud):

| Qubit | `cirq.Simulator` | `qsim` | Gyorsulás |
|---|---|---|---|
| 12 | 0.0024 s | 0.0006 s | 4.2× |
| 16 | 0.0046 s | 0.0009 s | 4.9× |
| 20 | 0.0747 s | 0.0082 s | 9.1× |
| 22 | 0.3703 s | 0.1039 s | 3.6× |
| 24 | 2.2274 s | 0.4697 s | 4.7× |

---

## 6. IBM Quantum hozzáférés (kvótamentes ellenőrzés)

A Fázis 2 előkészítéseként **olvasási** művelettel ellenőriztük a hozzáférést.
**Nem küldtünk be feladatot**, tehát QPU-időt nem fogyasztottunk.

### 6.1 Első kísérlet — hiányzó szolgáltatáspéldány

```
HIBA: IBMInputValueError: 'No matching instances found for the following filters: .'
── Diagnosztika ──
   API-kulcs érvényes      : IGEN
   Szolgáltatáspéldányok   : 0
```

A diagnosztika (IAM token-csere + Resource Controller lekérdezés) megállapította,
hogy az **API-kulcs érvényes**, de a fiókban nincs provisionált Qiskit Runtime
példány. A szkript ebből használható teendőt generált a rejtélyes hibaüzenet
helyett.

### 6.2 Második kísérlet — a CRN felvétele után ✅

```
Hitelesítő adat forrása : IBM.token (JSON, 'apikey' kulcs)
Token (maszkolva)       : C96******Rnz (44 karakter)
Csatorna                : ibm_quantum_platform
Példány (instance)      : quantum-computing / us-east / <maszkolva, 121 karakter>

Elérhető backendek: 3

név                      qubit   sor   2q hiba  státusz     típus
ibm_fez                    156     1    0.0028  üzemel      QPU Heron
ibm_marrakesh              156     0    0.0028  üzemel      QPU Heron
ibm_kingston               156     1    0.0020  üzemel      QPU Heron

Fázis 2 javaslat (legkisebb 2q hiba): ibm_kingston (156 qubit, 2q hiba 0.0020, sor: 1)
```

**A Fázis 2 ezzel feloldva.** A javasolt backend az `ibm_kingston` (legkisebb
kétqubites hibaarány).

---

## 7. Elfogadási kritériumok — összesítés

| # | Kritérium | Mért érték | Állapot |
|---|---|---|---|
| **AC-1M.1** | cirq + qsim telepítése | 71 csomag a lockban, pin ≡ lock | ✅ |
| **AC-1M.2** | Hamilton-konverzió mátrixszinten egzakt | `max\|ΔM\| = 0.00` | ✅ |
| **AC-1M.3** | Rossz sorrend kimutathatóan hibás | `max\|ΔM\| = 1.59` | ✅ |
| **AC-1M.4** | Áramkör-konverzió + szélességmegőrzés | átfedés 1.000000000000 | ✅ |
| **AC-1M.5** | Ismeretlen kapu `ValueError` | a kapu nevével | ✅ |
| **AC-1M.6** | Cirq ↔ Qiskit < 1e-9 Ha | **4.4 × 10⁻¹⁶** | ✅ |
| **AC-1M.7** | qsim ↔ Qiskit < 1e-5 Ha | **2.9 × 10⁻⁸** | ✅ |
| **AC-1M.8** | Mindhárom kémiai pontosságon belül | max 2.9 × 10⁻⁸ | ✅ |
| **AC-1M.9** | Determinizmus platformonként | 3/3 bitre azonos | ✅ |
| **AC-1M.10** | Variációs elv mindhárom platformon | teljesül | ✅ |
| **AC-1M.11** | qsim pontossága mérve | `complex64` igazolva | ✅ |
| **AC-1M.12** | A rekord tárolja a platformot | `platform`, `precision` | ✅ |
| **AC-1M.13** | CLI `--backend` | mindhárom fut | ✅ |
| **AC-1M.14** | ruff, mypy, tesztek | 0 / 0 / 345 zöld | ✅ |
| **AC-1M.15** | Titokkezelés | nincs szivárgás | ✅ |

---

## 8. A fázis során talált hibák és korrekciók

### H-10 — A gradiens-alapú optimalizálók csendben megbuknak egyszeres pontosságon

*Megtalálta:* a többplatformos validációs teszt (`test_multiplatform.py`).
*Ok:* a SciPy véges-differencia lépésköze (1.49 × 10⁻⁸) kisebb a qsim
célfüggvény-zajánál (1.13 × 10⁻⁷), ezért a becsült gradiens zajból származik.
*Tünete:* az optimalizáló **sikeresen konvergáltnak jelenti magát**, de 1.5 × 10⁻²
Ha hibát ad — ezerszer a kémiai pontosság fölött.
*Javítás:* a `PlatformInfo` mért `noise_floor_ha` értéket tárol, abból **számítja**
a `gradient_safe` besorolást, minden platformnak van mért ajánlott
optimalizálója, és a `run_vqe()` futásidejű `RuntimeWarning`-ot ad.
*Tanulság:* a **csendes** hibás eredmény veszélyesebb a hangos hibánál. Ahol egy
numerikus feltevés (itt: „a célfüggvény sima és pontos") sérülhet, ott a
rendszernek ki kell mondania.

### H-11 — Nem reprodukálható teljesítmény-állítás

*Megtalálta:* az ábragenerátor ismételt futtatása.
*Ok:* egy **egyszeri** időmérés 24 qubiten 22-szeres qsim-gyorsulást mutatott.
Ismételt méréssel ez nem volt reprodukálható.
*Javítás:* a skálázási mérés mostantól **3 ismétlésből a legrövidebbet** veszi (a
mérési zaj csak hozzáadni tud, elvenni nem). A valós tartomány **3.6–9.1×**.
Minden dokumentum javítva, a korrekció explicit megjegyzéssel.
*Tanulság:* **egyetlen időmérés nem mérés.** Egy benchmark-projektben egy
publikált teljesítményszám ismételhető eljárásból kell származzon.

### H-12 — Commitolt merge-konfliktusok

*Megtalálta:* a repó-állapot ellenőrzése a távoli repó csatolása után.
*Ok:* a `.gitignore` és a `LICENSE` fájlokban konfliktus-jelölők (`<<<<<<<`,
`=======`, `>>>>>>>`) kerültek **be a commitba**.
*Kockázat:* a `.gitignore` sérülése elvileg kinyithatta volna a titokvédelmet.
*Ellenőrzés:* a védelem **sértetlen maradt** — a `*.token` és `.env` minták
érvényesek voltak, a token egyetlen commitban sem szerepel.
*Javítás:* mindkét fájl kézzel feloldva; a `.gitignore` a helyi szabályok és a
GitHub Python-sablonjának egyesített, rendezett változata lett.

### H-13 — mypy: a Cirq implicit re-exportjai

*Megtalálta:* `mypy --strict`.
*Ok:* a Cirq **szállít** típusstubokat, de a névteret implicit re-exportokkal
építi (`cirq.X` a `cirq.ops.X` helyett). A strict mód ezt `attr-defined`
hibaként jelzi.
*Javítás:* célzott `mypy` override a `cirq.*` és `qsimcirq.*` modulokra — a
**saját** kódunk ellenőrzése változatlanul szigorú marad.

### H-14 — Késleltetett kötésű lezárások az időmérésben

*Megtalálta:* `ruff` (B023 szabály).
*Ok:* a skálázási mérés lambdái a ciklusváltozókat (`circuit`, `observable`) a
külső hatókörből kapták. A kód ebben az alakban helyesen működött (a hívás
azonnali), de a minta **törékeny**: egy későbbi átalakítás — például a mérések
listába gyűjtése és utólagos futtatása — csendben rossz áramkört mérne.
*Javítás:* a mérőfüggvény az áramkört és az observable-t **paraméterként** kapja.
*Tanulság:* a lint-szabály itt nem stílusról szólt, hanem egy valódi, jövőbeli
hibaosztály megelőzéséről.

---

## 9. Nyitott pontok

| # | Pont | Hol dől el |
|---|---|---|
| O10 | A lövészaj zajszintje nagyságrendekkel nagyobb a `complex64`-énél → az optimalizáló-választás még kritikusabb | Fázis 1b |
| O11 | A `qsim_noisy` backend (csatorna-mintavétel) megvalósítása | Fázis 1b |
| O12 | A valódi QPU-futtatás `ibm_kingston`-on, teljes dokumentációval | Fázis 2 |
| ~~O13~~ | ~~A `matplotlib` nincs pinnelve~~ — **megoldva**: `matplotlib==3.11.2` a `requirements.txt`-ben | ✅ Fázis 1M |

---

## 10. Kilépési nyilatkozat

Mind a hat kilépési feltétel teljesült:

1. ✅ 15 / 15 elfogadási kritérium;
2. ✅ három tesztkör lefutott, a negatív esetek az elvárt módon buktak;
3. ✅ [`docs/01m_multiplatform.md`](../01m_multiplatform.md) elkészült;
4. ✅ 5 generált ábra + nyers mérési adatok (`docs/figures/data/`);
5. ✅ `CHANGELOG.md` `0.3.0` bejegyzés;
6. ✅ `v0.3.0` annotált Git-tag.

**A Fázis 1M lezárható. A Fázis 1b megkezdhető, és a Fázis 2 feloldva.**

---

## 11. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. 15/15 kritérium, 5 talált hiba, 1 csendes hibamód felderítve. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
