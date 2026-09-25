# ADR-0007 — Ismétlésen alapuló statisztikai módszertan és hibaköltségvetés

| | |
|---|---|
| **Azonosító** | ADR-0007 |
| **Cím** | Zajos eredmény = eloszlás: ismétlés, újramintavételezés, t-alapú CI, hibaköltségvetés |
| **Státusz** | **Elfogadott** |
| **Dátum** | 2026-09-25 |
| **Döntéshozók** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Érinti** | Fázis 5, 6, 7 (dashboard), 9 (publikálás) |
| **Függ** | [ADR-0004](ADR-0004-adattarolas.md), [ADR-0005](ADR-0005-determinizmus.md), [ADR-0006](ADR-0006-tobbplatformos-architektura.md) |
| **Bizonyíték** | TR-F01B 6., TR-F03 v1.1.0, [`phase_05.md`](../plan/phase_05.md) 2–3. fejezet, TR-F05 |

---

## Kontextus

A v0.7.1 javítókör kimérte, hogy a v0.7.0-ig minden zajos kiértékelés ugyanazt a
mintavételi eltolást kapta. A „lövészaj” így valójában állandó torzítás volt.
A javítás után a zaj kiértékelésenként független, és ez három, eddig rejtett
következménnyel jár:

1. **Egy zajos futás egyetlen minta.** 8192 lövésnél egy kiértékelés szórása
   ~11 mHa, a H₂ teljes korrelációs energiája 20.3 mHa. Egyetlen VQE-futás
   végeredménye egy széles eloszlásból húzott érték (TR-F01B 6.3: ugyanaz a
   konfiguráció +26.8 és −4.8 mHa-t is adott, más iterációs korláttal).
2. **Egyik kézenfekvő végső érték sem jó.** Az optimalizáló *visszaadott*
   értéke (SciPy COBYLA: a végpontban mért utolsó érték) egyetlen zajos húzás. A
   kiértékelési előzmények *minimuma* kiválasztási torzítást hordoz: a sok húzás
   közül a kedvezőt választja, és a variációs határ alá visz (H₂-n mérve:
   −20…−37 mHa).
3. **A bináris „kémiailag pontos-e?” jelző egyetlen zajos mintán értelmetlen**
   (L5: −4.0 ± 12.5 mHa — sem igazolni, sem cáfolni nem tudja).

A felhasználói követelmény kifejezetten kérdezi, hogy a több különböző teszt
hozzájárul-e a pontossághoz, és ha igen, miért és hogyan. A válaszhoz el kell
választani a két hibafajtát (ISO 5725-1:1994 szóhasználatával):

- **precizitás** — a véletlen hiba; független ismétléssel csökken;
- **helyesség** — a rendszeres hiba (torzítás); ismétléssel **nem** csökken.

## Döntés

### D1 — Minden zajos konfiguráció N független ismétlés

A batch-motor (`vqebd.batch`) a zajos cellákat **N** különböző mester-seeddel
futtatja (`master_seed + ismétlés`). A seedek determinisztikusak, így a teljes
eloszlás bitre reprodukálható (ADR-0005). Egzakt backenden az ismétlés tilos
(`BatchCell` validáció), mert bitre azonos eredményt adna.

### D2 — A végső energia független újramintavételezésből

Zajos szinten a végső energia **K friss kiértékelés átlaga** θ_opt-ban
(`VQEConfig.reestimate`). A kiértékelő RNG-je továbblép, így ezek a minták az
optimalizáció során látott húzásoktól függetlenek. Hatásuk: a végső érték
szórása √K-szor kisebb, mint az optimalizáló végértékéé, és nincs kiválasztás.
A rekord tárolja az optimalizáló végértékét, az előzmény-minimumot és az
újramintavételezett átlagot. Az előzmény-minimum és az átlag különbsége a
„minimumot közlő” stratégia **mért** kiválasztási torzítása.

