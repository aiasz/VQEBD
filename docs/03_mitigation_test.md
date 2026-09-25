# 03 — Hibaenyhítés & Zero-Noise Extrapolation (Fázis 3)

| | |
|---|---|
| **Dokumentum** | `docs/03_mitigation_test.md` |
| **Dokumentum-verzió** | 1.1.0 |
| **Dátum** | 2026-09-23 · 2026-09-25 |
| **Projektverzió** | 0.7.1 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 3 — Hibaenyhítés (ZNE & Mitiq) |

---

## 1. Mit csinál ez a fázis

A Fázis 3 pluginalapú hibaenyhítési réteget valósít meg a VQEBD-ben (ADR-0003),
amely Zero-Noise Extrapolation (ZNE) segítségével csökkenti a szimulált és fizikai
hardverzaj hatását.

```bash
# VQE futtatása ZNE hibaenyhítéssel zajos szimulátoron (Richardson extrapoláció)
docker run --rm vqebd:0.7.1 python -m vqebd --backend qiskit_aer_noisy --optimizer COBYLA --mitigation zne_local --extrapolator richardson

# Futtatás exponenciális extrapolációval
docker run --rm vqebd:0.7.1 python -m vqebd --backend qiskit_aer_noisy --optimizer COBYLA --mitigation zne_local --extrapolator exponential
```

---

## 2. A ZNE működése és a referencialánc

A Zero-Noise Extrapolation a zajszint mesterséges növelésével mér több ponton,
majd matematikai illesztéssel extrapolál a zajmentes ($\lambda = 0$) határértékre:

1. **Unitáris hajtogatás ($U \to U (U^\dagger U)^n$):** A kvantumáramkör mélységét
   $\lambda \in \{1, 3, 5\}$ faktorokkal növeljük.
2. **Skálázott mérések:** Az energiát minden $\lambda$ értéknél kiértékeljük.
3. **Extrapoláció:** A Richardson, lineáris vagy exponenciális modellekkel
   meghatározzuk a $\lambda \to 0$ extrapolált értéket (**L4** szint).

Mért értékek a zajmentes optimumban ($\theta^*$), FakeManilaV2, v0.7.1
([TR-F03 v1.1.0](testing/TR-F03_mitigation.md)); hiba a Full CI-hez:

```
L0  Full CI (PySCF) ..................... -1.137306 Ha (elméleti igazság)
L2  VQE állapotvektor ................... Δ = +1e-14 Ha
L3b nyers, egzakt zajos várható érték ... Δ = +27.52 mHa ❌
L4  ZNE Richardson — TORZÍTÁS ........... Δ =  +0.23 mHa ✅ (precision = 0)
L4  ZNE Richardson — 1 futás, 8192 lövés  Δ =  −5.7 ± 26.2 mHa (50 seed)
L4  ZNE lineáris   — 1 futás, 8192 lövés  Δ =  +4.4 ± 11.7 mHa (legkisebb RMSE)
```

**Hogyan olvasd:** a ZNE *módszere* helyes (a torzítás a kémiai pontosságon
belül van, és a Mitiq független implementációja ugyanoda jut: +0.37 mHa). A
véges lövésszám zaját azonban az extrapoláció felnagyítja (Richardson: 2.28×),
ezért egyetlen futás 8192 lövéssel nem kémiailag pontos. Megjegyzés: az Aer
Estimator a readout-hibát nem modellezi (ADR-0003, 1. kiegészítés).

![Hibaenyhítés és ZNE extrapolációs görbe](figures/fig06_mitigacio.png)

---

## 3. Támogatott stratégiák és modellek

| Stratégia | Modul | Jellemzők |
|---|---|---|
| `none` | `vqebd.mitigation.none` | Nyers mérés, hibaenyhítés nélkül. |
| `zne_local` | `vqebd.mitigation.zne` | Saját, **ISA- és layout-biztos** unitáris hajtogatás. |
| `zne_mitiq` | `vqebd.mitigation.mitiq_zne` | Opcionális Mitiq ZNE referencia (GPL-3.0 izolált). |

Támogatott extrapolációs modellek:
- **`richardson`**: Lagrange-polinom interpoláció a $\lambda = 0$ pontra.
- **`linear`**: 1. fokú legkisebb négyzetes egyenesillesztés.
- **`quadratic` / `poly`**: 2. fokú polinomiális illesztés.
- **`exponential`**: $E(\lambda) = a e^{-b\lambda} + c$ nemlineáris exponenciális illesztés
  (3 pontra egzakt; zajos pontokon instabil — TR-F03 3. szakasz).
