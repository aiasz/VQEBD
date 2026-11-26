# TR-F11 — Fázis 11 jegyzőkönyv (a Heron-zajmodell validálása) — VÉGLEGES

| | |
|---|---|
| **Azonosító** | TR-F11 |
| **Dokumentum-verzió** | 1.0.1 (végleges, a szerző átnézte 2026-11-26-án; a 22. szakasz a kiadás előtti átnézés helyesbítéseit, a 21. szakasz az átnézés kérdéseire adott felderítő válaszokat, a 0. szakasz az összefoglaló, a 17. a leíró reziduum-áttekintés, a 18. a korlátok, a 19. az elfogadási kritériumok, a 20. a következő lépések; a 16. szakasz a kiegészítő C9-et és a végleges érzékenységi vizsgálatokat, a 15. szakasz az elsődleges elemzést (H1–H4), a 14. szakasz a C9 előtti, hardver nélküli bővítést és a C1–C8 kalibráció-életkorát, a 13. szakasz a C8-at (a megerősítő mérés vége) és az IBM-válasz hivatkozását, a 12. a C7-et és a kalibrációs várakozást tartalmazza; a 6. szakasz a C1-et, a 7. a C2-t, a 8. a C3-at, a 9. a C4-et és a köztes leíró összesítést, a 10. a C5-öt, a 11. a C6-ot és a megszakadt első kísérletét tartalmazza) |
| **Dátum** | 2026-11-02 (B0), 2026-11-04 (C1), 2026-11-06/07 (C2), 2026-11-08 (C3), 2026-11-10 (C4), 2026-11-12 (C5), 2026-11-14/16 (C6), 2026-11-22 (C7), 2026-11-24 (C8), 2026-11-26 (C9) |
| **Terv / tesztterv** | [`phase_11.md`](../plan/phase_11.md), [`TP-F11_heron_modell.md`](TP-F11_heron_modell.md) |
| **Kezdeményezte, irányította, engedélyezte** | Kormos Attila (a B0-t 2026-11-02-án, a C1-et 2026-11-04-én, a C2-t 2026-11-06-án, a C3-at 2026-11-08-án, a C4-et 2026-11-10-én, a C5-öt 2026-11-12-én, a C6-ot 2026-11-14-én és újraindítását 2026-11-15-én, a C7-et 2026-11-22-én, a C8-at 2026-11-24-én, a C9-et 2026-11-26-án külön jóváhagyta) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — a kódot és a szöveget az MI írta a szerző kérésére, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |
| **Státusz** | **Végleges (1.0.1, 2026-11-26) — a szerző átnézte; a kiadás előtti átnézés helyesbítései: 22. szakasz.** A hardveres mérések lezárultak (B0 pilot, C1–C8 megerősítő, C9 kiegészítő blokk); az előre rögzített elsődleges elemzés: **H1 elutasítva** (csak a 2,0 Å-nél egyenértékű), **H2 igaz**, a H3 felderítő, a H4 leíró; az előre rögzített érzékenységi vizsgálatok a képet nem változtatják. **A B0 feltáró, a C9 kiegészítő adat.** Összefoglaló: 0. szakasz; korlátok: 18. szakasz; a szerzői átnézés kérdései (felderítő): 21. szakasz. |

## 0. Összefoglaló — a Fázis 11 eredménye

**A kérdés.** Megjósolja-e az IBM által *közölt* kalibrációs adatokból (T1, T2, kiolvasási hiba, kapuhibák) épített Heron-zajmodell, mekkora hibát ad a
valódi `ibm_kingston` kvantumgép a H₂-molekula kétqubites VQE-számításában? A jóslat akkor jó, ha a gép nyers hibája és a modell közti átlagos eltérés
minden vizsgált kötéshossznál bizonyíthatóan ±3,0 mHa-en belül van (90%-os egyenértékűségi teszt, TOST). A szabályokat a mérések **előtt** rögzítettük
(`protocol-f11-frozen`, 2026-11-02).

**A mérés.** Egy pilot (B0), nyolc megerősítő (C1–C8) és egy kiegészítő blokk (C9), 2026. november 2. és 26. között, mindig ugyanazon a gépen és
qubitpáron ([1, 2]), blokkonként friss kalibrációs pillanatképpel és modell-előrejelzéssel, blokkonként a szerző külön jóváhagyásával; összesen
**408 QPU-másodperc** az ingyenes keretből (a keret végig ≤ 80%).

**Az eredmény az előre rögzített szabályok szerint** (15–16. szakasz):

| Hipotézis | Eredmény | Számok (mHa; 90% CI, ill. 95% CI) |
|---|---|---|
| **H1** *(elsődleges)*: kimutatható-e, hogy a modell átlagos eltérése a nyers hibától ±3,0 mHa-en belül van | **elutasítva** (1/3 geometria) | 0,735 Å: +7,5 [−0,1; +15,1] — nem mutatható ki; 1,5 Å: +2,8 [−1,9; +7,4] — nem mutatható ki (határozatlan); 2,0 Å: −0,2 [−2,6; +2,2] — kimutatva |
| **H2**: a kiolvasási hiba modellezése lényeges | **igaz** | +252 mHa² [+131; +373]; mind a 8 blokkban a kiolvasásos modell a jobb |
| **H3** *(felderítő)*: TREX-hardver ≈ kiolvasás nélküli modell | csak a 2,0 Å-nél egyenértékű | megerősítő állítást nem hoz |
| **H4** *(leíró)*: pontosabb-e a friss kalibráció egy rögzítettnél | nem bizonyult pontosabbnak | 8-ból 6 blokkban a rögzített (B0) kalibráció egyezett jobban |

- **Érzékenységi vizsgálatok** (2026-11-18-án, a C7–C9 előtt rögzítve; leíró, döntési szabály nélkül): mind a kilenc blokkal (C1–C9) és csak a legfeljebb
  48 órás kalibrációjú blokkokkal (a C6 nélkül) is ugyanez a kép — csak a 2,0 Å fér a sávba. A 0,735 Å-nél a pontbecslés 9 blokkból 8-ban pozitív, és a
  C9-cel együtt a 90%-os intervallum nem tartalmazza a nullát (leíró, nem előre rögzített összevetés); az elsődleges (C1–C8) intervallum a nullát tartalmazza.
- **Az előre kimondott következmény:** negatív eredmény, **közlendő**; a 11.E (nagyobb rendszerek szimulálása a modellel) **elmarad**; a következő lépés az
  eltérések okainak elemzése (első, leíró áttekintés: 17. szakasz).
- **Ami állítható:** ezen az eszközön, ezen a qubitpáron, a H₂ kétqubites VQE-jén, 2026 novemberében a közölt kalibrációból épített modellnél az előre
  rögzített teszt szerint **nem sikerült kimutatni**, hogy a gép nyers hibájától való átlagos eltérése ±3,0 mHa-en belül van — csak a leghosszabb, 2,0 Å-es
  kötésnél (ott is csak az átlagra: egy-egy blokk eltérése elérte a ±6 mHa-t); az 1,5 Å-nél az eredmény határozatlan. A kiolvasási hiba modellezése nélkül
  a modell sokkal rosszabb.
- **Ami nem állítható:** hogy a modell más gépen, qubitpáron vagy molekulán sem működne; hogy a kvantumgép „pontos” lenne (nyers hibája 8–55 mHa, a kémiai
  pontosság 1,6 mHa — a kísérlet a *zajmodellt* teszteli, nem a gépet); az eltérés oka.
- **Korlátok:** 18. szakasz; **az elfogadási kritériumok:** 19. szakasz; **a szerzői átnézés kérdései** (felderítő): 21. szakasz; **a kiadás előtti
  helyesbítések:** 22. szakasz. Az 1–14. szakasz a mérés időrendi naplója (blokkonként), a 15–16. a végleges elemzés.

**Közérthetően.** A gép hivatalos „műszerlapjából” (kalibrációs adataiból) épített számítógépes másolat azt próbálta előre megmondani, mennyit fog tévedni a
valódi kvantumgép. A legnagyobb kötéshossznál a másolat átlagosan eltalálta a gép tévedését. A legkisebbnél átlagosan kevesebbet jósolt, mint amennyit a gép
tévedett, és a napról napra mért eltérések is túl nagyok voltak ahhoz, hogy az előre kért ±3 mHa-es egyezést ki lehessen mutatni; a középsőnél az adat nem
dönti el a kérdést. A „nem sikerült kimutatni” itt is érvényes, előre vállalt eredmény: erre a feladatra a közölt kalibrációból épített modellre önmagában
nem lehet hagyatkozni.

## 1. Mi futott le

| Elem | Érték |
|---|---|
| Blokk | B0 (pilot): 5 geometria × (nyers + TREX), R = 0,5; 0,735; 1,0; 1,5; 2,0 Å |
| Eszköz, qubitpár | `ibm_kingston`, fizikai qubitek **[1, 2]** (a protokollban előre rögzítve) |
| Lövésszám | 8192 / PUB |
| Protokoll-ujjlenyomat | `6352160344462f26a5547a0874c2bc88412c970f886e5433ca755431147e93c9` (egyezik a `FROZEN` fájllal és a `protocol-f11-frozen` címkével; kód: `57a421b`) |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), majd a szerző külön jóváhagyása |
| Engedélyek | `VQEBD_ALLOW_HARDWARE=true`, `FROZEN` egyezik, az élő `usage()` kapu (57 s + 71,2 s ≤ 480 s) |
| Kimenet | [`docs/figures/data/f11/b0.json`](../figures/data/f11/b0.json), [`b0.log`](../figures/data/f11/b0.log) |

### 1.1 Jobok és QPU-idő

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 0 (nyers) | `dbkc5m0nceqs73aljbt0` | 17:05:28 | 17:38:25 | 17:39:01 | **24** | 24,0 |
| 1 (TREX) | `dbkclel6p51s73cmcas0` | 17:39:06 | 17:39:08 | 17:39:56 | **33** | 33,0 |

- **Összesen 57 QPU-s**, pontosan a becsült (4,8 s/PUB nyers, 6,6 s/PUB TREX) — a költségmodell a mérésben is igazolódott.
- **Kvóta (gördülő 28 nap, 600 s):** előtte 57 s, utána **114 s** használt, **486 s hátravan**. A 80%-os határ (480 s) alatt vagyunk.
- A nyers job **32,9 percet** állt sorban (a falióra-idő 2018 s ≈ 33,6 perc, a futással együtt); a sorban állás nem számít QPU-időnek. *(Helyesbítve, 22.4.)*
- Hibás vagy félbehagyott job nem keletkezett; hardveres újrafuttatásra nem volt szükség.

### 1.2 Kalibráció

A blokk előtti és utáni pillanatkép `last_update_date` mezője azonos: **2026-11-02T16:10:11Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*. A futás 17:38–17:40 UTC között volt,
tehát ~1,5 órával a kalibráció után. Ha a kiolvasási hiba a kalibráció óta változott, azt a `properties()` pillanatkép nem mutatja
(a frissítési gyakoriságot nem vizsgáltuk); a két pillanatkép azonossága tehát nem bizonyítja, hogy a hiba közben állandó volt.

## 2. Eredmény (feltáró, egyetlen blokk)

Hiba a Full CI-hez képest (mHa); `z` = különbség / a hardver ensemble standard hibája (blokkon belüli statisztikai hiba, **nem** a
blokk-közi szórás).

### 2.1 Nyers hardver ↔ kiolvasást modellező Heron-modell (a H1 pilot-megfelelője)

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z |
|---|---|---|---|---|
| 0,5 | 53,0 | 35,6 | +17,4 | 4,9 |
| 0,735 | 40,0 | 25,9 | +14,1 | 4,6 |
| 1,0 | 25,9 | 18,2 | +7,7 | 2,8 |
| 1,5 | 16,9 | 13,4 | +3,5 | 1,4 |
| 2,0 | 15,9 | 13,5 | +2,4 | 1,4 |

A hardver minden geometriánál **rosszabb**, mint amit a modell jósolt; a két rövidebb kötéstávolságnál a különbség 4–5σ.
A protokoll megerősítő geometriái közül (0,735; 1,5; 2,0 Å) a 0,735 és az 1,5 Å-nél a különbség kívül esik a ±3,0 mHa sávon,
a 2,0 Å-nél belül van. Ez egyetlen blokk; a TOST-ot csak a megerősítő blokkok adatán értékeljük.

### 2.2 TREX hardver ↔ kiolvasás nélküli modell (a H3 pilot-megfelelője)

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z |
|---|---|---|---|---|
| 0,5 | 13,7 | 11,9 | +1,8 | 0,5 |
| 0,735 | 7,1 | 9,1 | −2,0 | −0,7 |
| 1,0 | 3,2 | 5,8 | −2,5 | −0,9 |
| 1,5 | 2,8 | 3,9 | −1,1 | −0,5 |
| 2,0 | 2,4 | 3,3 | −1,0 | −0,5 |

A TREX-es hardver és a kiolvasás nélküli modell minden geometriánál 1σ-n belül egyezik (|z| ≤ 0,9).

### 2.3 Ugyanaz a hardver, ugyanaz a qubitpár, 8 órával korábban (5.H, 2026-11-02 09:41 UTC)

| R (Å) | Nyers 09:41 | Nyers 17:38 | Változás | z | TREX 09:41 | TREX 17:39 |
|---|---|---|---|---|---|---|
| 0,5 | 27,7 | 53,0 | +25,3 | 5,4 | 12,1 | 13,7 |
| 0,735 | 22,2 | 40,0 | +17,8 | 4,3 | 17,6 | 7,1 |
| 1,0 | 17,4 | 25,9 | +8,6 | 2,2 | 5,4 | 3,2 |
| 1,5 | 12,4 | 16,9 | +4,5 | 1,3 | −0,7 | 2,8 |
| 2,0 | 12,2 | 15,9 | +3,8 | 1,6 | 5,5 | 2,4 |

A **nyers** hiba a nap folyamán 4–25 mHa-val nőtt (a rövid kötéseknél a legtöbbel), a **TREX-es** nem változott szisztematikusan.
(A TREX-oszlop pontonkénti eltérései – pl. 17,6 → 7,1 mHa a 0,735 Å-nél – a statisztikai hiba többszörösei is lehetnek; ezt a
pilot egy blokkja nem dönti el.)

## 3. Értelmezés – és ami NEM következik belőle

**Ami a számokból következik (egyetlen blokk, feltáró):**

1. A kalibrációból épített, kiolvasást modellező Heron-modell ezen a blokkon **alulbecsülte** a nyers hardverhibát, a rövid
   kötéseknél jelentősen (14–17 mHa).
2. A nyers hardverhiba **ugyanazon az eszközön és qubitpáron 8 óra alatt** a statisztikai hibát többszörösen meghaladóan változott.
3. A TREX-szel javított hardver a kiolvasás nélküli modellel egyezett. Összhangban van azzal, hogy a nyers szintnél a nem
   modellezett, **időben változó kiolvasási hiba** okozta a többletet – de ez **hipotézis**, nem ellenőrzött ok.

**Ami NEM következik:**

- Nem döntjük el a H1–H4-et: a pilot nem megerősítő adat, és a megerősítő blokkok még nem futottak.
- Az 5.H-ban korábban látott "|z| < 2 egyezés" (feltáró, a modell és a 09:41-es nyers hardver között) ezzel a blokkal nem
  erősíthető meg; a két megfigyelés együtt a **blokk-közi változékonyságra** utal, amit a terv H4-e és a 8 megerősítő blokk éppen
  mérni hivatott.
- Okot nem állítunk. Lehetséges magyarázatok (nem vizsgáltak): a kiolvasási hiba a kalibráció óta nőtt; átmeneti eszközállapot;
  a kalibrációs pillanatkép felbontása; a modell egyszerűsítései (pl. nem modellezett áthallás, TLS-fluktuáció).
- Egy eszköz, egy qubitpár, egy molekula (H₂), egy blokk.

## 4. Következmények a tervre

- A protokoll **befagyasztva** marad; a pilot eredménye miatt a küszöb, a geometriák vagy a qubitpár nem módosítható
  (egy módosítás új protokoll lenne, és szelekciós rugalmasságnak számítana — R4).
- Az eredmény **erősíti** a terv azon elemeit, amelyek a változékonyságot kezelik: blokkonkénti kalibrációs pillanatkép, a
  blokkonként váltakozó nyers/TREX sorrend, a H4 (blokkonkénti vs. rögzített kalibráció).
- Az, hogy a TOST/H1 a 3,0 mHa küszöb mellett egyáltalán teljesülhet-e, ennek fényében **bizonytalan**; a "H1 elutasítva"
  ugyanúgy értékes, publikálható eredmény. A TR-F11 végleges változata ezt a pilotot feltáró adatként, külön jelöli.
- A következő blokk (C1) csak a szerző külön jóváhagyásával, friss `--dry-run` után indul. A kvóta ehhez elegendő
  (114 s + 34,2 s ≈ 148 s ≪ 480 s).

## 5. Eltérések és megjegyzések (őszintén)

- A futtatás **a tervtől nem tért el** (protokoll, qubitpár, lövésszám, kapuk).
- A futtató kimenetét a `grep`-es csővezeték a futás alatt pufferelte; a `b0.log` csak a végén telt meg. Adatvesztés nem volt,
  a `b0.json` a teljes mérést tartalmazza.
- A 2.3 szakasz összehasonlítása és a z-értékek **nem előre kimondott** vizsgálatok, hanem a pilot utáni leíró számítások
  (a `b0.json` és a `hardver_pes.json` alapján; a különbség / √(σ₁² + σ₂²), a σ a blokkon belüli ensemble hiba).
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 6. C1 — az első megerősítő blokk (2026-11-04)

**Megerősítő adat, de n = 1:** a blokk-közi szórást nem lehet becsülni, ezért a TOST és a H1–H4 nem értékelhető. Az alábbi számok
leíró jellegűek. A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a futás a tervtől nem tért el.

### 6.1 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C1, R = 0,735; 1,5; 2,0 Å, nyers + TREX, `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), a szerző külön jóváhagyása, az élő `usage()` kapu (114 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c1.json`](../figures/data/f11/c1.json), [`c1.log`](../figures/data/f11/c1.log) |

| Szint | Job | Beküldve (UTC) | Futás | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 1 (TREX) — a protokoll szerint C1-en ez az első | `dbleevm74qds73dqbib0` | 08:06:22 | 08:26:45 | 08:29:41 | **24** | 19,8 |
| 0 (nyers) | `dblepul8mdtc73d61nng` | 08:29:46 | 08:29:48 | 08:35:03 | **15** | 14,4 |

