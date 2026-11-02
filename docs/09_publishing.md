# 09 — Kiadás és publikálás: GitHub Release, Zenodo, DOI (Fázis 9)

| | |
|---|---|
| **Dokumentum** | `docs/09_publishing.md` |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Projektverzió** | 1.0.0 |
| **Szerző** | Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) |
| **Fázis** | 9 — Dokumentáció, validálás, publikálás |
| **Háttér** | [`phase_09.md`](plan/phase_09.md) · [`TR-F09`](testing/TR-F09_publikalas.md) |

---

## 1. Mit jelent a „kiadás"?

Egy **GitHub Release** egy címkézett (`vX.Y.Z`) pillanatkép a forráskódról, kiadási jegyzettel. A **Zenodo** minden
GitHub Release-t automatikusan **archivál**, és **DOI-t** (állandó, idézhető azonosítót) ad neki. A DOI két fajtája:

| DOI | Mire mutat | Mikor használd |
|---|---|---|
| **Koncepció-DOI** | a projekt *összes* verziójára (mindig a legfrissebbet oldja fel) | általános hivatkozás, README-jelvény |
| **Verzió-DOI** | egyetlen kiadás pontos pillanatképére | ha egy konkrét eredményt akarsz reprodukálhatóan idézni |

> **A Zenodo-archívum állandó és nyilvános; a DOI nem törölhető.** Egy GitHub Release törölhető, a Zenodo-rekord fájljai
> viszont nem. Ezért a kiadás előtti ellenőrzőlista (3. pont) nem formaság.

## 2. Egyszeri előkészítés (a felhasználó teendője)

A Zenodo-integrációt a **saját Zenodo-fiókodban** kell bekapcsolni, **a release előtt**. Ezt az asszisztens nem végezheti el.

1. Lépj be a <https://zenodo.org> oldalra a **GitHub-fiókoddal** (*Log in → GitHub*), és engedélyezd a hozzáférést.
2. A fiókmenüben nyisd meg a **GitHub** oldalt (*Account → GitHub*), nyomd meg a **Sync now** gombot.
3. Keresd meg a **`aiasz/VQEBD`** repót, és kapcsold **BE** a mellette lévő kapcsolót.

*Ezt az útvonalat az asszisztens **nem tudta ellenőrizni** (nincs hozzáférése a Zenodóhoz): emlékezetből és a Zenodo
GitHub-integrációjának általános működése alapján írtuk le. A felület változhat; ha az útvonal eltér, a fiókbeállításokban a
„GitHub" integrációt keresd.*

**Fontos:** a Zenodo csak a kapcsoló bekapcsolása **után** létrehozott release-eket archiválja. Egy korábban kiadott
release-t a kapcsoló nem archivál utólag.

### 2.1 Mit olvas a Zenodo a metaadathoz?

A repó gyökerében lévő [`CITATION.cff`](../CITATION.cff)-et (érvényes CFF 1.2.0; a `cffconvert --validate` igazolja).
A belőle képzett rekord: cím, szerzők, kétnyelvű leírás, kulcsszavak, MIT licenc, a verzió és a kiadás dátuma. A két
döntés, amelyet **a kiadás előtt** el kell dönteni, mert a rekordban utólag nehezen javítható:

- **Szerzők.** A `CITATION.cff` egyetlen szerzőt sorol fel: *Kormos Attila* (**a felhasználó döntése, 2026-11-02**: az AI nem
  szerepel a Zenodo-rekord szerzői között). A Zenodo ezt a listát a rekord szerzőiként jeleníti meg. Az AI közreműködése
  a README és a dokumentumok „Készítők" soraiban, valamint a `LICENSE` szerzői sorában továbbra is szerepel; ha ezt is
  egységesíteni kell, az külön döntés.
- **ORCID.** Ha van ORCID-azonosítód, a `CITATION.cff`-ben a szerzőhöz add meg (`orcid: "https://orcid.org/…"`), hogy a
  rekord hozzád kapcsolódjon.

## 3. Kiadás előtti ellenőrzőlista

| # | Mit ellenőrizz | Hogyan |
|---|---|---|
| 1 | A kiadási commiton a **GitHub CI minden jobja zöld** | `gh run list --limit 3` vagy a repó *Actions* oldala |
| 2 | A `VERSION`, a `CITATION.cff`, a `CHANGELOG.md`, a Compose-címkék és a dokumentumok egyező verziót mutatnak | `tests/repo/test_version_consistency.py`, `tests/repo/test_publication.py` |
| 3 | A teljes tesztkészlet zöld a szállított image-ben **és** a repóval | a CI két tesztlépése (`.github/workflows/ci.yml`) |
| 4 | A GitHub a licencet MIT-ként ismeri fel | `gh repo view --json licenseInfo` → `"key":"mit"` |
| 5 | A README-alapú telepítés működik egy tiszta klónból | `TR-F09` 3. pont |
| 6 | A Zenodo-kapcsoló **be van kapcsolva** (2. pont) | zenodo.org → GitHub |
| 7 | A szerzői lista és az ORCID rendben (2.1) | `CITATION.cff` |
| 8 | A `CHANGELOG.md` `[X.Y.Z]` szakasza a kiadási jegyzet | lásd 4. pont |
| 9 | **Az MI-használat jelölve van**: a kiadási jegyzet első sora, a README, a `CITATION.cff` és a Zenodo-rekord leírása hivatkozik az [`AI_DISCLOSURE.md`](../AI_DISCLOSURE.md)-re; a nyilatkozat a valós állapotot tükrözi (mi nem ellenőrzött) | `tests/repo/test_publication.py`; a Zenodo-leírást a szerző állítja a Zenodo felületén |
| 10 | Ha új hivatkozás vagy állítás került a pozicionálásba: a `docs/references.md` újragenerálva, a [`10_literature_positioning.md`](10_literature_positioning.md) korlátai (S1–S6) érvényesek | `python scripts/gen_references.py` |

