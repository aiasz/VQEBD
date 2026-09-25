# TR-F03 — Fázis 3 mérési jegyzőkönyve (Hibaenyhítés & ZNE)

| | |
|---|---|
| **Azonosító** | TR-F03 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.1.0 (javított — lásd 7. szakasz) |
| **Dátum** | 2026-09-23 (1.0.0) · 2026-09-25 (1. javítási kör, v0.7.1) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 3 — Hibaenyhítés (ZNE & Mitiq) |
| **Tesztterv** | [`TP-F03`](TP-F03_mitigation.md) |
| **Adatforrás** | [`docs/figures/data/mitigacio.json`](../figures/data/mitigacio.json) — `scripts/gen_report_figures.py --only mitigacio` |
| **Státusz** | **Lezárva — 7/7 AC teljesült (AC-3.4 indokoltan újrafogalmazva, 5. szakasz)** |

---

## 1. Összefoglalás

A ZNE két, egymástól független hibakomponensét **külön** mértük, mindkettőt a
zajmentes optimumban ($\theta^*$), ahol a hardveres L5 mérés is készült:

| Mit mér | Hogyan | Eredmény |
|---|---|---|
| **Torzítás** (a módszer rendszeres hibája) | Aer `precision=0`: a FakeManilaV2 zajmodell szerinti **egzakt** várható érték | Richardson **+0.23 mHa ✅**, exponenciális **+0.15 mHa ✅**, lineáris +3.15 mHa ❌ |
| **Szórás** (véges mintavétel) | 50 független seed, 11.05 mHa/kiértékelés | Richardson **σ = 26.2 mHa**, lineáris σ = 11.7 mHa, nyers σ = 10.6 mHa |
| **Keresztvalidáció** (M4) | `zne_mitiq` logikai hajtogatással, azonos zajmodell | Richardson +0.37 mHa ✅ — eltérés a saját implementációtól **0.13 mHa** |

**Következtetés:**

1. A ZNE **módszertanilag helyes**: a torzítás a kémiai pontosságon (1.59 mHa)
   belül van, és két független implementáció (ISA- vs. logikai szintű
   hajtogatás) ugyanoda jut.
2. **8192 lövés/pont mellett egyetlen ZNE-futás NEM ad kémiai pontosságot**: az
   extrapoláció a zajt a Lagrange-súlyok normájával erősíti
   ($\sqrt{\sum w_i^2} = 2.28$ a Richardson (1,3,5) esetén). Mért: 26.2 mHa, elmélet:
   2.28 × 10.6 = 24.2 mHa (az eltérés a 50 mintás becslés ~10%-os hibáján belül).
3. **Torzítás–szórás kompromisszum:** ennél a lövésszámnál a legkisebb
   négyzetes középhibát (RMSE) a **lineáris** extrapoláció adja (12.3 mHa), nem
   a Richardson (26.5 mHa). A nyers érték RMSE-je 28.6 mHa. Ez benchmark-szintű
   megállapítás: az extrapolátor választása a lövésszám függvénye.

Az 1.0.0 változat „+15.75 → +0.35 mHa ✅” eredménye **a TR-000 spike számai**
voltak, nem a Fázis 3 kódjáé, és egy azóta javított mérési hibát is elfedtek
(7. szakasz).

![ZNE torzítás és szórás](../figures/fig06_mitigacio.png)

*Bal: a ZNE torzítása egzakt zajos várható értékkel; a betét a λ→0 értékeket
nagyítja a kémiai pontossági sávhoz. Jobb: 50 független futás eloszlása, felül
átlag ± szórás és RMSE; lila: a hardveres L5 mérés két bizonytalansági mutatóval.*

---

## 2. Torzítás — egzakt zajos várható értékkel (`precision = 0`)

H2 / STO-3G / parity (2 qubit), UCCSD, $\theta^*$ = L2 optimum, `FakeManilaV2`.
Hiba a Full CI-hez (−1.1373060358 Ha), mHa.

| | λ = 1 (nyers) | λ = 3 | λ = 5 | Richardson | exponenciális | lineáris |
|---|---|---|---|---|---|---|
| `zne_local` (ISA-hajtogatás) | +27.52 | +79.32 | +127.45 | **+0.23 ✅** | **+0.15 ✅** | +3.15 ❌ |
| `zne_mitiq` (logikai hajtogatás) | +37.57 | +107.19 | +170.41 | **+0.37 ✅** | **+0.17 ✅** | +5.43 ❌ |
| Kétqubites kapuk (mindkettő) | 4 | 12 | 20 | | | |

A két út nyers hibája **szándékosan** eltér: a logikai hajtogatás
`optimization_level=0`-val más fizikai qubitekre kerül, mint az
`optimization_level=3` ISA-áramkör. Az extrapolált értékek mégis
0.02–0.13 mHa-en belül egyeznek, pedig a nyers értékek különböznek. Ez a
keresztvalidáció erős formája: ugyanaz a fizikai határérték, két független
hajtogatási és fordítási úton.