- **Összesen 39 QPU-s** a becsült 34,2 s helyett (**+14%**). A kvóta 114 → **153 / 600 s**; a 80%-os határ (480 s) alatt, a kapu
  1,25-ös biztonsági szorzója (42,7 s) fedte a többletet.
- **A költségbecslés nem pontos a TREX-nél:** 6,6 s/PUB (B0) helyett itt 8,0 s/PUB. A két méréspontból (B0: 5 PUB, C1: 3 PUB)
  *hipotézisként* illeszkedik egy rögzített többlet + 4,5 s/PUB modell (nyers ≈ 1,5 s + 4,5·n, TREX ≈ 10,5 s + 4,5·n). Két pontból
  ez nem igazolt; a következő blokkok megerősítik vagy cáfolják. Ha igaz, minden blokk **~39 s**.
- **Hatás az ütemtervre:** a maradék 7 blokk × 39 s = 273 s → a végén **~426 s (71%)**, a 80% (480 s) alatt, a tartalék ~174 s (29%).
  A korábbi terv 388 s-ot jósolt; a ≥ 20%-os tartalék teljesül, a ≥ 212 s-os nem (a 212 s a becsült költséggel számolt cél volt).
- Sorban állás: a TREX job 20 percet, a nyers ~2 másodpercet várt; QPU-időt nem fogyaszt.
- **Korrekció a munkamenetből:** a futás közben tévesen "nyers" jobként írtam le az elsőként sorban álló jobot; az a protokoll
  szerint (`level_order("C1") = [1, 0]`) TREX volt. A kód a tervnek megfelelően működött.

### 6.2 Kalibráció

A blokk előtti és utáni pillanatkép azonos (`last_update_date` 2026-11-04T07:49:27Z, a pillanatképek 08:03 és 08:35 UTC-kor) *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*. A
B0-hoz (2026-11-02T16:10Z) képest **változott** az [1, 2] pár kalibrációja: kiolvasási hiba q1 1,09% → 0,68%, q2 0,92% → 1,07%;
T1 q1 394 → 178 µs; cz-hiba 0,113% → 0,099%. A modell-előrejelzés ennek megfelelően máshol van, mint a B0-nál (0,735 Å:
+25,9 → +23,0 mHa), tehát a modell reagál a kalibrációra. A szárazfutás (07:14Z kalibráció) és a valódi indítás (07:49Z) közti
változás az [1, 2] párra nem hatott (azonos előrejelzés), vagyis a köztes frissítés feltehetően más qubiteket érintett (nem vizsgáltuk).

### 6.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | B0 különbség (összevetésül) |
|---|---|---|---|---|---|
| 0,735 | 54,8 | 23,0 | **+31,8** | 9,1 | +14,1 |
| 1,5 | 26,7 | 11,8 | **+14,9** | 6,2 | +3,5 |
| 2,0 | 18,0 | 11,9 | **+6,1** | 3,9 | +2,4 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | B0 különbség (összevetésül) |
|---|---|---|---|---|---|
| 0,735 | 15,6 | 8,2 | +7,4 | 2,1 | −2,0 |
| 1,5 | 9,2 | 3,6 | +5,6 | 2,2 | −1,1 |
| 2,0 | 2,5 | 3,0 | −0,5 | −0,3 | −1,0 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C1 | Modell C1 | Arány C1 | Hardver B0 | Modell B0 | Arány B0 |
|---|---|---|---|---|---|---|
| 0,735 | 39,2 | 14,8 | 2,66 | 32,9 | 16,8 | 1,96 |
| 1,5 | 17,5 | 8,2 | 2,13 | 14,1 | 9,5 | 1,49 |
| 2,0 | 15,5 | 8,9 | 1,74 | 13,6 | 10,2 | 1,33 |

### 6.4 Értelmezés – és ami NEM következik belőle

- **A C1 a B0 irányát erősíti és élesíti:** a nyers hardverhibát a kalibrációból épített, kiolvasást modellező modell mindhárom
  geometrián jelentősen alulbecsülte (+6 … +32 mHa; a δ = 3,0 mHa sávon mindhárom kívül van), a különbség a rövid kötésnél a legnagyobb.
- **A hiányzó rész nagyrészt a kiolvasáshoz társul:** a hardveren a nyers és a TREX közti különbség 1,3–2,7-szerese annak, amit a
  modell a kiolvasási hibából jósol, mindkét blokkban és mindhárom geometrián. Ez *összhangban van* azzal, hogy a hardveren a
  tényleges (a mérés pillanatában érvényes, esetleg korrelált) kiolvasási hiba nagyobb a kalibrációban szereplő, qubitenkénti
  átlagos értéknél. **Ez hipotézis, nem ellenőrzött ok.**
- **A TREX-es egyezés sem teljes:** a B0-nál a TREX-es hardver a kiolvasás nélküli modellel 1σ-n belül egyezett, a C1-en két pont
  (0,735 és 1,5 Å) ~2,1–2,2σ-val magasabb. Ez egy blokkon nem megkülönböztethető a blokk-közi változékonyságtól.
- **A hardver maga is változik:** a nyers hiba a B0-hoz képest 0,735 Å-nél 40,0 → 54,8 mHa, 1,5 Å-nél 16,9 → 26,7, 2,0 Å-nél 15,9 → 18,0
  (két nap, más kalibráció). A TREX-es hiba is nőtt (7,1 → 15,6; 2,8 → 9,2; 2,4 → 2,5). A blokk-közi változékonyság tehát nagy;
  pontosan ezt méri a terv. Nem tudjuk, mennyi a kalibráció változásának, mennyi a hardver pillanatnyi állapotának a hatása.
- **Nem állítható:** a H1–H4 eldöntése (n = 1); az ok; általánosítás más eszközre, qubitpárra vagy molekulára.
- **Várható irány (nem előrejelzés):** ha a C2…C8 is hasonlóan viselkedik, a H1 (egyenértékűség ±3,0 mHa-n belül) elutasított lesz.
  A protokoll a küszöböt nem engedi módosítani; az elutasítás értékes, publikálandó eredmény ("a kalibrációból épített modell
  nem jósolja a nyers hardverhibát, mert a kiolvasási hiba nagyobb a kalibrációnál").

### 6.5 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás); a TOST csak a megerősítő blokkok
  teljes sorozatán értékelhető (`scripts/analyze_heron.py`, C8 után).
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 7. C2 — a második megerősítő blokk (2026-11-06/07)

**Megerősítő adat, n = 2 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). Az alábbi számok leíró jellegűek.
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a futás a tervtől nem tért el.

### 7.1 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C2, R = 0,735; 1,5; 2,0 Å, nyers + TREX, a szintek sorrendje a protokoll szerint nyers először (`level_order("C2") = [0, 1]`), `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), a szerző külön jóváhagyása, az élő `usage()` kapu (153 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c2.json`](../figures/data/f11/c2.json), [`c2.log`](../figures/data/f11/c2.log) |

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 0 (nyers) | `dbmp1hd8ft8s738vagog` | 2026-11-06 08:33:09 | 2026-11-06 23:34:13 | 23:36:00 | **15** | 14,4 |
| 1 (TREX) | `dbn68ptt7fqc73aj0mm0` | 23:36:07 | 23:38:13 | 23:45:40 | **24** | 19,8 |

- **Összesen 39 QPU-s** (a C1-gyel azonos: 15 + 24), a becsült 34,2 s helyett (+14%). A kvóta 153 → **192 / 600 s** (32%), a
  80%-os határ (480 s) alatt. A 3 geometriás blokk költsége két egymás utáni blokkon **pontosan ugyanannyi** volt (nyers 15, TREX 24 s);
  a „~39 s / blokk" feltevés tehát két mérésre támaszkodik (nem általános törvény), de az ütemtervi jóslat (a C8 után ~426 s, 71%) változatlan.
- **Sorban állás:** a nyers job **15 óra 1 percet** állt sorban (08:33 → 23:34 UTC; az `ibm_kingston` függő jobjainak száma 152 → 47
  között mozgott, karbantartási szünettel), a TREX job 2 percet. A sorban állás QPU-időt nem fogyaszt. A nyers job tényleges futása
  107 s falióra-idő volt.
- A futtató végig élt, a jobot nem szakítottuk meg; hibás vagy félbehagyott job nem keletkezett.

### 7.2 Kalibráció

A blokk előtti (08:30 UTC) és utáni (23:45 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-06T01:30:29Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)* *(a job indulásakor, 23:34 UTC-kor érvényes kalibráció `last_update_date`-je 22:34 volt; a pár paraméterei
változatlanok, 14.2)*; a futás a
kalibrációhoz képest ~22 órával később volt. Mivel a job 15 órát várt, a kalibrációs pillanatkép és a mérés közt hosszabb idő telt
el, mint a B0/C1-nél; hogy a kiolvasási hiba közben változott-e, a `properties()` nem mutatja. Az [1, 2] pár kalibrációja a C1-hez
képest: kiolvasási hiba q1 0,68% → 0,88%, q2 1,07% → 0,98%; T1 q1 178 → 256 µs; a cz-hiba azonos (0,099%). A modell-előrejelzés
(nyers 24,3 / 12,6 / 12,6 mHa) a kalibrációhoz igazodik.

### 7.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | B0 | C1 |
|---|---|---|---|---|---|---|
| 0,735 | 34,5 | 24,3 | **+10,2** | 3,5 | +14,1 | +31,8 |
| 1,5 | 16,0 | 12,6 | **+3,4** | 1,4 | +3,5 | +14,9 |
| 2,0 | 14,3 | 12,6 | **+1,6** | 0,9 | +2,4 | +6,1 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | B0 | C1 |
|---|---|---|---|---|---|---|
| 0,735 | 12,8 | 8,7 | +4,1 | 1,4 | −2,0 | +7,4 |
| 1,5 | 3,2 | 3,8 | −0,6 | −0,2 | −1,1 | +5,6 |
| 2,0 | −0,1 | 3,3 | −3,4 | −1,9 | −1,0 | −0,5 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C2 | Modell C2 | Arány C2 | Arány C1 | Arány B0 |
|---|---|---|---|---|---|
| 0,735 | 21,7 | 15,6 | 1,39 | 2,66 | 1,96 |
| 1,5 | 12,7 | 8,7 | 1,46 | 2,13 | 1,49 |
| 2,0 | 14,4 | 9,4 | 1,54 | 1,74 | 1,33 |

### 7.4 Értelmezés – és ami NEM következik belőle

- **A C2-n a modell és a hardver közti eltérés kisebb, mint a C1-en:** a nyers hardverhibát a modell mindhárom geometrián továbbra is
  alulbecsüli (+10,2 / +3,4 / +1,6 mHa), de a C1-nél (+31,8 / +14,9 / +6,1) jóval kevésbé. A statisztikai hibán belül (z < 2) csak az
  1,5 és a 2,0 Å egyezik; a 0,735 Å-nél az eltérés (z = 3,5) és a ±3,0 mHa sáv is kizárja az egyezést. **Ez nem a TOST**, csak a pontbecslés leírása.
- **A hardver nyers hibája blokkról blokkra erősen változik:** 0,735 Å-nél 40,0 (B0) → 54,8 (C1) → 34,5 mHa (C2); 1,5 Å-nél 16,9 →
  26,7 → 16,0; 2,0 Å-nél 15,9 → 18,0 → 14,3. A modell-előrejelzés ennél sokkal kisebb mértékben mozog (0,735 Å: 25,9 → 23,0 → 24,3),
  tehát a blokkok közti eltérés nagy része a **hardver** változásából jön, amit a modell (kalibrációs pillanatkép alapján) nem követ.
  Ez összhangban van azzal, hogy a H1 nehezen teljesül; **az ok nem ismert** (kalibráció-elavulás, TLS-fluktuáció, egyéb).
- **A kiolvasási hozzájárulás aránya** a C2-n kisebb (1,39–1,54) és egymáshoz közelebbi, mint a C1-en (1,74–2,66); mindhárom blokkban
  (B0, C1, C2) a hardveré a nagyobb (1,33–2,66 ×). A korábbi hipotézis (a tényleges kiolvasási hiba nagyobb a kalibrációsnál)
  tehát nem cáfolódott, de a mértéke blokkonként 1,3 és 2,7 között mozog; ez továbbra is hipotézis.
- **A TREX-es egyezés a C2-n jobb**, mint a C1-en (|z| ≤ 1,9), de a 2,0 Å-nél a hardver az FCI **alá** esik (−0,1 mHa; a statisztikai
  hiba ±1,8 mHa): ez zajjal összeegyeztethető.
- **Nem állítható:** a H1–H4 eldöntése; az ok; általánosítás más eszközre, qubitpárra vagy molekulára. A három blokk (B0 feltáró, C1, C2)
  eltérő nagyságú különbséget ad, ami éppen azt indokolja, hogy a protokoll 8 megerősítő blokkot ír elő.
- **Várható irány (nem előrejelzés):** ha a nyers hiba blokk-közi szórása a C1–C2 szintjén marad, a TOST széles megerősítő sávot kap,
  és a H1 a ±3,0 mHa küszöbön valószínűleg nem teljesül. A küszöb nem módosítható.

### 7.5 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás); a TOST csak a megerősítő blokkok
  teljes sorozatán értékelhető (`scripts/analyze_heron.py`, C8 után).
- A 15 órás várakozás miatt a kalibráció-elavulás hatása a C2-n nem zárható ki; a kalibrációs pillanatkép időbélyege a `c2.json`-ban megvan,
  a végső elemzés (H4: blokkonkénti vs. rögzített kalibráció) ezt használhatja.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 8. C3 — a harmadik megerősítő blokk (2026-11-08)

**Megerősítő adat, n = 3 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). Az alábbi számok leíró jellegűek.
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a futás a tervtől nem tért el.

### 8.1 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C3, R = 0,735; 1,5; 2,0 Å, nyers + TREX, a szintek sorrendje a protokoll szerint **TREX először** (`level_order("C3") = [1, 0]`), `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), a szerző külön jóváhagyása, az élő `usage()` kapu (192 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c3.json`](../figures/data/f11/c3.json), [`c3.log`](../figures/data/f11/c3.log) |

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 1 (TREX) | `dbo3bhgou4as73b5eo50` | 2026-11-08 08:41:43 | 08:46:09 | 08:47:16 | **24** | 19,8 |
| 0 (nyers) | `dbo3e5s4148s7391t61g` | 08:47:20 | 08:52:43 | 08:53:25 | **15** | 14,4 |

- **Összesen 39 QPU-s**, a C1-gyel és a C2-vel azonos (15 + 24); kvóta 192 → **231 / 600 s** (38,5%), a 480 s határ alatt. Három
  egymás utáni 3 geometriás blokkon a költség pontosan ugyanannyi: a „~39 s / blokk" feltevés immár három mérésre támaszkodik.
  Az ütemtervi jóslat (a C8 után 231 + 5 × 39 = **426 s, 71%**) változatlan.
- **Sorban állás:** a TREX job 4,4 percet, a nyers 5,4 percet várt; az egész blokk 08:41 → 08:53 UTC, ~12 perc alatt lefutott
  (a C2 nyers jobja 15 órát várt). Hibás vagy félbehagyott job nem keletkezett.

**Korrekció a munkamenetből:** a jóváhagyási kérdésben tévesen azt írtam, hogy a nyers szint fut előbb. A protokoll szerint a C3-on
(páratlan blokk) a TREX az első; a kód ennek megfelelően működött, a költséget és a kapukat a sorrend nem érinti.

### 8.2 Kalibráció

A blokk előtti (08:39 UTC) és utáni (08:53 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-08T08:12:30Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*; a mérés a
kalibráció után 34–41 perccel készült, vagyis a pillanatkép és a mérés közt a lehető legkisebb volt az eltérés (a C2-nél ~22 óra).
Az [1, 2] pár kalibrációja a C2-höz képest: kiolvasási hiba q1 0,88% → 0,73%, **q2 0,98% → 1,51%**; T1 q1 256 → 315 µs; a cz-hiba
0,099% → 0,098%. A modell-előrejelzés ennek megfelelően magasabb (nyers 27,6 / 14,6 / 14,9 mHa).

### 8.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | B0 | C1 | C2 |
|---|---|---|---|---|---|---|---|
| 0,735 | 33,8 | 27,6 | **+6,2** | 2,1 | +14,1 | +31,8 | +10,2 |
| 1,5 | 15,8 | 14,6 | **+1,2** | 0,5 | +3,5 | +14,9 | +3,4 |
| 2,0 | 14,0 | 14,9 | **−0,9** | −0,5 | +2,4 | +6,1 | +1,6 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | B0 | C1 | C2 |
|---|---|---|---|---|---|---|---|
| 0,735 | 3,8 | 8,6 | −4,8 | −1,6 | −2,0 | +7,4 | +4,1 |
| 1,5 | 0,4 | 3,8 | −3,4 | −1,3 | −1,1 | +5,6 | −0,6 |
| 2,0 | 0,7 | 3,2 | −2,6 | −1,4 | −1,0 | −0,5 | −3,4 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C3 | Modell C3 | Arány C3 | Arány C2 | Arány C1 | Arány B0 |
|---|---|---|---|---|---|---|
| 0,735 | 30,0 | 19,0 | 1,58 | 1,39 | 2,66 | 1,96 |
| 1,5 | 15,4 | 10,8 | 1,42 | 1,46 | 2,13 | 1,49 |
| 2,0 | 13,3 | 11,7 | 1,15 | 1,54 | 1,74 | 1,33 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés zárójelben):

| R (Å) | B0 | C1 | C2 | C3 |
|---|---|---|---|---|
| 0,735 | 40,0 (25,9) | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) |
| 1,5 | 16,9 | 26,7 | 16,0 | 15,8 |
| 2,0 | 15,9 | 18,0 | 14,3 | 14,0 |

### 8.4 Értelmezés – és ami NEM következik belőle

- **A C3-on a nyers hardver és a modell a korábbiaknál jobban egyezik:** a különbség +6,2 / +1,2 / −0,9 mHa. Az 1,5 és a 2,0 Å-nél a
  statisztikai hibán belül van (|z| ≤ 0,5), és a ±3,0 mHa sávon belül is; a 0,735 Å-nél a különbség (+6,2 mHa, z = 2,1) a sávon kívül marad.
  **Ez nem a TOST**, csak a pontbecslés leírása, a TOST a teljes sorozatra, blokk-közi szórással számol.
