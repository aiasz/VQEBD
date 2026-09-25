# TR-F02 — Fázis 2 mérési jegyzőkönyve (Valódi IBM hardveres futtatás)

| | |
|---|---|
| **Azonosító** | TR-F02 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.1.0 (javított — lásd 6. szakasz) |
| **Dátum** | 2026-09-23 (mérés) · 2026-09-25 (1. javítási kör) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 2 — Valódi hardveres futtatás |
| **Célhardver** | `ibm_kingston` (IBM Heron r2, 156 qubit) |
| **Job ID** | `dapq25kak42c73cj1hu0` |
| **Tesztterv** | [`TP-F02`](TP-F02_hardware_run.md) |
| **Státusz** | **Lezárva — 5/5 elfogadási kritérium teljesült; az értelmezés javítva (6. szakasz)** |

---

## 1. Összefoglalás

A Fázis 2 során megtörtént az első éles fizikai kvantumprocesszoros mérés a
VQEBD projektben: a $H_2$ alapállapoti energiája az L2-n megtalált optimális
$\theta^*$ paramétereknél, **egyetlen** Qiskit Runtime `EstimatorV2` PUB-bal, a
156-qubites **`ibm_kingston`** Heron r2 QPU-n.

| | |
|---|---|
| Elfogadási kritériumok | **5 / 5 teljesült** |
| Hardveres Job ID | `dapq25kak42c73cj1hu0` |
| Lövésszám / randomizációk | 8192 shot, 32 mérés-twirling randomizáció |
| **Mitigáció (szerveroldali)** | **TREX mérésmitigáció BEKAPCSOLVA** (`resilience_level` nem volt megadva → szerver-alapértelmezés; ZNE/PEC ki) |
| Kvótafogyasztás | **15 QPU-másodperc** (`metrics.usage.quantum_seconds`) |
| Falióra-idő | 48.93 s = 26.9 s sorban állás + 20.9 s futás + kliens-oldal |
| Mért elektronos energia | −1.8612381202 Ha |
| **Mért teljes energia (L5)** | **−1.1412691258 Ha** |
| **Bizonytalanság** | `stds` = **53.3 mHa** · `ensemble_standard_error` = **12.5 mHa** |
| Eltérés az L0-tól | −3.96 mHa = **−0.07 σ** (`stds`) / **−0.32 σ** (ensemble) |
| Kémiai pontossági küszöb | 1.59 mHa |

**Helyes értelmezés (javítva):** a mért érték **statisztikailag összeférhető** a
Full CI referenciával (1σ-n belül), de a mérés **felbontása 8–33×-osa a kémiai
pontosságnak**, ezért **sem kémiai pontosság elérését, sem a hardver hibaszintjét
nem igazolja**. A −3.96 mHa eltérés előjele és nagysága a statisztikai szórás
része, nem a Heron kapuhibájának mértéke. Az 1.0.0 változat erre vonatkozó
állítása téves volt (6. szakasz).

---

## 2. A teljes referencialánc ($H_2$, $R = 0.735\ \text{Å}$)

| Szint | Backend | Optimalizáló / Mód | Energia (Hartree) | Hiba az L1-hez (Ha) | Megjegyzés |
|---|---|---|---|---|---|
| **L0** | PySCF Full CI | — | −1.1373060358 | 0.0 | Klasszikus fizikai referencia |
| **L1** | Egzakt diag. | — | −1.1373060358 | $+1.33 \times 10^{-15}$ | Leképezési ellenőrzés |
| **L2** | `qiskit_statevector` | SLSQP | −1.1373060358 | $+1.49 \times 10^{-15}$ | Egzakt állapotvektor ($\theta^*$) |
| **L3a**¹ | `qiskit_aer_shot` | COBYLA (8192 shot) | −1.1213780162 | $+1.59 \times 10^{-2}$ | Véges mintavételi (shot) zaj |
| **L3b**¹ | `qiskit_aer_noisy` | COBYLA (FakeManila) | −1.0938632143 | $+4.34 \times 10^{-2}$ | Szimulált kapu- és relaxációs zaj |
| **L5** | `ibm_kingston` (QPU) | egyetlen kiértékelés $\theta^*$-nál, TREX | **−1.1413 ± 0.0533** | $-3.96 \times 10^{-3}$ | Valódi QPU, **mérésmitigált** |

¹ A TR-F01B futásából, **v0.7.0 kóddal**. Ezek az értékek az azóta javított
Aer-mintavételi hibát hordozzák: minden kiértékelés ugyanazt a z·σ ≈ +16 mHa
eltolást kapta (TR-F03 v1.1.0, J4). Ezért az L3a „lövészaj-hibája” valójában
állandó torzítás volt. A v0.7.1 kóddal újramért értékek: TR-F01B 6. szakasz.

**Fontos módszertani különbség:** az L3a/L3b sorok **teljes VQE-optimalizálás**
eredményei (a zajos célfüggvényen keresett minimum), az L5 viszont **egyetlen
kiértékelés** a zajmentes $\theta^*$-nál. Az L5 tehát nem „hardveren futtatott
VQE”, hanem az ideális állapot hardveres energiamérése — ez kvótatakarékos
(ADR-0006), de nem hasonlítható közvetlenül az L3 sorokhoz.

### 2.1 Miért lehet az L5 a variációs határ ALATT?

A Rayleigh–Ritz-elv szerint egy valódi állapot energiája nem lehet kisebb az
alapállapotinál ($E_{L5} \ge E_{L1}$). A mért −1.14127 Ha mégis 3.96 mHa-val
alatta van. Ennek oka nem fizikai, hanem statisztikai:

