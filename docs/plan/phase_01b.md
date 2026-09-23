# Fázis 1b — Véges-lövéses és zajos szimuláció

| | |
|---|---|
| **Fázis** | 1b |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-23 |
| **Státusz** | Végrehajtás alatt |
| **Célverzió** | `v0.4.0` |
| **Előzmény** | [`phase_01m.md`](phase_01m.md), [`TR-000`](../testing/TR-000_spike.md) |

## 1. Cél

A Fázis 1M zajmentes L2 referenciája után a VQEBD külön méri a véges mintavétel
(**L3a**) és a kalibrációs hardverzaj (**L3b**) hatását, IBM-kvóta használata
nélkül.

| Szint | Backend | Jelentés |
|---|---|---|
| L2 | `qiskit_statevector` | egzakt, zajmentes referencia |
| L3a | `qiskit_aer_shot` | Aer véges pontossággal, zajmodell nélkül |
| L3b | `qiskit_aer_noisy` | Aer `FakeManilaV2` kalibrációs zajmodellel |

A fázis nem célozza a nyers L3b kémiai pontosságát. A zajcsökkentés Fázis 3
feladata; itt reprodukálható, nyers alapvonal készül hozzá.

## 2. Tervezési döntések

1. A közös `run_vqe()` és SciPy-hurok változatlan marad; új evaluatorok a
   meglévő `EnergyEvaluator` interfészen érkeznek.
2. Az Aer V2 `default_precision = 1/sqrt(shots)` opcióval modellezi a véges
   lövésszámot. Az alapértelmezés 8192 lövés.
3. Az L3b `AerSimulator.from_backend(FakeManilaV2())` útvonalat használja.
   Ez helyi szimuláció, nem hív IBM szolgáltatást és nem fogyaszt QPU-kvótát.
4. Transzpiláció után az observable fizikai qubitkiosztását mindig követni kell:
   `observable.apply_layout(transpiled.layout)`.
5. A szimulátor- és transzpilációs seed a `SeedSet` értékeiből jön. Azonos
   konfiguráció és seed mellett az eredmény determinisztikus.
6. Az L3a/L3b célfüggvény zajos, ezért a CLI alapértelmezése deriváltmentes
   `COBYLA`; gradiens-alapú kérésre a futtató figyelmeztet.

## 3. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| AC-1B.1 | `qiskit_aer_shot` L3a evaluator működik 8192 lövéssel | egység- és integrációs teszt |
| AC-1B.2 | `qiskit_aer_noisy` `FakeManilaV2` L3b evaluator működik | egység- és integrációs teszt |
| AC-1B.3 | A transzpilált observable a fizikai layoutot követi | egységteszt |
| AC-1B.4 | Azonos konfiguráció és seed L3a/L3b esetén bitre azonos | validációs teszt |
| AC-1B.5 | Az eltérő seed konfigurációs ujjlenyomatot ad; a seedek és Aer-paraméterek a rekordban vannak | egységteszt |
| AC-1B.6 | Zajos backendhez gradiens-alapú optimalizáló figyelmeztet; ajánlott a COBYLA | egységteszt |
| AC-1B.7 | A CLI kiírja a tényleges L3a/L3b referenciaszintet | integrációs teszt |
| AC-1B.8 | Nincs IBM Runtime/QPU hívás és kvótafogyasztás | implementációs audit |
| AC-1B.9 | `ruff`, `mypy --strict` és a teljes tesztkészlet zöld | CI |

## 4. Kizárások

- valódi QPU-futtatás (Fázis 2);
- ZNE és mérési hibaenyhítés (Fázis 3);
- `qsim_noisy`, amíg a csatorna-mintavételezés külön nem validált.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