### D3 — Student-t alapú konfidencia-intervallum

A csoport (azonos konfiguráció, N seed) átlagára 95%-os, **t-eloszlás alapú**
CI-t számolunk [student1908]. N = 10-nél `t₀.₉₇₅ = 2.26` a normális 1.96-jával
szemben, vagyis a z-alapú CI ~13%-kal szűkebb lenne a helyesnél. A tényleges
lefedettséget egységteszt méri (4000 kísérlet, N = 5: 95 ± 1.5%).

Nehéz farkú eloszlásnál (az exponenciális ZNE-extrapoláció, TR-F03 3.) a t-CI
félrevezető lehet. Ezért a medián és a kvartilisek is tárolódnak, a jegyzőkönyv
pedig jelzi az ilyen eseteket.

### D4 — Négyállapotú kémiai pontossági besorolás

| Besorolás | Feltétel |
|---|---|
| `confirmed` | a hiba teljes CI-je a ±1.6 mHa sávon belül |
| `consistent` | a CI metszi a sávot |
| `excluded` | a CI teljesen a sávon kívül |
| `undetermined` | egyetlen **zajos** minta (nincs becsülhető bizonytalanság) |

Egzakt backend egyetlen értékénél a CI pontra fajul, így az eredmény
`confirmed`/`excluded`, ami helyes.

### D5 — Hibaköltségvetés a referencialánc szintjeiből

A teljes hiba teleszkópikus felbontása: **csonkolás** (CASCI − FCI), **leképezés**
(L1 − CASCI), **ansatz** (L2 − L1) és **zaj-torzítás** (átlag(zajos) − L2). A
**statisztikus hiba** (SEM) nem additív tag, hanem a torzítás bizonytalansága. A
tagok összege a teljes hiba; ezt teszt ellenőrzi.

### D6 — Platformok között nem átlagolunk

A platformdimenzió (ADR-0006) **validáció**, nem ismétlés. A Qiskit ↔ Cirq hiba
korrelált (2·10⁻¹⁵), a qsim-é szisztematikus (`complex64`). Átlagolásuk
precizitásnyereséget színlelne, ami nem létezik.

## Következmények

### Pozitív

- A „hozzájárul-e a több teszt a pontossághoz?” kérdés dimenziónként, **mért**
  választ kap (`phase_05.md` 3. fejezet, fig08). Az ismétlés a precizitást
  javítja, a független módszerek a helyességet teszik mérhetővé.
- A zajos eredmények összehasonlíthatók: minden szám mellett ott van az N, a
  szórás, a SEM és a CI.
- A kiválasztási torzítás mérhető (és a VQEBD eleve nem követi el), a végső
  érték szórása pedig √K-szorosan csökken.

### Negatív / költség

- **Futásidő:** N × (optimalizálás + K újramintavétel). H₂-re N = 20, K = 16 mellett
  futásonként ~5–7 s (zajos) a ~0.3 s helyett.
- **Hardveren drága:** N ismétlés N-szeres QPU-kvótát jelent. Hardveren ezért az
  ismétlésszámot a kvótaterv határozza meg (`phase_05.md` 6.4), és a jegyzőkönyv
  közli, ha N = 1 (`undetermined`).

### Felülvizsgálati feltétel

- Ha a Fázis 6-ban Sampler-alapú (valódi lövéseket számoló) becslő kerül be, a
  kiértékelésenkénti szórás a Pauli-varianciából adódik, nem a `precision`
  konvencióból. A D2–D4 változatlan marad, de a σ értéke változik.

## Hivatkozások

- [student1908] — a t-eloszlás
- [wecker2015], [mcclean2016] — a VQE mérési költsége és a lövészaj skálázása
- ISO 5725-1:1994 — *Accuracy (trueness and precision) of measurement methods
  and results — Part 1: General principles and definitions*
- Mért bizonyíték: TR-F01B 6., TR-F03 v1.1.0, TR-F05

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
