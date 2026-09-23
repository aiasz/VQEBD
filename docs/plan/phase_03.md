# Fázis 3 — Hibaenyhítési stratégiák (ZNE & Mitiq)

| | |
|---|---|
| **Fázis** | 3 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Státusz** | Tervezés alatt |
| **Célverzió** | `v0.6.0` |
| **Előzmény** | [`phase_02.md`](phase_02.md), [`ADR-0003`](../adr/ADR-0003-mitigacios-architektura.md), [`TR-000`](../testing/TR-000_spike.md) |

## 1. Cél

A Fázis 3 a kvantumkémiai VQE számítások pontosságának javítását célozza
**Zero-Noise Extrapolation (ZNE)** hibaenyhítési stratégiák segítségével.

A fázis célkitűzései:
1. **Saját ISA-biztos unitáris hajtogatás (`zne_local`):** Közvetlenül fizikai
   ISA-áramkörökön hajtja végre a zajskálázást ($U \to U (U^\dagger U)^n$),
   megőrizve a fizikai qubit-hozzárendelést és a layoutot (kiküszöbölve az ADR-0003 M3 hibát).
2. **Keresztvalidáció a Mitiq referenciával (`zne_mitiq`):** A logikai szintű
   Mitiq ZNE implementáció párhuzamos futtatása a saját hajtogatás helyességének
   független igazolására (M4).
3. **Több extrapolációs modell támogatása:** Richardson (Lagrange $\lambda \to 0$),
   lineáris, másodfokú/polinomiális és exponenciális illesztés.
4. **Kémiai pontosság helyreállítása:** Zajos szimuláción (`FakeManilaV2`) és
   valódi hardveres mérésen igazolni, hogy a ZNE szignifikánsan csökkenti a hibát
   (TR-000 előzetes mérés: nyers $+15.75\ \text{mHa} \to$ mitigált $+0.35\ \text{mHa}$ ✅).

## 2. Architektúra (`src/vqebd/mitigation/`)

```
src/vqebd/mitigation/
├── __init__.py           — Stratégiák nyilvántartása és gyárfüggvény
├── base.py               — MitigationStrategy protokoll és MitigationResult
├── folding.py            — Saját, ISA- és layout-biztos unitáris hajtogatás
├── extrapolation.py      — Richardson, lineáris, polinom, exponenciális extrapolátorok
├── none.py               — NoMitigation (nyers alapvonal)
├── zne.py                — ZneLocalMitigation (saját ISA ZNE)
└── mitiq_zne.py          — MitiqZneMitigation (opcionális független referencia)
```

## 3. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-3.1** | `fold_global_unitary` $\lambda \in \{1, 3, 5\}$ esetén pontosan $1 + 2n$-szeresére növeli a kétqubites kapuk számát és megőrzi az ISA layoutot | egységteszt |
| **AC-3.2** | A saját `fold_global_unitary` és a Mitiq `fold_global` kapuszámai és unitárisai megegyeznek | keresztvalidációs teszt |
| **AC-3.3** | Richardson, lineáris, polinomiális és exponenciális extrapolátorok egzaktul visszaadják az analitikus $\lambda=0$ határértéket | egységteszt |
| **AC-3.4** | `qiskit_aer_noisy` + `FakeManilaV2` esetén a `zne_local` a nyers $+15\ \text{mHa}$ hibát $< 1.6\ \text{mHa}$ kémiai pontosságra javítja | validációs teszt |
| **AC-3.5** | A Mitiq opcionális függőségként működik; hiányában a `zne_local` önállóan, hibamentesen fut | izolációs teszt |
| **AC-3.6** | A `MitigationResult` tartalmazza a skálafaktorokat, a nyers és mitigált energiákat és az illesztési maradékokat | egységteszt |
| **AC-3.7** | A CLI és a `run_vqe` támogatja a `--mitigation` és `--extrapolator` kapcsolókat | integrációs teszt |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
