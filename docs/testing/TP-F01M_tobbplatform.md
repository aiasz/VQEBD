# TP-F01M — Fázis 1M tesztterve (Többplatformos validáció)

| | |
|---|---|
| **Azonosító** | TP-F01M |
| **Típus** | Test Plan (tesztterv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1M — Többplatformos validáció |
| **Célverzió** | `v0.3.0` |
| **Terv** | [`docs/plan/phase_01m.md`](../plan/phase_01m.md) |
| **Jegyzőkönyv** | [`TR-F01M`](TR-F01M_tobbplatform.md) |

---

## 1. A tesztelés célja

A Fázis 1 azt igazolta, hogy a **fizika helyes** — de egyetlen implementációval.
A Fázis 1M azt kell igazolja, hogy az eredmény **nem a Qiskit sajátossága**.

A központi kérdés:

> Ha a Qiskit szimulátor-rétegében szisztematikus hiba lenne, **észrevennénk-e?**

Egy független implementáció (Cirq) és egy eltérő számábrázolású, optimalizált
motor (qsim) erre ad választ.

---

## 2. Tesztstratégia — miért mátrix, és nem energia

A legveszélyesebb konverziós hiba a **qubit-sorrend (endianness)**. Ennek
kimutatására az energia-összehasonlítás **nem elegendő**:

- szimmetrikus Hamilton-operátoron a rossz sorrend **véletlenül helyes energiát
  is adhat**;
- a hiba csak aszimmetrikus rendszernél (LiH, BeH2 — Fázis 5) bukna ki, amikor
  már a teljes batch-infrastruktúra rá épül.

Ezért a konverziót **mátrixszinten** validáljuk, és a teszt **kétirányú**:

1. a helyes sorrend mátrixa **egyezik** (`< 1e-12`);
2. a helytelen sorrend mátrixa **kimutathatóan eltér** (`> 1e-6`).

A második nélkül az első triviálisan teljesülne, és semmit nem bizonyítana.

---

## 3. Platformonkénti toleranciák

A tolerancia a **számábrázolásból** következik, nem abból, „ami éppen átmegy":

| Platform | Aritmetika | Gépi ε | Tolerancia | Kémiai pontosság alatt |
|---|---|---|---|---|
| `qiskit_statevector` | complex128 | 2.2 × 10⁻¹⁶ | 1 × 10⁻⁹ Ha | 1 593 000× |
| `cirq_simulator` | complex128 | 2.2 × 10⁻¹⁶ | 1 × 10⁻⁹ Ha | 1 593 000× |
| `qsim` | **complex64** | **1.2 × 10⁻⁷** | 1 × 10⁻⁵ Ha | **159×** |

---

## 4. Tesztesetek

### 4.1 Kör 1 — funkcionális

| Teszteset | AC | Hol | Elfogadás |
|---|---|---|---|
| **TC-1M01** | AC-1M.1 | build + `requirements.lock` | cirq + qsim telepítve, pin ≡ lock |
| **TC-1M02** | AC-1M.2 | `test_ac_1m_2_hamiltonian_conversion_matches_matrix` | `max\|ΔM\| < 1e-12` |
| **TC-1M03** | AC-1M.3 | `test_ac_1m_3_wrong_qubit_order_is_detectably_different` | `max\|ΔM\| > 1e-6` |
| **TC-1M04** | AC-1M.2 | `test_hamiltonian_conversion_for_every_mapper` | mindhárom leképezésre egzakt |
| **TC-1M05** | AC-1M.4 | `test_ac_1m_4_circuit_conversion_preserves_the_state` | `\|⟨ψ₁\|ψ₂⟩\| = 1` |
| **TC-1M06** | AC-1M.4 | `test_ac_1m_4_circuit_conversion_preserves_width` | inaktív qubit sem vész el |
| **TC-1M07** | AC-1M.5 | `test_ac_1m_5_unknown_gate_raises_with_its_name` | `ValueError` a kapu nevével |
| **TC-1M08** | AC-1M.6 | `test_ac_1m_6_cirq_agrees_with_qiskit` | < 1e-9 Ha |
| **TC-1M09** | AC-1M.7 | `test_ac_1m_7_qsim_agrees_with_qiskit` | < 1e-5 Ha |
| **TC-1M10** | AC-1M.8 | `test_ac_1m_8_every_platform_is_chemically_accurate` | < 1.6 mHa |
| **TC-1M11** | AC-1M.9 | `test_ac_1m_9_determinism_per_platform` | **bitre azonos** |
| **TC-1M12** | AC-1M.10 | `test_ac_1m_10_variational_principle_on_every_platform` | E ≥ E_egzakt |
| **TC-1M13** | AC-1M.11 | `test_ac_1m_11_qsim_uses_single_precision` | dtype == `complex64` |
| **TC-1M14** | AC-1M.12 | `test_ac_1m_12_result_records_the_platform` | `platform`, `precision` a rekordban |
| **TC-1M15** | AC-1M.13 | `test_cli.py` | mindhárom backend fut a CLI-ből |
| **TC-1M16** | AC-1M.15 | `test_credentials.py` | a token nem szivárog |

### 4.2 Kör 2 — robusztussági és negatív

| Eset | Rontás | Elvárt bukás |
|---|---|---|
| **TC-N9** | A `requirements.txt` numpy-pinjének átírása | `test_required_package_is_pinned` |
| **TC-N10** | A GPL-3.0 licencű `mitiq` felvétele közvetlen függőségként | `test_gpl_package_is_not_a_direct_dependency` |
| **TC-N11** | A seed-származtatás elválasztójának átírása | `test_seed_set_matches_golden_values` |

Ezek a Fázis 0 nyolc esete mellé kerülnek (összesen 11).

Robusztussági esetek:

| Eset | Mit vizsgál |
|---|---|
| **TC-R1M1** | Ismeretlen kapu a konverterben → beszédes hiba, nem néma kihagyás |
| **TC-R1M2** | Eltérő qubit-számú áramkör és observable → `ValueError` |
| **TC-R1M3** | Gradiens-alapú optimalizáló qsimen → `RuntimeWarning`, nem csendes hiba |
| **TC-R1M4** | Hiányzó IBM-hitelesítő adat → a források felsorolása, titok nélkül |
| **TC-R1M5** | Csonkolt token → `ValueError`, a titok kiírása nélkül |

### 4.3 Kör 3 — keresztvalidáció

| Eset | Mit vizsgál |
|---|---|
| **TC-X1M1** | 3 platform × 3 leképezés = 9 kombináció, egyetlen energia |
| **TC-X1M2** | Mindhárom platform ↔ PySCF Full CI (L0) |
| **TC-X1M3** | Cirq sajátérték-diagonalizáció ↔ Qiskit sajátérték-diagonalizáció |
| **TC-X1M4** | Disszociációs görbe: **eltérő szerkezetű** Hamilton-operátorok |
| **TC-X1M5** | `cirq.Simulator(complex64)` ↔ `qsim` — a pontossági hipotézis igazolása |
| **TC-X1M6** | 8 optimalizáló × 3 platform — a gradiens-biztonság felderítése |
| **TC-X1M7** | A nyilvántartott zajszint ↔ a **ténylegesen mért** zajszint |

A **TC-X1M6** nem volt előre tervezett teszt: a platformok összevetése során
derült ki, hogy szükség van rá. A felfedezés utólag beépült a tervbe és a kódba.

---

## 5. Kilépési feltételek

1. TC-1M01 … TC-1M16 zöld;
2. TC-R1M1 … TC-R1M5 zöld;
3. TC-N1 … TC-N11 az elvárt módon elbukott;
4. TC-X1M1 … TC-X1M7 zöld;
5. az eredmények rögzítve a [`TR-F01M`](TR-F01M_tobbplatform.md) jegyzőkönyvben;
6. `docs/01m_multiplatform.md` és a generált ábrák elkészültek;
7. `CHANGELOG.md` `0.3.0` bejegyzés; `v0.3.0` annotált Git-tag.

---

## 6. Kockázatok a tesztelésben

| # | Kockázat | Kezelés |
|---|---|---|
| T1M.1 | A qubit-sorrend hibája szimmetrikus eseten elrejtőzik | Mátrixszintű **és** kétirányú teszt; disszociációs görbe eltérő geometriákkal |
| T1M.2 | A qsim toleranciája túl laza, elfedi a valódi hibát | A tolerancia a gépi epszilonból származik; a `Powell` mért hibája (2.9 × 10⁻⁸) három nagyságrenddel a tolerancia alatt van |
| T1M.3 | A platformok „egyetértése" közös hibából ered | A végső referencia a PySCF Full CI — **független elmélet, független implementáció** |
| T1M.4 | Az időmérés zaja félrevezető teljesítmény-állításhoz vezet | Min-of-3 ismétlés; lásd a TR-F01M H-11 megállapítását |

---

## 7. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
