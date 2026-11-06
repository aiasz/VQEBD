# TR-F11 — Fázis 11 jegyzőkönyv (a Heron-zajmodell validálása) — ELŐZETES: B0 pilot, C1 és C2

| | |
|---|---|
| **Azonosító** | TR-F11 |
| **Dokumentum-verzió** | 0.3.0 (előzetes: B0 pilot + C1 + C2; a 6. szakasz a C1-et, a 7. a C2-t tartalmazza) |
| **Dátum** | 2026-11-02 (B0), 2026-11-04 (C1), 2026-11-06/07 (C2) |
| **Terv / tesztterv** | [`phase_11.md`](../plan/phase_11.md), [`TP-F11_heron_modell.md`](TP-F11_heron_modell.md) |
| **Kezdeményezte, irányította, engedélyezte** | Kormos Attila (a B0-t 2026-11-02-án, a C1-et 2026-11-04-én, a C2-t 2026-11-06-án külön jóváhagyta) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — a kódot és a szöveget az MI írta a szerző kérésére, lásd [`AI_DISCLOSURE.md`](../../AI_DISCLOSURE.md) |
| **Státusz** | **Előzetes.** A pilot (B0) és az első két megerősítő blokk (C1, C2) futott le; C3…C8 még nem. **A B0 nem megerősítő adat; a C1 és a C2 megerősítő, de csak két blokk** (n = 2): a blokk-közi szórás már becsülhető, de nagyon bizonytalanul, és a H1–H4 szerinti döntés belőle nem hozható (a terv szerint 8 blokk kell). |

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

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
