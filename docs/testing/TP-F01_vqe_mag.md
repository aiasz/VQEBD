# TP-F01 — Fázis 1 tesztterve (VQE-mag, H2 szimulátoron)

| | |
|---|---|
| **Azonosító** | TP-F01 |
| **Típus** | Test Plan (tesztterv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 1 — H2-VQE szimulátoron |
| **Célverzió** | `v0.2.0` |
| **Terv** | [`docs/plan/phase_01.md`](../plan/phase_01.md) |
| **Jegyzőkönyv** | [`TR-F01`](TR-F01_vqe_mag.md) |

---

## 1. A tesztelés célja

A Fázis 0 azt igazolta, hogy az **infrastruktúra** működik. A Fázis 1 azt kell
igazolja, hogy a **fizika helyes**: a kód nem pusztán lefut, hanem a **helyes
számot** adja.

A központi kérdés nem „elszáll-e a program", hanem:

> Ha az eredmény eltér a valóditól, **meg tudjuk-e mondani, mi okozta?**

Ezért a tesztelés az öt referenciaszint (Mesterterv 3.2) közül az első hármat
külön-külön méri és hasonlítja össze.

---

## 2. Tesztkörnyezet

| | |
|---|---|
| Image | `vqebd:0.2.0` (`python:3.11-slim@sha256:da047cb8…95ba9`) |
| Stack | qiskit 1.4.6 · qiskit-aer 0.17.2 · qiskit-nature 0.7.2 · pyscf 2.14.0 · numpy 1.26.4 · scipy 1.13.1 |
| Determinizmus | `PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` |
| Referencia-eset | H2, 0.735 Å, STO-3G, paritás-leképezés 2-qubit redukcióval, UCCSD, SLSQP, `θ₀ = 0` |

---

## 3. A validálás logikája — a referencialánc

```
E_L0  Full CI (PySCF)            <- független implementáció, független elmélet
  │
  │  leképezési hiba  (AC-1.2: |Δ| < 1e-9 Ha)
  ▼
E_L1  a qubit-Hamiltoni egzakt legkisebb sajátértéke
  │
  │  ansatz-hiba      (AC-1.3: |Δ| < 1.6 mHa; H2-re < 1e-7 Ha)
  ▼
E_L2  VQE zajmentes állapotvektoron
```

**Miért erős ez?** Az L0 és az L1 két, egymástól teljesen független úton
számolja ugyanazt a mennyiséget: a PySCF determináns-alapú konfigurációs
kölcsönhatással, a Qiskit + NumPy pedig Pauli-operátor-mátrix
diagonalizációjával. Ha egyeznek, a leképezés bizonyítottan helyes. Ha az L2
ezután is egyezik, a hiba nem lehet sem a leképezésben, sem az ansatzban.

---

## 4. Tesztesetek

### 4.1 Kör 1 — funkcionális

| Teszteset | AC | Hol | Elfogadás |
|---|---|---|---|
| **TC-101** Image építése a teljes stackkel | AC-1.1 | manuális + CI | kilépési kód 0 |
| **TC-102** L0 ≡ L1 (leképezés helyes) | AC-1.2 | `test_h2_vqe.py::test_ac_1_2_mapping_is_exact` | \|Δ\| < 1e-9 Ha |
| **TC-103** L0 ≡ L1 mindhárom leképezéssel | AC-1.2 | `test_ac_1_2_all_mappers_are_exact` | \|Δ\| < 1e-9 Ha |
| **TC-104** Kémiai pontosság | AC-1.3 | `test_ac_1_3_within_chemical_accuracy` | \|Δ\| < 1.5936e-3 Ha |
| **TC-105** UCCSD H2-re gépi pontossággal egzakt | AC-1.3 | `test_ac_1_3_uccsd_is_essentially_exact_for_h2` | \|Δ\| < 1e-7 Ha |
| **TC-106** Teljes korrelációs energia visszanyerve | — | `test_full_correlation_energy_recovered` | 100 % ± 1e-4 % |
| **TC-107** **Az alapterv kritériuma** | AC-1.4 | `test_ac_1_4_plan_criterion` | E ∈ −1.137 ± 0.01 Ha |
| **TC-108** Variációs elv | AC-1.5 | `test_ac_1_5_variational_principle` | E_VQE ≥ E_egzakt − 1e-9 |
| **TC-109** HF felső korlát | AC-1.5 | `test_hartree_fock_is_an_upper_bound` | E_korr ≤ 0 |
| **TC-110** Determinizmus (D1) | AC-1.6 | `test_ac_1_6_determinism_bit_for_bit` | **bitre azonos** |
| **TC-111** Leképezés-függetlenség | AC-1.7 | `test_ac_1_7_mappers_agree` | szórás < 1e-7 Ha |
| **TC-112** 2-qubit redukció hatása | AC-1.7 | `test_two_qubit_reduction_saves_qubits` | 2 qubittel kevesebb |
| **TC-113** E(θ=0) ≡ E_HF | AC-1.8 | `test_ac_1_8_zero_parameters_give_hartree_fock` | \|Δ\| < 1e-9 Ha |
| **TC-114** CLI működik | AC-1.9 | `test_cli.py::test_default_run_succeeds` | kilépési kód 0 |
| **TC-115** Lint + típus + teszt | AC-1.10 | CI | 0 hiba |
| **TC-116** `requirements.lock` konzisztens | AC-1.11 | `test_requirements.py` | pin ≡ lock |
| **TC-117** Futásidő-korlát | AC-1.12 | mérés | validáció < 300 s |

### 4.2 Kör 2 — robusztussági és negatív

| Teszteset | Mit vizsgál | Elvárás |
|---|---|---|
| **TC-201** Érvénytelen molekula-leírás | üres név, üres geometria, negatív spin, nempozitív kötéshossz | `ValueError` beszédes üzenettel |
| **TC-202** Érvénytelen optimalizáló-beállítás | `maxiter ≤ 0`, `tol ≤ 0` | `ValueError` |
| **TC-203** Ismeretlen bázis | `--basis nincs-ilyen-bazis` | 2-es kilépési kód, a mi hibaüzenetünk |
| **TC-204** Ismeretlen optimalizáló | `--optimizer NINCS_ILYEN` | 2-es kilépési kód |
| **TC-205** Ismeretlen leképezés | `--mapper nincs_ilyen` | argparse szintű hiba |
| **TC-206** `maxiter=1` | szoros iterációs korlát | `converged=False`, **nem** kivétel |
| **TC-207** Paraméter nélküli ansatz | üres paramétervektor | egyetlen kiértékelés, nincs összeomlás |
| **TC-208** Iterációs korlát opciókulcsa | minden támogatott metódusra | nincs `OptimizeWarning` (a korlát érvényesül) |
| **TC-209** Konfiguráció immutabilitása | mezőmódosítás kísérlete | `FrozenInstanceError` |
| **TC-210** Ujjlenyomat-érzékenység | bármely mező módosítása | eltérő ujjlenyomat |

#### Negatív esetek (a védelmek bizonyítása)

A [`scripts/negative_test_harness.py`](../../scripts/negative_test_harness.py)
izolált repó-másolaton ront el dolgokat, és elvárja a megfelelő teszt bukását.
A Fázis 1-ben a Fázis 0 nyolc esete mellé újak kerülnek:

| Eset | Rontás | Elvárt bukás |
|---|---|---|
| **TC-N9** | A `requirements.txt` numpy-pinjének átírása | `test_required_package_is_pinned` |
| **TC-N10** | A `mitiq` felvétele a `requirements.txt`-be | `test_gpl_package_is_not_a_direct_dependency` |
| **TC-N11** | A seed-származtatás címkéjének átírása | `test_seed_set_matches_golden_values` |

### 4.3 Kör 3 — keresztvalidáció

| Teszteset | Két (vagy több) független út ugyanarra |
|---|---|
| **TC-X101** | PySCF Full CI ↔ qubit-Hamiltoni egzakt diagonalizáció |
| **TC-X102** | Jordan–Wigner ↔ paritás ↔ Bravyi–Kitaev leképezés |
| **TC-X103** | SLSQP ↔ COBYLA ↔ Nelder-Mead ↔ L-BFGS-B ↔ Powell |
| **TC-X104** | Qiskit `StatevectorEstimator` ↔ közvetlen `⟨ψ\|H\|ψ⟩` mátrixszorzás |
| **TC-X105** | PySCF Hartree–Fock ↔ VQE `θ = 0`-nál |
| **TC-X106** | 2-qubit redukcióval ↔ anélkül (ugyanaz az energia) |
| **TC-X107** | Fizikai viselkedés: a disszociációs görbe U-alakú, a minimum ~0.74 Å-nél |

A **TC-X104** külön fontos: az estimator-réteg megkerülésével, tisztán lineáris
algebrával számoljuk újra a várható értéket. Ez a Qiskit primitív-használatunk
független ellenőrzése — például egy elcsúszott paraméter-sorrendet vagy egy
illesztetlen observable-t kapna el.

---

## 5. Kilépési feltételek

1. TC-101 … TC-117 zöld;
2. TC-201 … TC-210 zöld;
3. TC-N1 … TC-N11 az **elvárt módon elbukott** (izolált másolaton);
4. TC-X101 … TC-X107 zöld;
5. az eredmények rögzítve a [`TR-F01`](TR-F01_vqe_mag.md) jegyzőkönyvben;
6. `docs/01_vqe_core.md` elkészült;
7. `CHANGELOG.md` `0.2.0` bejegyzése kész, `v0.2.0` annotált Git-tag létrehozva.

---

## 6. Kockázatok a tesztelésben

| # | Kockázat | Kezelés |
|---|---|---|
| T1.1 | A teszt zöld, mert a tolerancia túl laza. | A toleranciákat fizikai megfontolás adja (kémiai pontosság), nem „ami éppen átmegy"; a szigorúbb `1e-7` és `1e-9` szintek külön tesztekben. |
| T1.2 | A referencia és a mért érték ugyanabból a hibás forrásból jön. | Az L0 **más könyvtár, más algoritmus** (PySCF determináns-CI), nem a Qiskit-lánc része. |
| T1.3 | A determinizmus-teszt véletlenül megy át. | Bitre azonosságot követel (`==`, nem `approx`), és a szálszám is rögzített. |
| T1.4 | A lassú validációs tesztek elriasztanak a futtatástól. | Futásidő mérve és korlátozva (AC-1.12); a drága számítások modul-szintű fixture-ökben megosztva. |

---

## 7. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
