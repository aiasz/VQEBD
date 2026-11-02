# Fázis 11 — Kalibrációból épített Heron-zajmodell validálása valódi hardveren (`v1.1.0` terv)

| | |
|---|---|
| **Fázis** | 11 *(a mesterterv 10. „közösségi visszacsatolás" fázisától független, kísérleti ág; a számozás nem jelent időrendet)* |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Státusz** | **TERV — jóváhagyásra vár. Semmilyen hardveres futtatás nem indult, és nem is indítható a jóváhagyás nélkül.** |
| **Célverzió** | `v1.1.0` (ha a fázis lezárul) |
| **Előzmény** | [`phase_09.md`](phase_09.md), [`TR-F05` 7.](../testing/TR-F05_batch.md), [`10_literature_positioning.md`](../10_literature_positioning.md), v1.0.0 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic) — a terv MI-vel készült, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |

> **Fontos a tervről.** Ez a terv nem külső regiszterben (pl. OSF) előre regisztrált protokoll, hanem a repóban, git-commit
> időbélyeggel rögzített **belső előzetes meghatározás**. Az MI írta; a küszöbértékek (különösen a 3. fejezet δ-ja) **javaslatok**,
> amelyeket a szerzőnek jóvá kell hagynia vagy módosítania, *mielőtt* az első megerősítő mérés lefut.

---

## 1. Miért ez a következő lépés

A v1.0.0 hardveres H₂-görbéjén (5.H) a nyers (resilience 0) hiba +12 … +28 mHa, TREX-szel +5 … +18 mHa, pontonként **egyetlen
futás**. A [`10_literature_positioning.md`](../10_literature_positioning.md) szerint a VQEBD módszerei ismertek, és az egyetlen
kérdés, amely a keresés alapján nyitottnak *látszik*: **megjósolja-e a *jelenlegi kalibrációból épített* Heron-zajmodell
— kiolvasási hibával együtt — a valódi hardver VQE-energiahibáját?**

Ez azért érdemes, mert **kvóta nélkül** futtatható: ha a modell megbízható, a hardveres időt csak ellenőrzésre kell fordítani, a
nagyobb rendszereket pedig szimulálni lehet; ha nem, az is tudományos tartalmú, negatív eredmény.

---

## 2. Előzetes mérés (2026-11-02, v1.0.0) — **felderítő, nem megerősítő**

Mind **kvóta nélkül** futott (csak olvasás a szolgáltatótól + helyi szimuláció).

| # | Mérés | Eredmény | Következmény |
|---|---|---|---|
| M1 | `NoiseModel.from_backend(ibm_kingston)` felépítése | **4,4 s**; zajos műveletek: `cz, id, measure, reset, sx, x, xslow`; **readout-hiba mind a 156 qubitre** a modellben | A zajmodell gyorsan, kvóta nélkül előállítható |
| M2 | A mérés ISA-áramköre ugyanazzal a transzpilálással | mélység 23, **4 kétqubites kapu, 2 aktív qubit** (`[1, 2]`) | Az áramkör nagyon kicsi; **az eredmény a két qubitre és a kiolvasásra érzékeny, nem a processzor egészére** |
| M3 | Aer `EstimatorV2` (zajmodell, **kiolvasási hiba nélkül**), 0,735 Å | +0,45 ± 3,76 mHa (6 futás, szórás 9,2) | A hardver +22,2 ± 2,8 mHa-jától messze van, de a **precizitása rossz** (SE 3,8): önmagában gyenge bizonyíték |
| M4 | `BackendEstimatorV2` + `AerSimulator.from_backend` (**kiolvasási hibával**), 0,735 Å | **+21,97 ± 0,87 mHa** | Egyezik a nyers hardverrel (+22,2 ± 2,8) |
| M5 | M4 mind az 5 geometriára (n = 10 modellfuttatás/pont), a meglévő hardveres nyers görbével | modell: +31,8 / +23,2 / +18,6 / +12,4 / +11,9 mHa; hardver: +27,7 / +22,2 / +17,4 / +12,4 / +12,2 mHa; **z = +1,19, +0,33, +0,44, −0,03, −0,15** (mind \|z\| < 2) | Összeférhető, **de** a 0,5 Å-nél a modell ~4 mHa-val magasabb: az a pont lehet a leggyengébb |
| M6 | A mérés időigénye | 5 geometria × 14 kiértékelés ≈ **185 s** helyi számítás | Kvóta nélkül, percek alatt ismételhető |
| M7 | IBM Open Plan kvóta | **600 s / 28 nap**, ebből 57 s használt, **543 s hátravan**; költség: **~4,8 s/PUB** (nyers), **~6,6 s/PUB** (TREX) | A hardveres terv költségvetése (4. fejezet) innen jön |
| M8 | Kalibrációs pillanatkép | **jelenleg nem mentjük** a futásokhoz | Pótlandó (11.A): a modellt a *mérés idejének* kalibrációjával kell építeni |

