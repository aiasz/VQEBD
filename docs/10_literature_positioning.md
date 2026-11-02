# Szakirodalmi pozicionálás — hol áll a VQEBD a hasonló VQE- és hibaenyhítési benchmarkok között

| | |
|---|---|
| **Dokumentum** | `docs/10_literature_positioning.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Hivatkozások** | [`docs/references.md`](references.md) 1.2.0 — a szögletes zárójeles kulcsok oda mutatnak |
| **Státusz** | **Szisztematikus áttekintés NEM készült** — lásd az 1. fejezetet |

---

## 1. Mit jelent ez a dokumentum, és mit nem

**Mit jelent.** A projekt a `v1.0.0`-ig a szakirodalmat csak az alapmódszerekhez (VQE, ZNE, TREX, leképezések,
optimalizálók) használta. A tágabb kérdést — *mit tudunk már a VQE- és hibaenyhítési benchmarkokról, és mihez képest
állít bármit is a VQEBD* — a szerző nem vizsgálta meg. Ez a dokumentum ezt pótolja.

**Hogyan készült.** 2026-11-02-án, célzott keresésekkel (webes keresés, az arXiv API, a Crossref és a DataCite REST API).
A hivatkozott tételek **mindegyike** DOI-val azonosítható és gépileg ellenőrzött ([`references.md`](references.md)
módszertani megjegyzés): a szerzők, a cím és az évszám a regisztrált metaadatból származik, nem emlékezetből.

**Mit nem jelent — korlátok, amelyeket komolyan kell venni:**

| # | Korlát |
|---|---|
| S1 | **Nem szisztematikus áttekintés.** Nincs előre rögzített keresési protokoll, nincs kizárási/bekerülési kritérium, nincs két független értékelő (PRISMA-szerű eljárás). A találatok **egy** keresési menet eredményei. |
| S2 | **A hiányból nem következik a hiány.** Ha egy dolgot nem találtunk meg, az nem bizonyítja, hogy nincs. Az alábbi „nem találtunk” állítások kizárólag erre a keresésre vonatkoznak. |
| S3 | **Kivonat- és metaadat-szintű olvasás.** A tételek többségénél a címet, a kivonatot (abstract) és a regisztrált metaadatot használtuk, **nem a teljes szöveget**. Az eredmények részleteit (módszer, korlátok, statisztika) ezért nem értékeljük, csak azt állítjuk, amit a kivonat kimond. |
| S4 | **Preprintek.** A `[majumdar2023]`, `[belaloui2025]`, `[aharonov2025]`, `[illesova2025]`, `[novak2025]`, `[bautra2026]`, `[cosentino2026]` és `[koster2026]` arXiv-preprint: **nem lektorált**, tartalmuk még változhat. A `[lall2025]` poszterkivonat, a `[ji2026]` folyóiratcikk-metaadattal szerepel; egyiket sem olvastuk végig. |
| S5 | **Az asszisztens (MI) állítja össze.** A keresést és az összefoglalót az MI végezte; a szerző nem ellenőrizte a forrásokat egyenként. Az [`AI_DISCLOSURE.md`](../AI_DISCLOSURE.md) ezt részletezi. **Publikációba szánt szövegben minden itt hivatkozott művet emberi szakértőnek kell elolvasnia, mielőtt idézi.** |
| S6 | Időbeli hatókör: a keresés a 2026. november eleji állapotot tükrözi. |

---

## 2. A kérdések, amelyekre a keresés irányult

1. Vannak-e **VQE-benchmarkok**, amelyek a hibát forrásaira bontják, és valódi hardveren is mérnek?
2. Mit tudunk a **hibaenyhítés (ZNE, TREX) VQE-n való összehasonlításáról** valódi IBM-eszközökön?
3. Mit tudunk a **zajos optimalizálásról** és a **kiválasztási torzításról** (a legjobb iteráció közlése)?
4. Reprodukálja-e a **kalibrációból épített zajmodell** a valódi hardver eredményét? (A tervezett Fázis 11 alapkérdése.)
5. Milyen **benchmark-platformok és reprodukálhatósági mérések** léteznek, és hová illik a VQEBD?

---

## 3. Amit a szakirodalom már tud — és amit a VQEBD ezért **nem** állíthat újnak

| Téma | Ismert (forrás) | Következmény a VQEBD-re |
|---|---|---|
| A VQE mint NISQ-algoritmus, nyitott kérdései | Áttekintések: `[cerezo2021]` (variációs kvantumalgoritmusok), `[bharti2022]` (NISQ-algoritmusok), `[preskill2018]` (a NISQ-korszak fogalma); a molekuláris VQE-hez `[peruzzo2014]`, `[kandala2017]`, `[tilly2022]`, `[mcardle2020]` | A VQEBD **nem új módszert** javasol, hanem ismert módszereket mér együtt, reprodukálható keretben. |
| ZNE és hibaenyhítés hardveren | `[temme2017]`, `[li2017]`, `[kandala2019]` (hibaenyhítés zajos processzoron), `[endo2018]`, `[kim2023]` | A ZNE ötlete és hardveres alkalmazhatósága ismert. A VQEBD ISA-biztos ZNE-je **implementációs** megoldás (ADR-0003), nem új módszer. |
| Digitális ZNE gyakorlata | `[majumdar2023]` (preprint): bevált gyakorlatok a zajerősítéstől az extrapolációig és más módszerekkel való kompozícióig, szimulátoron és valódi hardveren | A VQEBD azon megfigyelése, hogy az extrapolátor választása a lövésszámtól függ (az egyetlen futás szórását az extrapoláció felnagyítja), **ebbe a bevált gyakorlati körbe tartozik**; nem állítjuk, hogy új. |
| TREX / kiolvasási hibaenyhítés | `[vandenberg2022trex]` (a módszer eredeti közleménye, az IBM Runtime *resilience 1* alapja); `[belaloui2025]` (preprint): kis molekulákon a TREX-szel enyhített régebbi 5 qubites eszköz egy nagyságrenddel pontosabb energiát adott, mint a nem enyhített 156 qubites IBM Fez, és a **paraméterek** minőségét is javította | A VQEBD hardveres mérései (TREX: +5…+18 mHa a nyers +12…+28 mHa helyett) **irányban egyeznek** azzal, hogy a kiolvasási hibaenyhítés sokat segít. Mértékben nem hasonlítjuk össze: más eszköz, más molekula, más protokoll. |
| Ellenpont a ZNE heurisztikus voltára | `[aharonov2025]` (preprint): a ZNE gyors, de „nincs pontossági garanciája", a PEC torzítatlan, de költséges; a szerzők saját módszert (QESEM) javasolnak. Lásd még `[vandenberg2023]` (PEC), `[cai2023]` (áttekintés) | Fenntartás: a VQEBD-ben mért ZNE-torzítás **szimulált zajmodellre** vonatkozik (L4), nem hardverre; hardveres ZNE-állítást nem teszünk. |
| Optimalizálók VQE-n | `[bonetmonroig2023]` (gradiensmentes optimalizálók kis molekulákon), `[singh2023]` (optimalizálók összehasonlítása kvantumkémiai VQA-ban, zajos szimulátoron is), `[illesova2025]` (preprint): nyolc optimalizáló H₂, H₄, LiH-n; a **véges lövésszám átrendezi az optimalizálók sorrendjét** | A VQEBD **nem optimalizáló-benchmark** (COBYLA, Powell, SLSQP szerepel, de nem ez a fókusz). Az optimalizáló-rangsor zajfüggése ismert eredmény. |
| Kiválasztási torzítás / „winner's curse" | `[novak2025]` (preprint): a véges lövészaj hamis minimumokat és „winner's curse" torzítást okoz; a javasolt korrekció a populációátlag követése. `[li2023kitaev]`: a mért energia a lövészaj miatt az alapállapot **alá** eshet | A VQEBD ADR-0007-ben és a TR-F05-ben mért kiválasztási torzítása (az előzmény-minimum 25–34 mHa-val alacsonyabb a friss átlagnál) **ismert jelenség független megerősítése**, nem új felfedezés. A VQEBD gyakorlati hozzájárulása: ez a torzítás itt *mérve és a hibaköltségvetésben szétválasztva* szerepel, és a rendszer a friss kiértékelést közli. |
| Zaj okozta tanulhatatlanság | `[wang2021]`: zaj okozta barren plateau a mély áramkörökben | Az UCCSD LiH (2e,3o) zajos +466 mHa-s hibáját (mélységi fal) **nem** ezzel az eredménnyel magyarázzuk bizonyítottan; a kapcsolat csak irányadó hipotézis. |

---

## 4. A zajmodell–hardver kérdés (a tervezett Fázis 11 alapja)

A VQEBD L3b szintje egy **archivált kalibrációjú** `FakeManilaV2` zajmodellt használ, az L5 pedig az `ibm_kingston` QPU-t.
A két szint **nem ugyanaz az eszköz**, ezért a hardver–szimuláció eltérésből nem lehet zajmodell-hibát leolvasni
(TR-F05 7.). A kérdés, hogy a *jelenlegi kalibrációból épített* Heron-zajmodell reprodukálja-e a hardver görbéjét.

Amit a keresés ehhez talált:

- `[bautra2026]` (preprint): kalibrációból épített „digitális ikreket" hasonlít össze az IBM QPU-kon mért kimenetekkel
  (`ibm_brisbane`, `ibm_sherbrooke`), véletlen ötqubites áramkörökön, különböző transzpilálási szinteken, négy
  ikervariánssal, közös protokollal, és a kimeneteloszlások hasonlóságát (súlyozott Jaccard) méri. **Más feladat és más
  mérőszám**, mint a VQE energiahiba, és nem Heron r2.
- `[ji2026]`: adathatékony zajmodellezés — a kivonat szerint a hagyományos modellek gyakran nem fogják meg a valódi
  hardver összetett hibadinamikáját, ezért paraméterezett zajmodellt tanítanak (Bayes-optimalizálással) kísérleti
  adatból. Ez **közvetetten** jelzi, hogy a kalibrációból épített modell és a tényleges zaj eltérhet; a kalibrációs
  modellek Heron-validálását nem ez a mű végzi.

**Következtetés (óvatos).** Ebben a keresésben **nem találtunk** olyan művet, amely egy kalibrációból épített *Heron*
zajmodellt a *VQE-energiahibán* mérne valódi hardverhez *kiolvasási hibával együtt* (S2 érvényes). Ez azt jelenti, hogy a
Fázis 11 kérdése nyitottnak *látszik*, nem azt, hogy az. Az előzetes, **felderítő** eredményünk (egyetlen kalibráció,
öt geometria, nem előre regisztrált teszt): a kiolvasást modellező becslő a hardver nyers görbéjét mind az 5 pontban
1,2σ-n belül adta, a kiolvasást nem modellező Aer-becslő viszont nem. Ez **hipotézis-generáló**, nem megerősítő; a
megerősítő mérés a [`phase_11.md`](plan/phase_11.md) feladata.

---

## 5. Benchmark-platformok és reprodukálhatóság

| Mű | Mit állít (a kivonat szerint) | Viszony a VQEBD-hez |
|---|---|---|
| `[lubinski2023]` | Alkalmazás-orientált kvantum-benchmarkok | A VQEBD **egy alkalmazás** (VQE) hibáját bontja, nem eszközt rangsorol. |
| `[cross2019]`, `[blumekohout2020]` | Kvantumkötet; a benchmarkok értelmezési problémái | A VQEBD nem eszközmetrika. |
| `[cirstoiu2023]` | A hibaenyhítés *volumetrikus* benchmarkolása (Qermit) valódi eszközökön | Rokon cél (hibaenyhítés mérése valódi eszközön); más módszertan és szoftver. A VQEBD saját mérései kisebb léptékűek. |
| `[cosentino2026]` (preprint) | Metriq: nyílt, együttműködő platform platformok közötti benchmarkolásra | A VQEBD eredményei szabad formátumban (SQLite/JSON/CSV) vannak; **Metriq-kompatibilitás nincs vizsgálva.** |
| `[lall2025]` | Kvantumszámítógép-metrikák és -benchmarkok áttekintése; a rekord egy **poszter** kivonata, amely egy korábbi cikket mutat be (a metrikák változatai eltérnek, és a közölt adat gyakran nem elég a mérés reprodukálásához) | Térkép a tágabb tájról; a VQEBD besorolása ebben nincs elvégezve. |
| `[koster2026]` (preprint) | Nagy léptékű elemzés a kvantumszámítási kutatás reprodukálhatóságáról: 127 cikk kézi, közel 5000 gépi értékelése kódelérhetőség, környezet, dokumentáció, hardverleírás és futtathatóság szerint | A VQEBD ezeket a szempontokat tudatosan célozza (rögzített lock, Docker, nyilvános kód, DOI), de **nem végeztünk saját mérést** arra, hogy a mi cikkünk hogyan teljesít a szerzők kérdőívén. |

---

## 6. Összegzés — hová illik a VQEBD

**Amit a VQEBD nem állít.**

1. Nem új hibaenyhítési, optimalizálási vagy leképezési módszer.
2. Nem eszköz-benchmark és nem platform-rangsor.
3. A hardveres eredmények **pontonként egyetlen futás** egyetlen eszközön, egy kis molekulán (H₂); általános
   következtetés nem vonható le.
4. A projekt nem esett át külső szakmai lektoráláson, és független replikáció sem történt (lásd az
   [`AI_DISCLOSURE.md`](../AI_DISCLOSURE.md)-t).

**Amit a VQEBD ajánl** (a fenti korlátokkal):

1. **Egyetlen, reprodukálható keretben** (rögzített lock, Docker, determinisztikus seedek) méri ugyanazt a feladatot
   az egzaktól a valódi hardverig, és a hibát forrásaira bontja.
2. A független irodalomban leírt jelenségeket (a lövészaj-függő optimalizáló-sorrend, a kiválasztási torzítás, a
   kiolvasási hibaenyhítés haszna) **ugyanabban a keretben, számszerűen** reprodukálja.
3. A negatív és a kellemetlen eredményeket (nincs kémiai pontosság zajosan; a javított mérési hibák története) nyíltan
   dokumentálja.

**Ami a keresés alapján ténylegesen nyitottnak látszik** (S2 fenntartásával): a kalibrációból épített Heron-zajmodell
kiolvasási hibával együtti validálása VQE-energián. Ez a tervezett Fázis 11 tárgya.

**Publikálás előtt kötelező:** (a) tényleges, szisztematikus keresés (előre rögzített protokoll), (b) a hivatkozott művek
teljes szövegének emberi elolvasása, (c) szakértői megerősítés arról, hogy a „nyitottnak látszik" állítás helyes.

---

## 7. Hogyan frissíthető

Új tétel: `scripts/gen_references.py` `ENTRIES` listája (DOI-val) → `python scripts/gen_references.py` → ez a dokumentum
bővítése. A `tests/repo/test_literature_and_disclosure.py` ellenőrzi, hogy minden itt használt hivatkozáskulcs létezik a jegyzékben, és hogy a
dokumentum kimondja a saját korlátait (S1–S6).

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
