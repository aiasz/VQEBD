# Közreműködés / Contributing

Köszönjük az érdeklődést! A VQEBD egy **reprodukálható benchmark**: az értéke azon áll, hogy minden szám
újramérhető és minden állítás mögött fájl, parancs vagy mérés áll. A közreműködés is ezt a szellemet követi.

*Thanks for your interest! VQEBD is a **reproducible benchmark**: its value rests on every number being re-measurable.
Issues and pull requests are welcome in Hungarian or English; the documentation is mostly Hungarian.*

## Mielőtt elkezdesz

- **Hibát vagy ötletet** a [GitHub Issues](https://github.com/aiasz/VQEBD/issues) között jelezz; a sablonok segítenek
  a szükséges adatok (verzió, parancs, kimenet) megadásában.
- **Nagyobb változtatás előtt** nyiss issue-t. A projekt fázisokban halad: minden fázishoz **terv készül a
  megvalósítás előtt** (`docs/plan/phase_NN.md`), utána **tesztterv és mérési jegyzőkönyv**
  (`docs/testing/TP-FNN_*.md`, `TR-FNN_*.md`). Az architektúra-döntések az `docs/adr/` mappában vannak.
- **Biztonsági problémát** ne issue-ban jelents: lásd a [`SECURITY.md`](SECURITY.md)-t.

## Fejlesztői környezet

Minden parancs **konténerben** fut (a PySCF nem támogatja natívan a Windowst, és a lebegőpontos determinizmus rögzített
környezetet igényel, ADR-0005). Szükséges: Docker (`docker compose` v2), Git. A `make` nem kötelező.

```bash
git clone https://github.com/aiasz/VQEBD.git && cd VQEBD
docker compose -f docker/docker-compose.yml build app      # image építése (a requirements.lock-ot betartatva)

# a teljes tesztkészlet, a repóval bind-mountolva (Windows / Git Bash alatt: MSYS_NO_PATHCONV=1 előtag)
docker run --rm -v "$PWD":/repo:ro -e VQEBD_REPO_ROOT=/repo -e PYTHONPATH=/repo/src \
    -e VQEBD_IN_CONTAINER=1 -w /repo vqebd:$(cat VERSION) python -m pytest tests -m "not hardware"
```

Make-kel: `make build`, `make test`, `make check` (lint + típusellenőrzés + teszt). A részletek:
[`docs/00_setup.md`](docs/00_setup.md), [`docs/08_deployment.md`](docs/08_deployment.md).

## Minőségi kapuk

Egy változtatás akkor kész, ha **mind** zöld:

| Kapu | Parancs (az image-ben) |
|---|---|
| Lint | `ruff check .` |
| Formázás | `ruff format --check .` |
| Típusok (strict) | `mypy` |
| Tesztek | `pytest tests -m "not hardware"` |

A `hardware` jelölésű tesztek **valódi IBM QPU-t** igényelnek, és a CI-ben soha nem futnak.

## Konvenciók

- **Commit-üzenetek:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`,
  `build:` …), tömör, a *miért* is szerepeljen.
- **Minden állítás mögött mérés:** egy szám, egy tűrés vagy egy „működik” állítás mellé kerüljön a parancs vagy a teszt,
  amely igazolja. Ha valamit nem mértél, írd le, hogy feltevés.
- **Tesztek:** új viselkedéshez új teszt. A tesztek a szállított image-ben is futnak (mount nélkül): a teljes repót
  igénylő tesztek a `repo_root` fixture-t használják, amely a szállított image-ben kihagyja őket.
- **Titkok:** soha ne commitolj IBM API-tokent. A védelem több rétegű, és teszt őrzi
  (`tests/repo/test_secrets_hygiene.py`); a `.gitignore` kizárja a `*.token` és `.env` fájlokat.
- **Függőségek:** minden közvetlen függőség `==` pinnel és indoklással szerepel a `requirements*.txt`-ben, a teljes fa a
  `requirements.lock`-ban. Függőségváltás után a lockot újra kell generálni, és a build 0 eltérést kell mutasson.
- **Hardver:** valódi QPU-futtatás csak kifejezett engedéllyel (`VQEBD_ALLOW_HARDWARE=true`) és kvótaellenőrzéssel
  történhet (ADR-0008). Az automatikus ütemező sosem indít hardvert.

## Viselkedési elv

Légy tisztelettudó és konstruktív; a kritika a kódra és az érvekre vonatkozzon, ne a személyre. A bizonytalanságot és a
hibákat nyíltan jelezzük: a projekt jegyzőkönyvei is rögzítik a saját tévedéseinket (pl. `TR-F07` 3.). Hasonlóan
várjuk a visszajelzéseket.

## Licenc

A közreműködéseddel elfogadod, hogy a hozzájárulásod a projekt [MIT licence](LICENSE) alatt kerül kiadásra.
