# TP-F01B — Fázis 1b tesztterv (véges-lövéses és zajos szimuláció)

| | |
|---|---|
| **Azonosító** | TP-F01B |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Fázis** | 1b — zajos szimuláció |
| **Terv** | [`phase_01b.md`](../plan/phase_01b.md) |

## 1. Referencialánc

```
L2  állapotvektor (egzakt)
 │  véges mintavétel
L3a Aer, 8192 ekvivalens lövés (zajmodell nélkül)
 │  FakeBackend kalibrációs zaj
L3b Aer + FakeManilaV2 (zajcsökkentés nélkül)
```

Az L3a és L3b nem összehasonlítható L2 szigorú toleranciájával. A cél a
hibaforrások elkülönítése és a reprodukálhatóság, nem a nyers zajos energia
kémiai pontossága.

## 2. Tesztesetek

| Eset | AC | Ellenőrzés |
|---|---|---|
| TC-1B01 | AC-1B.1 | Aer shot evaluator L3a energiát ad és jelenti a `shots` értékét. |
| TC-1B02 | AC-1B.2 | Aer noisy evaluator `FakeManilaV2` zajprofilt és L3b szintet jelent. |
| TC-1B03 | AC-1B.3 | A transzpilált áramkör és az observable azonos qubitszámú; az observable layoutolt. |
| TC-1B04 | AC-1B.4 | Két azonos L3a futás bitre azonos energiát ad. |
| TC-1B05 | AC-1B.4 | Két azonos L3b futás bitre azonos energiát ad. |
| TC-1B06 | AC-1B.5 | A lövésszám vagy zajprofil változása módosítja a konfiguráció hashét. |
| TC-1B07 | AC-1B.6 | SLSQP figyelmeztet, COBYLA nem figyelmeztet zajos backendhez. |
| TC-1B08 | AC-1B.7 | CLI-ben mindkét Aer backend választható; a jelentés L3a/L3b címkét ad. |
| TC-1B09 | AC-1B.8 | A tesztek csak `FakeManilaV2`-t használnak, IBM Runtime szolgáltatást nem. |

## 3. Negatív ellenőrzések

- Ha az `apply_layout()` elmarad, a layout-ellenőrző tesztnek buknia kell.
- Ha a zajos backend platform-metaadata gradiensbiztosnak van jelölve, az
  optimalizáló-kompatibilitási tesztnek buknia kell.
- Ha a seed továbbítása elmarad, a determinisztikus tesztnek buknia kell.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