**Mit NEM mutat M1–M6.** (a) A hardveres görbe már ismert volt a modellillesztéskor *(a modellnek nem voltak szabad paraméterei,
de a döntéseket — pl. hogy a `BackendEstimatorV2` utat nézzük — az eredmény ismeretében is hozhattuk)*, ezért ez
**hipotézis-generáló**; (b) a hardver egyetlen futás/pont, SE 1,7–3,0 mHa, ezért 1,2σ nem azt jelenti, hogy a modell jó, csak azt,
hogy nem zárható ki; (c) a modellt a **mostani** kalibrációból építettük, a hardvert **2026-11-02-án, más kalibráció mellett**
mértük (a történeti `backend.properties(datetime=…)` nincs kipróbálva); (d) egyetlen eszköz, egy molekula, 2 qubit.

---

## 3. Hipotézisek, végpontok, döntési szabályok (**javaslat — jóváhagyandó**)

**Egység:** a *blokk* (egy időben összetartozó hardveres futássorozat). A statisztikai egység a blokk, nem a lövés vagy a PUB:
egy blokkon belüli PUB-ok ugyanazt a kalibrációt látják.

**Megerősítő geometriák:** R ∈ {0,735; 1,5; 2,0} Å (egyensúly; a v1.0.0-ban egyetlen kémiai pontosságon belüli pont; disszociáció).
A 0,5 és 1,0 Å a *pilotban* (11.B) szerepel, de a megerősítő végpontokban nem.

| # | Hipotézis | Végpont | Döntési szabály |
|---|---|---|---|
| **H1** *(elsődleges)* | A kalibrációból épített, kiolvasást is modellező Heron-modell megjósolja a **nyers** hardveres hibát | geometriánként a Δ_g = ⟨HW_nyers − Modell⟩ a blokkokon át, 90%-os t-CI (TOST) | **Egyenértékű**, ha mindhárom geometriára a 90% CI ⊂ [−δ, +δ], **δ = 3,0 mHa** *(javaslat: ≈ 2× a kémiai pontosság; ≤ ~25% a hardveres jel (12–28 mHa) mellett)*. **Részben**: 2/3. **Elutasítva**: egyébként |
| **H2** | A kiolvasási hiba modellezése lényeges | a Δ_g négyzetes hibája kiolvasással vs. **kiolvasás nélkül** (azonos modell, `readout_error` kikapcsolva), páros különbség blokkonként | H2 igaz, ha a kiolvasásos modell blokkokon átlagolt négyzetes hibája kisebb, a páros különbség 95% CI-je kizárja a nullát |
| **H3** *(másodlagos, felderítő)* | A TREX-szel enyhített hardver ≈ a modell **kiolvasási hiba nélkül** | ugyanaz a TOST, δ = 3,0 mHa | **Nem** hozhat megerősítő állítást: a TREX-et a modell nem szimulálja, a kiolvasás-nélküli modell csak közelítés |
| **H4** *(másodlagos)* | A blokkonkénti (friss) kalibráció pontosabb, mint egy rögzített | páros különbség a blokkonkénti-kalibrációs és a pilot-kalibrációs modell négyzetes hibájában | csak leíró; ha a kalibráció a blokkok közt alig változik, nincs teljesítménye |
| **H5** *(opcionális, 11.D)* | A modell a θ-függést is jól adja (nem csak θ\*-nál) | 1D θ-scan: modell vs. hardver görbe, reziduumok | csak leíró (nincs elfogadási küszöb) |

