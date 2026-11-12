# TR-F11 — Fázis 11 jegyzőkönyv (a Heron-zajmodell validálása) — ELŐZETES: B0 pilot és C1–C5

| | |
|---|---|
| **Azonosító** | TR-F11 |
| **Dokumentum-verzió** | 0.6.0 (előzetes: B0 pilot + C1–C5; a 6. szakasz a C1-et, a 7. a C2-t, a 8. a C3-at, a 9. a C4-et és a köztes leíró összesítést, a 10. a C5-öt tartalmazza) |
| **Dátum** | 2026-11-02 (B0), 2026-11-04 (C1), 2026-11-06/07 (C2), 2026-11-08 (C3), 2026-11-10 (C4), 2026-11-12 (C5) |
| **Terv / tesztterv** | [`phase_11.md`](../plan/phase_11.md), [`TP-F11_heron_modell.md`](TP-F11_heron_modell.md) |
| **Kezdeményezte, irányította, engedélyezte** | Kormos Attila (a B0-t 2026-11-02-án, a C1-et 2026-11-04-én, a C2-t 2026-11-06-án, a C3-at 2026-11-08-án, a C4-et 2026-11-10-én, a C5-öt 2026-11-12-én külön jóváhagyta) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — a kódot és a szöveget az MI írta a szerző kérésére, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |
| **Státusz** | **Előzetes.** A pilot (B0) és az első öt megerősítő blokk (C1–C5) futott le; C6…C8 még nem. **A B0 nem megerősítő adat; a C1–C5 megerősítő, de csak öt blokk** (n = 5): a blokk-közi szórás már becsülhető, de nagyon bizonytalanul, és a H1–H4 szerinti döntés belőle nem hozható (a terv szerint 8 blokk kell). |

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
- A nyers job **33,6 percet** állt sorban (a falióra-idő 2018 s); a sorban állás nem számít QPU-időnek.
- Hibás vagy félbehagyott job nem keletkezett; hardveres újrafuttatásra nem volt szükség.

### 1.2 Kalibráció

A blokk előtti és utáni pillanatkép `last_update_date` mezője azonos: **2026-11-02T16:10:11Z**. A futás 17:38–17:40 UTC között volt,
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
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

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
- Sorban állás: a TREX job 20 percet, a nyers 5 másodpercet várt; QPU-időt nem fogyaszt.
- **Korrekció a munkamenetből:** a futás közben tévesen "nyers" jobként írtam le az elsőként sorban álló jobot; az a protokoll
  szerint (`level_order("C1") = [1, 0]`) TREX volt. A kód a tervnek megfelelően működött.

### 6.2 Kalibráció

A blokk előtti és utáni pillanatkép azonos (`last_update_date` 2026-11-04T07:49:27Z, a pillanatképek 08:03 és 08:35 UTC-kor). A
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
| 0,735 | 39,2 | 14,8 | 2,65 | 32,9 | 16,8 | 1,96 |
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
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

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

A blokk előtti (08:30 UTC) és utáni (23:45 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-06T01:30:29Z**; a futás a
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
- **A TREX-es egyezés a C2-n jobb**, mint a C1-en (|z| ≤ 1,9), de a 2,0 Å-nél a hardver a FCI **alá** esik (−0,1 mHa; a statisztikai
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
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

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

A blokk előtti (08:39 UTC) és utáni (08:53 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-08T08:12:30Z**; a mérés a
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
  alulbecslés mértéke blokkonként 0,9-szeres és 5,1-szeres között változik, a 0,735 Å-nél +6,2…+31,8 mHa (B0: +14,1).
- **A kiolvasási hozzájárulás aránya** a C3-on 1,15–1,58; a négy blokk (B0, C1, C2, C3) 1,15 és 2,66 között mozog. A hardver kiolvasási
  hozzájárulása mindig nagyobb a modellénél, de a C3 2,0 Å-nél már csak 15%-kal. A korábbi hipotézis (a tényleges kiolvasási
  hiba nagyobb a kalibrációsnál) tehát nem cáfolódott, de a mértéke blokkonként erősen változik; **továbbra is hipotézis**.
- **A TREX-es hardver a kiolvasás nélküli modellnél jobb** a C3-on mindhárom pontban (−4,8 / −3,4 / −2,6 mHa; |z| ≤ 1,6). Négy blokkon
  a TREX-es eltérés előjele vegyes (B0: negatív, C1: pozitív, C2: vegyes, C3: negatív), tehát nem egyirányú rendszerhiba.
- **Nem állítható:** a H1–H4 eldöntése; az ok; általánosítás más eszközre, qubitpárra vagy molekulára. A négy blokk (B0, C1, C2, C3)
  eltérő nagyságú különbséget ad, ami éppen azt indokolja, hogy a protokoll 8 megerősítő blokkot ír elő.
- **Várható irány (nem előrejelzés):** a C2 és a C3 jobban egyezik, mint a C1; ha a hátralévő blokkok a C2–C3 szintjén maradnak, a
  H1 a 0,735 Å-nél akkor is nehezen teljesül (a pontbecslés +6…+10 mHa, a ±3,0 sávon kívül). A küszöb nem módosítható.

### 8.5 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás); a TOST csak a megerősítő blokkok
  teljes sorozatán értékelhető (`scripts/analyze_heron.py`, C8 után).
- A C3 a kalibráció után 34–41 perccel futott (a C2: ~22 óra, a C1: ~25 perc a pillanatképhez képest), tehát a kalibráció-elavulás
  hatása itt a legkisebb; a C2 és C3 közel azonos nyers hardvereredménye ezzel *összhangban van*, de ezt két pont nem bizonyítja.
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

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

A blokk előtti (08:58 UTC) és utáni (09:01 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-10T08:43:26Z**; a mérés a
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
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

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
  érinti; erre a végső elemzésnél (H4: blokkonkénti vs. rögzített kalibráció) figyelni kell, de a szabályokat nem módosítjuk.
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

A blokk előtti (08:18 UTC) és utáni (08:25 UTC) pillanatkép `last_update_date` mezője azonos: **2026-11-12T07:58:36Z**; a mérés a kalibráció
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
- A blokkok **függetlenségét** a negatív előjelváltás nem támasztja alá és nem is cáfolja; a H4 (blokkonkénti vs. rögzített kalibráció) elemzése a végső kiértékelésben történik.

### 10.6 Megjegyzések

- A z-értékek leíró számítások (a blokkon belüli statisztikai hiba, **nem** a blokk-közi szórás).
- A korrelációs számítás **nem része** az előre rögzített elemzésnek; utólagos, feltáró jellegű, és a végleges TR-F11-ben is így jelöljük.
- Az eredményt az MI számolta és értelmezte; a szerző ellenőrzése a végleges TR-F11 előtt szükséges.

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
