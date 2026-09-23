# 03 — Hibaenyhítés & Zero-Noise Extrapolation (Fázis 3)

| | |
|---|---|
| **Dokumentum** | `docs/03_mitigation_test.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Projektverzió** | 0.6.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 3 — Hibaenyhítés (ZNE & Mitiq) |

---

## 1. Mit csinál ez a fázis

A Fázis 3 pluginalapú hibaenyhítési réteget valósít meg a VQEBD-ben (ADR-0003),
amely Zero-Noise Extrapolation (ZNE) segítségével csökkenti a szimulált és fizikai
hardverzaj hatását.

```bash
# VQE futtatása ZNE hibaenyhítéssel zajos szimulátoron (Richardson extrapoláció)
docker run --rm vqebd:0.6.0 python -m vqebd --backend qiskit_aer_noisy --optimizer COBYLA --mitigation zne_local --extrapolator richardson

# Futtatás exponenciális extrapolációval
docker run --rm vqebd:0.6.0 python -m vqebd --backend qiskit_aer_noisy --optimizer COBYLA --mitigation zne_local --extrapolator exponential
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

```
L0  Full CI (PySCF) .............. -1.137306 Ha (elméleti igazság)
L1  Egzakt diagonalizáció ........ -1.137306 Ha (Δ = +1.33e-15 Ha)
L2  VQE állapotvektor ............ -1.137306 Ha (Δ = +1.49e-15 Ha)
L3b VQE (FakeManilaV2, nyers) .... -1.121556 Ha (Δ = +15.75 mHa ❌)
L4  VQE + ZNE (Richardson) ....... -1.136959 Ha (Δ = +0.35 mHa ✅ Kémiai pontosság!)
```

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
- **`exponential`**: $E(\lambda) = a e^{b\lambda} + c$ nemlineáris exponenciális illesztés.