---

## 3. Szórás — 50 független seed (alapértelmezett precision)

Seedek: 20260923 … 20260972. Minden futás 3 független kiértékelés (λ = 1, 3, 5).

| | átlag | szórás | SEM | medián | [Q1, Q3] | RMSE | kémiai pontosságon belül |
|---|---|---|---|---|---|---|---|
| nyers (λ = 1) | +26.58 | 10.58 | 1.50 | +25.74 | [+21.1, +34.8] | 28.57 | 0 / 50 |
| ZNE Richardson | −5.72 | 26.19 | 3.70 | −1.26 | [−22.8, +10.3] | 26.55 | 6 / 50 |
| ZNE lineáris | +4.38 | 11.65 | 1.65 | +5.31 | [−3.3, +11.6] | **12.34** | 4 / 50 |
| ZNE exponenciális | −25.93 | 73.96 | 10.46 | −7.75 | [−28.8, +7.0] | 77.67 | 6 / 50 |

Megfigyelések:

- A Richardson-átlag (−5.7 ± 3.7) a +0.23 mHa-es torzítástól 1.6 SEM-re van:
  összeférhető vele.
- Az exponenciális modell a λ = 0 torzításban a legjobb, zajos pontokon viszont
  **instabil**: 2 futás −120 mHa alá extrapolál (legrosszabb: −488 mHa). A
  nemlineáris illesztés 3 pontra és 3 paraméterre egzakt, ezért a zajt nem
  simítja, hanem felnagyítja.
- **Lövésszám-becslés:** hogy a Richardson szórása 1.59 mHa alá essen, a
  kiértékelésenkénti σ-nak ≤ 0.70 mHa-nek kell lennie, vagyis az Aer
  $\sigma = 1/\sqrt{N}$ konvenciójában N ≳ 2·10⁶ lövés pontonként (≈ 250× több).
  **Megkötés:** az Aer `precision` → lövésszám megfeleltetés konvenció, nem a
  konkrét Hamilton-operátor Pauli-varianciájából számolt valódi lövészaj. A
  pontos hardveres lövésszám-igény a Fázis 5+ tervezési feladata.

### 3.1 Összevetés a hardveres L5 méréssel

| | hiba (mHa) | bizonytalanság |
|---|---|---|
| L5 `ibm_kingston`, 1 kiértékelés, TREX | −3.96 | ±12.5 (ensemble SE) / ±53.3 (`stds`) |
| szimulált nyers, 1 kiértékelés (FakeManilaV2) | +26.6 (átlag) | ±10.6 (szórás) |

A Heron-eszköz egyetlen mérése kisebb *torzítást* mutat, mint a FakeManilaV2
(Falcon-generációs eszköz rögzített kalibrációs pillanatképe) szimulációja, de a különbség a mérés
bizonytalanságán belül van. Eszközök összehasonlítására egyetlen mérés nem
elegendő (TR-F02 v1.1.0, 2.2).

---

## 4. Keresztvalidáció a Mitiq-kel (M4)

| λ | `zne_local` 2q-kapuk (ISA) | `zne_mitiq` 2q-kapuk (logikai) | Egyezés |
|---|---|---|---|
| 1 | 4 | 4 | ✅ |
| 3 | 12 | 12 | ✅ |
| 5 | 20 | 20 | ✅ |

A `zne_local` ISA-áramkörének teljes kapuszáma 23 / 97 / 171 (a `sxdg` →
`rz`/`sx` fordítás miatt nem pontosan 3×/5×). A **zajszorzót** a kétqubites
kapuk aránya határozza meg (azok hibája ~10× nagyobb), ez pontosan 1 : 3 : 5
— a metaadat `effective_scale_factors` mezője minden futásnál rögzíti.

---

## 5. Tesztesetek kiértékelése

| Eset | AC | Leírás | Eredmény |
|---|---|---|---|
| **TC-301** | AC-3.1 | `fold_global_unitary` λ-szorosra skáláz, megőrzi az ISA layoutot | ✅ |
| **TC-301b** | AC-3.1 | **Új regressziós teszt:** zajos kiértékelőn a 2q-kapuk száma pontosan λ-szoros (`effective_scale_factors == [1, 3, 5]`) | ✅ |
| **TC-302** | AC-3.2 | Mitiq keresztvalidáció: 2q-kapuszám egyezik, mindkét torzítás és az eltérésük < 1.59 mHa | ✅ — **v0.7.1 óta ténylegesen fut** (CI-lépés a `requirements-mitiq.txt`-vel) |
| **TC-303** | AC-3.3 | Extrapolátorok szintetikus görbéken egzaktak | ✅ |
| **TC-304** | AC-3.4* | ZNE (Richardson, exp) **torzítása** < 1.59 mHa; lineáris rosszabb; nyers > 15.9 mHa | ✅ (+0.23 / +0.15 / +3.15 / +27.5 mHa) |
| **TC-305** | AC-3.5 | Mitiq hiánya nem töri el a `zne_local`-t | ✅ |
| **TC-306** | AC-3.6 | `MitigationResult` szerializálható, teljes metaadattal | ✅ |
| **TC-307** | AC-3.7 | CLI `--mitigation` és `--extrapolator` | ✅ |

