# TR-F04 — Fázis 4 mérési jegyzőkönyve (Adatséma és tárolás)

| | |
|---|---|
| **Azonosító** | TR-F04 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.1.0 (2.1 javítási jegyzet) |
| **Dátum** | 2026-09-23 · 2026-09-25 (v0.7.1) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 4 — Adatséma és tárolás |
| **Tesztterv** | [`TP-F04`](TP-F04_storage.md) |
| **Státusz** | **Lezárva — mind a 7 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

A Fázis 4 során megvalósult a VQEBD strukturált, FAIR-megfelelő perzisztens
adattárolási rétege (`vqebd.storage`). Az SQLite kanonikus tároló, a WAL
konkurencia-kezelés és a determinisztikus CSV/JSON export sikeresen integrálva
lett a rendszerbe.

| | |
|---|---|
| Elfogadási kritériumok | **7 / 7 teljesült** |
| Kanonikus adatbázis | `data/db/vqebd.sqlite` (WAL mód, sémaverzió: `1`) |
| Exportált állományok | `data/exports/results_v1.csv`, `data/exports/results_v1.json` |
| Tárolt referenciaszintek | L0, L1, L2 (3 platform), L3a, L3b, L4 (ZNE), L5 (Heron QPU) |
| Összes tárolt benchmark futás | **8 rekord** |

---

## 2. Tárolt benchmark adatok összefoglalója ($H_2$, $0.735\ \text{Å}$)

| Run ID | Backend | Platform | Mitigáció | Energia (Hartree) | Hiba az L0-hoz (Ha) | Kémiai pontosság | Variációs elv |
|---|---|---|---|---|---|---|---|
| `bench-l2-qiskit_statevector` | `qiskit_statevector` | Qiskit | none | −1.1373060358 | $+9.33 \times 10^{-15}$ | ✅ | ✅ |
| `bench-l2-cirq_simulator` | `cirq_simulator` | Cirq | none | −1.1373060358 | $+8.88 \times 10^{-15}$ | ✅ | ✅ |
| `bench-l2-qsim` | `qsim` | qsim | none | −1.1373060068 | $+2.90 \times 10^{-8}$ | ✅ | ✅ |
| `bench-l3a-qiskit_aer_shot` | `qiskit_aer_shot` | Qiskit | none | −1.1421267225 | $-4.82 \times 10^{-3}$ | ❌ | ❌ ¹ |
| `bench-l3b-qiskit_aer_noisy` | `qiskit_aer_noisy` | Qiskit | none | −1.1145306932 | $+2.28 \times 10^{-2}$ | ❌ | ✅ |
| `bench-l4-zne-richardson` | `qiskit_aer_noisy` | Qiskit | zne_local (Rich.) | −1.1075860081 | $+2.97 \times 10^{-2}$ | ❌ | ✅ |
| `bench-l4-zne-exponential` | `qiskit_aer_noisy` | Qiskit | zne_local (Exp.) | −1.1202858217 | $+1.70 \times 10^{-2}$ | ❌ | ✅ |
| `bench-l5-ibm_kingston` | `ibm_qpu` | Qiskit | **ibm_resilience_1** (TREX) | −1.1412691258 | $-3.96 \times 10^{-3}$ | ❌ | ❌ ² |

*A táblázat a v0.7.1 kóddal újragenerált [`docs/figures/data/results_v1.json`](../figures/data/results_v1.json)
tartalma (friss adatbázisból, 2026-09-25). A rekordok `versions_json` mezője
v0.7.1 óta a `vqebd` saját verzióját is tartalmazza.*

¹ Statisztikus: a COBYLA visszaadott értéke egyetlen zajos húzás a végpontban
(σ ≈ 11 mHa; TR-F01B 6.3, javított szöveg). ² 1σ-n belüli statisztikus ingadozás
(TR-F02 v1.1.0, 2.1). A „❌” itt nem kódhiba, hanem a rekord **helyes**, számított
jelzője; a v0.7.0 ezt kézzel `1`-re írta.

### 2.1 Javítási jegyzet (v0.7.1)

Az 1.0.0 táblázat L3a/L3b/L4 sorai a v0.7.0 kóddal készültek, amelyben (1) az
Aer-mintavétel minden kiértékelésnél ugyanazt az eltolást adta, (2) a
`zne_local` hajtogatását a transzpiler részben kiejtette (TR-F03 v1.1.0, J3–J4).
Az L5 rekordban a `mitigation_strategy` `none` volt (valójában TREX), a
`satisfies_variational_principle` és a `correlation_recovered` pedig kézzel beírt
érték volt (1, ill. 1.20). Mindhárom most számított. **Egy helyi, v0.7.0-val
feltöltött `data/db/vqebd.sqlite` a régi rekordokat tartalmazza**: a betöltő a
meglévő `run_id`-kat nem írja felül. Ilyenkor friss adatbázisba kell exportálni
(`--db`).

---

## 3. Tesztesetek kiértékelése

| Eset | AC | Leírás | Eredmény |
|---|---|---|---|
| **TC-401** | AC-4.1 | SQLite inicializálás, WAL mód, sémaverzió ellenőrzés | ✅ Teljesült |
| **TC-402** | AC-4.2 | `insert_result` és `get_result` bitpontos visszaolvasás | ✅ Teljesült |
| **TC-403** | AC-4.3 | `query_results` szűrés molekula, backend, pontosság szerint | ✅ Teljesült |
| **TC-404** | AC-4.4 | Determinisztikus CSV/JSON exportálás rendezett kulcsokkal | ✅ Teljesült |
| **TC-405** | AC-4.5 | Történeti adatok betöltése (8 rekord, minden szint) | ✅ Teljesült |
| **TC-406** | AC-4.6 | Integritás: duplikált run_id IntegrityError hibát ad | ✅ Teljesült |
| **TC-407** | AC-4.7 | Dokumentáció (`docs/04_data_schema.md`) teljes körű | ✅ Teljesült |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
