# AI-felhasználási nyilatkozat / AI-use disclosure

| | |
|---|---|
| **Projekt** | VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard |
| **Nyilatkozat verziója** | 1.0.0 (2026-11-02) |
| **Vonatkozik** | a `v1.0.0` kiadásra (Zenodo DOI: [10.5281/zenodo.23886002](https://doi.org/10.5281/zenodo.23886002)) és minden későbbi verzióra, amíg ez a fájl módosítatlan |

**🇭🇺 [Magyar](#magyar) | 🇬🇧 [English](#english)**

---

## Magyar

### Röviden

**Ez a projekt és minden eredménye mesterséges intelligenciával (MI) készített kísérlet.** A kódot, a kísérletek tervezését és
lefuttatását, az elemzést és a dokumentációt lényegében teljes egészében az Anthropic **Claude** nyelvi modelljei
(a Claude Code ügynökön keresztül) készítették, **Kormos Attila** irányításával és jóváhagyásaival. Az eredmények
**nem estek át független szakmai lektoráláson, és független replikáció sem történt.** A projekt eszköz- és
adatműtermék, nem lektorált tudományos eredmény.

### Ki mit végzett

| Feladat | MI (Claude) | Kormos Attila |
|---|---|---|
| Célkitűzés, az irány kiválasztása, a fázisok jóváhagyása | javaslatokat tett | **döntött** és jóváhagyott |
| Kód (`src/`, `scripts/`, `tests/`, `docker/`) | **megírta** | irányította, jóváhagyta a fázisokat |
| Kísérlettervezés (fázisterv, tesztterv, hipotézisek, elfogadási kritériumok) | **megírta** | jóváhagyta |
| Kísérletek lefuttatása szimulátoron és az IBM-hardveren | **lefuttatta** (a felhasználó engedélyével) | **biztosította az IBM-hozzáférést és a kvótát**, jóváhagyta a hardveres futtatást, és figyelmeztette a kvóta betartására |
| Elemzés, statisztika, értelmezés, ábrák | **elvégezte** | jóváhagyta |
| Dokumentáció, jegyzőkönyvek, README, hivatkozásjegyzék, szakirodalmi áttekintés | **megírta** | jóváhagyta |
| Kiadás (GitHub Release, Zenodo-fiók és -integráció), a szerzői lista | előkészítette | **elvégezte / eldöntötte** (a Zenodo-rekord szerzője csak Kormos Attila) |

### Milyen MI-modellek

A commitok `Co-Authored-By` sorai alapján (43 commit a `v1.0.0`-ig, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (23),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 korai commit nem tartalmaz ilyen sort**, ezért ott a modell nincs a
történetben rögzítve; a dokumentumok „Készítők" sora egységesen a „Claude AI (Anthropic, Claude Opus 5)" megnevezést
használja, ami **nem pontos** minden commitra. A pontos modell-hozzárendelés így nem rekonstruálható teljesen.

### Mi NEM történt meg (és mi nem ellenőrzött)

1. **Nincs független szakértői lektorálás** a fizikai/kémiai állításokról, a módszertanról vagy a kódról.
2. **Nincs külső replikáció.** A „külső személyes" telepítési próbát (TR-F09 AC-9.8) is az MI végezte ugyanazon a gépen.
3. **A szerző kódátnézésének mértékét ez a nyilatkozat nem állítja.** A fejlesztés a fázisonkénti jóváhagyásra épült, nem
   dokumentált soronkénti emberi átnézésre. Aki a kódot használja, ezt vegye figyelembe.
4. **A szakirodalmi pozicionálást** ([`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)) az MI végezte
   egy keresési menetben, kivonat- és metaadat-szinten; nem szisztematikus áttekintés, és a hivatkozott művek teljes
   szövegét senki nem olvasta végig.
5. **A hardveres eredmények** pontonként egyetlen futásúak egyetlen eszközön, kis molekulán (H₂). Általános következtetés
   nem vonható le belőlük.
6. **A tudományos újdonságot nem állítjuk.** Ismert módszerek reprodukálható együttes mérése; az őszinte értékelés a
   [`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)-ban olvasható.

### Dokumentált MI-hibák és javításuk

Az MI hibázott, és a hibák egy részét a saját ellenőrzései tárták fel. Ezek nyilvánosak:

- **v0.7.1 javítókör:** három mérési hiba (állandó mintavételi eltolás a „lövészajban"; a ZNE-hajtogatást a transzpiler
  részben kiejtette; a hardveres bizonytalanság és a mitigációs szint nem volt rögzítve). A korábban közölt ZNE-érték egy
  előzetes spike-ból származott, nem a leszállított kódból ([`CHANGELOG.md`](CHANGELOG.md), TR-F03).
- **CI piros volt a v0.9.0 óta** egy rosszul írt teszt miatt, amit helyben nem vettünk észre (TR-F09 4. pont).
- **Hibás licenc-felismerés** a `LICENSE` fájl miatt; **hibás `pyarrow` rögzítés**; **téves qubitszámok** a dokumentációban;
  egy **téves forrásmegjelölés** (a TREX-cikk folyóirata). Mind javítva, a CHANGELOG-ban és a jegyzőkönyvekben.

Az MI-vel készült szöveg további, itt fel nem tárt hibákat is tartalmazhat.

### Hol van ez jelölve

- [`README.md`](README.md): „Készítők" sor és az „MI-felhasználás" szakasz (HU/EN)
- [`CITATION.cff`](CITATION.cff): az `abstract` és a `message` mondata
- GitHub Release `v1.0.0` jegyzete
- [`docs/09_publishing.md`](docs/09_publishing.md): kötelező ellenőrzőpont a kiadásoknál
- a LICENSE szerzői sora az MI-t is nevesíti (jogi jelentősége nincs eldöntve)

> **A Zenodo-rekord leírása** csak a szerző Zenodo-fiókjában szerkeszthető (vagy új kiadással frissíthető); a rekord
> szerzőlistája a szerző döntése szerint csak Kormos Attila. Ezért a rekordnál az MI-használat a leírásban (és a
> kiadás jegyzetében) szerepeljen. Állapota: lásd a CHANGELOG-ot.

### Javasolt szöveg cikkbe / ajánlott hivatkozásmód

> *Az itt bemutatott szoftvert, kísérlettervet, számításokat és dokumentációt lényegében teljes egészében az Anthropic
> Claude nyelvi modelljei (Claude Sonnet 5.5, Claude Opus 5, Claude Opus 5.5; Claude Code ügynök) állították elő a
> szerző irányításával. A szerző határozta meg a célokat, jóváhagyta a lépéseket, biztosította az IBM Quantum
> hozzáférést és hozta a kiadási döntéseket. Független szakértői lektorálás és külső replikáció nem történt; az eredmények
> kis rendszerekre vonatkozó, nem lektorált mérések. A szakirodalmi áttekintés nem szisztematikus.*

---

## English

### In short

**This project and all of its results are an AI-assisted experiment.** The code, the design and execution of the experiments,
the analysis and the documentation were produced almost entirely by Anthropic's **Claude** language models (through the
Claude Code agent), under the direction and approval of **Attila Kormos**. The results have **not been independently
peer-reviewed or independently replicated.** The project is a tool and data artifact, not a peer-reviewed scientific result.

### Who did what

| Task | AI (Claude) | Attila Kormos |
|---|---|---|
| Goals, direction, approval of each phase | made proposals | **decided** and approved |
| Code (`src/`, `scripts/`, `tests/`, `docker/`) | **wrote it** | directed it; approved phases |
| Experimental design (phase plans, test plans, hypotheses, acceptance criteria) | **wrote it** | approved |
| Running experiments on simulators and IBM hardware | **ran them** (with the user's permission) | **provided IBM access and quota**, approved hardware runs, and instructed staying within the free quota |
| Analysis, statistics, interpretation, figures | **performed** | approved |
| Documentation, test reports, README, reference list, literature review | **wrote it** | approved |
| Release (GitHub Release, Zenodo account and integration), author list | prepared | **performed / decided** (the Zenodo record lists only Attila Kormos as author) |

### Which AI models

From the commit `Co-Authored-By` trailers (43 commits up to `v1.0.0`, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (23),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 early commits carry no such trailer**, so the model is not recorded
there; the documents' "Authors" lines uniformly say "Claude AI (Anthropic, Claude Opus 5)", which is **not accurate for
every commit**. The exact model attribution cannot be fully reconstructed.

### What was NOT done (and is not verified)

1. **No independent expert review** of the physics/chemistry claims, the methodology or the code.
2. **No external replication.** The "outside person" installation trial (TR-F09 AC-9.8) was also performed by the AI on the same machine.
3. **This statement does not claim any particular degree of line-by-line human code review.** Development relied on
   per-phase approval, not on documented line-by-line human review. Users of the code should take this into account.
4. **The literature positioning** ([`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)) was done by the AI
   in a single search pass at abstract/metadata level; it is not a systematic review, and nobody has read the full text of the cited works.
5. **The hardware results** are single runs per point on one device, for one small molecule (H₂). No general conclusion follows.
6. **No scientific novelty is claimed.** It is a reproducible joint measurement of known methods; the candid assessment is in
   [`docs/10_literature_positioning.md`](docs/10_literature_positioning.md).

### Documented AI errors and their fixes

The AI made mistakes, some of which its own checks uncovered. They are public:

- **v0.7.1 correction round:** three measurement errors (a constant sampling offset in "shot noise"; ZNE folding partly removed
  by the transpiler; hardware uncertainty and mitigation level not recorded). A previously reported ZNE value came from a
  preliminary spike, not from the shipped code ([`CHANGELOG.md`](CHANGELOG.md), TR-F03).
- **CI was red since v0.9.0** because of a badly written test that was not noticed locally (TR-F09 item 4).
- A **wrong license detection** due to the `LICENSE` file; a **wrong `pyarrow` pin**; **wrong qubit counts** in the docs; one
  **wrong source attribution** (the journal of the TREX paper). All fixed, recorded in the CHANGELOG and test reports.

AI-generated text may contain further errors not uncovered here.

### Where this is marked

- [`README.md`](README.md): the "Authors" line and the "AI use" section (HU/EN)
- [`CITATION.cff`](CITATION.cff): a sentence in `abstract` and `message`
- the GitHub Release `v1.0.0` notes
- [`docs/09_publishing.md`](docs/09_publishing.md): a mandatory checkpoint for releases
- the LICENSE copyright line names the AI as well (its legal significance has not been decided)

> **The Zenodo record description** can only be edited in the author's Zenodo account (or updated with a new release); per the
> author's decision the record's author list contains only Attila Kormos. The AI use should therefore be stated in the
> record's description (and in the release notes). Status: see the CHANGELOG.

### Suggested text for a paper / how to cite

> *The software, experimental design, computations and documentation presented here were produced almost entirely by
> Anthropic's Claude language models (Claude Sonnet 5.5, Claude Opus 5, Claude Opus 5.5; the Claude Code agent) under the
> author's direction. The author set the goals, approved the steps, provided the IBM Quantum access and made the release
> decisions. No independent expert review or external replication has taken place; the results are non-peer-reviewed
> measurements on small systems. The literature review is not systematic.*

---

*Készítők / Authors: Kormos Attila, Claude AI (Anthropic) — MIT licenc / MIT License*
