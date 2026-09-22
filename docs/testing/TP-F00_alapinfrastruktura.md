# TP-F00 — Fázis 0 tesztterve (Alapinfrastruktúra)

| | |
|---|---|
| **Azonosító** | TP-F00 |
| **Típus** | Test Plan (tesztterv) |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-09-22 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Fázis** | 0 — Alapinfrastruktúra és repó-szerkezet |
| **Célverzió** | `v0.1.0` |
| **Terv** | [`docs/plan/phase_00.md`](../plan/phase_00.md) |
| **Jegyzőkönyv** | [`TR-F00`](TR-F00_alapinfrastruktura.md) |

---

## 1. A tesztelés célja és hatóköre

A Fázis 0 terméke a **konténer-infrastruktúra és a repó-szerkezet**. Ez a tesztterv
a [`phase_00.md`](../plan/phase_00.md) 4. fejezetében rögzített **tíz elfogadási
kritériumot** (AC-0.1 … AC-0.10) fordítja le konkrét, végrehajtható ellenőrzésekre.

**Hatókörön kívül:** bármilyen kvantumszámítás, VQE, IBM-hitelesítés, adatbázis,
dashboard. Ezek a Fázis 1-től kerülnek tesztelésre.

---

## 2. Tesztkörnyezet

| | |
|---|---|
| Gazdagép | Windows 11 Pro 10.0.26200, x86_64 |
| Docker | 29.1.3 (szerver: linux/amd64) |
| Docker Compose | v5.0.0-desktop.1 |
| Vizsgált image | `vqebd:0.1.0` — `python:3.11-slim@sha256:da047cb8…95ba9` |
| Tesztfuttató | pytest 9.1.1 |
| Lint / típus | ruff 0.16.8, mypy 2.3.1 |

---

## 3. Teszthatókörök

| Hatókör | Könyvtár | Mit vizsgál | Hol fut |
|---|---|---|---|
| **Kód** | `tests/unit/` | A `vqebd` csomag viselkedését, a futtatási környezetet. | Mindenhol, a szállított image-ben is. |
| **Repó** | `tests/repo/` | A checkout szerkezetét, verzióegyezést, titokhigiéniát. | Gazdagépen és bind-mountolt repóval. |

A repó-hatókörű tesztek a szállított image-ben **kihagyásra kerülnek**, mert ott
nincs teljes checkout. Ez tervezett viselkedés, nem hiba — és a `pytest -ra`
kimenetben **látható indoklással** történik, nem némán.

---

## 4. Tesztesetek

### 4.1 Kör 1 — funkcionális

| Teszteset | AC | Végrehajtás | Elfogadás |
|---|---|---|---|
| **TC-01** Image építése | AC-0.1 | `make build` | 0 kilépési kód, image létrejön |
| **TC-02** Python-verzió | AC-0.2 | `docker run --rm vqebd:0.1.0 python --version` | `Python 3.11.x` |
| **TC-03** Tesztek a konténerben | AC-0.3 | `docker run --rm -e VQEBD_IN_CONTAINER=1 vqebd:0.1.0 python -m pytest tests -ra` | 0 hiba, 0 error |
| **TC-04** Nem-root futás | AC-0.4 | `docker run --rm vqebd:0.1.0 id -u` | ≠ `0` (várt: `1000`) |
| **TC-05** Determinizmus-környezet | AC-0.5 | `docker run --rm vqebd:0.1.0 printenv PYTHONHASHSEED` | `0` |
| **TC-06** Hash-randomizáció tényleg kikapcsolt | AC-0.5 | `tests/unit/test_runtime_environment.py::test_hashing_is_actually_stable` | `sys.flags.hash_randomization == 0` |
| **TC-07** Repó-szerkezet | AC-0.6 | `tests/repo/test_project_structure.py` | minden kötelező könyvtár és fájl megvan, nem üres |
| **TC-08** Verzióegyezés | AC-0.7 | `tests/repo/test_version_consistency.py` | `VERSION` == `__version__` == CHANGELOG == CITATION.cff == compose tag |
| **TC-09** Titokhigiénia | AC-0.8 | `tests/repo/test_secrets_hygiene.py` | minden titokminta megvan mindkét ignore-fájlban |
| **TC-10** Lint és típusellenőrzés | AC-0.9 | `make lint && make typecheck` | 0 hiba |
| **TC-11** ADR-0002 betartatása | — | `tests/unit/test_package.py::test_no_qiskit_algorithms_import_in_source` | nincs `qiskit_algorithms` import a `src/vqebd` alatt |
| **TC-12** Compose-útvonal | — | `make compose-build && make compose-run` | `Python 3.11.x` |