## 4. A release létrehozása

A címkét a `git tag -a vX.Y.Z -m "…"` hozza létre (a repóban már megvan, és a `git push --tags` felviszi). A GitHub Release a
`CHANGELOG.md` megfelelő szakaszából készül:

```bash
# a [X.Y.Z] szakasz kinyerése a kiadási jegyzetnek (a következő "## [" sorig)
awk '/^## \[1.0.0\]/{f=1;next} /^## \[/{f=0} f' CHANGELOG.md > release-notes.md

gh release create v1.0.0 --title "VQEBD v1.0.0" --notes-file release-notes.md --verify-tag
```

A `--verify-tag` biztosítja, hogy a címke már a távoli repóban legyen. A release létrejötte után a Zenodo általában rövid időn belül
archiválja, és megjelenik a DOI (a pontos idő a Zenodo terheltségétől függ). Az ellenőrzés: zenodo.org → *Uploads*, vagy a GitHub release oldalon a Zenodo-jelvény.

## 5. A DOI beírása

A DOI kiosztása **után** (nem előtte; előre nem ismert):

1. **`CITATION.cff`:** add hozzá a koncepció-DOI-t:

   ```yaml
   doi: "10.5281/zenodo.XXXXXXX"          # koncepció-DOI (a projekt minden verziójára)
   identifiers:
     - type: doi
       value: "10.5281/zenodo.XXXXXXX"
       description: "Zenodo, az összes verzió"
   ```

2. **`README.md`:** cseréld a „A Zenodo DOI a `v1.0.0` kiadás után kerül ide" mondatot a DOI-jelvényre és a hivatkozásra
   (mindkét nyelvi szakaszban):

   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
   ```

3. Commit: `docs: Zenodo DOI beírása (10.5281/zenodo.XXXXXXX)`. **Új címkét nem kell tenni:** a DOI a már kiadott verzió
   utáni dokumentációs frissítés; a következő kiadás már tartalmazza.

## 6. Későbbi kiadások

Minden új GitHub Release a Zenodóban **új verzióként** archiválódik ugyanazon koncepció-DOI alatt. Kiadás előtt:

1. frissítsd a `VERSION`-t, a `CITATION.cff` `version` és `date-released` mezőjét, a Compose-címkéket és a `CHANGELOG`-ot
   (a `test_version_consistency` és a `test_publication` jelzi az elcsúszást);
2. futtasd a 3. pont ellenőrzőlistáját;
3. hozd létre a címkét és a release-t (4. pont).

A szemantikus verziózás szerint a **MINOR** a fázislezárásoknál lép (mesterterv 8.1); törés esetén **MAJOR**.

## 7. Ha hiba derül ki a kiadás után

| Eset | Teendő |
|---|---|
| Elírás a dokumentációban | javítás `main`-en; a következő kiadásban megjelenik |
| Hibás metaadat a Zenodo-rekordban (szerző, leírás) | a Zenodo-rekord metaadata **szerkeszthető** a zenodo.org-on; a fájlok nem |
| Kritikus kódhiba | javítás, `PATCH` kiadás (`vX.Y.Z+1`), a `CHANGELOG`-ban a hiba nyílt rögzítésével; a régi release-t a GitHubon *Pre-release*-re lehet állítani, de a Zenodo-archívum megmarad |
| Véletlenül kiszivárgott token | azonnal **vond vissza** az IBM Cloud konzolon (a `SECURITY.md` szerint); a Zenodo-archívumból a fájl nem törölhető, ezért a kiadás előtti titokellenőrzés (`tests/repo/test_secrets_hygiene.py`) kötelező |

## 8. Ismert korlátok

| # | Korlát |
|---|---|
| L1 | A Zenodo-integrációt csak a felhasználó kapcsolhatja be; az asszisztens a DOI-t nem tudja előre kiosztani |
| L2 | A Zenodo felületének leírása (2. pont) **nem volt ellenőrizhető** az asszisztens számára; a felület változhat |
| L3 | A `CITATION.cff` leírása kétnyelvű, de a Zenodo-rekord többi része (pl. a kulcsszavak) angol; magyar nyelvű metaadat külön nincs |

*Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc*