- **A C2 és a C3 nyers hardvereredménye közel azonos** (0,735 Å: 34,5 és 33,8; 1,5 Å: 16,0 és 15,8; 2,0 Å: 14,3 és 14,0 mHa), a **C1 kiugró**
  (54,8 / 26,7 / 18,0). A C1 kalibrációja szokatlan volt (az [1, 2] pár q1 T1 értéke 178 µs, a három blokk közül a legkisebb), de hogy
  ez okozta-e az eltérést, **nem tudjuk**; három blokkból nem állapítható meg. A modell-előrejelzés a C1-en alig tért el a többitől
  (0,735 Å: 23,0 vs. 24,3 és 27,6), vagyis a C1 kiugró hibáját **a modell nem jelezte előre**.
- **Az irány nem egyértelmű:** a nyers hibát a modell B0-n, C1-en és C2-n alulbecsülte; a C3-on 2,0 Å-nél kismértékben (−0,9 mHa)
  túlbecsülte. A korábbi, a C1/C2 alapján megfogalmazott „a modell rendszeresen alulbecsül" általánosítás **a C3-mal gyengül**; az
  alulbecslés mértéke a 0,735 Å-nél +6,2…+31,8 mHa (B0: +14,1).
- **A kiolvasási hozzájárulás aránya** a C3-on 1,15–1,58; a négy blokk (B0, C1, C2, C3) 1,15 és 2,66 között mozog. A hardver kiolvasási
  hozzájárulása mindig nagyobb a modellénél, de a C3 2,0 Å-nél már csak 15%-kal. A korábbi hipotézis (a tényleges kiolvasási
  hiba nagyobb a kalibrációsnál) tehát nem cáfolódott, de a mértéke blokkonként erősen változik; **továbbra is hipotézis**.
- **A TREX-es hardver a kiolvasás nélküli modellnél jobb** a C3-on mindhárom pontban (−4,8 / −3,4 / −2,6 mHa; |z| ≤ 1,6). Négy blokkon
  a TREX-es eltérés előjele vegyes (B0: negatív, C1: vegyes, C2: vegyes, C3: negatív), tehát nem egyirányú rendszerhiba.
- **Nem állítható:** a H1–H4 eldöntése; az ok; általánosítás más eszközre, qubitpárra vagy molekulára. A négy blokk (B0, C1, C2, C3)
  eltérő nagyságú különbséget ad, ami éppen azt indokolja, hogy a protokoll 8 megerősítő blokkot ír elő.
- **Várható irány (nem előrejelzés):** a C2 és a C3 jobban egyezik, mint a C1; ha a hátralévő blokkok a C2–C3 szintjén maradnak, a
  H1 a 0,735 Å-nél akkor is nehezen teljesül (a pontbecslés +6…+10 mHa, a ±3,0 sávon kívül). A küszöb nem módosítható.

### 8.5 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás); a TOST csak a megerősítő blokkok
  teljes sorozatán értékelhető (`scripts/analyze_heron.py`, C8 után).
- A C3 a kalibráció után 34–41 perccel futott (a C2: ~22 óra, a C1: ~25 perc a pillanatképhez képest), tehát a kalibráció-elavulás
  hatása itt a legkisebb *(helyesbítve, 22.3: ez a `last_update_date`-hez mérve igaz; a pár saját adatai szerint a C3 kalibrációja 30,4 órás volt, a
  nyolc blokkból a negyedik legidősebb, 14.2)*; a C2 és C3 közel azonos nyers hardvereredménye ezzel *összhangban van*, de ezt két pont nem bizonyítja.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 9. C4 — a negyedik megerősítő blokk és a köztes leíró összesítés (2026-11-10)

**Megerősítő adat, n = 4 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). A C4 a terv szerinti **köztes
elemzés** blokkja, ezért a 9.6 szakasz **csak leíró** összesítést ad a C1–C4-ről; **TOST-ot, konfidenciaintervallumot és döntést
szándékosan nem számoltunk** (a protokoll szerint a kiértékelés a C8 után történik, a végpont és a küszöb nem változik).
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a futás a tervtől nem tért el.

### 9.1 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C4, R = 0,735; 1,5; 2,0 Å, nyers + TREX, a szintek sorrendje a protokoll szerint **nyers először** (`level_order("C4") = [0, 1]`, a kódban ellenőrizve), `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), a szerző külön jóváhagyása, az élő `usage()` kapu (231 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c4.json`](../figures/data/f11/c4.json), [`c4.log`](../figures/data/f11/c4.log) |

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 0 (nyers) | `dbpdqb0qtr0c738e8uh0` | 2026-11-10 09:00:29 | 09:00:31 | 09:01:07 | **15** | 14,4 |
| 1 (TREX) | `dbpdqmc4148s739uf7h0` | 09:01:13 | 09:01:15 | 09:01:50 | **24** | 19,8 |

- **Összesen 39 QPU-s**, a C1–C3-mal azonos (15 + 24); kvóta 231 → **270 / 600 s** (45%), a 480 s határ alatt. Négy egymás utáni
  3 geometriás blokkon a költség pontosan ugyanannyi. Az ütemtervi jóslat (a C8 után 270 + 4 × 39 = **426 s, 71%**) változatlan.
- **Sorban állás:** egyik job sem várt (2 másodperc); az egész blokk ~1,5 perc alatt lefutott. Hibás vagy félbehagyott job nem keletkezett.

### 9.2 Kalibráció

A blokk előtti (08:58 UTC) és utáni (09:01 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-10T08:43:26Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*; a mérés a
kalibráció után 17–18 perccel készült. Az [1, 2] pár kalibrációja a C3-hoz képest: kiolvasási hiba **q1 0,73% → 0,39%** (az eddigi
legkisebb), q2 1,51% → 1,32%; T1 q1 315 → 342 µs; **cz-hiba 0,098% → 0,079%** (az eddigi legkisebb). A modell-előrejelzés ennek
megfelelően alacsonyabb (nyers 22,4 / 11,5 / 11,8 mHa).

### 9.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | B0 | C1 | C2 | C3 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 25,0 | 22,4 | **+2,7** | 0,9 | +14,1 | +31,8 | +10,2 | +6,2 |
| 1,5 | 14,1 | 11,5 | **+2,6** | 1,1 | +3,5 | +14,9 | +3,4 | +1,2 |
| 2,0 | 9,7 | 11,8 | **−2,1** | −1,3 | +2,4 | +6,1 | +1,6 | −0,9 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | B0 | C1 | C2 | C3 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 12,6 | 7,7 | +4,9 | 1,6 | −2,0 | +7,4 | +4,1 | −4,8 |
| 1,5 | 2,0 | 3,3 | −1,3 | −0,5 | −1,1 | +5,6 | −0,6 | −3,4 |
| 2,0 | 1,0 | 2,9 | −1,9 | −1,1 | −1,0 | −0,5 | −3,4 | −2,6 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C4 | Modell C4 | Arány C4 | C3 | C2 | C1 | B0 |
|---|---|---|---|---|---|---|---|
| 0,735 | 12,4 | 14,7 | **0,85** | 1,58 | 1,39 | 2,66 | 1,96 |
| 1,5 | 12,1 | 8,2 | 1,48 | 1,42 | 1,46 | 2,13 | 1,49 |
| 2,0 | 8,6 | 8,8 | **0,98** | 1,15 | 1,54 | 1,74 | 1,33 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | B0 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| 0,735 | 40,0 (25,9) | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) |
| 1,5 | 16,9 | 26,7 | 16,0 | 15,8 | 14,1 |
| 2,0 | 15,9 | 18,0 | 14,3 | 14,0 | 9,7 |

### 9.4 Értelmezés – és ami NEM következik belőle

- **A C4-en a nyers hardver és a modell eddig a legjobban egyezik:** a különbség +2,7 / +2,6 / −2,1 mHa; mindhárom pontbecslés a
  ±3,0 mHa sávon belül van, és |z| ≤ 1,3, vagyis a blokkon belüli statisztikai hibán belül is. **Ez nem a TOST**: egyetlen blokk, a
  blokk-közi szórás nélkül; a protokoll szerinti egyenértékűség a teljes sorozat átlagára és annak 90%-os konfidenciaintervallumára vonatkozik.
- **A kiolvasási hozzájárulás aránya a C4-en először esik 1 közelébe vagy alá** (0,85 / 1,48 / 0,98; korábban 1,15–2,66). Ez a
  „a hardveren a kiolvasási hiba mindig nagyobb a kalibrációsnál" korábbi észlelést **gyengíti**: a C4-en a 0,735 és a 2,0 Å-nél a
  hardver kiolvasási hozzájárulása már nem nagyobb a modellénél. A hipotézis (a tényleges kiolvasási hiba nagyobb a kalibrációsnál) **nem
  általános**; a mértéke blokkonként 0,85 és 2,66 között mozog.
- **A C4 kalibrációja a legkedvezőbb az eddigiek közül** (q1 kiolvasási hiba 0,39%, cz-hiba 0,079%), és a hardver nyers hibája is itt
  a legkisebb (25,0 / 14,1 / 9,7 mHa). Ez összhangban van azzal, hogy a hardver pillanatnyi állapota (itt: jobb kalibráció) erősen
  befolyásolja az eredményt, de **ok-okozati kapcsolatot négy blokkból nem lehet megállapítani**.
- **Nem állítható:** a H1–H4 eldöntése; az ok; általánosítás más eszközre, qubitpárra vagy molekulára; az, hogy a modell
  „egyenértékű" lenne (lásd 9.6: a blokkok közti szórás nagy, és a C1–C4 sorozat csökkenő tendenciát mutat).

### 9.5 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás).
- A mérés a kalibráció után 17–18 perccel készült (C3: 34–41 perc, C2: ~22 óra, C1: ~25 perc), ezért a kalibráció-elavulás hatása a
  C4-en is kicsi.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

### 9.6 Köztes leíró összesítés (C1–C4, a terv szerinti „köztes elemzés")

**Mi ez és mi nem:** a négy megerősítő blokk nyers hardver − modell különbségeinek egyszerű leíró statisztikája (átlag, a blokkok
közti szórás). **Nem TOST, nem konfidenciaintervallum, nem döntés**; a H1–H4 kiértékelése a C8 után, a `scripts/analyze_heron.py`-val
és a befagyasztott szabályok szerint történik. A küszöb (δ = 3,0 mHa) és a végpont nem változik; a köztes összesítés eredménye ezeket nem módosíthatja.

| R (Å) | Nyers hardver − modell (C1, C2, C3, C4) | Átlag | Szórás (blokkok közt) | TREX hardver − modell, átlag | TREX szórás |
|---|---|---|---|---|---|
| 0,735 | +31,8; +10,2; +6,2; +2,7 | **+12,7** | 13,1 | +2,9 | 5,3 |
| 1,5 | +14,9; +3,4; +1,2; +2,6 | **+5,5** | 6,3 | +0,1 | 3,9 |
| 2,0 | +6,1; +1,6; −0,9; −2,1 | **+1,2** | 3,6 | −2,1 | 1,2 |

- **A blokkok közti szórás nagy** (3,6–13,1 mHa), a küszöbhöz (3,0 mHa) képest is. Az átlagra épülő egyenértékűség-teszt ezért a szórás
  és a blokkszám (4) mellett szélesebb intervallumot adna, mint a pontbecslések alapján látszik. A szórást a **C1 kiugró értéke** hajtja
  (+31,8 / +14,9 / +6,1); a C1 elhagyásával kisebb lenne, de **kiugró érték elhagyása utólag nem megengedett** (a protokoll nem ír elő ilyet,
  és szelekciós rugalmasság lenne), ezért ezt csak információként közöljük.
- **Csökkenő tendencia a C1–C4 sorozatban:** a 0,735 Å-nél +31,8 → +10,2 → +6,2 → +2,7, a 2,0 Å-nél +6,1 → +1,6 → −0,9 → −2,1, az 1,5 Å-nél
  +14,9 → +3,4 → +1,2 → +2,6 (az utolsó lépésnél nem csökken). Négy ponton ez **nem bizonyít tendenciát**, és az ok nem ismert (jobb kalibráció,
  a hardver állapota, véletlen). Ha azonban a blokkok közt időbeli korreláció (sodródás) van, a blokkok nem függetlenek, ami a TOST feltevését
  érinti; erre a végső elemzésnél (H4: blokkonkénti vs. rögzített kalibráció) figyelni kell, de a szabályokat nem módosítjuk. *(Helyesbítés: a H4 nem
  függetlenségi teszt; a függetlenséget az elemzés nem vizsgálta, 18.12.)*
- **Amit ebből levonhatunk:** a pontbecslések a C2 óta közelednek a nullához, a C4-en mindhárom a ±3,0 mHa sávban van. **Amit nem:** hogy a H1
  teljesülne. A végső válaszhoz a C5–C8 is kell, és az, hogy a C4 szintje tartós-e, vagy egy kedvező kalibráció eseti hatása.
- **Következmény a tervre:** a protokoll, a küszöb és a blokkok száma változatlan. A kvóta 270 / 600 s (45%); a hátralévő 4 blokk ~156 s,
  a C8 után ~426 s (71%), a 480 s határ alatt.

## 10. C5 — az ötödik megerősítő blokk (2026-11-12): **az eltérés előjele megfordult**

**Megerősítő adat, n = 5 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). Az alábbi számok leíró jellegűek.
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a futás a tervtől nem tért el.

### 10.1 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C5, R = 0,735; 1,5; 2,0 Å, nyers + TREX, a szintek sorrendje a protokoll szerint **TREX először** (`level_order("C5") = [1, 0]`), `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett), a szerző külön jóváhagyása, az élő `usage()` kapu (270 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c5.json`](../figures/data/f11/c5.json), [`c5.log`](../figures/data/f11/c5.log) |

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 1 (TREX) | `dbqndvmjjaos73ahjrsg` | 2026-11-12 08:21:18 | 08:21:20 | 08:21:59 | **24** | 19,8 |
| 0 (nyers) | `dbqneanv5hds73dgchlg` | 08:22:02 | 08:22:04 | 08:25:34 | **15** | 14,4 |

- **Összesen 39 QPU-s**, a C1–C4-gyel azonos (15 + 24); kvóta 270 → **309 / 600 s** (51,5%), a 480 s határ alatt. Öt egymás utáni 3
  geometriás blokkon a költség pontosan ugyanannyi. Az ütemtervi jóslat (a C8 után 309 + 3 × 39 = **426 s, 71%**) változatlan.
- **Sorban állás:** egyik job sem várt érdemben (2 másodperc); az egész blokk ~4 perc alatt lefutott. Hibás vagy félbehagyott job nem keletkezett.

### 10.2 Kalibráció

A blokk előtti (08:18 UTC) és utáni (08:25 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-12T07:58:36Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*; a mérés a kalibráció
után 20–27 perccel készült. A szárazfutás (08:10 UTC) még a 07:45:16Z kalibrációt látta, a valódi indítás (08:18 UTC) már a 07:58:36Z-t; a
modell-előrejelzés mindkettőből azonos (33,83 / 18,03 / 18,39 mHa), vagyis a köztes frissítés az [1, 2] pár paramétereit nem érintette
(ugyanez történt a C1-nél). Az [1, 2] pár kalibrációja a C4-hez képest: **kiolvasási hiba q1 0,39% → 1,66%** (az eddigi legnagyobb; a C4 volt a legkisebb),
q2 1,32% → 1,27%; T1 q1 342 → 259 µs; **cz-hiba 0,079% → 0,103%**. A C5 kalibrációja tehát a **C1–C5 közül a legrosszabb kiolvasású** volt, ezért a
modell magasabb hibát jósol (nyers 33,8 / 18,0 / 18,4 mHa, a C4-nél 22,4 / 11,5 / 11,8).

### 10.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 25,6 | 33,8 | **−8,2** | −2,9 | +31,8 | +10,2 | +6,2 | +2,7 |
| 1,5 | 7,9 | 18,0 | **−10,1** | −4,3 | +14,9 | +3,4 | +1,2 | +2,6 |
| 2,0 | 11,9 | 18,4 | **−6,5** | −3,9 | +6,1 | +1,6 | −0,9 | −2,1 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 7,2 | 8,9 | −1,7 | −0,6 | +7,4 | +4,1 | −4,8 | +4,9 |
| 1,5 | 4,2 | 3,9 | +0,3 | 0,1 | +5,6 | −0,6 | −3,4 | −1,3 |
| 2,0 | 4,1 | 3,3 | +0,8 | 0,4 | −0,5 | −3,4 | −2,6 | −1,9 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C5 | Modell C5 | Arány C5 | C4 | C3 | C2 | C1 |
|---|---|---|---|---|---|---|---|
| 0,735 | 18,4 | 25,0 | **0,74** | 0,85 | 1,58 | 1,39 | 2,66 |
| 1,5 | 3,8 | 14,2 | **0,27** | 1,48 | 1,42 | 1,46 | 2,13 |
| 2,0 | 7,8 | 15,1 | **0,52** | 0,98 | 1,15 | 1,54 | 1,74 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|
| 0,735 | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) | 25,6 (33,8) |
| 1,5 | 26,7 | 16,0 | 15,8 | 14,1 | 7,9 |
| 2,0 | 18,0 | 14,3 | 14,0 | 9,7 | 11,9 |

### 10.4 Értelmezés – és ami NEM következik belőle

- **Az eltérés előjele megfordult:** a C1–C4-en a modell a nyers hardverhibát (túlnyomórészt) alulbecsülte, a C5-ön **mindhárom geometrián túlbecsülte**
  (−8,2 / −10,1 / −6,5 mHa; z = −2,9…−4,3). A C4 kedvező egyezése tehát **nem volt tartós**: egyetlen kedvező blokk (C4) után a következő
  ugyanakkora nagyságrendű, de ellenkező irányú eltérést ad.
- **A modell követi a kalibrációt, a hardver nem ugyanúgy:** a C5 kalibrációja a legrosszabb kiolvasású volt (q1 1,66%), ezért a modell magas hibát jósolt
  (33,8 mHa a 0,735 Å-nél), a hardver nyers hibája viszont a legkisebbek közé tartozott (25,6 / 7,9 / 11,9 mHa; az 1,5 Å-nél az eddigi minimum). A C1–C5
  blokkok között a modell-előrejelzés és a hardver nyers hibája **negatívan korrelál** (Pearson r = −0,43 / −0,70 / −0,24 a 0,735 / 1,5 / 2,0 Å-nél), tehát a
  napról napra változó modell-előrejelzés nem követi a hardver napi változását. **Ez utólagos, leíró számítás, öt ponton**: sem szignifikanciát, sem okot nem
  állít; a hardver napi ingadozásának forrása ismeretlen.
