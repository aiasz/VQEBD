# 04 — Adatséma és perzisztens tárolás (Fázis 4)

| | |
|---|---|
| **Dokumentum** | `docs/04_data_schema.md` |
| **Dokumentum-verzió** | 1.1.0 |
| **Dátum** | 2026-09-23 · 2026-09-25 (séma v2) |
| **Projektverzió** | 0.8.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 4 — Adatséma és tárolás |

---

## 1. Architektúra és alapelvek

A VQEBD adattárolási rétege (`vqebd.storage`) a **FAIR adatkezelési alapelvek**
[wilkinson2016] szerint készült (ADR-0004):

1. **Kanonikus tároló:** SQLite adatbázis (`data/db/vqebd.sqlite`), WAL móddal,
   szigorú `CHECK` megszorításokkal és indexekkel.
2. **Append-only működés:** A korábbi futások rekordjai nem módosulnak;
   a tároló a teljes tudományos auditálhatóságot és reprodukálhatóságot garantálja.
3. **Környezet- és konfigurációs ujjlenyomat:** Minden rekord hordozza az
   eredeti `config_hash` és `environment_fingerprint` értékeket.
4. **Determinisztikus export:** A tárolt adatok CSV és JSON formátumba
   exportálhatók (`scripts/export_results.py`).

---

## 2. Az adatbázis sémája (`results` tábla, v1)

| Mező neve | Típus | Leírás | Mértékegység / Példa |
|---|---|---|---|
| `run_id` | `TEXT UNIQUE` | A futás egyedi azonosítója (UUID vagy benchmark-címke). | `bench-l2-qiskit_statevector` |
| `timestamp` | `TEXT` | A futás időpontja UTC-ben (ISO-8601). | `2026-09-23T09:52:06Z` |
| `schema_version` | `INTEGER` | Az adatséma verziószáma. | `1` |
| `molecule_name` | `TEXT` | A vizsgált molekula neve. | `H2` |
| `geometry` | `TEXT` | Atomkoordináták. | `H 0 0 0; H 0 0 0.735` |
| `bond_length` | `REAL` | Kötéshossz. | `0.735` Å |
| `basis` | `TEXT` | Gauss-pályák báziskészlete. | `sto3g` |
| `charge` | `INTEGER` | A molekula nettó töltése. | `0` |
| `spin` | `INTEGER` | Multiplicitás index ($2S$). | `0` |
| `mapper` | `TEXT` | Fermion $\to$ qubit leképezés. | `parity`, `jordan_wigner`, `bravyi_kitaev` |
| `two_qubit_reduction` | `INTEGER` | Kétqubites redukció (1 = aktív, 0 = inaktív). | `1` |
| `ansatz_kind` | `TEXT` | Variációs próbaállapot típusa. | `uccsd` |
| `optimizer_method` | `TEXT` | Klasszikus optimalizáló algoritmus. | `SLSQP`, `COBYLA`, `Powell` |
| `n_iterations` | `INTEGER` | Lefutott iterációk száma. | `3` |
| `n_function_evaluations` | `INTEGER` | Célfüggvény kiértékelések száma. | `14` |
| `converged` | `INTEGER` | Konvergált-e (1 = igen, 0 = nem). | `1` |
| `backend` | `TEXT` | Platform-backend azonosító. | `qiskit_statevector`, `ibm_qpu`, stb. |
| `platform` | `TEXT` | Mögöttes platform neve. | `qiskit`, `cirq`, `qsim` |
| `precision` | `TEXT` | Lebegőpontos számábrázolás. | `complex128`, `complex64` |
| `shots` | `INTEGER` | Mintavételi lövésszám (ha értelmezett). | `8192` |
| `hardware_backend_name` | `TEXT` | Fizikai QPU neve (ha hardveren futott). | `ibm_kingston` |
| `hardware_job_id` | `TEXT` | IBM Quantum felhő feladatazonosító. | `dapq25kak42c73cj1hu0` |
| `mitigation_strategy` | `TEXT` | Hibaenyhítési eljárás neve. | `none`, `zne_local`, `zne_mitiq` |
| `mitigation_extrapolator` | `TEXT` | ZNE extrapolációs modell. | `richardson`, `exponential` |
| `energy_ha` | `REAL` | Végleges teljes VQE / mitigált alapállapoti energia. | `-1.1373060358` Ha |
| `electronic_energy_ha` | `REAL` | Elektronikus alapállapoti energia. | `-1.8572750302` Ha |
| `nuclear_repulsion_ha` | `REAL` | Magtaszítási energia. | `0.7199689944` Ha |
| `hartree_fock_ha` | `REAL` | Hartree–Fock energia. | `-1.1169989968` Ha |
| `full_ci_ha` | `REAL` | L0 Full CI klasszikus referencia. | `-1.1373060358` Ha |
| `exact_diag_ha` | `REAL` | L1 Egzakt diagonalizáció referencia. | `-1.1373060358` Ha |
| `error_vs_fci_ha` | `REAL` | Eltérés a Full CI referenciától ($E - E_{\text{FCI}}$). | `+1.33e-15` Ha |
| `within_chemical_accuracy` | `INTEGER` | Kémiai pontosságon belül van-e ($|\Delta| < 1.6\ \text{mHa}$). | `1` / `0` |
| `config_hash` | `TEXT` | A konfiguráció SHA-256 hash ujjlenyomata (64 char). | `a52e7c035a93...` |
| `environment_fingerprint`| `TEXT` | A futásidejű csomagverziók hash lenyomata. | `0ed6e85afa3c...` |
| `master_seed` | `INTEGER` | Mester véletlenszám-mag (ADR-0005). | `20260922` |

