# TP-F11 — Fázis 11 tesztterv (a Heron-zajmodell validálása)

| | |
|---|---|
| **Azonosító** | TP-F11 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 11 — Kalibrációból épített Heron-zajmodell validálása valódi hardveren |
| **Terv** | [`phase_11.md`](../plan/phase_11.md) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — a terv szövegét az MI írta a szerző kérésére, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |
| **Státusz** | **A 11.A (kód, kvóta nélkül) tesztjei kész; a B0 pilot (11.B) lefutott, eredménye az előzetes TR-F11-ben. A C1 (11.C) lefutott (2026-11-04), a C2 is (2026-11-06/07), a C3 is (2026-11-08), a C4 is (2026-11-10; köztes leíró összesítéssel); a C5 is (2026-11-12), a C6 is (2026-11-16; az első kísérlet megszakadt, újraindítva); a C7 is (2026-11-22, a kalibrációs várakozás után); a C8 is (2026-11-24; a megerősítő mérés teljes); a C9 előtti, hardver nélküli bővítés (TC-1123–TC-1126) és a kalibráció-életkor rekonstrukciója kész (2026-11-24); a kiegészítő C9, az elsődleges elemzés és a végleges TR-F11 még nem készültek.** |

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
| **TC-1112** | AC-11.4 | `--dry-run` B0: 0 QPU-s, beküldés nélkül lefut, modell-előrejelzést ad | kézi végrehajtás, `phase_11.md` M9–M11; megismételve a B0 előtt (2026-11-02), ✅ |
| **TC-1123** | AC-11.4 | a kiegészítő C9: a `BLOCK_RE` elfogadja, `block_kind = supplementary`, TREX először, csak a teljes C1–C8 mentett kimenete után indítható (szárazfutásban is); a C10 / C0 / B1 / X1 / c9 elutasítva; a C9 kapuja a tényleges 426 s után is ≤ 480 s, ≥ 20% tartalékkal | `tests/unit/test_heron_model.py` (2026-11-24) |
| **TC-1124** | AC-11.4 | `final_metrics`: a futtató megvárja a végleges használati adatot (`status: complete`), `status` nélkül a pozitív értéket elfogadja, a kísérletek elfogyása után `usage_final = false`-szal rögzít | ugyanott |
| **TC-1125** | AC-11.3 | a kiegészítő blokk az elsődleges elemzést nem változtatja (szélsőséges értékkel sem); a leíró érzékenységi vizsgálatok: (a) C1–C9, a pilot nélkül; (b) ≤ 48 h, a határ beletartozik, az idősebb és az ismeretlen életkorú blokkok külön listázva; döntési mező nincs; a szkript jelzi, ha a megerősítő sorozat nem teljes | `tests/unit/test_heron_analysis.py` (2026-11-24) |
| **TC-1126** | AC-11.2 | a kalibráció-életkor definíciója: csak a pár T1 / T2 / kiolvasás / cz-hibája számít (az sx és a `last_update_date` nem); C6-példa ~85,8 h; a pillanatképpel való egyezés ellenőrzése; hiányzó paraméter vagy a job utáni mérés hibát ad | `tests/unit/test_heron_calibration_age.py`; élő rekonstrukció 2026-11-24 (`calibration_age.json`, mind a 8 blokk egyezik a pillanatképpel) — ✅ |
| **TC-1122** | AC-11.4 | a C8 (az utolsó megerősítő blokk) valódi futtatása a kalibrációs-frissességi szabály teljesülése után: a kapuk átengedik, a tényleges QPU-idő 39 s, a kvóta 387 → 426 s, a kimenet teljes, a kalibráció-életkor ~10,7 h; eltérés: a TREX job `quantum_seconds` mezője a mentéskor 0 (utólagos lekérdezés: 24 s) | `c8.json`, `c8.log`, TR-F11 13. szakasz — ✅ (megjegyzéssel) |
| **TC-1121** | AC-11.4 | a C7 valódi futtatása a kalibrációs-frissességi szabály teljesülése után: a kapuk átengedik, a tényleges QPU-idő 39 s, a kvóta 348 → 387 s, a kimenet teljes, a kalibráció-életkor (~37 h) a rögzített definíció szerint számolva | `c7.json`, `c7.log`, TR-F11 12. szakasz — ✅ |
| **TC-1120** | AC-11.4 | a C6 valódi futtatása: a megszakadt első kísérlet (Docker leállt) után a feladat lemondva, a blokk a protokoll szerint újraindítva; a kapuk átengedik, a tényleges QPU-idő 39 s, a kvóta 309 → 348 s, a kimenet teljes | `c6.json`, `c6.log`, `c6_megszakadt_1.log`, TR-F11 11. szakasz — ✅ |
| **TC-1119** | AC-11.4 | a C5 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő 39 s (a becslés 34,2 s, a kapu 42,7 s-mal számolt), a kvóta 270 → 309 s, a kimenet teljes | `c5.json`, `c5.log`, TR-F11 10. szakasz — ✅ |
| **TC-1118** | AC-11.4 | a C4 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő 39 s (a becslés 34,2 s, a kapu 42,7 s-mal számolt), a kvóta 231 → 270 s, a kimenet teljes; köztes leíró összesítés, döntés nélkül | `c4.json`, `c4.log`, TR-F11 9. szakasz — ✅ |
| **TC-1117** | AC-11.4 | a C3 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő 39 s (a becslés 34,2 s, a kapu 42,7 s-mal számolt), a kvóta 192 → 231 s, a kimenet teljes | `c3.json`, `c3.log`, TR-F11 8. szakasz — ✅ |
| **TC-1116** | AC-11.4 | a C2 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő 39 s (a becslés 34,2 s, a kapu 42,7 s-mal számolt), a kvóta 153 → 192 s, a kimenet teljes | `c2.json`, `c2.log`, TR-F11 7. szakasz — ✅ |
| **TC-1115** | AC-11.4 | a C1 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő 39 s (a becslés 34,2 s, a kapu 42,7 s-mal számolt), a kvóta 114 → 153 s, a kimenet teljes | `c1.json`, `c1.log`, TR-F11 6. szakasz — ✅ |
| **TC-1114** | AC-11.4 | a B0 valódi futtatása: a kapuk átengedik, a tényleges QPU-idő = a becsült (57 s), a kvóta 57 → 114 s, a kimenet teljes | `b0.json`, `b0.log`, TR-F11 1. szakasz — ✅ |
| **TC-1113** | AC-11.6 | a mért adat H1–H4 szerinti kiértékelése, a feltáró és megerősítő adat külön jelölve | `scripts/analyze_heron.py` a mérések után (TR-F11) |

## 3. A mérések kapui (nem teszt, hanem eljárás)

Minden hardveres blokk (B0, C1…C8 és a kiegészítő C9) előtt, sorrendben: (1) `--dry-run`; (2) a szerző külön igenje; (3) a futtató élő
`usage()` ellenőrzése. A blokk után: a kimeneti fájl és a kvóta-állás ellenőrzése, a következő blokk csak ezek után.

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