- **A „kiolvasási hiba a hardveren mindig nagyobb a modellnél" hipotézis cáfolódott mint általános állítás:** a hozzájárulás aránya a C5-ön 0,27–0,74 (a hardver
  kiolvasási hozzájárulása *kisebb* a modellénél), korábban 0,85–2,66. A hardver tényleges kiolvasási hibája tehát nem állandó többszöröse a kalibrációsnak; vagy
  a kalibrációs érték nem megbízható a mérés pillanatára, vagy mást is mér, vagy a nyers/TREX különbség nem csak a kiolvasást tükrözi. **Az ok nem ismert.**
- **A TREX-es hardver a kiolvasás nélküli modellel jól egyezik** a C5-ön (+0,3 és +0,8 mHa az 1,5 és a 2,0 Å-nél; |z| ≤ 0,6 mindhárom pontban), vagyis a *kiolvasás
  nélkül* modellezett zaj a hibaenyhített hardvert leírja, a kiolvasást modellező rész az, ahol a modell napról napra eltér.
- **A C1–C4-ből a köztes összesítésben (9.6) megfigyelt „csökkenő tendencia" a C5-tel megszakadt:** a különbség nem tart 0 felé, hanem negatívba vált. Az akkori
  megfogalmazás (négy ponton nem bizonyít tendenciát) így utólag is helytálló volt.
- **Nem állítható:** a H1–H4 eldöntése; az ok; hogy a modell a hardvernél „többet" vagy „kevesebbet" jósol (az előjel blokkonként változik); általánosítás más eszközre,
  qubitpárra vagy molekulára.

### 10.5 Leíró összesítés C1–C5 (nem TOST, nem döntés)

| R (Å) | Nyers hardver − modell (C1…C5) | Átlag | Szórás (blokkok közt) | TREX hardver − modell, átlag | TREX szórás |
|---|---|---|---|---|---|
| 0,735 | +31,8; +10,2; +6,2; +2,7; −8,2 | **+8,5** | 14,7 | +2,0 | 5,0 |
| 1,5 | +14,9; +3,4; +1,2; +2,6; −10,1 | **+2,4** | 8,9 | +0,1 | 3,4 |
| 2,0 | +6,1; +1,6; −0,9; −2,1; −6,5 | **−0,3** | 4,6 | −1,5 | 1,7 |

- Az átlag a 2,0 Å-nél a nullához közel esik, de ezt **az ellentétes előjelű eltérések kioltása** okozza, nem az egyedi egyezés; a blokkok közti szórás (4,6–14,7 mHa)
  többszöröse a küszöbnek (3,0 mHa). Az átlagra épülő egyenértékűség-teszt a szórás és az 5 blokk mellett széles intervallumot ad; a H1 teljesülése így
  **valószínűtlen**, de ezt a C8 utáni, előre rögzített teszt dönti el, nem ez a leíró összesítés. A küszöb nem módosítható.
- A blokkok **függetlenségét** a negatív előjelváltás nem támasztja alá és nem is cáfolja; a H4 (blokkonkénti vs. rögzített kalibráció) elemzése a végső kiértékelésben történik. *(Helyesbítés: a H4 nem függetlenségi teszt, 18.12.)*

### 10.6 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás).
- A korrelációs számítás **nem része** az előre rögzített elemzésnek; utólagos, feltáró jellegű, és a végleges TR-F11-ben is így jelöljük.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 11. C6 — a hatodik megerősítő blokk (2026-11-14 → 2026-11-16): az előjel újra pozitív; a megszakadt első kísérlet

**Megerősítő adat, n = 6 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). Az alábbi számok leíró jellegűek.
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a mérés a tervtől nem tért el.

### 11.1 A megszakadt első kísérlet (nem adat; átláthatóan rögzítve)

| Elem | Érték |
|---|---|
| Mi történt | 2026-11-14-én a szerző jóváhagyta a C6-ot (friss szárazfutás, kapu rendben), a nyers szint jobja (`dbsa6j0k09pc73avu44g`, 2026-11-14 18:07 UTC) a sorban maradt (**QUEUED, legfeljebb ~21 óra**, a gépen 246–267 várakozó job). Közben a **helyi Docker-környezet leállt** (a futtató folyamat 137-es kóddal, külsőleg kilőve fejeződött be), a második (TREX) jobot a futtató még nem küldte be |
| Következmény | **Nem keletkezett mérési adat, nem fogyott kvóta** (309 / 600 s változatlan) |
| Intézkedés | A szerző döntése (a séma és a kísérlet egységessége az ütemtervnél fontosabb): a sorban álló jobot **lemondtam (CANCELLED)**, részleges blokkot vagy a protokolltól eltérő „befejező" szkriptet nem használtunk; a blokkot az **egész protokoll szerint újraindítottuk** (friss `--dry-run`, új külön jóváhagyás 2026-11-15-én) |
| Napló | [`c6_megszakadt_1.log`](../figures/data/f11/c6_megszakadt_1.log) (a beküldés előtti állapotig tart) |
| Az újrakezdés oka | **kizárólag technikai** (a futtató leállása), az eredménytől nem függött: eredmény nem is létezett. A modell-előrejelzés a két kísérletben azonos (23,53 / 12,12 / 12,30 mHa) |

### 11.2 Mi futott le, és mibe került

| Elem | Érték |
|---|---|
| Blokk, geometriák | C6, R = 0,735; 1,5; 2,0 Å, nyers + TREX, a szintek sorrendje a protokoll szerint **nyers először** (`level_order("C6") = [0, 1]`), `ibm_kingston`, qubitpár **[1, 2]**, 8192 lövés |
| Előzetes lépések | friss `--dry-run` (0 QPU-s, a kapu elengedett, 2026-11-15 15:10 UTC), a szerző külön jóváhagyása, az élő `usage()` kapu (309 s + 42,7 s ≤ 480 s) |
| Kimenet | [`c6.json`](../figures/data/f11/c6.json), [`c6.log`](../figures/data/f11/c6.log) |

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s | Becslés |
|---|---|---|---|---|---|---|
| 0 (nyers) | `dbssobvq0h0s73bk2vng` | 2026-11-15 15:13:51 | 2026-11-16 09:23:49 | 09:27:31 | **15** | 24,5 (job-becslés) |
| 1 (TREX) | `dbtcp27q0h0s73bkk020` | 2026-11-16 09:27:36 | 09:29:27 | 09:30:06 | **24** | 29,9 (job-becslés) |

- **Összesen 39 QPU-s**, a C1–C5-tel azonos (15 + 24); kvóta 309 → **348 / 600 s** (58%), a 480 s határ alatt. Hat egymás utáni 3 geometriás blokkon a költség
  pontosan ugyanannyi. Az ütemtervi jóslat (a C8 után 348 + 2 × 39 = **426 s, 71%**) változatlan.
- **Sorban állás: ~18 óra 10 perc** a nyers jobnál (beküldés 15:13 → futás 09:23), a TREX job ~2 percet várt. A korábbi blokkoknál a várakozás másodpercekben mérhető volt;
  a sor hosszú volt (a gépen 246 → 317 várakozó job, majd 124-re csökkent). A sorban állás **nem fogyaszt kvótát**; a tényleges mérés (az első job indulásától a második végéig)
  ~6 perc alatt zajlott le, a beküldés és a mérés között viszont ~18 óra telt el.
- Hibás vagy félbehagyott job a **valódi** futásban nem keletkezett.

### 11.3 Kalibráció

A blokk előtti (2026-11-15 15:11 UTC) és utáni (2026-11-16 09:30 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-13T14:57:10Z** *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*; vagyis az IBM által közölt
legutóbbi kalibráció a mérés idején ~66 órás volt (a C5-nél a mérés a kalibráció után 20–27 perccel készült). *(Javítva 2026-11-22-én: a `last_update_date` a pár frissességét nem mutatja. A 2026-11-19-én rögzített definíció szerint — az [1, 2] pár T1/T2/kiolvasás/cz paramétereinek legrégebbi mérési időpontja, itt a q1 T1, 2026-11-12 19:33:48 UTC — a C6 kalibráció-életkora az első job indulásakor (2026-11-16 09:23:49 UTC) **~85,8 óra** volt; lásd 12.2.)* A szárazfutás ugyanezt a kalibrációt látta, a
modell-előrejelzés mindkét időpontban azonos. Hogy a közölt kalibráció valóban ennyire régi volt, vagy a közlés késett, **nem ismert**. Az [1, 2] pár kalibrációja a C5-höz képest:
**kiolvasási hiba q1 1,66% → 0,44%**, q2 1,27% → 1,32%; T1 q1 259 → 341 µs; cz-hiba 0,103% → 0,097%; vagyis a C4-hez hasonló (kiolvasás q1 0,39%).
A modell nyers előrejelzése: 23,5 / 12,1 / 12,3 mHa (C5-nél 33,8 / 18,0 / 18,4).

### 11.4 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 29,9 | 23,5 | **+6,4** | +2,1 | +31,8 | +10,2 | +6,2 | +2,7 | −8,2 |
| 1,5 | 19,1 | 12,1 | **+7,0** | +2,9 | +14,9 | +3,4 | +1,2 | +2,6 | −10,1 |
| 2,0 | 13,8 | 12,3 | **+1,5** | +0,9 | +6,1 | +1,6 | −0,9 | −2,1 | −6,5 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 6,9 | 8,5 | −1,6 | −0,5 | +7,4 | +4,1 | −4,8 | +4,9 | −1,7 |
| 1,5 | 8,1 | 3,8 | +4,3 | +1,7 | +5,6 | −0,6 | −3,4 | −1,3 | +0,3 |
| 2,0 | 3,8 | 3,2 | +0,6 | +0,3 | −0,5 | −3,4 | −2,6 | −1,9 | +0,8 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C6 | Modell C6 | Arány C6 | C5 | C4 | C3 | C2 | C1 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 23,0 | 15,0 | **1,53** | 0,74 | 0,85 | 1,58 | 1,39 | 2,66 |
| 1,5 | 11,1 | 8,4 | **1,32** | 0,27 | 1,48 | 1,42 | 1,46 | 2,13 |
| 2,0 | 10,0 | 9,1 | **1,11** | 0,52 | 0,98 | 1,15 | 1,54 | 1,74 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | C1 | C2 | C3 | C4 | C5 | C6 |
|---|---|---|---|---|---|---|
| 0,735 | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) | 25,6 (33,8) | 29,9 (23,5) |
| 1,5 | 26,7 | 16,0 | 15,8 | 14,1 | 7,9 | 19,1 |
| 2,0 | 18,0 | 14,3 | 14,0 | 9,7 | 11,9 | 13,8 |

### 11.5 Értelmezés – és ami NEM következik belőle

- **Az eltérés előjele a C6-on újra pozitív** (a modell a nyers hardverhibát alulbecsüli: +6,4 / +7,0 / +1,5 mHa), a C5 negatív előjele után. Az előjel tehát blokkonként változik
  (C1–C4 +, C5 −, C6 +); két-három egymást követő blokkból nem olvasható ki állandó irány. A z-értékek (+2,1 / +2,9 / +0,9) a blokkon belüli statisztikai hibához mérten
  a 0,735 és az 1,5 Å-nél 2 fölöttiek, a 2,0 Å-nél nem.
- **A hardver nyers hibája a C6-on a C5-nél nagyobb (29,9 / 19,1 / 13,8 mHa), a modellé a C5-nél kisebb** (a kiolvasási hiba q1-en 1,66% → 0,44%), vagyis ezúttal a modell az
  alacsonyabb kiolvasási hiba irányában mozdult, a hardver pedig a magasabb hiba irányában: **a negatív korreláció megmaradt** (C1–C6, Pearson r = −0,36 / −0,72 / −0,24 a 0,735 / 1,5 / 2,0 Å-nél).
  **Ez utólagos, leíró számítás hat ponton**: sem szignifikanciát, sem okot nem állít; a hardver napi ingadozásának forrása ismeretlen. A C6 kalibrációja a mérés idején
  ~66 órás volt *(a pár saját adatai szerint ~85,8 órás, lásd 12.2)*, ami a modell és a hardver eltérésének egyik lehetséges, de nem igazolt oka.
- **A kiolvasási hozzájárulás aránya a C6-on 1,11–1,53** (a C5-ön 0,27–0,74, a C1–C4-en 0,85–2,66): a hardver kiolvasási hozzájárulása ismét nagyobb a modellénél, de az arány hat blokkon át
  0,27 és 2,66 között ingadozik, így sem a „mindig nagyobb", sem a „mindig kisebb" nem állítható.
- **A TREX-es hardver a kiolvasás nélküli modellel** a C6-on két pontban egyezik (−1,6 és +0,6 mHa, |z| ≤ 0,5), az 1,5 Å-nél a hardver nagyobb (+4,3 mHa, z = +1,7).
- **Nem állítható:** a H1–H4 eldöntése; az ok; hogy a modell a hardvernél „többet" vagy „kevesebbet" jósol; általánosítás más eszközre, qubitpárra vagy molekulára.

### 11.6 Leíró összesítés C1–C6 (nem TOST, nem döntés)

| R (Å) | Nyers hardver − modell (C1…C6) | Átlag | Szórás (blokkok közt) | TREX hardver − modell, átlag | TREX szórás |
|---|---|---|---|---|---|
| 0,735 | +31,8; +10,2; +6,2; +2,7; −8,2; +6,4 | **+8,2** | 13,2 | +1,4 | 4,7 |
| 1,5 | +14,9; +3,4; +1,2; +2,6; −10,1; +7,0 | **+3,2** | 8,2 | +0,8 | 3,5 |
| 2,0 | +6,1; +1,6; −0,9; −2,1; −6,5; +1,5 | **−0,0** | 4,2 | −1,2 | 1,7 |

- A blokkok közti szórás (4,2–13,2 mHa) a küszöb (3,0 mHa) többszöröse; az átlag a 2,0 Å-nél a nullához közel esik, de ezt az ellentétes előjelű eltérések kioltása okozza. A H1 teljesülése
  **valószínűtlen**, de ezt a C8 utáni, előre rögzített teszt dönti el, nem ez a leíró összesítés. A küszöb nem módosítható.

### 11.7 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás). A korrelációs és az összesítő számítás nem része az előre rögzített elemzésnek.
- Ütemterv: a C6 a 2026-11-16-i mérés után a C7 2026-11-18-ra, a C8 2026-11-20-ra esik (2 napos távolság); az ütemterv a sorban állás miatt tolódott, a blokkok közti 2 napos távolság megmaradt.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 12. C7 — a hetedik megerősítő blokk (2026-11-22): várakozás a kalibrációra, a nyers eltérés kicsi, a TREX-oldal negatív

**Megerősítő adat, n = 7 blokk:** a H1–H4 és a TOST még nem értékelhető (a terv 8 blokkra készült). Az alábbi számok leíró jellegűek.
A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a mérés a tervtől nem tért el.

### 12.1 A várakozás (2026-11-18 → 2026-11-22)

| Dátum (UTC) | Megfigyelés (csak olvasás) | Döntés |
|---|---|---|
| 11-18 07:20 | `ibm_kingston` `last_update_date` 2026-11-13 14:57 (~5 napos); az `ibm_marrakesh` aznap frissült | a C7 friss szárazfutása rendben volt, de a szerző **nem hagyta jóvá**; kalibrációs-frissességi szabály rögzítve (`phase_11.md`), határidő 11-22 |
| 11-18 | — | a C9 kiegészítő blokk rögzítve (`phase_11.md`; az elsődleges elemzés a C1–C8-on marad) |
| 11-19 09:58 | a `last_update_date` 2026-11-19 00:06-ra frissült, de az [1, 2] pár adatai **2026-11-12-iek** (a modell-előrejelzés a C6-éval azonos) | a **kalibráció-életkor definíciója** rögzítve (a pár T1/T2/kiolvasás/cz legrégebbi mérési időpontja); a C7 vár |
| 11-19 18:01, 11-20 05:42, 11-21 09:32 | a Kingston **mind a 156 qubitjének** kiolvasási adata 2026-11-12-i; az `ibm_fez` és az `ibm_marrakesh` minden nap friss adatot kapott | várakozás; a szerző az IBM támogatásának jelezte (válasz a dokumentáció lezárásáig nem érkezett az MI által látható postafiókba) |
| 11-22 14:15 | a Kingston újrakalibrálva (`last_update_date` 14:01:47; mind a 156 qubit kiolvasása 11-22-i); a pár adatai 11-21 01:03 … 11-22 13:56 közöttiek | a feltétel teljesült: friss szárazfutás, a szerző külön jóváhagyása, futás |

A várakozás alatt **hardverfutás nem volt, kvóta nem fogyott**. Az, hogy az IBM a Kingston qubitjeit 10 napig nem mérte újra (vagy csak nem közölte), **kívülről nem
ismert okú**.

### 12.2 Kalibráció és kalibráció-életkor

| Paraméter (az [1, 2] pár) | C6 (a mérés idején) | C7 | Mérési időpont (C7) |
|---|---|---|---|
| kiolvasási hiba q1 / q2 | 0,44% / 1,32% | **1,04% / 1,06%** | 2026-11-22 13:56:18 |
| T1 q1 / q2 | 341 / 308 µs | **199** / 288 µs | 11-21 01:03:46 / 11-21 22:42:07 |
| T2 q1 / q2 | 598 / 122 µs | **22** / 127 µs | 11-21 22:42:12 / 22:42:14 |
| cz-hiba [1, 2] | 0,097% | 0,082% | 11-21 23:38:08 |
| sx/x hiba q1 / q2 (nem része az életkornak) | 0,023% / 0,027% | 0,015% / 0,014% | 11-21 23:14 |

- **Kalibráció-életkor** (a 2026-11-19-i definíció): C7 = az első job indulása (2026-11-22 14:22:15 UTC) − a legrégebbi paraméter (q1 T1, 2026-11-21 01:03:46) = **~37,3 óra**
  (a 48 órás érzékenységi határon belül); a kiolvasást 26 perccel a mérés előtt mérték. A C6-é ugyanígy számolva **~85,8 óra** (a 11.3 pont javítva). A C1–C5 életkorát
  a végső dokumentációban az IBM történeti adataiból rekonstruáljuk.
