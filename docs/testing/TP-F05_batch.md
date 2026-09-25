# TP-F05 — Fázis 5 tesztterv (batch, aktív tér, statisztika)

| | |
|---|---|
| **Azonosító** | TP-F05 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-25 |
| **Fázis** | 5 — Batch-futtatás, aktív tér, statisztikai módszertan |
| **Terv** | [`phase_05.md`](../plan/phase_05.md) |
| **Döntés** | [`ADR-0007`](../adr/ADR-0007-batch-statisztika.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Mit kell igazolni

1. **Helyesség aktív térben:** a redukció és az energiaeltolás hibátlan (két
   független kódút egyezik), a Fázis 1–4 eredményei bitre változatlanok.
2. **Reprodukálhatóság batch-szinten:** a futáslista determinisztikus, a
   megszakított batch folytatva ugyanazt adja.
3. **A statisztika helyessége:** a függvények ismert eloszláson a várt értéket
   adják, és a „hozzájárul-e az ismétlés a pontossághoz” kérdésre a mért válasz
   egyértelmű (N^−½ a szórásra, 0 a torzításra).

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl |
|---|---|---|---|
| **TC-501** | AC-5.1 | L1 (Qiskit Nature) = L0′ (PySCF CASCI) ≤ 1e-10 Ha; LiH (2e,3o), (2e,5o), BeH₂ (2e,3o); a csonkolás nemnegatív | `tests/validation/test_active_space.py` |
| **TC-502** | AC-5.2 | Teljes térben `energy_offset == nuclear_repulsion_energy` bitre; a v0.7.1 ujjlenyomatok (`config_hash`) változatlanok | ugyanott |
| **TC-503** | AC-5.3 | LiH (2e,3o) VQE mindhárom platformon: 0 ≤ L2 − L1 < 1.6 mHa, platformtolerancián belül | ugyanott |
| **TC-504** | AC-5.4 | Azonos spec → azonos futáslista és `run_id`; az ismétlések csak a seedben térnek el; a preset-méretek a tervvel egyeznek (50 / 180 / 5) | `tests/unit/test_batch.py` |
| **TC-505** | AC-5.5 | `max_runs=2` után folytatott batch = megszakítás nélküli batch (energia, újramintavételezett átlag, paraméterek bitre) | `tests/validation/test_batch_statistics.py` |
| **TC-506a** | AC-5.6 | Szintetikus: független zajnál a blokkátlag-meredekség −0.5 ± 0.1; közös eltolásnál (a v0.7.0-s hibamód) > −0.1 | `tests/unit/test_stats.py` |
| **TC-506b** | AC-5.6 | Valódi Aer-mintákon (512 kiértékelés) a meredekség −0.5 ± 0.15 | `tests/validation/test_batch_statistics.py` |
| **TC-506c** | AC-5.6 | A zajos torzítás N = 16 és N = 256 mellett ugyanaz (4 SEM-en belül), és > 10 SEM | ugyanott |
| **TC-507** | AC-5.7 | t-CI lefedettség N = 5-nél 95 ± 1.5% (4000 kísérlet); besorolás határesetei; egyetlen zajos minta `undetermined` | `tests/unit/test_stats.py` |
| **TC-508** | AC-5.8 | Újramintavételezett végső energia: \|átlag − egzakt zajos érték θ_opt-ban\| < 4 SEM, lövészajos és zajos backenden | `tests/validation/test_batch_statistics.py` |
| **TC-509** | AC-5.9 | v1 adatbázis → v2 migráció; a v1 rekord bitre változatlan; a második megnyitás nem migrál újra; friss és migrált séma azonos | `tests/unit/test_storage.py` |
| **TC-510** | AC-5.10 | Az `f5-deterministic` és `f5-statistical` batch lefut; az ábrák és a TR-F05 a generált adatokból készülnek | végrehajtás, TR-F05 |

## 3. Negatív és robusztussági ellenőrzések

- Értelmetlen aktív tér (több pálya, mint amennyi van; páratlan elektronszám zárt
  héjon): beszédes `ValueError`, nem mély Qiskit Nature kivétel.
- `ActiveSpaceSpec` érvénytelen paraméterekkel (0 elektron, 0 pálya, túl sok elektron).
- Egzakt backend ismétléssel, 0 ismétlés, `:`-ot tartalmazó `batch_id`, üres batch,
  duplikált cella: `ValueError`.
- Ismeretlen preset: a hibaüzenet felsorolja az ismerteket.
- `ibm_qpu` cella `VQEBD_ALLOW_HARDWARE` nélkül: `PermissionError` (kvótavédelem).
- `reestimate = 1` vagy negatív: `ValueError` (egyetlen mintából nincs SEM).
- Ismeretlen (újabb) sémaverzió: hiba, nem próbál migrálni.
- A statisztikai függvények üres / nem véges bemenetre és érvénytelen
  konfidenciaszintre `ValueError`-t adnak.
- Hibaizoláció: egy futás kivétele nem állítja le a batchet (a jelentés `failed` listája).

## 4. Keresztvalidációk

| Mit | Mivel | Várt |
|---|---|---|
| Aktívtér-redukció | PySCF CASCI ↔ Qiskit Nature + egzakt diag. | ≤ 1e-10 Ha |
| Aktív térbeli VQE | Qiskit ↔ Cirq ↔ qsim | platformtoleranciák (1e-9 / 1e-9 / 1e-5 Ha) |
| t-CI | analitikus lefedettség (Monte Carlo) | 95 ± 1.5% |
| SEM(N) | elméleti σ/√N | log-log meredekség −½ |
| Séma v2 | friss ↔ migrált adatbázis | azonos oszlopok, sorrenddel |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