1. A becslő ($\hat{E} = \sum_k c_k \langle P_k \rangle_{\text{mért}}$) véges
   mintából származik; a szórása (≥ 12.5 mHa) sokszorosa az eltérésnek.
2. A TREX mitigáció a mért várható értékeket az olvasási hűséggel **átskálázza**,
   ami a becslő varianciáját növeli, és a torzítatlanságot csak átlagban őrzi.

Egyetlen minta tehát a határ mindkét oldalára eshet. A variációs elv sértése
**csak akkor** lenne hibajel, ha az eltérés több σ-s volna.

### 2.2 Mennyi mérés kellene a kémiai pontossághoz?

$1/\sqrt{N}$ skálázást feltételezve a szükséges lövésszám-szorzó
$(\sigma / 1.59\ \text{mHa})^2$: az ensemble-hibával **≈ 62×** (≈ 5·10⁵ shot),
a `stds` alapján **≈ 1100×**. Ez becslés, nem mérés; a Fázis 5+ hardveres
futásainak kvótatervezéséhez rögzítjük (Open Plan: 600 QPU-s / 28 nap).

---

## 3. Tesztesetek kiértékelése

| Eset | AC | Leírás | Eredmény |
|---|---|---|---|
| **TC-201** | AC-2.1 | `IBMQpuEnergyEvaluator` kapcsolódás és job indítás IBM Heron QPU-ra | ✅ Teljesült (`ibm_kingston`) |
| **TC-202** | AC-2.2 | ISA transzpiláció és `observable.apply_layout()` | ✅ Teljesült — 156 qubit széles ISA-áramkör, ebből **2 aktív** (fizikai 1, 2); 13 `rz`, 11 `sx`, 4 `cz`, mélység 23 |
| **TC-203** | AC-2.3 | Reális energiamérés $E \approx -1.137 \pm 0.1\ \text{Ha}$ tartományban | ✅ Teljesült (−1.141269 Ha; a kritérium tág, lásd 2.1) |
| **TC-204** | AC-2.4 | Job ID, backend név, időbélyeg és adatok mentése | ✅ Teljesült (`docs/figures/data/hardware_h2_kingston.json`) |
| **TC-205** | AC-2.5 | `requires_quota=True`, CI automatikusan kizárja a valódi QPU hívásokat | ✅ Teljesült (`not hardware`) |

---

## 4. Kalibrációs háttér (a mérés időpontjára visszakérve)

`backend.properties(datetime=2026-09-23T09:51Z)` — utolsó kalibráció:
2026-09-22 14:13 UTC.

| Mutató | Érték | Megjegyzés |
|---|---|---|
| CZ hiba, eszköz-medián | 1.97·10⁻³ (n = 344) | az 1.0.0 „0.0020” értéke ezt kerekítette — **igazolt** |
| CZ hiba, **használt pár** (1, 2) | **8.2·10⁻⁴** | a ténylegesen futó kapuké |
| Kiolvasási hiba, eszköz-medián | 8.67·10⁻³ | |
| Kiolvasási hiba, qubit 1 / 2 | 1.12·10⁻² / 8.30·10⁻³ | ezt korrigálja a TREX |

4 CZ × 8.2·10⁻⁴ ≈ 0.3% kapuhiba-valószínűség: a kapuzaj ennél a sekély
áramkörnél **kisebb**, mint a mérési statisztika; a domináns hibaforrás a
kiolvasás (ezt a TREX kezeli) és a véges mintaszám.

---

## 5. Futtatási adatok és naplózás

- Adatfájl: [`docs/figures/data/hardware_h2_kingston.json`](../figures/data/hardware_h2_kingston.json)
  (az 1.0.0 `data/raw/` hivatkozása téves volt)
- A bizonytalanság, a szerveroldali metaadatok és a kvótaadat **utólag**, a
  tárolt jobból lettek visszaolvasva: [`scripts/fetch_ibm_job.py`](../../scripts/fetch_ibm_job.py)
  (QPU-futtatás nélkül; a letöltött `evs` bitre egyezik a tárolttal — a szkript ezt ellenőrzi).
- Hitelesítés: `IBM.token` (maszkolva, soha nem kerül a repóba)
- Transzpilációs szint: `optimization_level=3`

---

## 6. Javítási napló

### 1. javítási kör (2026-09-25, v0.7.1)

| # | Hiba az 1.0.0-ban | Javítás |
|---|---|---|
| J1 | „A mért **nyers** fizikai hardverhiba ~4 mHa” | Nem nyers: a szerver TREX-et alkalmazott (`result.metadata.resilience.measure_mitigation = true`). |
| J2 | A ~4 mHa-t a Heron alacsony hibarátájának tulajdonította | Az eltérés 0.07–0.32 σ; a mérés ezt nem tudja feloldani (1., 2.1). |
| J3 | Bizonytalanság nem volt közölve | `IBMQpuEnergyEvaluator` most rögzíti a `stds`, `ensemble_standard_error` és a metaadatokat; a meglévő job adatai visszaolvasva. |
| J4 | `resilience_level` implicit volt | Explicit paraméter, alapértelmezés 1 (a mért szerver-viselkedés); `0` = valóban nyers. `--resilience-level` kapcsoló a futtató szkriptben. |
| J5 | Adatútvonal: `data/raw/…` | Helyesen: `docs/figures/data/hardware_h2_kingston.json`. |
| J6 | „Végrehajtási idő 48.93 s” QPU-időként olvasható | Bontás: 26.9 s sor + 20.9 s futás; **számlázott: 15 QPU-s**. |

A mérés maga (job, energiaérték) **nem változott**; csak az értelmezése és a
hozzá tartozó bizonytalansági adatok.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
