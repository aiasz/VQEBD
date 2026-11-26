# AI-felhasználási nyilatkozat / AI-use disclosure

| | |
|---|---|
| **Projekt** | VQEBD — Variational Quantum Eigensolver Benchmark & Dashboard |
| **Nyilatkozat verziója** | 1.2.1 (2026-11-26) |
| **Vonatkozik** | a `v1.0.0` és a `v1.1.0` kiadásra (Zenodo koncepció-DOI: [10.5281/zenodo.23886002](https://doi.org/10.5281/zenodo.23886002)) és minden későbbi verzióra, amíg ez a fájl módosítatlan |

**🇭🇺 [Magyar](#magyar) | 🇬🇧 [English](#english)**

---

## Magyar

### Röviden

**Ez a projekt Kormos Attila kezdeményezése és irányítása alatt, mesterséges intelligenciával (MI) készített kísérlet.** Az
irányt és minden érdemi döntést a szerző adta, a kérdéseket ő választotta ki (egyeseket — például a Fázis 11 kérdését — az MI által írt szakirodalmi
áttekintés vetett fel); az IBM-hozzáférést, a kvótát és az MI-használat
költségét ő biztosította és viselte. A kódot, valamint a tervek és a dokumentáció szövegét az Anthropic **Claude** nyelvi
modelljei írták meg (a Claude Code ügynökön keresztül) — a szerző kérésére, az ő utasításai szerint és jóváhagyásával. Az MI
javaslatokat tett (például a Fázis 11 kérdése és a kalibrációs-frissességi szabály megfogalmazása), de a szerző jóváhagyása nélkül semmit nem
hajtott végre, és a szerző külön engedélye nélkül egyetlen hardveres futtatás sem indult. A végeredményért
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
| Fázis 11: a menet közbeni problémák és döntések | **a szerző oldotta meg és döntötte el**: a megszakadt C6 lemondása és teljes újraindítása (a kísérlet egysége az ütemterv előtt); a 10 napos kalibrációs szünet miatti várakozás; a kiegészítő C9 javaslata; az IBM-támogatás értesítése | lehetőségeket, kockázatokat és számításokat adott, a döntéseket végrehajtotta, az IBM-levelet megfogalmazta |
| Fázis 11: ellenőrzés és átnézés | **a szerző végezte és rendelte el**: minden blokk egyenkénti jóváhagyása próbafuttatás után; a kiadás előtti alapos átnézés és adatvédelmi ellenőrzés; a végleges jegyzőkönyv átnézése nyolc kérdéssel (ezekből derült ki a szimmetrikus kiolvasás korlátja) | az ellenőrzéseket lefuttatta (független MI-ügynökökkel is), a talált hibákat javította, a kérdéseket megválaszolta |
| Kiadás (GitHub Release, Zenodo-fiók és -integráció), a szerzői lista | **elvégezte / eldöntötte** (a Zenodo-rekord szerzője csak Kormos Attila) | előkészítette |
| Felelősség az eredményekért és a kiadásért | **a szerző** | — (eszközként nem vállalhat felelősséget) |

Az MI-t a szakmai kiadói gyakorlat (pl. COPE, ICMJE) szerint nem tekintjük szerzőnek, mert felelősséget nem vállalhat; ezért
nem szerepel a Zenodo szerzői listán. Mivel a kód és a szöveg nagy részét az MI írta meg, a megvalósítót névvel és modellel
jelöljük.

### Milyen MI-modellek

A commitok `Co-Authored-By` sorai alapján (41 commit a `v1.0.0`-ig, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (21),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 korai commit nem tartalmaz ilyen sort**, ezért ott a modell nincs a
történetben rögzítve; a dokumentumok szerzői sora egységesen „Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic)" (a konkrét
modellt nem nevezi meg, mert az nem minden commitra rekonstruálható). A pontos modell-hozzárendelés így nem rekonstruálható teljesen.
A `v1.0.0` után a `v1.1.0` címkéig minden commit tartalmaz ilyen sort (Claude Sonnet 5.5 és Claude Opus 5.5); a kiadás előkészítéséig (`2aee690`)
34 commit: **Claude Sonnet 5.5** (24), **Claude Opus 5.5** (10); a pontos szám: `git log v1.0.0..v1.1.0`.

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
5. **A hardveres eredmények** egyetlen eszközön, kis molekulán (H₂) készültek: a Fázis 2 és az 5.H mérései pontonként egyetlen futásúak, a Fázis 11
   geometriánként 8 (+1) blokkot mért, egy qubitpáron. Általános következtetés nem vonható le belőlük.
6. **A tudományos újdonságot nem állítjuk.** Ismert módszerek reprodukálható együttes mérése; az őszinte értékelés a
   [`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)-ban olvasható.
7. **A Fázis 11 (`v1.1.0`)** tervét, kódját, statisztikai elemzését és jegyzőkönyvét is az MI írta; a hipotéziseket, a küszöböt és minden hardveres
   blokkot a szerző hagyta jóvá. **Független emberi statisztikus nem vett részt**, és a C9 előtti kódellenőrzést (TR-F11 14.3) is MI végezte (egy
   külön MI-ügynök) — ez nem emberi lektorálás. Külső előregisztráció nincs; a rögzítés a `protocol-f11-frozen` git-címke.

### Dokumentált MI-hibák és javításuk

Az MI hibázott, és a hibák egy részét a saját ellenőrzései tárták fel. Ezek nyilvánosak:

- **v0.7.1 javítókör:** három mérési hiba (állandó mintavételi eltolás a „lövészajban"; a ZNE-hajtogatást a transzpiler
  részben kiejtette; a hardveres bizonytalanság és a mitigációs szint nem volt rögzítve). A korábban közölt ZNE-érték egy
  előzetes spike-ból származott, nem a leszállított kódból ([`CHANGELOG.md`](CHANGELOG.md), TR-F03).
- **CI piros volt a v0.9.0 óta** egy rosszul írt teszt miatt, amit helyben nem vettünk észre (TR-F09 4. pont).
- **Hibás licenc-felismerés** a `LICENSE` fájl miatt; **hibás `pyarrow` rögzítés**; **téves qubitszámok** a dokumentációban;
  egy **téves forrásmegjelölés** (a TREX-cikk folyóirata). Mind javítva, a CHANGELOG-ban és a jegyzőkönyvekben.

- **Fázis 11 (`v1.1.0`):** a C8 egyik jobjának QPU-ideje hibásan (0 s) rögzült (TR-F11 13.2); a C9 előtti független MI-kódellenőrzés a futtatóban
  adatvesztéshez vezethető hibákat talált, a C9 előtt javítva (14.3); a kiadás előtti átnézés kiderítette, hogy a blokk utáni kalibrációs pillanatkép a
  gyorsítótárból származott (22.1), és hogy egy fizikai értelmezés („koherencia”, 21.2/6) és a TOST-eredmény egyes megfogalmazásai tévesek voltak (22.3); a C6 kalibráció-életkora először tévesen (66 h helyett 85,8 h) szerepelt (11.3);
  egy konfidencia-határ dupla kerekítéssel +7,5 lett +7,4 helyett (javítva); **a modell a kiolvasási hibát szimmetrikusnak vette** — ezt az MI a
  protokoll befagyasztása előtt nem vette észre, a szerző átnézési kérdése nyomán derült ki (TR-F11 18.11, 21.); és ez a nyilatkozat (1.2.0) a
  kiegészítő C9-et tévesen az MI javaslataként írta le — a szerző javasolta (1.2.1-ben javítva).

Az MI-vel készült szöveg további, itt fel nem tárt hibákat is tartalmazhat.

### Hol van ez jelölve

- [`README.md`](README.md): a szerzői sor és az „MI-felhasználás" szakasz (HU/EN)
- [`CITATION.cff`](CITATION.cff): az `abstract` és a `message` mondata
- a GitHub Release `v1.0.0` és `v1.1.0` jegyzete és a Zenodo-rekord leírása
- [`docs/09_publishing.md`](docs/09_publishing.md): kötelező ellenőrzőpont a kiadásoknál
- a `LICENSE` szerzői sora (copyright) csak Kormos Attila nevét tartalmazza; a README lábléce és a dokumentumok szerzői sora jelöli a megvalósítást végző MI-eszközt

> **A Zenodo-rekord** (`10.5281/zenodo.23886003`) leírásának elején ugyanez a jelölés szerepel (a szerző vezette be a Zenodo
> felületén, 2026-11-02). A rekord szerzőlistája a szerző döntése szerint csak Kormos Attila.

### Javasolt szöveg cikkbe / ajánlott hivatkozásmód

> *A kísérletet Kormos Attila kezdeményezte és irányította: ő határozta meg a kérdést, a célokat és a döntéseket, biztosította
> az IBM Quantum hozzáférést és az MI-használat költségét, jóváhagyta az egyes lépéseket és hozta a kiadási döntéseket. A
> szoftvert, a dokumentáció szövegét és a statisztikai elemzést az Anthropic Claude nyelvi modelljei (Claude Sonnet 5.5, Claude Opus 5,
> Claude Opus 5.5; Claude Code ügynök) készítették a szerző kérésére és utasításai szerint; a szimulátoros és — a szerző blokkonkénti
> engedélyével — a hardveres futtatásokat is az MI végezte. Független szakértői lektorálás, külső replikáció és független (emberi) statisztikai
> ellenőrzés nem történt; az eredmények kis rendszerekre vonatkozó, nem lektorált mérések. A szakirodalmi áttekintés
> nem szisztematikus.*

---

## English

### In short

**This project is an AI-assisted experiment, initiated and directed by Attila Kormos.** The direction and every substantive
decision came from the author, who also chose the questions (some, such as the Phase 11 question, were raised by the AI-written literature review); the IBM access, the quota and the cost of the AI use were provided and
borne by the author. The code, and the text of the plans and documentation, were written by Anthropic's **Claude** language
models (through the Claude Code agent) — at the author's request, following the author's instructions and with the author's
approval. The AI made proposals (for example the Phase 11 question and the wording of the calibration-freshness rule), but carried out nothing
without the author's approval, and no hardware run started without the author's separate permission. The author
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
| Phase 11: problems and decisions along the way | **solved and decided by the author**: cancelling and fully restarting the interrupted C6 (the integrity of the experiment before the schedule); waiting out the 10-day calibration gap; proposing the supplementary block C9; notifying IBM support | offered options, risks and calculations, carried out the decisions, drafted the IBM message |
| Phase 11: checking and review | **done and ordered by the author**: approving every block one by one after a dry run; ordering the thorough pre-release review and privacy check; reviewing the final report with eight questions (which revealed the symmetric-readout limitation) | ran the checks (also with independent AI agents), fixed the errors found, answered the questions |
| Release (GitHub Release, Zenodo account and integration), author list | **performed / decided** (the Zenodo record lists only Attila Kormos) | prepared |
| Responsibility for the results and the release | **the author** | — (as a tool it cannot take responsibility) |

By professional publishing practice (e.g. COPE, ICMJE) the AI is not treated as an author because it cannot take
responsibility; hence it is not on the Zenodo author list. Since it wrote most of the code and text, the implementer is named,
with the model.

### Which AI models

From the commit `Co-Authored-By` trailers (41 commits up to `v1.0.0`, 2026-09-22 … 2026-11-02): **Claude Sonnet 5.5** (21),
**Claude Opus 5** (3), **Claude Opus 5.5** (2). **15 early commits carry no such trailer**, so the model is not recorded
there; the documents' author lines uniformly say "Author: Kormos Attila · Implemented with an AI tool: Claude (Anthropic)" (without
naming a specific model, because that cannot be reconstructed for every commit). The exact model attribution cannot be fully reconstructed.
After `v1.0.0`, every commit up to the `v1.1.0` tag carries such a trailer (Claude Sonnet 5.5 and Claude Opus 5.5); up to the release preparation
(`2aee690`) there are 34 commits: **Claude Sonnet 5.5** (24), **Claude Opus 5.5** (10); the exact count: `git log v1.0.0..v1.1.0`.

### What was NOT done (and is not verified)

1. **No independent expert review** of the physics/chemistry claims, the methodology or the code.
2. **No external replication.** The "outside person" installation trial (TR-F09 AC-9.8) was also performed by the AI on the same machine.
3. **Human code review — according to the author, roughly 80% of the code was reviewed line by line** (stated in the session,
   2026-11-02). This is **self-reported**: it is not documented, and which 80% (files, lines) is not recorded, so this statement
   **does not claim** that all of the code, or any specific part of it, has been reviewed. The review is not an independent
   expert review. Users of the code should take this into account.
4. **The literature positioning** ([`docs/10_literature_positioning.md`](docs/10_literature_positioning.md)) was done by the AI
   in a single search pass at abstract/metadata level; it is not a systematic review, and nobody has read the full text of the cited works.
5. **The hardware results** come from one device and one small molecule (H₂): the Phase 2 and 5.H measurements are single runs per point; Phase 11
   measured each geometry in 8 (+1) blocks on one qubit pair. No general conclusion follows.
6. **No scientific novelty is claimed.** It is a reproducible joint measurement of known methods; the candid assessment is in
   [`docs/10_literature_positioning.md`](docs/10_literature_positioning.md).
7. **Phase 11 (`v1.1.0`):** its plan, code, statistical analysis and report were also written by the AI; the hypotheses, the threshold and every
   hardware block were approved by the author. **No independent human statistician was involved**, and the code review before C9 (TR-F11 14.3)
   was also done by AI (a separate AI agent) — this is not a human review. There is no external pre-registration; the protocol was fixed by
   the `protocol-f11-frozen` git tag.

### Documented AI errors and their fixes

The AI made mistakes, some of which its own checks uncovered. They are public:

- **v0.7.1 correction round:** three measurement errors (a constant sampling offset in "shot noise"; ZNE folding partly removed
  by the transpiler; hardware uncertainty and mitigation level not recorded). A previously reported ZNE value came from a
  preliminary spike, not from the shipped code ([`CHANGELOG.md`](CHANGELOG.md), TR-F03).
- **CI was red since v0.9.0** because of a badly written test that was not noticed locally (TR-F09 item 4).
- A **wrong license detection** due to the `LICENSE` file; a **wrong `pyarrow` pin**; **wrong qubit counts** in the docs; one
  **wrong source attribution** (the journal of the TREX paper). All fixed, recorded in the CHANGELOG and test reports.

- **Phase 11 (`v1.1.0`):** the QPU time of one C8 job was recorded wrongly (0 s; TR-F11 13.2); the independent AI code review before C9 found
  bugs in the runner that could have lost data, fixed before C9 (14.3); the pre-release review found that the post-block calibration snapshot came
  from a cache (22.1), and that one physical interpretation ("coherence", 21.2/6) and some wording of the TOST result were wrong (22.3); the calibration age of C6 was first stated wrongly (66 h instead of
  85.8 h; 11.3); one confidence bound was double-rounded to +7.5 instead of +7.4 (fixed); **the model treated the readout error as
  symmetric** — the AI did not notice this before the protocol was frozen; it emerged from the author's review questions (TR-F11 18.11, 21.); and this
  disclosure (1.2.0) wrongly attributed the supplementary block C9 to the AI — the author proposed it (fixed in 1.2.1).

AI-generated text may contain further errors not uncovered here.

### Where this is marked

- [`README.md`](README.md): the author line and the "AI use" section (HU/EN)
- [`CITATION.cff`](CITATION.cff): a sentence in `abstract` and `message`
- the GitHub Release `v1.0.0` and `v1.1.0` notes and the Zenodo record description
- [`docs/09_publishing.md`](docs/09_publishing.md): a mandatory checkpoint for releases
- the `LICENSE` copyright line names only Attila Kormos; the README footer and the documents' author lines mark the AI tool that did the implementation

> **The Zenodo record** (`10.5281/zenodo.23886003`) carries the same marking at the start of its description (added by the
> author in the Zenodo interface, 2026-11-02). Per the author's decision the record's author list contains only Attila Kormos.

### Suggested text for a paper / how to cite

> *The experiment was initiated and directed by Attila Kormos, who set the question, the goals and the decisions, provided the
> IBM Quantum access and the cost of the AI use, approved each step and made the release decisions. The software, the
> text of the documentation and the statistical analysis were produced by Anthropic's Claude language models (Claude Sonnet 5.5,
> Claude Opus 5, Claude Opus 5.5; the Claude Code agent) at the author's request and following the author's instructions; the AI also
> carried out the simulator runs and, with the author's block-by-block permission, the hardware runs. No independent expert review,
> external replication or independent (human) statistical check has taken place; the results are non-peer-reviewed measurements on small
> systems. The literature review is not systematic.*

---

*Szerző / Author: Kormos Attila · Megvalósítás MI-eszközzel / Implemented with an AI tool: Claude (Anthropic) — MIT licenc / MIT License*
