# TP-F03 — Fázis 3 tesztterv (Hibaenyhítés & ZNE)

| | |
|---|---|
| **Azonosító** | TP-F03 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Fázis** | 3 — Hibaenyhítés (ZNE & Mitiq) |
| **Terv** | [`phase_03.md`](../plan/phase_03.md) |

## 1. Referencialánc hibaenyhítéssel

```
L0  Full CI (klasszikus egzakt)
 └── L1  Egzakt diagonalizáció
      └── L2  VQE zajmentes állapotvektoron
           └── L3b VQE zajos szimulátoron (nyers L3b)
                └── L4  VQE hibaenyhítéssel (ZNE: λ ∈ {1,3,5} → λ=0)
```

A cél annak igazolása, hogy a mitigált L4 energiaszint közelebb kerül az L2/L0
referenciához, mint a nyers L3b vagy L5 szint, ideális esetben elérve a
kémiai pontosságot ($|\Delta| < 1.6\ \text{mHa}$).

## 2. Tesztesetek

| Eset | AC | Ellenőrzés |
|---|---|---|
| **TC-301** | AC-3.1 | `fold_global_unitary` a kétqubites kapukat pontosan $\lambda$-szorosára skálázza és megőrzi az ISA layoutot. |
| **TC-302** | AC-3.2 | Keresztvalidáció: a saját `fold_global_unitary` és a Mitiq `fold_global` kapuszámai és mátrixai megegyeznek. |
| **TC-303** | AC-3.3 | Richardson, lineáris, polinom és exponenciális extrapolátorok szintetikus görbéken egzakt $\lambda=0$ értéket adnak. |
| **TC-304** | AC-3.4 | `FakeManilaV2` zajos szimuláción a `zne_local` (Richardson) a kémiai pontossági küszöb ($1.6\ \text{mHa}$) alá csökkenti a hibát. |
| **TC-305** | AC-3.5 | A `mitiq` hiánya nem akadályozza a `zne_local` működését (izoláció). |
| **TC-306** | AC-3.6 | A `MitigationResult` szerializálható és teljes diagnosztikát nyújt. |
| **TC-307** | AC-3.7 | A CLI kezeli a `--mitigation` és `--extrapolator` opciókat. |

## 3. Negatív ellenőrzések

- Nem páratlan egész $\lambda$ (pl. $\lambda=2$) kérése esetén `ValueError`.
- Nem pozitív skálafaktor esetén `ValueError`.
- 1-nél kevesebb vagy duplikált skálázási pont esetén az extrapolátor hibát dob.
- Érvénytelen extrapolátor név esetén egyértelmű `ValueError`.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