**A döntés következménye (előre kimondva):**

- **H1 egyenértékű** → a modell *adott eszközre, adott molekulára, adott kalibrációs korszakban* érvényesnek mondható. Csak ekkor
  készülhet a 11.E (nagyobb rendszerek **szimulálva**, minden ábrán „Heron-modell, nem mérés" jelöléssel).
- **H1 részben/elutasítva** → negatív eredmény, **közlendő**. A 11.E elmarad. A reziduumok elemzése (drift? áthallás? egy-qubites
  hiba?) a következő lépés.
- **Nem szabad** a küszöböt a mérés után módosítani. Ha a mérés közben kiderül, hogy δ rossz, az új δ-val **új, külön protokoll**
  készül, és a régi eredmény változatlanul közölve marad.

**Feltáró/megerősítő szétválasztás.** Az 5 geometriás meglévő hardveres görbe (M5) **feltáró**. A megerősítő mérések **új**
hardveres blokkok, új kalibrációval; a modell beállításait (becslő, `AerSimulator` opciók, ismétlésszám, seed-kezelés,
transzpiler-seed, **fix fizikai qubitpár**) a 11.A végén **befagyasztjuk** (git-címke `protocol-f11-frozen`), az első megerősítő
blokk előtt.

---

## 4. Hardveres terv: darabolás az ingyenes keretbe

**Alapelv.** Egy blokk legfeljebb a kvóta ~6–10%-a; a blokkok **külön napokon** futnak (a kalibráció naponta frissül, és ez a drift
becsléséhez is kell); a keret használt hányada soha nem lépi át a **80%-ot** (≥ 120 s tartalék). A beküldés előtti kapu az élő
`service.usage()`: ha a becsült igény + a már használt > 480 s, a blokk **nem fut** (a meglévő K7-védelem, `VQEBD_ALLOW_HARDWARE`,
`assert_quota_available`, `--dry-run` ezt kikényszeríti).

**Blokkonként** (páros, egymás utáni beküldés, a sorrend blokkonként keverve: nyers↔TREX, hogy az idő hatása ne egy feltételhez
tapadjon):

| Blokk típus | Tartalom | Költség (becslés) |
|---|---|---|
| **Pilot (B0)** | 5 geometria × (nyers + TREX), a *fix* qubitpáron; **kalibrációs pillanatkép** | 5 × (4,8 + 6,6) = **57 s** |
| **Megerősítő (C1…C8)** | 3 geometria × (nyers + TREX) | 3 × (4,8 + 6,6) = **34,2 s** |
| **θ-scan (D)** | 0,735 Å-nél 15 θ-pont egyetlen jobban, nyers | 15 × 4,8 = **72 s** |

**Ütemezés** (a napok a **jóváhagyás utáni 0. naphoz** viszonyítva; az „ablak" az IBM gördülő 28 napos keretére vonatkozik, a valódi
szabad keretet a futtatás előtt mindig az élő `usage()` adja):

| Blokk | Nap | Költség | A keret használt hányada utána (a 57 s meglévő használattal) | Megjegyzés |
|---|---|---|---|---|
| — (jelenlegi állapot) | — | — | 57 / 600 = 9,5% | 543 s hátravan |
| B0 pilot | 0 | 57 s | 114 / 600 = 19% | kalibrációs pillanatkép; a költség/PUB újramérése |
| C1 | 2 | 34,2 s | 148 / 600 = 25% | |
| C2 | 4 | 34,2 s | 182 / 600 = 30% | |
| C3 | 6 | 34,2 s | 217 / 600 = 36% | |
| C4 | 8 | 34,2 s | 251 / 600 = 42% | **Köztes elemzés** (csak leíró; a végpont nem változik) |
| C5 | 10 | 34,2 s | 285 / 600 = 48% | |
| C6 | 12 | 34,2 s | 319 / 600 = 53% | |
| C7 | 14 | 34,2 s | 353 / 600 = 59% | |
| C8 | 16 | 34,2 s | 388 / 600 = 65% | **A megerősítő szakasz vége; a H1–H4 kiértékelése** |
| D θ-scan | ≥ 30 (új ablak) | 72 s | az akkor élő `usage()` szerint | a 2. ablakban, amikor a nov. 2-i 57 s és a B0 már kikopott |

- Az 1. ablak összes használata: 57 s (meglévő) + 57 s (B0) + 8 × 34,2 s = **~388 s ≤ 480 s** (a 80% küszöb). **A tartalék ≥ 212 s.**
- Ha a pilot a **per-PUB költséget > 20%-kal eltérőnek** mutatja a becsléstől (kisebb jobok költsége nem biztos, hogy lineáris), a
  táblázatot **a C1 előtt** újraszámoljuk; a kapu amúgy is az élő használatot nézi.
- Ha egy blokk kimarad (leállás, kvóta, a backend elérhetetlen), **nem pótoljuk ugyanazon a napon**: az ütemezés tolódik. Ha az
  `ibm_kingston` megszűnik, **másik eszközre nem váltunk** (az új tanulmány lenne).
- **Sehol nincs automatikus hardveres futtatás** (ADR-0008): minden blokkot a szerző indít, előtte `--dry-run`.
- A **QPU-optimalizálót** nem használjuk (a 2026-09-23-i eset: 42 job, 630 s); mindig a már ismert θ\*-ot mérjük.

**Statisztikai teljesítmény (becslés a meglévő adatból).** A hardveres nyers görbén a lövés-SE 1,7–3,0 mHa/job. 8 blokk után a
blokkok közti átlag SE-je ≈ 0,6–1,1 mHa *(drift nélkül)*; a t₇ = 1,89 (90%) mellett a CI fél-szélessége ≈ 1,1–2,0 mHa < δ = 3,0.
**Mi nincs benne:** a blokkok közti drift és a modell saját szórása; a 0,5 Å-es ~4 mHa-s eltérés típusú rendszeres hiba esetén H1
valódi elutasítást adhat. A pilot ad első becslést a blokkok közti szórásra, és ha az túl nagy (CI fél-szélesség > δ nyolc blokkal
is), a protokoll **módosítása** helyett a **blokkszám növelését** javasoljuk (a 600 s keretig, ablakonként).

**Mit nem csinál több ismétlés.** A hardveres hiba (5–28 mHa) ≫ a lövészaj (2–3,5 mHa): az ismétlés a *rendszeres* eltérést (modell vs.
hardver) pontosítja, nem javítja a hardver eredményét.

---

## 5. Szükséges kódváltozások (kvóta nélkül, 11.A)

| # | Változás | Megjegyzés |
|---|---|---|
| C1 | Új szimulátor-útvonal: **kiolvasást is modellező** becslő (`BackendEstimatorV2` + `AerSimulator.from_backend(backend)`), a mostani `qiskit_aer_noisy` (FakeManila, readout nélküli Aer-becslő) **mellett**, nem helyett | az ADR-0003 1. kiegészítése (K1) szerint az Aer `EstimatorV2` nem modellez kiolvasási hibát |
| C2 | A modell a **tényleges backendből** (`NoiseModel.from_backend`) építhető, a kalibráció-időbélyeg rögzítve | a DB-sémában új mező (v4) vagy a `metadata` JSON |
| C3 | **Kalibrációs pillanatkép** minden hardveres blokkhoz: időbélyeg, a használt qubitek T1/T2/readout/kapuhibái, `last_update_date` | csak olvasás, QPU-idő nélkül; fájlba (`docs/figures/data/f11/`) |
| C4 | **Fix fizikai qubitpár** (`initial_layout`) a pilotból; a transzpiler `seed`-je rögzítve | különben a blokkok nem összehasonlíthatók (az optimalizált layout a kalibrációtól függ) |
| C5 | `scripts/run_heron_blocks.py` — blokkonkénti futtató: `--block B0|C1…C8|D`, `--dry-run`, kapu, **nyers job-adatok mentése** (job-azonosító, eredmények, időbélyeg) | a meglévő `run_hardware_pes.py` mintájára |
| C6 | **Elemző szkript**, a mérések előtt megírva és **szintetikus adaton tesztelve** (TOST, blokk-szintű t-CI, páros különbségek) | az elemzési rugalmasság ellen |
| C7 | Dashboard-nézet (opcionális, 11.F) | |

---

## 6. Lépések, elfogadási kritériumok, tesztek

| Lépés | Tartalom | Kvóta | Jóváhagyás |
|---|---|---|---|
| **11.A** | C1–C4, C6 megvalósítása, tesztek, TP-F11 | 0 s | a terv jóváhagyása után |
| **11.A-fagyasztás** | git-címke `protocol-f11-frozen`; a δ és a geometriák végleges jóváhagyása | 0 s | **szerző** |
| **11.B** | B0 pilot (+ költség-újramérés) | 57 s | **szerző, blokk előtt** |
| **11.C** | C1…C8 | 8 × 34,2 s | **szerző, blokkonként** |
| **11.D** | θ-scan *(opcionális)* | 72 s | szerző |
| **11.E** | nagyobb rendszerek **szimulálva** — *csak ha H1 egyenértékű* | 0 s | szerző |
| **11.F** | TR-F11, README/CHANGELOG, `v1.1.0` | 0 s | szerző |

| AC | Kritérium |
|---|---|
| AC-11.1 | A readout-aware útvonal 0,735 Å-nél reprodukálja az M4 értékét (+22 ± ~2 mHa) a konténerben |
| AC-11.2 | A kalibrációs pillanatkép minden hardveres blokkhoz mentve, a modell *ebből* épül |
| AC-11.3 | Az elemző szkript szintetikus adaton: ismert eltolást (pl. 5 mHa) kimutat; eltolás nélkül TOST-egyenértékűséget ad (negatív kontroll is) |
| AC-11.4 | Egyetlen blokk sem lépi át a 80%-os használatot; a kapu tesztelt (`--dry-run`, kimerült kvóta, hiányzó engedély) |
| AC-11.5 | A `protocol-f11-frozen` címke megelőzi az első megerősítő blokkot (a commit-időbélyegek igazolják) |
| AC-11.6 | A H1–H4 az előre kimondott szabály szerint kiértékelve; az eredmény (pozitív vagy negatív) közölve; a feltáró és a megerősítő adat külön jelölve |
| AC-11.7 | A TR-F11 minden korlátot kimond (egy eszköz, 2 qubit, H₂, ~8 blokk, MI-vel készített terv, nincs külső regisztráció) |

---

## 7. Kockázatok és korlátok

| # | Kockázat / korlát | Kezelés |
|---|---|---|
| R1 | **Kalibrációs drift:** a modell a mérés *idejének* kalibrációjából épül, de a pillanatkép és a futás között idő telik | pillanatkép közvetlenül a blokk előtt **és** után; H4 |
| R2 | **Csak 2 qubit, 4 CZ:** a modell érvényessége nem általánosítható | a 11.E csak a *mért* paraméter-tartományra utalhat, kimondva |
| R3 | **A TREX-et a modell nem szimulálja** (H3 csak közelítés) | H3 másodlagos, nem megerősítő |
| R4 | **Szelekciós rugalmasság:** a küszöb vagy a geometria utólagos módosítása | `protocol-f11-frozen`; a változtatás új protokoll |
| R5 | A kvóta/ablak szabályai változhatnak, a „gördülő 28 nap" a mért viselkedésből (K7) következik | az élő `usage()` az egyetlen hiteles kapu |
| R6 | A terv és az elemzés MI-munka; **nem lektorált** | AI_DISCLOSURE; a szerző a küszöböket jóváhagyja; külső (emberi) statisztikus bevonása javasolt a közlés előtt |
| R7 | Az eredmény a „jó modell" mellett is csak a H₂/2 qubit esetre szól | a közlés nem állíthat általános validitást |

---

## 8. Nyitott kérdések a szerzőnek (a jóváhagyáshoz)

1. **δ = 3,0 mHa** elfogadható? (Szigorúbb δ = 1,6 mHa csak sokkal több blokkal lenne megvalósítható; lásd a teljesítmény-becslést.)
2. A megerősítő geometriák **{0,735; 1,5; 2,0} Å** jók?
3. Jó-e a **8 megerősítő blokk / 2 naponként** ütem, vagy más ritmus kell (pl. hétvégék nélkül)?
4. Kéri-e az **opcionális θ-scant (11.D)**?
5. Kéri-e a protokollt **külső regiszterben** (pl. OSF) is rögzíteni a `protocol-f11-frozen` címke mellett?

*Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc*
