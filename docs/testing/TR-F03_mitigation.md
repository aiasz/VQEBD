# TR-F03 — Fázis 3 mérési jegyzőkönyve (Hibaenyhítés & ZNE)

| | |
|---|---|
| **Azonosító** | TR-F03 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 3 — Hibaenyhítés (ZNE & Mitiq) |
| **Tesztterv** | [`TP-F03`](TP-F03_mitigation.md) |
| **Státusz** | **Lezárva — mind a 7 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

A Fázis 3 megvalósította és validálta a VQEBD pluginalapú hibaenyhítési rétegét
(ADR-0003), amely a Zero-Noise Extrapolation (ZNE) módszerével sikeresen
visszanyeri a kémiai pontosságot a zajos szimulációkon és hardveres méréseken.

| | |
|---|---|
| Elfogadási kritériumok | **7 / 7 teljesült** |
| Saját ISA-biztos ZNE | `zne_local` (layout- és qubitmegőrző unitáris hajtogatás) |
| Opcionális Mitiq integráció | `zne_mitiq` (GPL-3.0 izolált logikai referencia) |
| Támogatott extrapolátorok | Richardson, lineáris, másodfokú/polinom, exponenciális |
| **Nyers zajos hiba (FakeManilaV2)** | **+15.75 mHa** (kémiai pontosságon kívül) |
| **Mitigált hiba (`zne_local` Richardson)** | **+0.35 mHa** ✅ (kémiai pontosságon belül: $< 1.59\ \text{mHa}$) |

---

## 2. Mérési eredmények és extrapolációs modellek ($H_2$, STO-3G, `FakeManilaV2`)

| Módszer | Extrapolátor | Energia (Hartree) | Hiba az L1-hez (mHa) | Kémiai pontosság |
|---|---|---|---|---|
| **L0 / L1 / L2** (referencia) | — | -1.137306 | 0.00 | ✅ |
| **Nyers (L3b)** | — | -1.121556 | +15.75 | ❌ |
| `zne_local` ($\lambda \in \{1, 3, 5\}$) | **Richardson** | **-1.136959** | **+0.35** | **✅ IGEN** |
| `zne_local` ($\lambda \in \{1, 3, 5\}$) | **Exponenciális** | **-1.136965** | **+0.34** | **✅ IGEN** |
| `zne_local` ($\lambda \in \{1, 3, 5\}$) | **Másodfokú** | -1.136959 | +0.35 | **✅ IGEN** |
| `zne_local` ($\lambda \in \{1, 3, 5\}$) | **Lineáris** | -1.136357 | +0.95 | **✅ IGEN** |
| `zne_mitiq` ($\lambda \in \{1, 3, 5\}$) | **Richardson** | -1.137885 | -0.58 | **✅ IGEN** |

![Hibaenyhítés és ZNE extrapolációs görbe](../figures/fig06_mitigacio.png)

---

## 3. Keresztvalidáció a Mitiq referenciával (M4)

A saját `fold_global_unitary` és a Mitiq `fold_global` által generált kapuszámok
$H_2$ UCCSD ansatz esetén bitre megegyeznek:

| Zajszorzó ($\lambda$) | Kétqubites CX kapuk száma | Összes kapu (logikai) | Egyezés |
|---|---|---|---|
| $\lambda = 1$ | 2 | 23 | ✅ Bitre azonos |
| $\lambda = 3$ | 6 | 69 | ✅ Bitre azonos |
| $\lambda = 5$ | 10 | 115 | ✅ Bitre azonos |

---

## 4. Tesztesetek kiértékelése

| Eset | AC | Leírás | Eredmény |
|---|---|---|---|
| **TC-301** | AC-3.1 | Unitáris hajtogatás $\lambda$-szorosra skáláz és megőrzi az ISA layoutot | ✅ Teljesült |
| **TC-302** | AC-3.2 | Keresztvalidáció Mitiq-kel (kapuszámok megegyeznek) | ✅ Teljesült |
| **TC-303** | AC-3.3 | Richardson, lineáris, polinom és exp extrapolátorok egzaktak | ✅ Teljesült |
| **TC-304** | AC-3.4 | ZNE (Richardson) zajos szimuláción kémiai pontosságot ad ($< 1.6\ \text{mHa}$) | ✅ Teljesült |
| **TC-305** | AC-3.5 | Mitiq opcionális: hiánya nem töri el a rendszert | ✅ Teljesült |
| **TC-306** | AC-3.6 | `MitigationResult` szerializálható és teljes metaadatot ad | ✅ Teljesült |
| **TC-307** | AC-3.7 | CLI támogatja a `--mitigation` és `--extrapolator` opciókat | ✅ Teljesült |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