**\*AC-3.4 újrafogalmazása.** Az eredeti szöveg („a ZNE a hibát a kémiai
pontosság alá csökkenti”) egyetlen, 8192 lövéses futásra **nem teljesíthető**, és
ez nem implementációs hiba, hanem a 3. szakasz mért szórása
(σ_Richardson = 26 mHa). A teszt ezért a módszer **torzítását** ellenőrzi
determinisztikusan; a szórást a jegyzőkönyv méri és dokumentálja. Az 1.0.0
tesztje (`zne_error < raw_error or zne_error < 0.05`) gyakorlatilag mindig
teljesült, így semmit nem igazolt.

Tesztkészlet (vqebd:0.7.1): **455 passed** mitiq-kel, **454 passed + 1 skipped**
(TC-302) nélküle.

---

## 6. Reprodukálás

```bash
docker run --rm -v "$PWD:/app" -w /app -e PYTHONPATH=/app/src vqebd:0.7.1 \
  sh -c "pip install -q -r requirements-mitiq.txt && \
         python scripts/gen_report_figures.py --only mitigacio"
```

Futásidő: ~18 s. Az eredmény determinisztikus (ADR-0005): az Aer-kiértékelők
zaja saját, `seeds.simulator`-ból indított generátorból származik.

---

## 7. Javítási napló

### 1. javítási kör (2026-09-25, v0.7.1)

| # | Hiba a v0.7.0-ban / TR-F03 1.0.0-ban | Hatás | Javítás |
|---|---|---|---|
| J1 | A 2. szakasz számai (+15.75 → +0.35 mHa, Mitiq −0.58 mHa) és a 3. szakasz kapuszámai (23/69/115) a **TR-000 spike**-ból származtak, nem a Fázis 3 kódjából. | A jegyzőkönyv nem a leszállított kódot mérte. | Minden szám a `mitigacio.json`-ból, a v0.7.1 kóddal újramérve. |
| J2 | A tényleges v0.7.0 mérés (`mitigacio.json`) +24.3 mHa-t adott a ZNE-re — ellentmondott a jegyzőkönyvnek. | Téves „kémiai pontosság ✅”. | 1–3. szakasz. |
| J3 | `zne_local` a **logikai** áramkört hajtogatta, majd `optimization_level=3`-mal fordított: a transzpiler az U·U† párok egy részét kiejtette (4/10/16 CX a várt 4/12/20 helyett, tényleges λ = 1/2.5/4). | A Richardson rossz abszcisszákkal extrapolált. | ISA-szintű hajtogatás, `optimization_level=0` fordítás (`IsaEnergyEvaluator`); regressziós teszt TC-301b. |
| J4 | **Aer mintavételi hiba:** az Aer `EstimatorV2` minden `run()`-nál `default_rng(seed_simulator)`-ból húzott — rögzített seed mellett **minden kiértékelés ugyanazt a z·σ eltolást** kapta (itt +15.9 mHa). | A „lövészaj” valójában állandó torzítás volt: a VQE eltolt, zajmentes felületet optimalizált; a ZNE-ben közös módusként kiesett. Minden korábbi L3a-érték ≈ +16 mHa ezt tükrözi. | Egzakt várható érték + saját, hívásonként továbblépő RNG (`_AerIsaEnergyEvaluator`); 3 regressziós teszt (TC-1B10). |
| J5 | `zne_mitiq` a `scaled_energies` mezőbe a nyers értéket ismételte (helykitöltő). | Hamis adat a tárolt rekordban. | Valódi értékek a Mitiq `Factory`-ból. |
| J6 | `zne_mitiq` kötetlen paraméteres áramkört adott a Mitiq-nek, és az executor `optimization_level=3`-mal fordított. | Nem futott volna (QASM-konverzió), és a hajtogatást kiejtette volna. | Paraméter-bekötés, logikai bázis, `level=0` executor. |
| J7 | A Mitiq az executor visszatérési **annotációjából** következtet a típusra; `from __future__ import annotations` mellett ez a `"float"` szöveg lett. | `ValueError: Could not parse executed results`. | Explicit `__annotations__["return"] = float`, magyarázó kommenttel. |
| J8 | `requirements-mitiq.txt` hiányzott (az ADR-0003 hivatkozott rá); a mitiq-ág soha nem futott. | TC-302 mindig kihagyódott. | Fájl létrehozva (mért hatás: +mitiq, +tabulate, `pip check` tiszta); CI-lépés. |
| J9 | Az exponenciális extrapoláció hiba esetén **csendben** másodfokúra váltott, de „exponential” címkével tárolódott. | Hamis címke. | `RuntimeWarning` a tartalékágon. |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
