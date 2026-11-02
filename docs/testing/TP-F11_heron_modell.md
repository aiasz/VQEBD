# TP-F11 — Fázis 11 tesztterv (a Heron-zajmodell validálása)

| | |
|---|---|
| **Azonosító** | TP-F11 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 11 — Kalibrációból épített Heron-zajmodell validálása valódi hardveren |
| **Terv** | [`phase_11.md`](../plan/phase_11.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic) — a terv MI-vel készült, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |
| **Státusz** | **A 11.A (kód, kvóta nélkül) tesztjei kész. A hardveres mérések (11.B, 11.C) és a TR-F11 még nem készültek.** |

---

## 1. Mit kell igazolni

1. **A kód a mérés előtt helyes:** a modell valóban kapcsolja a kiolvasási hibát; az ismétlések seedjei különbözők; az
   elemzés ismert eltolást kimutat, eltolás nélkül egyenértékűséget ad (pozitív és negatív kontroll).
2. **A kvótát a kód védi, nem az emlékezet:** a használat blokk után sem lépheti át a keret 80%-át; engedély és
   befagyasztott protokoll nélkül nincs beküldés; a szárazfutás 0 QPU-s.
3. **A mérés után** (TR-F11): a H1–H4 az előre kimondott szabály szerint kiértékelve, a feltáró és a megerősítő adat külön.

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl / mód |
|---|---|---|---|
| **TC-1101** | AC-11.1 | `build_simulator(readout=True)` bitre azonos az `AerSimulator.from_backend`-del; `readout=False` eltér | élő olvasás (`phase_11.md` 6.1); `test_build_simulator_really_toggles_the_readout_error` |
| **TC-1102** | AC-11.1 | az ismétlésenként más seed más lövészajt ad, azonos seed azonosat (a v0.7.1-es hiba ellen) | `tests/unit/test_heron_model.py` |
| **TC-1103** | AC-11.2 | a kalibrációs pillanatkép csak a használt qubiteket olvassa, JSON-szerializálható | `tests/unit/test_heron_model.py` |
| **TC-1104** | AC-11.3 | a TOST ismert 5 mHa eltolást kimutat; nulla eltolásnál egyenértékű; túl nagy szórásnál nem az | `tests/unit/test_heron_analysis.py` |
| **TC-1105** | AC-11.3 | a H1 döntési szabálya (3/3 egyenértékű, 2/3 részben, egyébként elutasítva) | ugyanott |
| **TC-1106** | AC-11.3 | H2/H4 páros különbség; a pilot nem számít a megerősítő végpontokba; < 2 blokk és eltérő geometria hibát ad | ugyanott |
| **TC-1107** | AC-11.4 | `assert_block_within_budget`: pontosan 480 s megengedett, fölötte megtagadva, ismeretlen kvótaállásnál megtagadva | `tests/unit/test_heron_model.py` |
| **TC-1108** | AC-11.4 | a teljes ütemterv (57 s meglévő + B0 + 8 blokk) az 1,25-ös biztonsági szorzós kapuval is a 80% alatt marad, ≥ 20% tartalékkal | ugyanott |
| **TC-1109** | AC-11.4 | a futtató megtagadja a blokkot, ha a keret átlépődne (kilépési kód 2); engedély nélkül `HardwareNotAllowedError`; `FROZEN` nélkül `RuntimeError`; ismeretlen blokknév elutasítva | ugyanott |
| **TC-1110** | AC-11.5 | a protokoll-ujjlenyomat módosításra változik; az eltérő `FROZEN` megtagadja a beküldést | ugyanott |
| **TC-1111** | AC-11.4 | a protokoll a jóváhagyott értékeket tartalmazza (δ = 3,0 mHa; {0,735; 1,5; 2,0} Å; 8 blokk; 80%; qubitpár [1, 2]) | ugyanott |
| **TC-1112** | AC-11.4 | `--dry-run` B0: 0 QPU-s, beküldés nélkül lefut, modell-előrejelzést ad | kézi végrehajtás, `phase_11.md` M9–M11 |
| **TC-1113** | AC-11.6 | a mért adat H1–H4 szerinti kiértékelése, a feltáró és megerősítő adat külön jelölve | `scripts/analyze_heron.py` a mérések után (TR-F11) |

## 3. A mérések kapui (nem teszt, hanem eljárás)

Minden hardveres blokk (B0, C1…C8) előtt, sorrendben: (1) `--dry-run`; (2) a szerző külön igenje; (3) a futtató élő
`usage()` ellenőrzése. A blokk után: a kimeneti fájl és a kvóta-állás ellenőrzése, a következő blokk csak ezek után.

*Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc*
