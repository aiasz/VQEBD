# TR-F04 — Fázis 4 mérési jegyzőkönyve (Adatséma és tárolás)

| | |
|---|---|
| **Azonosító** | TR-F04 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
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

| Run ID | Backend | Platform | Mitigáció | Energia (Hartree) | Hiba (Ha) | Kémiai pontosság |
|---|---|---|---|---|---|---|
| `bench-l2-qiskit_statevector` | `qiskit_statevector` | Qiskit | none | -1.1373060358 | $+1.33 \times 10^{-15}$ | ✅ IGEN |
| `bench-l2-cirq_simulator` | `cirq_simulator` | Cirq | none | -1.1373060358 | $+4.44 \times 10^{-16}$ | ✅ IGEN |
| `bench-l2-qsim` | `qsim` | qsim | none | -1.1373060068 | $+2.90 \times 10^{-8}$ | ✅ IGEN |
| `bench-l3a-qiskit_aer_shot` | `qiskit_aer_shot` | Qiskit | none | -1.1208540086 | $+1.65 \times 10^{-2}$ | ❌ NEM |
| `bench-l3b-qiskit_aer_noisy` | `qiskit_aer_noisy` | Qiskit | none | -1.0927745684 | $+4.45 \times 10^{-2}$ | ❌ NEM |
| `bench-l4-zne-richardson` | `qiskit_aer_noisy` | Qiskit | zne_local (Rich.) | -1.1130006901 | $+2.43 \times 10^{-2}$ | ❌ NEM |
| `bench-l4-zne-exponential` | `qiskit_aer_noisy` | Qiskit | zne_local (Exp.) | -1.1130367673 | $+2.43 \times 10^{-2}$ | ❌ NEM |
| `bench-l5-ibm_kingston` | `ibm_qpu` | Qiskit | none | -1.1412691258 | $-3.96 \times 10^{-3}$ | ❌ NEM |

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
