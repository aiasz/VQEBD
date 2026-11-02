# TP-F09 — Fázis 9 tesztterv (dokumentáció, validálás, publikálás)

| | |
|---|---|
| **Azonosító** | TP-F09 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 9 — Dokumentáció, validálás, publikálás |
| **Terv** | [`phase_09.md`](../plan/phase_09.md) |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |

---

## 1. Mit kell igazolni

1. **A GitHub-oldal rendben van:** zöld CI, felismert (MIT) licenc, közösségi fájlok.
2. **A publikáció géppel idézhető és konzisztens:** érvényes `CITATION.cff`, a verzió, a dátum, a BibTeX és a `CHANGELOG` egyezik.
3. **A README bejárata működik:** egy tiszta klónból, a parancsait szó szerint követve a rendszer felépül, lefut, és a
   dashboard elérhető.

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl / mód |
|---|---|---|---|
| **TC-901** | AC-9.1 | a GitHub CI minden jobja zöld a kiadási commiton; helyben mindkét tesztlépés reprodukálva (szállított image mount nélkül; repó `:ro` mounttal) | `gh run list` (push után), helyi futás |
| **TC-902** | AC-9.2 | a `LICENSE` szabványos MIT (cím, szerzői sor, a kanonikus törzs); nincs benne GPL/Mitiq/harmadik-fél-függelék; a `NOTICE` tartalmazza a Mitiq/GPL megjegyzést, a modulútvonalat, a lockot, az ADR-0003-at; a GitHub `licenseInfo.key` = `mit` | `tests/repo/test_publication.py`, `gh repo view` (push után) |
| **TC-903** | AC-9.3 | `cffconvert --validate` (CFF 1.2.0); a `version`, a `license` és a `date-released` egyezik a `VERSION`-nel és a `CHANGELOG` dátumával; angol leírás van | végrehajtás, `test_publication.py` |
| **TC-904** | AC-9.4 | `CONTRIBUTING.md`, `SECURITY.md`, 3 issue-sablon-fájl létezik; a README mindkét nyelven hivatkozik rájuk; a `SECURITY.md` nevezi a token-szabályokat és elérhetőséget ad; a `CONTRIBUTING.md` a valódi minőségi kapukat sorolja | `test_publication.py` |
| **TC-905** | AC-9.5 | a README-ben megvan a „Röviden" / „In short" blokk, a háromparancsos gyors indítás mindkét nyelven, a CI-jelvény; a parancsok létező szolgáltatásokat hívnak | `test_publication.py` |
| **TC-906** | AC-9.6 | az összes Markdown-fájl minden relatív hivatkozása létező fájlra mutat (> 100 hivatkozás ellenőrizve) | `test_publication.py` |
| **TC-907** | AC-9.7 | a README két kulcsverzió-táblázata (HU, EN) azonos egymással, és minden sora egyezik a `requirements.lock`-kal | `test_publication.py` |
| **TC-908** | AC-9.8 | tiszta klón + a README parancsai szó szerint: build, `python -m vqebd` (a példa kimenet 5 sora egyezik), `up -d dashboard` (`healthy`, HTTP 200, loopback) | végrehajtás |
| **TC-909** | AC-9.9 | a `VERSION`, a `CITATION.cff`, a Compose-címkék, a BibTeX (HU és EN) és a dokumentumok verziója egyezik; `docs/09_publishing.md` megvan, és a Zenodo-előfeltételt nevezi | `test_version_consistency.py`, `test_publication.py` |
| **TC-910** | AC-9.10 | a GitHub Release `v1.0.0` létezik; a Zenodo-DOI kiosztva és beírva | **jóváhagyással**, a Zenodo-kapcsoló után |

## 3. Negatív és robusztussági ellenőrzések

- A hivatkozás-ellenőrző **bizonyítottan működik**: a `TR-F09` hiányában valóban elbukott (a hiányzó fájlt nevezte meg).
- A licenc-teszt a **teljes** törzset hasonlítja a kanonikus szöveghez (szóköz-normalizálva), nem csak kulcsszavakat.
- A verziótáblázat-teszt mindkét nyelvi táblázatot, és a lockhoz való egyezést külön ellenőrzi.
- A BibTeX-teszt pontosan két bejegyzést vár (HU és EN).

## 4. Amit a terv nem fed

- **Független külső személy telepítési próbája:** a TC-908-at az asszisztens végzi, ugyanazon a gépen (TR-F09 4.).
- **A Zenodo felületének működése** (nem érhető el az asszisztens számára).
- Böngészős vizuális ellenőrzés, Windows- és macOS-specifikus telepítés.

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