- **A q1 T2 598 → 22 µs-ra esett** (a pár többi paramétere kisebb mértékben változott). A modell emiatt nagyobb dekoherenciát és nagyobb hibát jósol
  (kiolvasással 32,5 / 16,3 / 16,1 mHa; kiolvasás nélkül 15,0 / 6,4 / 5,6 mHa — a C6-nál 23,5 / 12,1 / 12,3, illetve 8,5 / 3,8 / 3,2). A protokoll szerint a
  paraméterek értéke alapján a futás időpontját nem választhattuk meg; a C7 a szabály szerinti első lehetséges napon futott.

### 12.3 Mi futott le, és mibe került

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s |
|---|---|---|---|---|---|
| 1 (TREX) | `dc1fl5anj2vs73df9ja0` | 2026-11-22 14:22:13 | 14:22:15 | 14:22:58 | **24** |
| 0 (nyers) | `dc1flheq4uuc73a3s8c0` | 14:23:01 | 14:23:03 | 14:23:22 | **15** |

- A szintek sorrendje a protokoll szerint **TREX először** (`level_order("C7") = [1, 0]`); `ibm_kingston`, qubitpár [1, 2], 8192 lövés. Kimenet: [`c7.json`](../figures/data/f11/c7.json),
  [`c7.log`](../figures/data/f11/c7.log).
- **Összesen 39 QPU-s** (hetedszer ugyanannyi); kvóta 348 → **387 / 600 s** (64,5%). Sorban állás 2 s; a blokk ~1 perc alatt lefutott. A blokk utáni pillanatkép azonos a blokk előttivel *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*.
- Ütemterv: C8 a 2 napos távolság szerint **2026-11-24** (nyers először), utána a kiegészítő C9 (TREX először); 426 s, majd 465 s (77,5%).

### 12.4 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | C1 | C2 | C3 | C4 | C5 | C6 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 35,4 | 32,5 | **+3,0** | +1,0 | +31,8 | +10,2 | +6,2 | +2,7 | −8,2 | +6,4 |
| 1,5 | 15,9 | 16,3 | **−0,3** | −0,1 | +14,9 | +3,4 | +1,2 | +2,6 | −10,1 | +7,0 |
| 2,0 | 15,3 | 16,1 | **−0,8** | −0,5 | +6,1 | +1,6 | −0,9 | −2,1 | −6,5 | +1,5 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | C1 | C2 | C3 | C4 | C5 | C6 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 11,1 | 15,0 | **−3,9** | −1,3 | +7,4 | +4,1 | −4,8 | +4,9 | −1,7 | −1,6 |
| 1,5 | 2,6 | 6,4 | **−3,8** | −1,5 | +5,6 | −0,6 | −3,4 | −1,3 | +0,3 | +4,3 |
| 2,0 | 0,4 | 5,6 | **−5,2** | −2,9 | −0,5 | −3,4 | −2,6 | −1,9 | +0,8 | +0,6 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C7 | Modell C7 | Arány C7 | C6 | C5 | C4 | C3 | C2 | C1 |
|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 24,3 | 17,5 | **1,39** | 1,53 | 0,74 | 0,85 | 1,58 | 1,39 | 2,66 |
| 1,5 | 13,3 | 9,8 | **1,36** | 1,32 | 0,27 | 1,48 | 1,42 | 1,46 | 2,13 |
| 2,0 | 15,0 | 10,6 | **1,41** | 1,11 | 0,52 | 0,98 | 1,15 | 1,54 | 1,74 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| 0,735 | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) | 25,6 (33,8) | 29,9 (23,5) | 35,4 (32,5) |
| 1,5 | 26,7 | 16,0 | 15,8 | 14,1 | 7,9 | 19,1 | 15,9 |
| 2,0 | 18,0 | 14,3 | 14,0 | 9,7 | 11,9 | 13,8 | 15,3 |

### 12.5 Értelmezés – és ami NEM következik belőle

- **A nyers eltérés a C7-en kicsi** (+3,0 / −0,3 / −0,8 mHa; |z| ≤ 1,0), a hét blokk közül az 1,5 és a 2,0 Å-nél a legkisebb abszolút értékű. **Ez egyetlen blokk**, és a
  C4 tapasztalata szerint (kedvező egyezés, utána előjelváltás) nem jelez tartós egyezést.
- **A kis nyers eltérés két ellentétes irányú eltérés összegéből adódik:** a TREX-oldalon a kiolvasás nélküli modell **túlbecsüli** a hibaenyhített hardver hibáját
  (−3,9 / −3,8 / −5,2 mHa; a 2,0 Å-nél z = −2,9), a kiolvasási hozzájárulást viszont **alulbecsüli** (arány 1,36–1,41). Egy lehetséges, **nem igazolt** magyarázat, hogy
  a modell a q1 T2 = 22 µs értéket használja, és ha a hardver a mérés idején valójában kisebb dekoherenciát mutatott, a modell a dekoherencia-részt túlbecsüli. Ezt az adat
  nem dönti el.
- **A negatív korreláció gyengült, de megmaradt** (C1–C7, Pearson r = −0,28 / −0,67 / −0,13); utólagos, leíró számítás hét ponton, okot nem állít.
- **Nem állítható:** a H1–H4 eldöntése; az ok; hogy a modell a hardvert most „eltalálta"; általánosítás más eszközre, qubitpárra vagy molekulára.

### 12.6 Leíró összesítés C1–C7 (nem TOST, nem döntés)

| R (Å) | Nyers hardver − modell (C1…C7) | Átlag | Szórás (blokkok közt) | TREX hardver − modell, átlag | TREX szórás |
|---|---|---|---|---|---|
| 0,735 | +31,8; +10,2; +6,2; +2,7; −8,2; +6,4; +3,0 | **+7,4** | 12,2 | +0,6 | 4,7 |
| 1,5 | +14,9; +3,4; +1,2; +2,6; −10,1; +7,0; −0,3 | **+2,7** | 7,6 | +0,2 | 3,6 |
| 2,0 | +6,1; +1,6; −0,9; −2,1; −6,5; +1,5; −0,8 | **−0,1** | 3,9 | −1,7 | 2,2 |

- A blokkok közti szórás (3,9–12,2 mHa) továbbra is a küszöb (3,0 mHa) többszöröse; a H1 teljesülése **valószínűtlen**, de ezt a C8 utáni, előre rögzített teszt dönti el, nem
  ez a leíró összesítés. A küszöb nem módosítható.

### 12.7 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás). A korrelációs és az összesítő számítás nem része az előre rögzített elemzésnek.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 13. C8 — a nyolcadik, utolsó megerősítő blokk (2026-11-24): a megerősítő mérés teljes

**Megerősítő adat, n = 8 blokk — a terv szerinti teljes megerősítő adatsor.** Az előre rögzített elsődleges elemzés (`scripts/analyze_heron.py`, H1–H4, TOST)
**ebben a szakaszban nem fut**; az alábbi számok leíró jellegűek. A protokoll-ujjlenyomat egyezik a `FROZEN` fájllal (`63521603…e93c9`); a mérés a tervtől nem tért el.

### 13.1 Feltételek és kalibráció

Előzetes ellenőrzés (2026-11-24 09:28 UTC, csak olvasás): `ibm_kingston` aktív, 0 várakozó job, `last_update_date` 09:11:14; a pár **minden** életkor-paraméterét a C7
(2026-11-22 14:22) **után** mérték újra, így a kalibrációs-frissességi szabály teljesült. Utána friss szárazfutás, majd a szerző külön jóváhagyása.

| Paraméter (az [1, 2] pár) | C7 | C8 | Mérési időpont (C8, UTC) |
|---|---|---|---|
| kiolvasási hiba q1 / q2 | 1,04% / 1,06% | **0,72% / 1,29%** | 2026-11-24 08:52:43 |
| T1 q1 / q2 | 199 / 288 µs | 233 / 299 µs | 2026-11-23 22:52:01 |
| T2 q1 / q2 | 22 / 127 µs | **301** / 122 µs | 11-23 22:52:07 / 22:52:09 |
| cz-hiba [1, 2] | 0,082% | 0,101% | 11-23 23:47:35 |
| sx/x hiba q1 / q2 (nem része az életkornak) | 0,015% / 0,014% | 0,018% / 0,015% | — |

- **Kalibráció-életkor** (a 2026-11-19-i definíció): C8 = az első job indulása (2026-11-24 09:36:01 UTC) − a legrégebbi paraméter (q1 T1, 2026-11-23 22:52:01) =
  **~10,7 óra**; a kiolvasást ~43 perccel a mérés előtt mérték. (A pár dátumait 09:28-kor olvastuk; a blokk előtti pillanatkép `last_update_date`-je 09:11:14; a blokk utáni a gyorsítótárból származott, 22.1.)
  Az eddigi életkorok: C6 ~85,8 h, C7 ~37,3 h, C8 ~10,7 h; a C1–C5-öt a végső dokumentációban rekonstruáljuk.
- **A q1 T2 a C7-es 22 µs-ról 301 µs-ra állt vissza.** A modell-előrejelzés ennek megfelelően kisebb: kiolvasással 24,4 / 12,8 / 13,1 mHa, kiolvasás nélkül
  7,5 / 3,3 / 2,8 mHa (a C7-nél 32,5 / 16,3 / 16,1, illetve 15,0 / 6,4 / 5,6).

### 13.2 Mi futott le, és mibe került

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s |
|---|---|---|---|---|---|
| 0 (nyers) | `dc2lkvuq4uuc73a5hbbg` | 2026-11-24 09:35:59 | 09:36:01 | 09:36:23 | **15** |
| 1 (TREX) | `dc2ll6inj2vs73dgu8h0` | 09:36:26 | 09:36:28 | 09:37:08 | **24** ¹ |

- A szintek sorrendje a protokoll szerint **nyers először** (`level_order("C8") = [0, 1]`); `ibm_kingston`, qubitpár [1, 2], 8192 lövés. Kimenet:
  [`c8.json`](../figures/data/f11/c8.json), [`c8.log`](../figures/data/f11/c8.log).
- **Összesen 39 QPU-s** (nyolcadszor ugyanannyi); kvóta 387 → **426 / 600 s** (71%). Sorban állás ~2 s; a blokk ~1 perc alatt lefutott. A blokk utáni
  pillanatkép azonos a blokk előttivel *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*.
- ¹ **Rögzítési eltérés (az eredményt nem érinti):** a `c8.json` és a `c8.log` a TREX jobnál `quantum_seconds = 0`-t rögzített: a futtató a job metrikáit közvetlenül
  a befejezés után olvasta ki, amikor az IBM a használati adatot még nem véglegesítette. Utólagos, csak olvasó lekérdezés (2026-11-24, `job.usage()` és `job.metrics()`,
  `status: complete`): **24 s**; a kvóta-különbség (387 → 426 s = 39 s) ezt megerősíti. A nyers kimeneti fájlokat utólag **nem módosítottuk**; az elemzés ezt a mezőt
  nem használja. A futtatót a C9 előtti, hardver nélküli bővítéssel együtt (tesztekkel) javítjuk; a `PROTOCOL`-t és az ujjlenyomatot ez nem érinti.

### 13.3 Eredmény (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

**Nyers hardver ↔ kiolvasást modellező Heron-modell:**

| R (Å) | Hardver (nyers) | Modell (kiolvasással) | Különbség | z | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 32,2 | 24,4 | **+7,8** | +2,7 | +31,8 | +10,2 | +6,2 | +2,7 | −8,2 | +6,4 | +3,0 |
| 1,5 | 16,2 | 12,8 | **+3,4** | +1,4 | +14,9 | +3,4 | +1,2 | +2,6 | −10,1 | +7,0 | −0,3 |
| 2,0 | 12,8 | 13,1 | **−0,3** | −0,2 | +6,1 | +1,6 | −0,9 | −2,1 | −6,5 | +1,5 | −0,8 |

**TREX hardver ↔ kiolvasás nélküli modell:**

| R (Å) | Hardver (TREX) | Modell (kiolvasás nélkül) | Különbség | z | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 9,0 | 7,5 | **+1,6** | +0,5 | +7,4 | +4,1 | −4,8 | +4,9 | −1,7 | −1,6 | −3,9 |
| 1,5 | 8,3 | 3,3 | **+5,0** | +2,0 | +5,6 | −0,6 | −3,4 | −1,3 | +0,3 | +4,3 | −3,8 |
| 2,0 | 4,5 | 2,8 | **+1,7** | +0,9 | −0,5 | −3,4 | −2,6 | −1,9 | +0,8 | +0,6 | −5,2 |

**A kiolvasási hiba hozzájárulása** (nyers − TREX a hardveren, ill. kiolvasásos − kiolvasás nélküli a modellben):

| R (Å) | Hardver C8 | Modell C8 | Arány C8 | C7 | C6 | C5 | C4 | C3 | C2 | C1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 23,2 | 16,9 | **1,37** | 1,39 | 1,53 | 0,74 | 0,85 | 1,58 | 1,39 | 2,66 |
| 1,5 | 7,9 | 9,6 | **0,82** | 1,36 | 1,32 | 0,27 | 1,48 | 1,42 | 1,46 | 2,13 |
| 2,0 | 8,4 | 10,3 | **0,81** | 1,41 | 1,11 | 0,52 | 0,98 | 1,15 | 1,54 | 1,74 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---|---|---|---|---|---|---|---|
| 0,735 | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) | 25,6 (33,8) | 29,9 (23,5) | 35,4 (32,5) | 32,2 (24,4) |
| 1,5 | 26,7 | 16,0 | 15,8 | 14,1 | 7,9 | 19,1 | 15,9 | 16,2 |
| 2,0 | 18,0 | 14,3 | 14,0 | 9,7 | 11,9 | 13,8 | 15,3 | 12,8 |

### 13.4 Értelmezés – és ami NEM következik belőle

- **A nyers eltérés** +7,8 / +3,4 / −0,3 mHa: a 0,735 Å-nél a hardver hibája a modellénél nagyobb (z = +2,7), a 2,0 Å-nél egyezik. Az előjel a C1–C4 és a C6
  mintájához hasonló.
- **A TREX-oldal a C7-hez képest megfordult:** a kiolvasás nélküli modell most **alulbecsüli** a hibaenyhített hardver hibáját (+1,6 / +5,0 / +1,7 mHa; az 1,5 Å-nél
  z = +2,0), a C7-en túlbecsülte. A kiolvasási hozzájárulás aránya a 0,735 Å-nél 1,37 (a C7-hez hasonló), az 1,5 és a 2,0 Å-nél 0,82 / 0,81 (itt a modell a
  kiolvasási részt túlbecsüli).
- **A q1 T2 visszaállása a modellt mozgatta, a hardvert alig:** a 0,735 Å-nél a modell-előrejelzés 32,5 → 24,4 mHa-ra csökkent, a hardver nyers hibája
  35,4 → 32,2 mHa. Leíró megfigyelés a C2–C8-on: a hardver nyers hibája a 0,735 Å-nél 25–35 mHa, a modell-előrejelzés 22–34 mHa között mozog, de a blokkonkénti
  változásuk nem követi egymást (Pearson r, C1–C8: −0,26 / −0,66 / −0,10; utólagos, leíró számítás nyolc ponton, okot nem állít). Egy lehetséges, **nem igazolt**
  értelmezés, hogy a közölt kalibrációs paraméterek (különösen a T2) nem mindig a mérés idején érvényes állapotot írják le, vagy a modell egyes paraméterekre érzékenyebb,
  mint a hardver; lásd 13.6.
- **Nem állítható:** a H1–H4 eldöntése (az előre rögzített elemzés még nem futott); az ok; általánosítás más eszközre, qubitpárra vagy molekulára.

### 13.5 Leíró összesítés C1–C8 (nem TOST, nem döntés)

| R (Å) | Nyers hardver − modell (C1…C8) | Átlag | Szórás (blokkok közt) | TREX hardver − modell, átlag | TREX szórás |
|---|---|---|---|---|---|
| 0,735 | +31,8; +10,2; +6,2; +2,7; −8,2; +6,4; +3,0; +7,8 | **+7,5** | 11,3 | +0,8 | 4,4 |
| 1,5 | +14,9; +3,4; +1,2; +2,6; −10,1; +7,0; −0,3; +3,4 | **+2,8** | 7,0 | +0,8 | 3,8 |
| 2,0 | +6,1; +1,6; −0,9; −2,1; −6,5; +1,5; −0,8; −0,3 | **−0,2** | 3,6 | −1,3 | 2,4 |

- A blokkok közti szórás (3,6–11,3 mHa) mindhárom kötéshossznál a küszöb (δ = 3,0 mHa) fölött van; a H1 teljesülése **valószínűtlen**, de ezt az előre rögzített
  elsődleges elemzés dönti el, nem ez a leíró összesítés. A küszöb nem módosítható.

### 13.6 Az IBM támogatás válasza (2026-11-23)

- A szerző a 12.1-ben leírt kalibrációs szünetet jelezte az IBM támogatásának. A szerző tájékoztatása szerint a válasz (2026-11-23) a részletekért az IBM Quantum
  dokumentáció *Refresh backend properties with real-time benchmarking* oktatóanyagára hivatkozott:
  <https://quantum.cloud.ibm.com/docs/en/tutorials/refresh-backend-properties-with-real-time-benchmarking>. A válasz szövegét az MI nem látta; a 10 napos szünet
  konkrét okáról ez a jegyzőkönyv nem tartalmaz információt.
- Az oktatóanyag szerint a közölt tulajdonságok olyan kalibrációs eljárásokból származnak, amelyek „typically run about once a day”, és a qubitek ennél rövidebb idő
  alatt is elmászhatnak (pl. átmeneti TLS-hibák miatt). Javaslata: közvetlenül a futtatás előtt saját karakterizálás (kiolvasás, 1q és rétegzett 2q randomizált
  benchmarking, T1, T2; `qiskit-device-benchmarking`), és a friss értékekkel a qubitválasztás. A teljes csomag egy 156 qubites Heronon ~70 QPU-s; Qiskit ≥ 2.0 kell.
  Az oktatóanyag maga is jelzi, hogy a saját mérés és a közölt érték **módszertani okból** is eltérhet (pl. T2 medián 75 µs a közölt 300 µs-mal szemben).