---

## 2b. Séma v2 (Fázis 5, `v0.8.0`)

A v2 tizenegy **nullázható** oszlopot ad a `results` táblához ([`phase_05.md`](plan/phase_05.md)
7. fejezet). Egy v1 rekordnál a `NULL` jelentése: teljes pályatér, nem batch-futás,
nincs újramintavételezés.

| Oszlop | Típus | Jelentés |
|---|---|---|
| `active_electrons`, `active_orbitals` | INTEGER | aktív tér; `NULL` = teljes tér |
| `casci_ha` | REAL | L0′ — CASCI (PySCF) az aktív térben |
| `energy_offset_ha` | REAL | konstans eltolás: magtaszítás + inaktív energia |
| `batch_id`, `repeat_index` | TEXT, INTEGER | batch és ismétlés (`vqebd.batch`) |
| `optimizer_final_ha` | REAL | az optimalizáló visszaadott értéke (egyetlen zajos húzás) |
| `optimizer_history_min_ha` | REAL | az optimalizálás közbeni kiértékelések minimuma (kiválasztott, torzított) |
| `reestimate_mean_ha`, `reestimate_sem_ha`, `reestimate_n` | REAL, REAL, INTEGER | független újramintavételezés θ_opt-ban (ADR-0007 D2) |

**Migráció:** egy v1 adatbázis megnyitásakor a `Database` automatikusan hozzáadja
az oszlopokat (`ALTER TABLE … ADD COLUMN`). Egyetlen tranzakcióban frissíti a
`meta.schema_version`-t 2-re, és naplózza a `migrated_v1_to_v2_at` időpontot.
Meglévő sort nem módosít (append-only). Friss adatbázis ugyanezen az úton jön
létre, ezért a friss és a migrált séma konstrukció szerint azonos. Ezt a TC-509
teszt ellenőrzi. Ismeretlen (újabb) verziójú adatbázist a kód nem migrál, hanem
hibát ad.

## 3. Használat

### Adatbázis elérése Pythonból

```python
from vqebd.storage import Database, load_results, save_result

# 1. Eredmények betöltése szűréssel
records = load_results(molecule="H2", within_chemical_accuracy=True)
for r in records:
    print(f"{r['backend']} -> E = {r['energy_ha']:.6f} Ha (Hiba: {r['error_vs_fci_ha']:.2e} Ha)")

# 2. Új eredmény mentése
# save_result(vqe_result)
```

### Exportálás CSV / JSON formátumba

```bash
docker run --rm -v "${PWD}:/repo" vqebd:0.8.0 python scripts/export_results.py
```