### 4.2 Kör 2 — robusztussági és **negatív** tesztek

Egy zöld teszt csak akkor ér valamit, ha **piros is tud lenni**. Ebben a körben
szándékosan elrontunk dolgokat, és **elvárjuk a hibát**. Ha egy negatív teszt
*nem* bukik el, az a teszt hibája, nem siker.

| Teszteset | Mit rontunk el | Elvárt eredmény |
|---|---|---|
| **TC-N1** | `VERSION` átírása `9.9.9`-re | `test_version_consistency` **elbukik** (CHANGELOG, CITATION, compose eltér) |
| **TC-N2** | `.env.example` `IBM_QUANTUM_TOKEN` kitöltése álértékkel | `test_env_example_has_no_real_token` **elbukik** |
| **TC-N3** | A `.gitignore`-ból a `.env` sor törlése | `test_gitignore_covers_secret` **elbukik** |
| **TC-N4** | Egy kötelező könyvtár átnevezése | `test_required_directory_exists` **elbukik** |
| **TC-N5** | 64 hexa karakteres álkulcs beszúrása egy `.py` fájlba | `test_no_token_like_strings_in_tracked_files` **elbukik** |
| **TC-N6** | `qiskit_algorithms` import beszúrása a `src/vqebd`-be | `test_no_qiskit_algorithms_import_in_source` **elbukik** |

Minden negatív teszt után az eredeti állapot **visszaállítandó**, és a visszaállítás
után a teljes készletnek újra zöldnek kell lennie.

| Teszteset | Mit vizsgál | Elfogadás |
|---|---|---|
| **TC-R1** Build gyorsítótár nélkül | `make rebuild` | ugyanaz a Python-verzió (AC-0.10) |
| **TC-R2** Ismételt futtatás | `make verify` kétszer | azonos kimenet |
| **TC-R3** Bind-mount jogosultság | `make test` | nincs `permission denied` |

### 4.3 Kör 3 — keresztvalidáció

| Teszteset | Mit vizsgál | Elfogadás |
|---|---|---|
| **TC-X1** Gazdagép ↔ konténer | ugyanaz a tesztkészlet mindkettőn | azonos pass/fail halmaz (a konténer-specifikus tesztek a gazdagépen kihagyva) |
| **TC-X2** `docker run` ↔ `docker compose` | ugyanaz a kimenet mindkét útvonalon | azonos Python-verzió |
| **TC-X3** Baked image ↔ bind-mountolt repó | a kódtesztek mindkét forráson | azonos eredmény |

---

## 5. Kilépési feltételek

A fázis akkor zárható le, ha **mind** teljesül:

1. TC-01 … TC-12 zöld;
2. TC-N1 … TC-N6 az **elvárt módon elbukott**, majd visszaállítás után újra zöld;
3. TC-R1 … TC-R3 zöld;
4. TC-X1 … TC-X3 zöld;
5. az eredmények rögzítve a [`TR-F00`](TR-F00_alapinfrastruktura.md) jegyzőkönyvben;
6. `CHANGELOG.md` `0.1.0` bejegyzése kész, `v0.1.0` annotált Git-tag létrehozva.

---

## 6. Kockázatok a tesztelésben

| # | Kockázat | Kezelés |
|---|---|---|
| T0.1 | A teszt zöld, mert nem fut le semmi (üres gyűjtés). | A jegyzőkönyv rögzíti a **gyűjtött tesztek darabszámát**. |
| T0.2 | A repó-tesztek némán kihagyódnak, és ezt sikernek véljük. | `pytest -ra` kötelező; a jegyzőkönyv rögzíti a skip-okokat. |
| T0.3 | A negatív tesztek visszaállítása elmarad. | Git `status` és `diff` ellenőrzés a kör végén. |
| T0.4 | A CI más eredményt ad, mint a helyi futtatás. | A CI ugyanazt az image-et és parancsokat használja. |

---

## 7. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. |

---

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