- **A Fázis 11-ben nem alkalmazzuk:** a protokoll befagyasztott (a modell a *közölt* kalibrációból épül, éppen ezt validáljuk); a befagyasztott környezet
  (`vqebd:1.0.0`, Qiskit 1.4.6) nem teljesíti a követelményt; és a 80%-os kvótaszabály mellett erre nincs keret. **Korlátként és jövőbeli irányként** rögzítjük: egy
  későbbi fázisban összevethető a közölt és a saját, futás előtti karakterizálásból épített modell.

### 13.7 Teendők a megerősítő mérés után

1. A C9 előtti, hardver nélküli bővítés tesztekkel: a futtató `BLOCK_RE`/`block_kind` (C9 = `supplementary`), a `quantum_seconds` rögzítésének javítása (13.2 ¹), az
   elemző szkript (elsődleges teszt csak a `confirmatory` blokkokon; az előre rögzített érzékenységi vizsgálatok: C1–C9, illetve ≤ 48 órás kalibráció), és a C1–C5
   kalibráció-életkorának rekonstrukciója.
2. Az előre rögzített elsődleges elemzés (`scripts/analyze_heron.py`) a C1–C8-on, majd a végleges TR-F11.
3. A C9 a 2 napos távolság szerint legkorábban 2026-11-26-án (TREX először), a szokásos szabályokkal; kvóta 426 → 465 s (77,5%).

### 13.8 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás). A korrelációs és az összesítő számítás nem része az előre rögzített elemzésnek.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 14. A C9 előtti, hardver nélküli bővítés és a C1–C8 kalibráció-életkora (2026-11-24)

**Az elsődleges elemzés futtatása előtt rögzítve.** QPU-idő nem fogyott (kvóta 426 / 600 s); a `PROTOCOL`, az ujjlenyomat (`63521603…e93c9`) és a `FROZEN`
változatlan (ellenőrizve 2026-11-24). Az elsődleges elemzés kódja (`vqebd.heron_analysis.analyze`, a mérések előtt megírva) **nem változott**.

### 14.1 Mi változott (TP-F11 TC-1123–TC-1126)

| Elem | Változás | Teszt |
|---|---|---|
| `scripts/run_heron_blocks.py` | a C9 elfogadott blokknév, `kind = "supplementary"`; csak a teljes C1–C8 mentett kimenete után indítható; a szintek sorrendje a meglévő szabály szerint (C9: TREX először) | TC-1123 |
| `scripts/run_heron_blocks.py` | `final_metrics`: a job metrikáit a **végleges** használati adatig várja (`usage.status == "complete"`); ha nem véglegesül, `usage_final = false`-szal rögzít (a 13.2 ¹ hibája ellen) | TC-1124 |
| `vqebd.heron_analysis` | új, csak leíró függvények: `describe_differences`, `sensitivity_analyses` (a 2026-11-18-án rögzített (a) C1–C9 és (b) ≤ 48 órás vizsgálat, döntési mező nélkül) | TC-1125 |
| `scripts/analyze_heron.py` | a kimenet három részre bomlik: `primary` (változatlanul az `analyze`, csak megerősítő blokkok), `confirmatory_complete` (8 megerősítő blokk megvan-e), `sensitivity` | TC-1125 |
| `vqebd.heron_calibration_age`, `scripts/heron_calibration_age.py` | a 2026-11-19-i életkor-definíció kódja és a történeti rekonstrukció (`backend.properties(datetime=…)`, csak olvasás) → [`calibration_age.json`](../figures/data/f11/calibration_age.json) | TC-1126 |

Egy teszt azt is rögzíti, hogy egy kiegészítő blokk — szélsőséges értékkel is — az elsődleges eredményt **bitre azonosan** hagyja.

### 14.2 Kalibráció-életkor, C1–C8 (rekonstrukció a 2026-11-19-i definíció szerint)

| Blokk | Az első job indulása (UTC) | Legrégebbi paraméter | Mérési időpontja (UTC) | Életkor | ≤ 48 h (b) | Egyezik a pillanatképpel |
|---|---|---|---|---|---|---|
| C1 | 2026-11-04 08:26:45 | q1 T1 | 2026-11-03 23:15:27 | **9,2 h** | igen | igen |
| C2 | 2026-11-06 23:34:13 | q1 T2 | 2026-11-04 23:47:08 | **47,8 h** | igen | igen |
| C3 | 2026-11-08 08:46:08 | cz-hiba | 2026-11-07 02:22:55 | **30,4 h** | igen | igen |
| C4 | 2026-11-10 09:00:31 | q1 T1 | 2026-11-09 21:53:06 | **11,1 h** | igen | igen |
| C5 | 2026-11-12 08:21:19 | q1 T1 | 2026-11-11 17:25:24 | **14,9 h** | igen | igen |
| C6 | 2026-11-16 09:23:49 | q1 T1 | 2026-11-12 19:33:48 | **85,8 h** | **nem** | igen |
| C7 | 2026-11-22 14:22:15 | q1 T1 | 2026-11-21 01:03:46 | **37,3 h** | igen | igen |
| C8 | 2026-11-24 09:36:01 | q1 T1 | 2026-11-23 22:52:01 | **10,7 h** | igen | igen |

- A lekérdezett történeti értékek **mind a nyolc blokknál** megegyeznek a blokk elején mentett pillanatképpel (a modell bemenetével), tehát a rekonstrukció
  ugyanazt a kalibrációt látja, amelyből a modell-előrejelzés készült. A C6–C8 életkora egyezik a mérés napján élőben megfigyelt értékkel (85,8 / 37,3 / 10,7 h).
- A (b) érzékenységi vizsgálatból a C8 után **csak a C6 esik ki**. A **C2 (47,8 h) a határ közelében** van; a 48 órás határ előre rögzített (2026-11-18), nem
  módosítható, és a határ a vizsgálatba beletartozik.
- A C2 nyers jobját 2026-11-06 08:33-kor küldtük be, de 15 órát állt sorban, és csak 23:34-kor indult (7. szakasz); ezért volt a kalibráció a
  mérés idején ilyen idős.
- *Helyesbítés (22.3):* a 6–11. szakasz kalibráció-frissességi megjegyzései a `last_update_date`-hez mértek; a pár saját adatai szerinti életkort ez a
  táblázat adja. Az időpontok itt másodpercre csonkolva szerepelnek (a 8.1 és a 10.1 kerekít).

### 14.3 Független kódellenőrzés és javítások a C9 előtt (2026-11-26)

A C9 napján, a hardveres futtatás **előtt** egy független MI-ellenőrző (külön ügynök, a saját következtetéseim átadása nélkül) átnézte a 14.1 változásait;
két kört futott. Az elsődleges elemzés kódja (`analyze`) bájtra azonos a mérések előttivel (`57a421b`); a javított kód a feltöltött `analysis.json`-t
**bitre azonosan** adja vissza. A `PROTOCOL` / ujjlenyomat / `FROZEN` változatlan.

| # | Talált hiba (a 14.1 változataiban) | Javítás | Teszt |
|---|---|---|---|
| 1 | a `final_metrics` a `status: complete` + 0 s állapotot végesnek fogadta volna el (a C8 hibája megismétlődhetett volna, „végleges” jelöléssel) | végleges csak a pozitív `quantum_seconds` | TC-1127 |
| 2 | a két job között futó, ismételt metrika-lekérdezés hibája a mentés előtt leállíthatta volna a futtatót (a mért adat elveszett volna, és a kvóta az újrafuttatásra már nem elég: 450 + 42,75 > 480 s) | a két job között ismét **egyetlen, hibatűrő** olvasás (mint a C1–C8-nál); a blokkfájl azonnal mentődik; a végleges használat lekérdezése **utána**, kivétel nélkül; a blokk utáni kalibráció/kvóta hibája esetén `null` | TC-1127 |
| 3 | a várakozás a két job közé esett volna (a második job ~1 perccel később indult volna, mint a C1–C8-nál) | lásd 2. — a két job közti ütem a C1–C8-cal azonos | TC-1127 |
| 4 | egy meglévő blokkfájl (pl. elírt `--block C8`) felülírható volt | valódi futtatás megtagadva, ha a kimenet létezik | TC-1127 |
| 5 | a 48 órás határ kerekített életkoron dőlt el | az életkor kerekítés nélkül tárolva | TC-1128 |
| 6 | egy hibás kiegészítő blokk vagy életkor-rekord az elsődleges eredmény kiírását is megakaszthatta | az elsődleges rész előbb, az érzékenységi rész hibatűrően; elavult / hiányos életkor-rekord kizárva | TC-1128 |
| 7 | a cz-hiba pillanatkép-egyezése irány szerint téves eltérést jelezhetett | ugyanazon irány összevetése | TC-1128 |
| 8 | az életkor-szkript egy átmeneti hiba miatt jó rekordokat írhatott felül, ill. egy hiányzó `running` időbélyeg csendben későbbi indulást adott | a korábbi érvényes rekord megmarad; hiányzó `running` → ismeretlen életkor | TC-1128 |
| 9 | az első job eredménye a második végéig csak a memóriában volt; a fájl újraírása nem volt atomi | részleges mentés (`c9.partial.json`, az elemzés nem olvassa; siker után törlődik); atomi írás | TC-1127 |

A C1–C8 adatait egyik hiba sem érintette (a C8 `quantum_seconds` rögzítési hibáját a 13.2 írja le). Az ellenőrzést MI végezte; emberi kódellenőrzés nem történt.

## 15. Az elsődleges elemzés (2026-11-24): **H1 elutasítva**, H2 igaz

**Megerősítő eredmény.** Az előre rögzített elemzés (`scripts/analyze_heron.py` → `vqebd.heron_analysis.analyze`; a mérések előtt megírva, szintetikus adaton
tesztelve, AC-11.3) a C1–C8-on, a befagyasztott protokoll szerint (δ = 3,0 mHa; 90%-os TOST; 8 blokk). Kimenet: [`analysis.json`](../figures/data/f11/analysis.json)
(`confirmatory_complete: true`; az ujjlenyomat egyezik a `FROZEN`-nel). A futtatás a C9 előtti bővítés commitja (`78cbcc1`) után történt; a kiegészítő C9 az
elsődleges eredményt nem változtathatja (TC-1125).

### 15.1 H1 (elsődleges): megjósolja-e a modell a nyers hardveres hibát ±3,0 mHa-en belül

Δ = nyers hardver − kiolvasásos modell (mHa), blokkonként; a 90%-os t-intervallum a C1–C8-on.

| R (Å) | n | Átlag Δ | SE | 90% CI | A CI ⊂ [−3,0; +3,0]? |
|---|---|---|---|---|---|
| 0,735 | 8 | +7,48 | 4,00 | [−0,09; +15,05] | **nem** |
| 1,5 | 8 | +2,76 | 2,48 | [−1,93; +7,45] | **nem** |
| 2,0 | 8 | −0,16 | 1,26 | [−2,56; +2,23] | **igen** |

**Döntés az előre rögzített szabály szerint** (mindhárom geometria egyenértékű → egyenértékű; 2/3 → részben; egyébként elutasítva): **1/3 → H1 ELUTASÍTVA.**

- **Az előre kimondott következmény** (`phase_11.md` 3. fejezet): negatív eredmény, **közlendő**; a 11.E (nagyobb rendszerek szimulálása a Heron-modellel)
  **elmarad**; a következő lépés a reziduumok elemzése (drift? áthallás? egy-qubites hiba?). A küszöb utólag nem módosítható; egy új δ csak új, külön protokollban
  vizsgálható, és ez az eredmény változatlanul közölve marad.
- **Mi okozza leíróan az elutasítást:** elsősorban a blokkok közti szórás (11,3 / 7,0 / 3,6 mHa). Nyolc blokknál még nulla átlag mellett is csak ~4,5 mHa
  alatti szórásnál férne a 90%-os intervallum a ±3,0 mHa-es sávba (t₀,₉₅; ₇ ≈ 1,895); ez csak a 2,0 Å-nél teljesült. A 0,735 Å-nél az átlag is nagy: a modell
  átlagosan ~7,5 mHa-val alulbecsüli a nyers hibát (az intervallum alsó széle −0,09, a nullát éppen tartalmazza).

### 15.2 H2: lényeges-e a kiolvasási hiba modellezése

Végpont: blokkonként a három geometrián átlagolt négyzetes hiba **kiolvasás nélkül − kiolvasással** (páros különbség, 95% CI).

- **Átlagos különbség +252,0 mHa², 95% CI [+131,4; +372,6]** — a CI kizárja a nullát: **H2 igaz.** Mind a nyolc blokkban a kiolvasásos modell hibája a kisebb.

| Blokk | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---|---|---|---|---|---|---|---|
| Négyzetes hiba, kiolvasással (mHa²) | 424,1 | 39,4 | 13,7 | 6,1 | 70,7 | 30,6 | 3,2 | 24,2 |
| Négyzetes hiba, kiolvasás nélkül (mHa²) | 976,4 | 311,7 | 299,3 | 154,1 | 123,5 | 268,1 | 201,4 | 293,7 |
| Négyzetes hiba, rögzített B0-kalibráció (mHa², H4) | 344,1 | 26,9 | 22,9 | 5,3 | 10,9 | 16,3 | 33,5 | 16,0 |

### 15.3 H3 (másodlagos, felderítő — nem megerősítő)

Δ = TREX-szel enyhített hardver − kiolvasás nélküli modell; ugyanaz a TOST.

| R (Å) | Átlag Δ | SE | 90% CI | ⊂ [−3,0; +3,0]? |
|---|---|---|---|---|
| 0,735 | +0,75 | 1,56 | [−2,20; +3,70] | nem |
| 1,5 | +0,77 | 1,33 | [−1,75; +3,29] | nem |
| 2,0 | −1,32 | 0,83 | [−2,89; +0,26] | igen |

A terv szerint a H3 megerősítő állítást nem hozhat: a TREX-et a modell nem szimulálja, a kiolvasás nélküli modell csak közelítés.

### 15.4 H4 (másodlagos, csak leíró): pontosabb-e a blokkonkénti (friss) kalibráció egy rögzítettnél

A rögzített modell a pilot (B0, 2026-11-02) kalibrációjából épült (0,735 / 1,5 / 2,0 Å: 25,9 / 13,4 / 13,5 mHa). Páros különbség a négyzetes hibában
(rögzített − blokkonkénti): **átlag −17,0 mHa², 95% CI [−47,1; +13,1]**.

- A blokkonkénti kalibráció **nem bizonyult pontosabbnak**; leíróan a rögzített modell hibája 8-ból 6 blokkban kisebb volt (a blokkonkéntié csak a C3-ban és a
  C7-ben). A terv szerint a H4 csak leíró, okot nem állít. Összhangban van a 13.4 leíró megfigyelésével (a modell a közölt kalibráció ingadozását követi, a
  hardver kevésbé) — ez utólagos, **nem igazolt** értelmezés, a reziduum-elemzés tárgya.

### 15.5 Érzékenységi vizsgálatok — ideiglenes, a C9 nélkül (csak leíró, döntési szabály nincs)

- **(a) C1–C9:** a C9 még nem futott, ezért jelenleg azonos az elsődleges adatsorral (C1–C8).
- **(b) legfeljebb 48 órás kalibráció** (14.2): C1–C5, C7, C8 (n = 7; a C6 kiesik).

| R (Å) | Átlag Δ (nyers − modell) | Szórás | 90% CI |
|---|---|---|---|
| 0,735 | +7,64 | 12,20 | [−1,32; +16,60] |
| 1,5 | +2,15 | 7,33 | [−3,23; +7,54] |
| 2,0 | −0,40 | 3,79 | [−3,19; +2,38] |

A C6 elhagyása a képet nem javítja (a szórás nem csökken). A végleges érzékenységi táblázat a C9 után készül.

### 15.6 Mi állítható, és mi nem

- **Állítható:** ezen az eszközön (`ibm_kingston`, [1, 2] qubitpár), a H₂ kétqubites VQE-jén, 2026. november 4. és 24. között a *közölt* kalibrációból épített
  Heron-zajmodellnél az előre rögzített teszt szerint **nem sikerült kimutatni**, hogy a nyers hardveres hibától való átlagos eltérése ±3,0 mHa-en belül
  van (csak a 2,0 Å-nél; az 1,5 Å-nél az eredmény határozatlan); a kiolvasási hiba modellezése lényeges (H2).
- **Nem állítható:** hogy a modell más eszközön, qubitpáron vagy molekulán sem működne; az eltérés oka (a 13.4 és a 15.4 csak lehetséges magyarázat); hogy egy
  másik küszöb mellett „megfelelne” (a küszöb nem módosítható).
- **Korlátok** (a végleges jegyzőkönyvben részletesen, AC-11.7): egy eszköz, 2 qubit, H₂, 8 blokk; a terv és az elemzés MI-vel készült, nem lektorált; külső
  regisztráció nincs (a rögzítés a `protocol-f11-frozen` git-címke); a 10 napos kalibrációs szünet (12.1) és a C6 85,8 órás kalibrációja.
- **Következik** *(a 2026-11-24-i állapot; azóta: 16., 20–22. szakasz)*: a kiegészítő C9 (legkorábban 2026-11-26, külön jóváhagyással) és a végleges érzékenységi vizsgálat; a reziduum-elemzés (előre kimondott következő
  lépés); a végleges TR-F11 a szerző ellenőrzésével; utána README / CHANGELOG, `v1.1.0` és új Zenodo-verzió — mindez csak a szerző jóváhagyásával.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 16. C9 — a kiegészítő blokk (2026-11-26) és a végleges érzékenységi vizsgálatok

**Kiegészítő (`supplementary`) adat, nem megerősítő.** Az elsődleges elemzés (15. szakasz) a C9 után **bitre azonos** (az `analysis.json` `primary`
része változatlan; TC-1125). Az érzékenységi vizsgálatok előre rögzítettek (2026-11-18), csak leírók, döntési szabályuk nincs; a 15.5 ideiglenes táblázatát
ez a szakasz váltja fel. A protokoll-ujjlenyomat egyezik a `FROZEN`-nel; a futtató a 14.3 javításai utáni, feltöltött kód (`382a2d9`).

### 16.1 Feltételek, kalibráció, költség

Előzetes ellenőrzés (2026-11-26 07:39 és 08:01 UTC, csak olvasás): `ibm_kingston` aktív, 0 várakozó job; a pár **minden** életkor-paraméterét a C8
(2026-11-24 09:36) után mérték újra → a kalibrációs-frissességi szabály teljesült; kvóta 426 / 600 s. Friss szárazfutás, majd a szerző külön jóváhagyása.

