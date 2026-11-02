# AI-felhasználási nyilatkozat / AI-use disclosure

| | |
|---|---|
| **Projekt** | VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard |
| **Nyilatkozat verziója** | 1.1.0 (2026-11-02) |
| **Vonatkozik** | a `v1.0.0` kiadásra (Zenodo DOI: [10.5281/zenodo.23886002](https://doi.org/10.5281/zenodo.23886002)) és minden későbbi verzióra, amíg ez a fájl módosítatlan |

**🇭🇺 [Magyar](#magyar) | 🇬🇧 [English](#english)**

---

## Magyar

### Röviden

**Ez a projekt Kormos Attila kezdeményezése és irányítása alatt, mesterséges intelligenciával (MI) készített kísérlet.** Az
ötletet, a kérdést, az irányt és minden érdemi döntést a szerző adta; az IBM-hozzáférést, a kvótát és az MI-használat
költségét ő biztosította és viselte. A kódot, valamint a tervek és a dokumentáció szövegét az Anthropic **Claude** nyelvi
modelljei írták meg (a Claude Code ügynökön keresztül) — a szerző kérésére, az ő utasításai szerint és jóváhagyásával. Az MI
önállóan nem kezdeményezett semmit, és a szerző külön engedélye nélkül egyetlen hardveres futtatás sem indult. A végeredményért
a szerző felel. Az eredmények **nem estek át független szakmai lektoráláson, és független replikáció sem történt.** A projekt
eszköz- és adatműtermék, nem lektorált tudományos eredmény.

### Ki mit végzett

| Feladat | Kormos Attila (szerző) | MI (Claude) |
|---|---|---|
| Ötlet, kutatási kérdés, célkitűzés, irány | **kezdeményezte és kitűzte** | alternatívákat és javaslatokat adott |
| Döntések (fázisok, küszöbök, geometriák, kvótahatár, qubitpár, mit publikálunk, szerzői lista) | **döntött** | lehetőségeket, kockázatokat és számításokat adott a döntéshez |
| Erőforrások: IBM-fiók és -kvóta, az MI-használat költsége | **biztosította és viselte** | — |
| Kód (`src/`, `scripts/`, `tests/`, `docker/`) | **kérte, irányította, jóváhagyta**; közlése szerint kb. 80%-át soronként átnézte (önbevallás, lásd lent, 3. pont) | **megírta**, a szerző kérésére |
| Kísérlettervezés (fázisterv, tesztterv, hipotézisek, elfogadási kritériumok) | megadta a feladatot, **jóváhagyta, módosította** | megfogalmazta |
| Kísérletek lefuttatása szimulátoron és az IBM-hardveren | **blokkonként engedélyezte**, és előírta a kvóta betartását | lefuttatta az engedély és a kódba épített védelmek keretein belül |
| Elemzés, statisztika, ábrák, dokumentáció, jegyzőkönyvek, szakirodalmi áttekintés | jóváhagyta, ellenőrizte, javíttatta | **megírta** |
| Kiadás (GitHub Release, Zenodo-fiók és -integráció), a szerzői lista | **elvégezte / eldöntötte** (a Zenodo-rekord szerzője csak Kormos Attila) | előkészítette |
| Felelősség az eredményekért és a kiadásért | **a szerző** | — (eszközként nem vállalhat felelősséget) |

Az MI-t a szakmai kiadói gyakorlat (pl. COPE, ICMJE) szerint nem tekintjük szerzőnek, mert felelősséget nem vállalhat; ezért
nem szerepel a Zenodo szerzői listán. Mivel a kód és a szöveg nagy részét ő írta meg, a megvalósítót névvel és modellel
jelöljük.

### Milyen MI-modellek

A commitok `Co-Authored-By` sorai alapján (43 commit a `v1.0.0`-ig, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (23),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 korai commit nem tartalmaz ilyen sort**, ezért ott a modell nincs a
történetben rögzítve; a dokumentumok „Készítők" sora egységesen a „Claude AI (Anthropic, Claude Opus 5)" megnevezést
használja, ami **nem pontos** minden commitra. A pontos modell-hozzárendelés így nem rekonstruálható teljesen.

### Mi NEM történt meg (és mi nem ellenőrzött)

1. **Nincs független szakértői lektorálás** a fizikai/kémiai állításokról, a módszertanról vagy a kódról.
2. **Nincs külső replikáció.** A „külső személyes" telepítési próbát (TR-F09 AC-9.8) is az MI végezte ugyanazon a gépen.
3. **Emberi kódátnézés — a szerző közlése szerint a kód körülbelül 80%-át soronként átnézte** (2026-11-02, a munkamenetben
   elmondva). Ez **önbevallás**: nincs róla dokumentáció, és nem rögzített, melyik 80% (fájlok, sorok), ezért ez a nyilatkozat
   **nem állítja**, hogy a kód egésze vagy egy meghatározott része átnézett. Az átnézés nem független szakértői lektorálás.
   Aki a kódot használja, ezt vegye figyelembe.
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
- GitHub Release `v1.0.0` jegyzete és a Zenodo-rekord leírása
- [`docs/09_publishing.md`](docs/09_publishing.md): kötelező ellenőrzőpont a kiadásoknál
- a LICENSE szerzői sora az MI-t is nevesíti (jogi jelentősége nincs eldöntve)

> **A Zenodo-rekord** (`10.5281/zenodo.23886003`) leírásának elején ugyanez a jelölés szerepel (a szerző vezette be a Zenodo
> felületén, 2026-11-02). A rekord szerzőlistája a szerző döntése szerint csak Kormos Attila.

### Javasolt szöveg cikkbe / ajánlott hivatkozásmód

> *A kísérletet Kormos Attila kezdeményezte és irányította: ő határozta meg a kérdést, a célokat és a döntéseket, biztosította
> az IBM Quantum hozzáférést és az MI-használat költségét, jóváhagyta az egyes lépéseket és hozta a kiadási döntéseket. A
> szoftvert, a számításokat és a dokumentáció szövegét az Anthropic Claude nyelvi modelljei (Claude Sonnet 5.5, Claude Opus 5,
> Claude Opus 5.5; Claude Code ügynök) írták meg a szerző kérésére és utasításai szerint. Független szakértői lektorálás és
> külső replikáció nem történt; az eredmények kis rendszerekre vonatkozó, nem lektorált mérések. A szakirodalmi áttekintés
> nem szisztematikus.*

---

## English

### In short

**This project is an AI-assisted experiment, initiated and directed by Attila Kormos.** The idea, the question, the direction
and every substantive decision came from the author; the IBM access, the quota and the cost of the AI use were provided and
borne by the author. The code, and the text of the plans and documentation, were written by Anthropic's **Claude** language
models (through the Claude Code agent) — at the author's request, following the author's instructions and with the author's
approval. The AI initiated nothing on its own, and no hardware run started without the author's separate permission. The author
is responsible for the final result. The results have **not been independently peer-reviewed or independently replicated.**
The project is a tool and data artifact, not a peer-reviewed scientific result.

### Who did what

| Task | Attila Kormos (author) | AI (Claude) |
|---|---|---|
| Idea, research question, goals, direction | **initiated and set them** | offered alternatives and proposals |
| Decisions (phases, thresholds, geometries, quota limit, qubit pair, what to publish, author list) | **decided** | supplied options, risks and calculations for the decision |
| Resources: IBM account and quota, the cost of the AI use | **provided and bore them** | — |
| Code (`src/`, `scripts/`, `tests/`, `docker/`) | **requested, directed, approved**; per the author, ~80% was reviewed line by line (self-reported, see item 3 below) | **wrote it**, at the author's request |
| Experimental design (phase plans, test plans, hypotheses, acceptance criteria) | gave the task, **approved and amended** | drafted it |
| Running experiments on simulators and IBM hardware | **permitted each block**, and required staying within the quota | ran them within the permission and the guards built into the code |
| Analysis, statistics, figures, documentation, test reports, literature review | approved, checked, had errors fixed | **wrote it** |
| Release (GitHub Release, Zenodo account and integration), author list | **performed / decided** (the Zenodo record lists only Attila Kormos) | prepared |
| Responsibility for the results and the release | **the author** | — (as a tool it cannot take responsibility) |

By professional publishing practice (e.g. COPE, ICMJE) the AI is not treated as an author because it cannot take
responsibility; hence it is not on the Zenodo author list. Since it wrote most of the code and text, the implementer is named,
with the model.

### Which AI models

From the commit `Co-Authored-By` trailers (43 commits up to `v1.0.0`, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (23),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 early commits carry no such trailer**, so the model is not recorded
there; the documents' "Authors" lines uniformly say "Claude AI (Anthropic, Claude Opus 5)", which is **not accurate for
every commit**. The exact model attribution cannot be fully reconstructed.

### What was NOT done (and is not verified)

1. **No independent expert review** of the physics/chemistry claims, the methodology or the code.
2. **No external replication.** The "outside person" installation trial (TR-F09 AC-9.8) was also performed by the AI on the same machine.
3. **Human code review — according to the author, roughly 80% of the code was reviewed line by line** (stated in the session,
   2026-11-02). This is **self-reported**: it is not documented, and which 80% (files, lines) is not recorded, so this statement
   **does not claim** that all of the code, or any specific part of it, has been reviewed. The review is not an independent
   expert review. Users of the code should take this into account.
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
- the GitHub Release `v1.0.0` notes and the Zenodo record description
- [`docs/09_publishing.md`](docs/09_publishing.md): a mandatory checkpoint for releases
- the LICENSE copyright line names the AI as well (its legal significance has not been decided)

> **The Zenodo record** (`10.5281/zenodo.23886003`) carries the same marking at the start of its description (added by the
> author in the Zenodo interface, 2026-11-02). Per the author's decision the record's author list contains only Attila Kormos.

### Suggested text for a paper / how to cite

> *The experiment was initiated and directed by Attila Kormos, who set the question, the goals and the decisions, provided the
> IBM Quantum access and the cost of the AI use, approved each step and made the release decisions. The software, the
> computations and the text of the documentation were written by Anthropic's Claude language models (Claude Sonnet 5.5,
> Claude Opus 5, Claude Opus 5.5; the Claude Code agent) at the author's request and following the author's instructions. No
> independent expert review or external replication has taken place; the results are non-peer-reviewed measurements on small
> systems. The literature review is not systematic.*

---

*Szerző / Author: Kormos Attila · Megvalósítás MI-eszközzel / Implemented with an AI tool: Claude (Anthropic) — MIT licenc / MIT License*
