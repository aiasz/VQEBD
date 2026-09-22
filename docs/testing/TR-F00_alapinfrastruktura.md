# TR-F00 — Fázis 0 mérési jegyzőkönyve (Alapinfrastruktúra)

| | |
|---|---|
| **Azonosító** | TR-F00 |
| **Típus** | Test Report (mérési jegyzőkönyv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 0 — Alapinfrastruktúra és repó-szerkezet |
| **Vizsgált verzió** | `0.1.0` |
| **Tesztterv** | [`TP-F00`](TP-F00_alapinfrastruktura.md) |
| **Státusz** | **Lezárva — mind a 10 elfogadási kritérium teljesült** |

---

## 1. Összefoglalás

| | |
|---|---|
| Elfogadási kritériumok | **10 / 10 teljesült** |
| Automatikus tesztek (konténer) | **109 futott, 109 zöld, 0 hiba** |
| Automatikus tesztek (szállított image) | 22 zöld, 87 kihagyva (indokolt), 0 hiba |
| Negatív tesztek | **8 / 8 az elvárt módon elbukott** |
| Lint (`ruff check`) | 0 hiba (30 fájl) |
| Formázás (`ruff format --check`) | 30 / 30 megfelelő |
| Típusellenőrzés (`mypy --strict`) | 0 hiba (14 forrásfájl) |
| A tesztelés során talált és javított hibák | **4** (lásd 6. fejezet) |

---

## 2. Tesztkörnyezet

| | |
|---|---|
| Gazdagép | Windows 11 Pro 10.0.26200, x86_64 |
| Gazdagép Python | 3.10.11 (**nem támogatott** — lásd TC-X1) |
| Docker | 29.1.3 (szerver: linux/amd64, 8 165 470 208 B) |
| Docker Compose | v5.0.0-desktop.1 |
| Git | 2.50.1.windows.1 |
| Image | `vqebd:0.1.0` |
| Alap-image | `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9` |
| Konténer Python | **3.11.16** |
| Eszközök | pytest 9.1.1, ruff 0.16.8, mypy 2.3.1 |

---

## 3. Kör 1 — funkcionális tesztek

### TC-01 · AC-0.1 — Image építése ✅

```
docker build --platform linux/amd64 -f docker/Dockerfile -t vqebd:0.1.0 -t vqebd:latest .
```

Eredmény: sikeres, kilépési kód 0.
`exporting manifest list sha256:a38349ef48f8b521dc3b1b520f960145844910944ebdebe82ed0b73773ca455c`

### TC-02 · AC-0.2 — Python-verzió ✅

```
$ docker run --rm vqebd:0.1.0 python --version
Python 3.11.16
```

### TC-04 · AC-0.4 — Nem-root futás ✅

```
$ docker run --rm vqebd:0.1.0 id
uid=1000(vqebd) gid=1000(vqebd) groups=1000(vqebd)
```

### TC-05 · AC-0.5 — Determinizmus-környezet ✅

```
$ docker run --rm vqebd:0.1.0 printenv PYTHONHASHSEED
0
$ docker run --rm vqebd:0.1.0 printenv PYTHONPATH
/app/src
```

### TC-06 · AC-0.5 — A hash-randomizáció ténylegesen kikapcsolt ✅

`tests/unit/test_runtime_environment.py::test_hashing_is_actually_stable` —
`sys.flags.hash_randomization == 0`. Ez erősebb állítás a környezeti változó
meglétnél: azt igazolja, hogy a beállítás **hatályba is lépett** az értelmező
indulásakor.

### TC-03 · AC-0.3 — Tesztek a szállított image-ben ✅

```
$ docker run --rm -e VQEBD_IN_CONTAINER=1 vqebd:0.1.0 python -m pytest tests -ra
22 passed, 87 skipped in 0.09s
```

A 87 kihagyás **tervezett**: a repó-hatókörű tesztek a futtatási image-ben nem
értelmezhetők (nincs `docs/`, `LICENSE`). A kihagyás **nem néma** — minden esetnél
megjelenik az indoklás:

```
SKIPPED [1] tests/repo/test_version_consistency.py:41: Nem érhető el teljes
repó-checkout (hiányzik a jelölők egyike: pyproject.toml, VERSION, LICENSE,
docs, src). Ez a szállított image-ben normális — a repó-hatókörű teszteket a
gazdagépen futtasd, vagy bind-mountold a repót és állítsd be a VQEBD_REPO_ROOT
változót.
```

### TC-07, TC-08, TC-09 · AC-0.6, AC-0.7, AC-0.8 — Teljes tesztkészlet ✅

```
$ docker run --rm -v "$PWD:/repo:ro" -e VQEBD_REPO_ROOT=/repo \
    -e PYTHONPATH=/repo/src -e VQEBD_IN_CONTAINER=1 -w /repo \
    vqebd:0.1.0 python -m pytest tests -ra -p no:cacheprovider
109 passed in 1.74s
```

Lefedett ellenőrzések:

| Modul | Tartalom |
|---|---|
| `tests/repo/test_project_structure.py` | 19 kötelező könyvtár, 33 kötelező fájl, 6 csomag-`__init__`, `src/` tisztasága, `data/` üressége |
| `tests/repo/test_version_consistency.py` | SemVer-érvényesség, `VERSION` ↔ `__version__` ↔ `CHANGELOG` ↔ `CITATION.cff` ↔ compose tag, `pyproject` dinamikus verzió |
| `tests/repo/test_secrets_hygiene.py` | 5 titokminta × 2 ignore-fájl, `.env.example` allowlist, üres tokenmezők, tokenszerű string keresése |
| `tests/repo/test_line_endings.py` | LF sorvégek, záró sortörés, `.gitattributes` szabály |
| `tests/unit/test_package.py` | verzió, készítők, licenc, 5 alcsomag importja, `py.typed`, **ADR-0002 betartatása** |
| `tests/unit/test_runtime_environment.py` | Python-verzió, nem-root, `PYTHONHASHSEED`, hash-randomizáció |

### TC-10 · AC-0.9 — Minőségi kapuk ✅

```
$ ruff check --no-cache .              -> All checks passed!
$ ruff format --no-cache --check .     -> 30 files already formatted
$ mypy                                 -> Success: no issues found in 14 source files
```

A `mypy` **strict** módban fut a `src/vqebd`, a `tests` és a
`scripts/gen_references.py` felett.

### TC-11 — ADR-0002 betartatása ✅

`test_no_qiskit_algorithms_import_in_source`: a `qiskit_algorithms` importja
tiltott a `src/vqebd/` alatt. Jelenleg 0 sértés. A védelem működőképességét a
TC-N6 negatív eset igazolja.

### TC-12 — Compose-útvonal ✅

```
$ docker compose -f docker/docker-compose.yml build
 Image vqebd:0.1.0 Built
$ docker compose -f docker/docker-compose.yml run --rm app python --version
Python 3.11.16
```

---

## 4. Kör 2 — robusztussági és negatív tesztek

### 4.1 Negatív tesztek — a védelmek bizonyítása

Eszköz: [`scripts/negative_test_harness.py`](../../scripts/negative_test_harness.py).
A harness **nem nyúl az eredeti repóhoz**: minden esethez izolált másolatot készít
egy ideiglenes könyvtárban, ott ront el valamit, és a másolat ellen futtat pytestet.
A másolat a futás végén automatikusan törlődik — így a visszaállítás nem emberi
fegyelem kérdése (T0.3 kockázat kezelve).

**Előfeltétel-ellenőrzés:** a sértetlen másolaton minden teszt zöld. ✅

| Eset | Rontás | Elbukott tesztek | Eredmény |
|---|---|---|---|
| **TC-N1** | `VERSION` → `9.9.9` | `test_changelog_top_entry_matches`, `test_citation_cff_version_matches`, `test_compose_image_tag_matches` | ✅ |
| **TC-N2** | `.env.example` tokenmező kitöltése | `test_env_example_has_no_real_token` | ✅ |
| **TC-N3** | `.env` törlése a `.gitignore`-ból | `test_gitignore_covers_secret[.env]` | ✅ |
| **TC-N4** | `docs/adr` átnevezése | `test_required_directory_exists[docs/adr]` + 5 fájlteszt | ✅ |
| **TC-N5** | 64 hexa karakteres álkulcs beszúrása | `test_no_token_like_strings_in_tracked_files` | ✅ |
| **TC-N6** | `qiskit_algorithms` import beszúrása | `test_no_qiskit_algorithms_import_in_source` + 2 import-teszt | ✅ |
| **TC-N7** | CRLF bevezetése egy dokumentumba | `test_no_crlf_in_tracked_text_files` | ✅ |
| **TC-N8** | `CHANGELOG` legfelső kiadásának átírása | `test_changelog_top_entry_matches` | ✅ |

```
Eredmény: 8/8 negatív eset bukott el az elvárt módon.
Minden védelmi teszt bizonyítottan képes hibát jelezni.
```

> **Megjegyzés a TC-N6-hoz.** A `qiskit_algorithms` import a `test_subpackage_imports`
> tesztet is elbuktatja, mert a Fázis 0 image nem tartalmazza a csomagot. Ez nem
> mellékhatás-hiba, hanem **kettős védelem**: a tiltott import a statikus
> ellenőrzésen *és* a futásidejű importon is fennakad.

### 4.2 TC-R1 · AC-0.10 — Újraépítés gyorsítótár nélkül

Lásd az 5. fejezet mérését.

### 4.3 TC-R3 — Bind-mount jogosultságok ✅

A `:ro` mountolt repóval futtatott tesztek `permission denied` nélkül lefutottak.
Az írást igénylő műveletek (`ruff format`, generátor) külön, írható mounttal futnak.

---

## 5. Kör 3 — keresztvalidáció

### TC-X1 — Gazdagép ↔ konténer ✅

| Környezet | Python | Eredmény |
|---|---|---|
| Konténer (`vqebd:0.1.0`) | 3.11.16 | **109 passed** |
| Gazdagép (Windows) | 3.10.11 | **104 passed, 1 failed, 4 skipped** |

A gazdagépen a 4 kihagyás a konténer-specifikus teszt (`in_container` fixture), az
egyetlen hiba pedig **pontosan a várt**:

```
FAILED tests/unit/test_runtime_environment.py::test_python_minor_is_supported
AssertionError: Python 3.10 nem támogatott; engedélyezett: (11, 12) (ADR-0001)
```

**Ez az eredmény önmagában értékes bizonyíték.** A gazdagépen telepített Python
3.10 nem elégíti ki az ADR-0001 szerinti követelményt (a `mitiq` `>=3.10,<3.13`
korlátja mellett a projekt a 3.11-et rögzíti), és a verzió-őr ezt észleli. Ez
megerősíti a projekt alapdöntését: **minden számítás konténerben fut**, mert a
gazdagép környezete sem verzióban, sem platformban (PySCF ⊄ Windows) nem alkalmas.

### TC-X2 — `docker run` ↔ `docker compose` ✅

Mindkét útvonal `Python 3.11.16`-ot ad, azonos image-ből (`vqebd:0.1.0`).

### TC-X3 — Baked image ↔ bind-mountolt repó ✅

| Forrás | Futott | Zöld | Kihagyva |
|---|---|---|---|
| Baked (`/app`, mount nélkül) | 109 | 22 | 87 |
| Bind-mountolt repó (`/repo`) | 109 | 109 | 0 |

A kódtesztek mindkét forráson azonos eredményt adnak; az eltérés kizárólag a
repó-hatókörű tesztek kihagyásából ered, ami tervezett.

### TC-X4 (kiegészítő) — A hivatkozás-generátor determinizmusa ✅

A `scripts/gen_references.py` kétszeri futtatása azonos bemenetből **bitre azonos**
kimenetet ad:

```
$ python scripts/gen_references.py --out /tmp/refs.md --date 2026-09-22
$ diff -q docs/references.md /tmp/refs.md
AZONOS - determinisztikus
```

37 tétel, ebből 35 gépileg DOI-validált (Crossref / DataCite).

---

## 6. A tesztelés során talált és javított hibák

Ez a fejezet a Mesterterv 9.3 szerinti **többkörös hibakeresés** tényleges hozadéka.
Mind a négy hibát a saját automatikus tesztek, illetve a minőségi kapuk tárták fel —
nem kézi átnézés.

### H-01 — A `py.typed` jelölő üres, a strukturális teszt viszont nem-üres fájlt várt

*Megtalálta:* `test_required_file_exists[src/vqebd/py.typed]`
*Ok:* a PEP 561 a `py.typed` jelölőt kifejezetten **üres** fájlként definiálja; a
puszta létezése a jelzés. A generikus „ne legyen üres fájl" szabály ezzel ütközött.
*Javítás:* `INTENTIONALLY_EMPTY` halmaz bevezetése, a kivétel dokumentált indoklással.
*Tanulság:* a szigorú szabályoknak **nevesített, indokolt** kivételük legyen, ne
általános lazítása.

### H-02 — A `CHANGELOG` magyar „Nem kiadott" címkéje megtörte a gépi feldolgozást

*Megtalálta:* `test_changelog_top_entry_matches`
*Ok:* a „Keep a Changelog" szabvány az angol `Unreleased` kulcsszót használja, és a
szabványt feldolgozó eszközök erre támaszkodnak. A magyar fordítás elrontotta ezt.
*Javítás:* a szakaszcím `## [Unreleased] — Nem kiadott` lett (gépileg szabványos,
emberileg magyar), a teszt pedig mindkét alakot elfogadja.
*Tanulság:* a dokumentáció nyelve nem írhatja felül a gépi interfészek szabványát.

### H-03 — A hivatkozás-generátor kimenete platformfüggő volt (CRLF ↔ LF)

*Megtalálta:* a generátor determinizmus-ellenőrzése (TC-X4) — a `diff` a fájl
**minden** sorát eltérésként jelezte.
*Ok:* a `Path.write_text()` szövegmódban alapértelmezésben `os.linesep`-re fordítja
a `\n`-t. Windowson így CRLF, Linuxon LF sorvégű fájl születik **ugyanabból a
bemenetből** — a generált, verziózott műtermék tehát nem reprodukálható.
*Javítás:* explicit `newline="\n"` minden generátor-íráson, dokumentált kommenttel.
*Tanulság:* a generált, verziózott műtermékeknek platformfüggetlenül bitre azonosnak
kell lenniük; ez nem esztétika, hanem a reprodukálhatóság feltétele.

### H-04 — Hét forrásfájl CRLF sorvéggel keletkezett (R0.2 kockázat bekövetkezett)

*Megtalálta:* célzott sorvég-ellenőrzés a H-03 nyomán.
*Ok:* ugyanaz, mint a H-03 — Windowson futtatott szerkesztő-szkriptek.
*Érintett fájlok:* `.gitignore`, `CHANGELOG.md`, `scripts/gen_references.py`,
`src/vqebd/__init__.py` és három `tests/repo/` modul (összesen 1218 CRLF).
*Javítás:* konvertálás LF-re, **és** állandó automatikus teszt bevezetése
(`tests/repo/test_line_endings.py`), amely a `.gitattributes` szabályát is ellenőrzi.
*Tanulság:* a `.gitattributes` csak *commitoláskor* normalizál — a munkakönyvtárban
lévő fájlokat nem javítja. Az egyszeri javítás mellé **állandó őr** kell.

> **Módszertani megjegyzés.** Mind a négy hiba olyan, amelyet kézi átnézés
> nagy valószínűséggel nem talált volna meg: három közülük láthatatlan
> (sorvégek), egy pedig szabványértelmezési kérdés. Ez igazolja a Mesterterv
> 9.3 szerinti háromkörös eljárás értelmét.

---

## 7. Elfogadási kritériumok — összesítés

| # | Kritérium | Mérés | Állapot |
|---|---|---|---|
| **AC-0.1** | `docker build` hiba nélkül lefut | kilépési kód 0 | ✅ |
| **AC-0.2** | `python --version` → 3.11.x | `Python 3.11.16` | ✅ |
| **AC-0.3** | `pytest` zölden lefut a konténerben | 109 / 109 (mounttal), 22 + 87 skip (baked) | ✅ |
| **AC-0.4** | A konténer nem root-ként fut | `uid=1000(vqebd)` | ✅ |
| **AC-0.5** | `PYTHONHASHSEED=0` | `0`, `hash_randomization == 0` | ✅ |
| **AC-0.6** | A repó-szerkezet megfelel a tervnek | 19 könyvtár + 33 fájl ellenőrizve | ✅ |
| **AC-0.7** | A verziószám mindenhol egyezik | 5 helyen, `0.1.0` | ✅ |
| **AC-0.8** | A `.gitignore` kizárja a titkokat | 5 minta × 2 fájl + tartalmi szűrés | ✅ |
| **AC-0.9** | `ruff` és `mypy` hiba nélkül fut | 0 + 0 + 0 hiba | ✅ |
| **AC-0.10** | Kétszeri build ugyanazt adja | lásd 8. fejezet | ✅ |

---

## 8. AC-0.10 — Újraépítés gyorsítótár nélkül

```
docker build --platform linux/amd64 --no-cache -f docker/Dockerfile -t vqebd:rebuild-test .
```

| Ellenőrzés | `vqebd:0.1.0` | `vqebd:rebuild-test` | Egyezés |
|---|---|---|---|
| `python --version` | `Python 3.11.16` | `Python 3.11.16` | ✅ |
| `id -u` | `1000` | `1000` | ✅ |
| `printenv PYTHONHASHSEED` | `0` | `0` | ✅ |
| beépített tesztek | 22 passed, 87 skipped | 22 passed, 87 skipped | ✅ |

A digest-pin (`sha256:da047cb8…95ba9`) tehát ténylegesen rögzíti az alap-image-et:
a gyorsítótár teljes megkerülése mellett is bitazonos alapról indul a build.

---

## 9. Nyitott pontok a következő fázisra

| # | Pont | Hol dől el |
|---|---|---|
| O1 | A gazdagép Pythonja (3.10) nem támogatott — érdemes-e 3.11-et telepíteni a szerkesztő-integrációhoz? | Fejlesztői döntés; a CI és a futtatás nem érintett. |
| O2 | A `requirements.txt` üres; a Fázis 1-ben a teljes stack `==` pinnekkel kerül be. | Fázis 1 |
| O3 | A `requirements.lock` (tranzitív függőségekkel) még nem készült el. | Fázis 1 |
| O4 | A CI még nem futott valódi GitHub-környezetben (a repó lokális). | Fázis 9 (publikálás) |

---

## 10. Kilépési nyilatkozat

A [`TP-F00`](TP-F00_alapinfrastruktura.md) 5. fejezete szerinti **mind a hat**
kilépési feltétel teljesült:

1. ✅ TC-01 … TC-12 zöld;
2. ✅ TC-N1 … TC-N8 az elvárt módon elbukott, izolált másolaton (visszaállítás
   automatikus);
3. ✅ TC-R1 … TC-R3 zöld;
4. ✅ TC-X1 … TC-X4 zöld;
5. ✅ az eredmények rögzítve ebben a jegyzőkönyvben;
6. ✅ `CHANGELOG.md` `0.1.0` bejegyzése kész; `v0.1.0` annotált Git-tag létrehozva.

**A Fázis 0 lezárható. A Fázis 1 megkezdhető.**

---

## 11. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. 10/10 elfogadási kritérium, 4 talált és javított hiba. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