| Paraméter (az [1, 2] pár) | C8 | C9 | Mérési időpont (C9, UTC) |
|---|---|---|---|
| kiolvasási hiba q1 / q2 | 0,72% / 1,29% | 0,70% / **1,45%** | 2026-11-26 07:47:07 |
| T1 q1 / q2 | 233 / 299 µs | **361** / 322 µs | 01:00:32 |
| T2 q1 / q2 | 301 / 122 µs | **641** / 115 µs | 01:00:38 / 01:00:40 |
| cz-hiba [1, 2] | 0,101% | 0,104% | 02:01:47 |

- **Kalibráció-életkor:** az első job indulása (08:09:59) − q1 T1 (01:00:32) = **~7,2 óra** (a legfrissebb blokk); a visszakeresett értékek egyeznek a pillanatképpel.
- Modell-előrejelzés: kiolvasással 25,5 / 13,5 / 13,7 mHa, kiolvasás nélkül 7,2 / 3,2 / 2,7 mHa.

| Szint | Job | Beküldve (UTC) | Futás kezdete | Vége | QPU-s |
|---|---|---|---|---|---|
| 1 (TREX) | `dc3uilds2omc738e9rfg` | 2026-11-26 08:09:57 | 08:09:59 | 08:10:33 | **24** |
| 0 (nyers) | `dc3uiuts2omc738e9s0g` | 08:10:36 | 08:10:37 | 08:10:57 | **15** |

- A szintek sorrendje a protokoll szerint **TREX először** (`level_order("C9") = [1, 0]`); a két job között 3 s (mint a C1–C8-nál). Kimenet:
  [`c9.json`](../figures/data/f11/c9.json), [`c9.log`](../figures/data/f11/c9.log).
- **Összesen 39 QPU-s** (kilencedszer ugyanannyi); kvóta 426 → **465 / 600 s (77,5%)**. A használati adat mindkét jobnál már az első olvasáskor végleges volt
  (`usage_final: true`); részleges vagy ideiglenes fájl nem maradt. A blokk utáni pillanatkép azonos a blokk előttivel *(nem informatív: a blokk utáni pillanatkép a gyorsítótárból származott, 22.1)*.

### 16.2 A C9 eredménye (mHa a Full CI-hez; z = különbség / blokkon belüli ensemble hiba)

| R (Å) | Nyers hardver | Modell (kiolvasással) | Különbség | z | TREX hardver | Modell (kiolvasás nélkül) | Különbség | z | Kiolvasási arány |
|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 35,1 | 25,5 | **+9,6** | +3,3 | 6,4 | 7,2 | −0,9 | −0,3 | 1,57 |
| 1,5 | 15,4 | 13,5 | **+2,0** | +0,8 | −1,6 | 3,2 | −4,8 | −1,9 | 1,65 |
| 2,0 | 13,7 | 13,7 | **0,0** | 0,0 | 2,4 | 2,7 | −0,3 | −0,1 | 1,02 |

**A hardver nyers hibája blokkonként** (mHa; a modell-előrejelzés a 0,735 Å-nél zárójelben):

| R (Å) | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 |
|---|---|---|---|---|---|---|---|---|---|
| 0,735 | 54,8 (23,0) | 34,5 (24,3) | 33,8 (27,6) | 25,0 (22,4) | 25,6 (33,8) | 29,9 (23,5) | 35,4 (32,5) | 32,2 (24,4) | 35,1 (25,5) |
| 1,5 | 26,7 | 16,0 | 15,8 | 14,1 | 7,9 | 19,1 | 15,9 | 16,2 | 15,4 |
| 2,0 | 18,0 | 14,3 | 14,0 | 9,7 | 11,9 | 13,8 | 15,3 | 12,8 | 13,7 |

- A 0,735 Å-nél a hardver nyers hibája ismét jóval nagyobb a modellénél (z = +3,3), a 2,0 Å-nél egyezik — a C8 mintája. Leíró megfigyelés: a C7–C9-ben a q1 T2
  22 → 301 → 641 µs között változott, a modell-előrejelzés ennek megfelelően 32,5 → 24,4 → 25,5 mHa, a hardver nyers hibája viszont 35,4 → 32,2 → 35,1 mHa
  maradt (utólagos, nem igazolt értelmezés; a reziduum-elemzés tárgya).
- Az 1,5 Å-nél a TREX-szel enyhített hardver a Full CI alá került (−1,6 mHa): az enyhítés túllőhet; egyetlen blokk, statisztikai zajjal összeegyeztethető.

### 16.3 A végleges érzékenységi vizsgálatok (csak leíró; a 15.5-öt felváltja)

Δ = nyers hardver − kiolvasásos modell (mHa); 90%-os t-intervallum (a TOST-tal azonos számítás, döntés nélkül).

| Vizsgálat | Blokkok | R (Å) | Átlag Δ | Szórás | 90% CI | ⊂ [−3,0; +3,0]? |
|---|---|---|---|---|---|---|
| **(a)** C1–C9 | 9 | 0,735 | +7,72 | 10,60 | [+1,15; +14,29] | nem |
| | | 1,5 | +2,67 | 6,55 | [−1,39; +6,73] | nem |
| | | 2,0 | −0,15 | 3,34 | [−2,22; +1,93] | igen |
| **(b)** ≤ 48 h kalibráció (a C6 nélkül) | 8 | 0,735 | +7,89 | 11,32 | [+0,31; +15,47] | nem |
| | | 1,5 | +2,13 | 6,79 | [−2,42; +6,68] | nem |
| | | 2,0 | −0,36 | 3,51 | [−2,71; +2,00] | igen |

- **Mindkét vizsgálat az elsődleges eredmény képét adja:** csak a 2,0 Å-nél fér a 90%-os intervallum a ±3,0 mHa-es sávba. A 0,735 Å-nél az intervallum mindkét
  vizsgálatban teljesen pozitív (a C9-cel együtt; az elsődleges C1–C8 intervallum a nullát tartalmazza): leíróan a modell az egyensúlyi geometrián
  többnyire alulbecsüli a nyers hardveres hibát (a pontbecslés 9 blokkból 8-ban pozitív); ez nem előre rögzített összevetés.
- **A C6 (85,8 órás kalibráció) kihagyása a képet nem változtatja**, tehát az eredményt nem az elavult kalibrációjú blokk okozza.
- A TREX-oldal (mint a H3, felderítő), (a) / (b): 0,735 Å +0,57 [−2,00; +3,15] / +0,85 [−2,07; +3,76]; 1,5 Å +0,16 [−2,31; +2,62] / −0,36 [−2,98; +2,26];
  2,0 Å −1,20 [−2,58; +0,18] / −1,42 [−2,94; +0,10].
- Kalibráció-életkor (14.2 kiegészítve): C9 = 7,2 h; a (b) vizsgálatból egyedül a C6 esik ki.

### 16.4 A hardveres mérések lezárása

- A Fázis 11 QPU-felhasználása: B0 57 s + C1–C9 9 × 39 s = **408 s**; a gördülő 28 napos keret a teljes mérés alatt ≤ 80% maradt (a csúcs 465 / 600 s =
  77,5%, ≥ 20% tartalékkal). Minden blokk a szerző külön jóváhagyásával, friss szárazfutás után futott; egy kísérlet megszakadt (C6, kvóta nem fogyott).
- A terv szerinti további hardveres mérés **nincs**. Hátravan *(a 16. szakasz írásakor; azóta: 20–22. szakasz)*: a végleges, a szerző által ellenőrzött TR-F11 (AC-11.7, minden korlát kimondva), a reziduum-elemzés
  (az előre kimondott következő lépés), README / CHANGELOG, `v1.1.0` és új Zenodo-verzió — a szerző jóváhagyásával.
- Az eredményt az MI számolta és értelmezte; a szerző a végleges jegyzőkönyvet 2026-11-26-án átnézte (21–22.).

## 17. Leíró reziduum-áttekintés (felderítő, utólagos — nem része az előre rögzített elemzésnek)

Az előre kimondott következő lépés a reziduumok elemzése (`phase_11.md` 3. fejezet). Ez a szakasz csak az **első, leíró áttekintés** a meglévő adatokon;
okot nem állít. Reziduum = nyers hardver − kiolvasásos modell (mHa), C1–C9 (n = 9); Pearson-féle r a blokk elején mentett kalibrációs paraméterekkel.
**Óvatosság:** 8 paraméter × 3 geometria = 24 korreláció kilenc ponton — több közepes |r| a véletlenből is adódhat (egyetlen tesztnél n = 9 mellett
|r| ≳ 0,67 felelne meg p < 0,05-nek); szignifikanciát nem állítunk.

### 17.1 A kalibrációs paraméterek blokkonként (a modell bemenete)

| Blokk | T1 q1 / q2 (µs) | T2 q1 / q2 (µs) | Kiolvasás q1 / q2 | cz-hiba | Életkor |
|---|---|---|---|---|---|
| C1 | 178 / 306 | 284 / 131 | 0,68% / 1,07% | 0,10% | 9,2 h |
| C2 | 256 / 277 | 462 / 117 | 0,88% / 0,98% | 0,10% | 47,8 h |
| C3 | 315 / 254 | 419 / 127 | 0,73% / 1,51% | 0,10% | 30,4 h |
| C4 | 342 / 318 | 597 / 128 | 0,39% / 1,32% | 0,08% | 11,1 h |
| C5 | 259 / 258 | 431 / 106 | **1,66%** / 1,27% | 0,10% | 14,9 h |
| C6 | 341 / 308 | 598 / 122 | 0,44% / 1,32% | 0,10% | 85,8 h |
| C7 | 199 / 288 | **22** / 127 | 1,04% / 1,06% | 0,08% | 37,3 h |
| C8 | 233 / 299 | 301 / 122 | 0,72% / 1,29% | 0,10% | 10,7 h |
| C9 | 361 / 322 | 641 / 115 | 0,70% / 1,45% | 0,10% | 7,2 h |

### 17.2 Megfigyelések (0,735 / 1,5 / 2,0 Å)

1. **A modell ingadozását főleg a q1 közölt kiolvasási hibája hajtja; a gépé ezt nem követi egyértelműen.** r(modell, q1 kiolvasás) = +0,87 / +0,90 / +0,90 (ez mechanikus: a
   modell ezt az értéket használja), r(gép, q1 kiolvasás) = −0,16 / −0,58 / +0,01. Ezért a reziduum a q1 kiolvasási hibájával negatívan korrelál
   (−0,47 / −0,73 / −0,59; a C1 nélkül −0,71 / −0,91 / −0,71). Példa: a C5-nél (q1 kiolvasás 1,66%) a modell 33,8 mHa-t jósolt, a gép 25,6 mHa-t adott.
2. **A kiolvasás hozzájárulása (nyers − TREX) a gépen átlagosan nagyobb, mint a modellben** (24,6 vs. 17,4 / 12,3 vs. 9,8 / 11,6 vs. 10,6 mHa), és
   blokkonként sem követi a modellt (r = −0,15 / −0,56 / −0,35).
3. **A modell és a gép blokkonkénti értéke nem követi egymást** (r = −0,26 / −0,65 / −0,10). A gép nyers hibájának blokkok közti szórása a 0,735 Å-nél
   8,7 mHa (a C1 nélkül 4,2), a modellé 4,2 mHa.
4. **A kalibráció életkora** a reziduummal nem mutat egyértelmű kapcsolatot (r = −0,13 / +0,13 / +0,18).
5. **A C1** (az első megerősítő blokk, +31,8 mHa a 0,735 Å-nél) erősen befolyásolja a korrelációkat; nélküle több előjel megfordul.
6. **Más paraméterek is:** a reziduum a q2 T2-vel (+0,58 / +0,72 / +0,62; a C1 nélkül +0,42 / +0,64 / +0,47) és a q2 T1-gyel (+0,40 / +0,55 / +0,43)
   legalább olyan erősen korrelál, mint a q1 kiolvasási hibájával — a felderítő korrelációk tehát nem jelölnek ki egyetlen okot. *(Kiegészítve, 22.3.)*

**Lehetséges, nem igazolt értelmezés:** a közölt kiolvasási hiba (különösen a q1-é) nem azt a kiolvasási hibát írja le, amely a futás idején a mi
áramkörünkre hatott (eltérő mérési feltételek, egyidejű kiolvasás, időbeli ingadozás) — összhangban az IBM-oktatóanyag megjegyzésével a közölt és a
saját mérésű értékek eltéréséről (13.6). Ez a következő fázis lehetséges kérdése, nem következtetés.

## 18. Korlátok (AC-11.7)

1. **Egy eszköz, egy qubitpár:** `ibm_kingston` (Heron r2), fizikai qubitek [1, 2]; 2 qubit, 4 CZ-kapu. Az eredmény nem általánosítható más eszközre,
   qubitpárra vagy nagyobb áramkörre (R2, R7).
2. **Egy molekula, három geometria:** H₂, R = 0,735 / 1,5 / 2,0 Å, egy ansatz, a θ\*-pontban (a θ-scan és a H5 elhagyva, döntés 4.).
3. **Kis minta:** 8 megerősítő (+ 1 kiegészítő) blokk 22 nap alatt (C1–C9; a B0 pilottal 24 nap). A kapott blokk-közi szórás mellett a 0,735 és az 1,5 Å-nél még tökéletes átlagos
   egyezés esetén sem lett volna elég 8 blokk (≈ 4,5 mHa alatti szórás kellett volna); a minta nagyságát a QPU-keret korlátozta.
4. **A modell a közölt kalibrációból épül.** A közölt értékek mérési módszere és időpontja eltérhet a futásétól (13.6); a Kingston párunk adatait 10 napig nem mérték
   újra (vagy nem közölték, 12.1), a C6 85,8 órás kalibrációval futott — az érzékenységi vizsgálat szerint ez a képet nem változtatja (16.3).
5. **A TREX-et a modell nem szimulálja:** a H3 csak közelítés (R3).
6. **MI-vel készült munka, nem lektorált:** a terv, a kód, az elemzés és a szöveg MI-vel (Claude, Anthropic) készült a szerző irányításával; a kód ~80%-át a
   szerző saját bevallása szerint soronként átnézte (`AI_DISCLOSURE.md`); független emberi statisztikus nem vett részt (R6 javaslata nem teljesült); a 14.3
   kódellenőrzése is MI-vel történt.
7. **Nincs külső előzetes regisztráció** (OSF, döntés 5.): a rögzítés a `protocol-f11-frozen` git-címke és a `FROZEN` ujjlenyomat. A mérések közben
   rögzített kiegészítések (kalibrációs-frissességi szabály, életkor-definíció, a C9) a további, még nem mért adatok **előtt** készültek, de a C1–C6
   ismeretében (a C6 elavult kalibrációja volt az ok); az elsődleges elemzést nem érintik, az érzékenységi vizsgálatok ezért csak leírók.
8. **A futtató módosult a mérési szakaszban** (14.1, 14.3): a mérés logikája, a protokoll és az elsődleges elemzés nem; a C8 TREX jobjának QPU-ideje hibásan
   rögzült (13.2, az eredményt nem érinti).
9. **A gép nyers hibája (8–55 mHa) messze a kémiai pontosság (1,6 mHa) fölött van:** a kísérlet a zajmodellt teszteli, nem a gép pontosságát; a pontos
   referenciát a klasszikus Full CI adja.
10. **A 17. és a 21. szakasz utólagos, felderítő:** okot nem állít; a megfigyelések új, előre rögzített vizsgálatot igényelnek.
11. **A modell a kiolvasási hibát szimmetrikusnak vette:** az IBM backend-objektuma az Aer zajmodelljének csak az átlagos `readout_error`-t adja át, a 0→1 és az 1→0 tévesztés külön értékét nem. A felderítő ellentényes számítás szerint ez a 0,735 Å-es átlagos eltérésből ~1,3 mHa-t magyaráz (21.2).
12. **A blokkok függetlenségét, az időbeli sodródást és a normalitást** az elemzés nem vizsgálta (n = 8, a C1 kiugró); a TOST ezeket feltételezi. A 9.6 és a
    10.5 utalása, hogy ezt a H4 kezeli, téves volt: a H4 nem függetlenségi teszt.
13. **A blokkon belüli kalibrációváltozás figyelése (R1) nem működött:** a blokk utáni pillanatkép a gyorsítótárból származott (22.1); a modell bemenetét a
    történeti rekonstrukció igazolja (14.2, 16.1).
14. **Kisebb modellezési részletek:** a modell 8193 lövéssel számolt 8192 helyett (a `BackendEstimatorV2` kerekítése), és a mérési bázisváltó kapukat
    zajmentesen adta hozzá (becsült hatás ≲ 0,1 mHa) — mindkettő elhanyagolható a δ = 3,0 mHa-hez képest.

## 19. Az elfogadási kritériumok állapota (`phase_11.md` 6. fejezet)

| AC | Állapot |
|---|---|
| AC-11.1 | ✅ a modell bitre azonos a felderítő útvonallal, a kiolvasás kapcsolható (`phase_11.md` 6.1) |
| AC-11.2 | ✅ minden blokkhoz pillanatkép a blokk előtt, a modell ebből épült; a történeti rekonstrukció mind a 9 blokknál egyezik (14.2, 16.1). A blokk utáni pillanatkép a gyorsítótárból származott, ezért nem informatív (22.1) |
| AC-11.3 | ✅ az elemzés szintetikus adaton tesztelve a mérések előtt; a kiegészítő blokk az elsődleges eredményt nem változtatja (TC-1125) |
| AC-11.4 | ✅ egyetlen blokk sem lépte át a 80%-ot (csúcs 465 / 600 s = 77,5%); a kapu tesztelt (TC-1107–TC-1109, TC-1123, TC-1127) |
| AC-11.5 | ✅ a `protocol-f11-frozen` címke megelőzte az első hardveres blokkot (`phase_11.md` 6.1) |
| AC-11.6 | ✅ a H1–H4 az előre rögzített szabály szerint kiértékelve (15.); a negatív eredmény ebben a jegyzőkönyvben közölve; a feltáró (B0), a megerősítő (C1–C8) és a kiegészítő (C9) adat külön jelölve; a nyilvános kiadás (`v1.1.0`, Zenodo) a szerző jóváhagyásával |
| AC-11.7 | ✅ a korlátok a 18. szakaszban; a szerző átnézte (2026-11-26) |

## 20. Következtetés és lehetséges következő lépések (a döntés a szerzőé)

- **A Fázis 11 mérési része lezárult.** A 11.E elmarad (H1 nem egyenértékű). A 11.F-ből a végleges TR-F11 (a szerző átnézte) és a README / CHANGELOG
  elkészült; a `v1.1.0` és az új Zenodo-verzió a szerző külön jóváhagyásával.
- **Lehetséges irányok egy következő fázishoz** (javaslat, nem döntés; mindegyikhez új, külön, előre rögzített protokoll kell):
  1. saját, futás előtti karakterizálás (különösen a kiolvasásé) és az ebből épített modell összevetése a közölt kalibrációs modellel — az IBM-oktatóanyag
     módszere (13.6), Qiskit ≥ 2.0, tehát új környezet;
  2. a 0,735 Å-es eltérés forrásának célzott vizsgálata szimulációban (mely zajkomponens hiányzik a modellből: koherens hiba, áthallás, szivárgás);
  3. más qubitpár vagy eszköz — a QPU-keret korlátai mellett (a gördülő keretből 2026-11-30-án a Fázis 5.H és a B0 57–57 s-a, összesen 114 s, 12-02-án a C1 39 s-a kerül ki).

## 21. A szerzői átnézés kérdései (2026-11-26) — felderítő válaszok

A szerző a végleges tervezet átnézésekor nyolc kérdést vetett fel. A válaszok **utólagos, felderítő** vizsgálatból származnak
([`scripts/explore_heron_review.py`](../../scripts/explore_heron_review.py) → [`explore_review.json`](../figures/data/f11/explore_review.json)): jobot nem
küldtünk be, QPU-idő nem fogyott, az IBM-től csak a történeti kalibrációt kérdeztük le. **Az elsődleges eredményt és a döntést nem érintik** (a küszöb és
a szabály változatlan). Kilenc blokk, sok párhuzamos összevetés — szignifikanciát nem állítunk.

### 21.1 Az eszköz: a protokoll-modell újraépítése

A történeti kalibrációból (`backend.properties(datetime=…)` → `convert_to_target` → ugyanaz a `NoiseModel.from_backend`, mint a protokollban) újraépített
modell **mind a kilenc blokknál 0,00 mHa eltéréssel** adja vissza a mérés napján mentett előrejelzést; az alábbi ellentényes („mi lett volna, ha”)
változatok erre épülnek.

### 21.2 A kérdések és a válaszok

1. **Mi okozta a C1 kiugrását?** Bitstring-gyakoriság és Pauli-tagonkénti hardveres érték **nem áll rendelkezésre**: az Estimator PUB-onként az összesített
   Hamilton-operátor egyetlen várható értékét adja, és a job eredménye sem tartalmaz többet. A meglévő adatból: a 0,735 Å-es nyers hibán belül a kiolvasási
   rész (nyers − TREX) a gépen 39,2 mHa, a modellben 14,8 mHa; a C1 többletének (+31,8 mHa) ~77%-a (+24,5) a kiolvasásból, ~23%-a (+7,4) a többi zajból jön.
   Az aszimmetrikus kiolvasás (4. pont) ebből ~4 mHa-t magyaráz.
2. **Számít-e a szintek sorrendje?** Nyers reziduum, nyers először (C2, C4, C6, C8) ↔ TREX először (C1, C3, C5, C7, C9): +6,8 / +4,1 / +0,2 ↔ +8,5 / +1,5 / −0,4
   mHa (a C1 nélkül +2,6 / −1,8 / −2,0); TREX-reziduum: +2,2 / +1,9 / −0,8 ↔ −0,8 / −1,2 / −1,6 mHa. A TREX-oldali ~3 mHa-es különbség 4, ill. 5 blokk és
   3–5 mHa szórás mellett nem választható el a zajtól — szisztematikus sorrendhatás nem mutatható ki (a váltakoztatás éppen ezt védi). Pontosítás: a második
   job a C2-nél 133 s, a C6-nál 116 s, a C3-nál 327 s múlva indult, a többi blokkban 4,6–8,2 s múlva.
3. **Miért reagált a modell ~8 mHa-val a q1 T2 változására (C7 → C8), ha az áramkör rövid?** Az ISA-áramkör 15 RZ, 12 SX és 4 CZ kapu, becsült hossza
   **0,50 µs** (CZ: 68 ns); a kiolvasás 2,18 µs. A modell a kiolvasási műveletre kvantumhibát **nem** tesz (zajjal terhelt műveletek: `cz`, `id`, `reset`,
   `sx`, `x`, `xslow`; a kiolvasásra csak kiolvasási hiba), tehát nem a kiolvasási ablak dekoherenciája okozza. **Ellentényes számítás:** ha a C7 modelljében
   csak a q1 T2-jét cseréljük a C8-asra (22 → 301 µs), a 0,735 Å-es előrejelzés 32,5 → **24,3** mHa (a C8 tényleges modellje 24,4) — a C7–C8 közti
   nettó modellugrás ≈ a T2-csere hatása (a többi paraméter változásának hatásai közel kioltják egymást; a q1 kiolvasási hibájának cseréje önmagában
   32,5 → 29,8 mHa). Valószínű mechanizmus: a 0,5 µs a 22 µs-nak
   ~2%-a, a kapuk alatti fázisvesztés azonban a későbbi kapuk után betöltöttségi hibává alakul, és a 0,735 Å-nél a Z-tagok együtthatója ±0,40 Ha, így már ~1%
   betöltöttség-hiba ~8 mHa. A gép nyers hibája közben alig változott (35,4 → 32,2 mHa): ez arra utal (nem igazolt), hogy a közölt 22 µs nem a futás alatti
   koherenciát írta le (vö. 13.6).
4. **Tartalmaz-e a kalibráció külön 0→1 és 1→0 tévesztést, és számít-e?** A blokkfájl pillanatképe csak az átlagos `readout_error`-t tárolta; a történeti
   kalibráció a `prob_meas0_prep1` (1→0) és a `prob_meas1_prep0` (0→1) értéket is tartalmazza. **A protokoll-modell a kiolvasást szimmetrikusnak vette:** a
   qiskit-ibm-runtime a Target `measure` tulajdonságába csak az átlagos hibát teszi, így az Aer mindkét irányba ugyanazt a tévesztést modellezi (18.11). A q1-nél
   az 1→0 tévesztés **kilenc blokkból nyolcban nagyobb** (pl. C5: 2,44% ↔ 0,88%, C1: 1,07% ↔ 0,29%; a C4-ben egyenlő). A 0,735 Å-es ideális állapot 98,8%-ban
   |01⟩, azaz a fizikai q1 |1⟩-ben van — tehát éppen az 1→0 tévesztésre érzékeny. Aszimmetrikus kiolvasással a reziduum: 0,735 Å +7,72 → **+6,46** mHa
   (90% CI [+0,31; +12,60]); 1,5 Å +2,67 → +2,21; 2,0 Å −0,15 → −0,35. Az irány jó, de a 0,735 Å-es torzításnak csak ~1/6-át magyarázza.
5. **Összefügg-e a sorban állás a reziduummal?** A nyers job várakozása a C2-nél 15,0, a C6-nál 18,2 óra volt, a többi blokkban legfeljebb 5,4 perc (C3); a TREX-jobok közül a C1-é várt a legtovább, 20 percet.
   r(várakozás, TREX-reziduum) = +0,06 / +0,28 / −0,01; r(várakozás, nyers reziduum) = +0,03 / +0,24 / +0,30 — összefüggés nem látszik.
6. **Mely Pauli-tagok számítanak, és miért egyezik a 2,0 Å?** A kétqubites (paritás, kétqubites redukció) H₂-Hamilton-operátor tagjai: II, IZ, ZI, ZZ, XX (YY
   nincs). A C8 kalibrációjával modellezett hiba tagonként:

   | R (Å) | IZ / ZI együttható (Ha) | ZZ | XX | Z-bázis: \|01⟩ / \|10⟩ | Modellhiba: Z-tagok / XX (mHa) |
   |---|---|---|---|---|---|
   | 0,735 | ±0,398 | −0,011 | +0,181 | 98,8% / 1,2% | +20,6 / +2,0 |
   | 1,5 | ±0,129 | −0,004 | +0,230 | 87,4% / 12,6% | +4,8 / +7,5 |
   | 2,0 | ±0,061 | −0,001 | +0,259 | 71,2% / 28,8% | +0,9 / +11,5 |

   *(A tagonkénti bontás egyetlen, mintavételezett szimulációból készült; összege 22,6 / 12,4 / 12,5 mHa a mentett 24,4 / 12,8 / 13,1 mHa-es modellel
   szemben.)*

   A 0,735 Å-nél a modellhiba ~90%-a a Z-tagokból, a 2,0 Å-nél ~93%-a az XX-tagból jön — ez a Hamilton-együtthatókat tükrözi, nem a hibaforrást: az
   XX-tagot is terheli a kiolvasási hiba (a (1 − 2p₁)(1 − 2p₂) ≈ 0,96-os tényező a 2,0 Å-es XX-hibából ~9 mHa-t ad a 11,5-ből). *(Helyesbítve, 22.3: a
   korábbi „koherencia” értelmezés téves volt.)* A 2,0 Å-es egyezés leíró oka a 17.2/2: ott a gép és a modell kiolvasási része egyezik (11,6 ↔ 10,6 mHa),
   a 0,735 Å-nél nem (24,6 ↔ 17,4). A hardver tagonkénti eltérése nem mérhető vissza (1. pont).
7. **Mennyit javítana egy futás előtt mért kiolvasási mátrix?** Új mérés nélkül nem számszerűsíthető. **Felső becslés:** ha a modell a gép saját kiolvasási
   hatását használná (nyers − TREX), a reziduum a TREX-reziduum lenne: 0,735 Å **+0,57** mHa, 90% CI [−2,00; +3,15] (most +7,72 [+1,15; +14,29]); 1,5 Å +0,16
   [−2,31; +2,62]; 2,0 Å −1,20 [−2,58; +0,18]. Feltétele, hogy a TREX a kiolvasási hibát torzítás nélkül eltávolítja. A 0,735 Å-es torzítás nagy része
   eltűnne, a ~4 mHa-es blokk-közi szórás megmaradna — ez egy következő fázisban **előre rögzíthető hipotézis**.
8. **Szerepet játszhatott-e az áthallás vagy a szomszédos qubitek?** A pár szomszédai a heavy-hex rácson: q0 és q3. A C1-nél a q0 kiolvasási hibája 2,50%, a
   q3 T1-e 161 µs; a C5-nél 2,29%, ill. 248 µs; a C8-nál 1,21% (q3: 0,61%), a C9-nél 2,23% (q3: 0,57%) — a C1 és a C5 nem kiugró. Az IBM-gépeken egyszerre
   egy job fut, ezért a sor hossza nem a futás alatti terhelés mértéke; az adat az áthallást nem teszteli (ehhez külön kísérlet kellene).

### 21.3 Mit jelent ez a projektnek

- **Az elsődleges eredmény és a döntés változatlan** (H1 elutasítva); a korlátok a 18.11 ponttal bővültek (szimmetrikus kiolvasás a modellben).
- **Javaslat egy következő fázis protokolljához** (nem döntés): (a) a Pauli-tagonkénti várható értékek és Z-bázisú bitstringek mentése (alig több QPU-idő;
  az 1. és a 6. kérdés közvetlenül mérhető lenne); (b) aszimmetrikus kiolvasás a modellben; (c) futás előtti saját kiolvasási mátrix az [1, 2] páron —
  hipotézis: a 0,735 Å-es torzítás nagy része eltűnik (7. pont); (d) a T2-érzékenység kezelése (saját T2-mérés vagy a bizonytalanság bevitele a modellbe);
  (e) a szintek sorrendjének váltakoztatása és a várakozási idők rögzítése marad.

## 22. A kiadás előtti átnézés (2026-11-26): helyesbítések és javítások

A szerző kérésére a `v1.1.0` kiadása előtt három független MI-ellenőrzés futott: a jegyzőkönyv számainak újraszámolása az adatfájlokból, a nyilvános szövegek
és a `v1.0.0` óta változott kód átnézése. **A mért adat, az előre rögzített elemzés és a H1–H4 döntése nem változott** (az `analysis.json` elsődleges része
bájtra azonos; minden blokkérték, a 15–17. és a 21. szakasz számai reprodukálódnak). A helyesbített mondatok a helyükön jelölve vannak.

### 22.1 A „blokk utáni” kalibrációs pillanatkép a gyorsítótárból származott

- A `calibration_snapshot` a `backend.properties()`-t paraméter nélkül hívta; a qiskit-ibm-runtime 0.41 ekkor a gyorsítótárazott tulajdonságokat adja vissza
  (`refresh=False`). Ezért **mind a 10 blokkban** a „blokk utáni” pillanatkép a blokk előttinek a másolata (csak a `captured_utc` tér el), és a jegyzőkönyv „a
  kalibráció a blokk előtt és után azonos” megállapításai nem informatívak. Példa: a C2-nél a két pillanatkép 15 óra különbséggel készült, és az IBM közben
  (22:34 UTC) frissítette a kalibrációt.
- **Az eredményt nem érinti:** a modell a blokk előtti pillanatképből épült, és a történeti rekonstrukció (14.2, 16.1) mind a 9 blokknál igazolja, hogy a jobok
  indulásakor a pár ugyanazon paraméterei voltak érvényben. Ami elveszett: a blokkon belüli kalibrációváltozás közvetlen figyelése (R1, 18.13) — a blokkok
  ~1 perc alatt lefutottak, a két hosszú várakozású blokkot (C2, C6) a rekonstrukció lefedi.
- **Javítás (a jövőre):** `calibration_snapshot(…, refresh=True)`, teszttel (TC-1130).

### 22.2 További kódjavítások (a mért adatot nem érintik)

- Valódi futtatás csak a protokoll gépével, lövésszámával, seedjével és ismétlésszámával indul (a parancssori kapcsolók nem írhatják felül); a seed és az
  ismétlésszám a blokkfájlba is bekerül. A meglévő 10 blokk mind `ibm_kingston`, 8192 lövés, [1, 2]; a protokoll seedjét és ismétlésszámát a modell
  0,00 mHa-es újraépíthetősége (21.1) igazolja.
- Az elemző szkript a bemenetet ellenőrzi (egyedi blokknevek, a név és a `kind` egyezése, a gép / lövésszám / qubitpár, véges értékek, azonos geometriák), és
  a megerősítő sorozat teljességét a C1…C8 halmazon vizsgálja; az `analyze` (az elsődleges elemzés) változatlan.
- Mindkét szint transzpilálása a rögzített párra és azonos ISA-áramkörre kell, hogy kerüljön (eddig csak az elsőt ellenőrizte); egy korábbi, megszakadt
  kísérlet részleges mentése mellett nem indul új futtatás.
- A modell lövésszáma és a bázisváltó kapuk: 18.14.

### 22.3 Helyesbített megfogalmazások

- **TOST:** a nem teljesülő egyenértékűség azt jelenti, hogy **nem sikerült kimutatni** a ±3,0 mHa-en belüli átlagos egyezést — nem azt, hogy a modell
  bizonyítottan téved; az 1,5 Å-nél (+2,76 mHa, a pontbecslés a sávon belül) az eredmény határozatlan. A 2,0 Å-es egyenértékűség az *átlagos* eltérésre
  vonatkozik; egy-egy blokk eltérése ennél nagyobb volt (C1 +6,1, C5 −6,5 mHa). A 0. és a 15.6, valamint a nyilvános szövegek ennek megfelelően javítva.
- **„Rendszeresen alulbecsüli”** (0., 16.3): túlzás volt; az elsődleges 0,735 Å-es intervallum a nullát tartalmazza, teljesen pozitív csak a C9-cel együtt,
  és ez nem előre rögzített összevetés.
- **21.2/6:** a Z–XX megoszlás a Hamilton-együtthatókat tükrözi; az XX-tagot is terheli a kiolvasási hiba; a „koherencia” értelmezés téves volt.
- **17.2:** a q2 T2-vel és T1-gyel való korrelációk kiegészítve; a „gépét nem” megfogalmazás túlzás volt.
- **18.7:** a 48 órás határt és az életkor-definíciót a C1–C6 ismeretében rögzítettük (a további adatok előtt); **18.12:** a függetlenség és a sodródás nem
  vizsgált.
- **21.2/3:** a C7–C8 modellugrás „egésze” helyett a nettó hatás; „a kapuk közti” helyett „a kapuk alatti” fázisvesztés.
- **6–11. szakasz:** a kalibráció-frissességi megjegyzések a `last_update_date`-hez mértek; a pár saját adatai szerinti életkort a 14.2 adja (például a C3 30,4
  órás volt, nem a legfrissebb).

### 22.4 Számszerű és időponti helyesbítések

| Hely | Korábban | Helyesen |
|---|---|---|
| 1.1, a B0 nyers jobja | 33,6 perc sorban állás | 32,9 perc (a 33,6 perc a falióra-idő) |
| 6.1, a C1 nyers jobja | 5 s várakozás | ~2 s |
| 6.3, a C1 kiolvasási aránya (0,735 Å) | 2,65 | 2,66 |
| 8.4 | „C1: pozitív”; „0,9-szeres és 5,1-szeres” | „C1: vegyes”; az arány nem reprodukálható, törölve |
| 11.1, a C6 első kísérlete | ~22 óra sorban | legfeljebb ~21 óra |
| 11.2, a C6 szárazfutása | 16:10 (időzóna nélkül) | 15:10 UTC |
| 12.2 és 13.1, a C7 modellje (2,0 Å) | 16,2 mHa | 16,1 mHa |
| 12.6, C1–C7, 2,0 Å | átlag −0,2; TREX-átlag −1,8 | −0,1; −1,7 |
| 16.1, a C9 modellje (2,0 Å) | 13,8 mHa | 13,7 mHa |
| 18.3 | 24 nap | 22 nap (C1–C9; a B0-val 24) |
| 20., a kvóta visszatöltődése | a B0 57 s-a 11-30-án | 11-30-án a Fázis 5.H és a B0 57–57 s-a (114 s) |
| 21.2/2 | 5–8 s | 4,6–8,2 s |
| 21.2/5 | „a többi blokkban legfeljebb ~20 perc” | a nyers jobok legfeljebb 5,4 percet (C3), a C1 TREX-jobja 20 percet vártak |
| nyelvi | „a FCI”, „mHa-lel” | „az FCI”, „mHa-val” |

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
