# =============================================================================
# VQEBD — fejlesztői parancsok
# Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
# =============================================================================
# Minden parancs KONTÉNERBEN fut. Indok: a PySCF nem támogatja natívan a Windowst,
# és a lebegőpontos determinizmus is rögzített környezetet igényel (ADR-0005).
#
# Windowson `make` helyett a docs/00_setup.md nyers docker-parancsait használd,
# vagy telepítsd a GNU Make-et (pl. Git for Windows / Chocolatey / winget).
# =============================================================================

SHELL := /bin/sh

VERSION      := $(shell cat VERSION)
IMAGE        := vqebd:$(VERSION)
IMAGE_LATEST := vqebd:latest
COMPOSE      := docker compose -f docker/docker-compose.yml

# A repót csak olvasásra csatoljuk, hogy a konténer ne írhassa felül a forrást.
# A VQEBD_REPO_ROOT jelzi a teszteknek, hol van a teljes checkout (tests/conftest.py).
RUN_IN_REPO := docker run --rm \
	-v "$(CURDIR)":/repo:ro \
	-e VQEBD_REPO_ROOT=/repo \
	-e PYTHONPATH=/repo/src \
	-e VQEBD_IN_CONTAINER=1 \
	-w /repo $(IMAGE)

.DEFAULT_GOAL := help
.PHONY: help build rebuild test verify lint format typecheck check shell clean \
        compose-build compose-run docs-refs ci

help:  ## Az elérhető parancsok listája
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Image -------------------------------------------------------------------

build:  ## Docker-image építése (AC-0.1)
	docker build --platform linux/amd64 -f docker/Dockerfile -t $(IMAGE) -t $(IMAGE_LATEST) .

rebuild:  ## Image építése gyorsítótár nélkül (2. tesztkör — robusztusság)
	docker build --platform linux/amd64 --no-cache -f docker/Dockerfile -t $(IMAGE) .

# --- Tesztelés ---------------------------------------------------------------

test:  ## Teljes tesztkészlet a konténerben, bind-mountolt repóval
	$(RUN_IN_REPO) python -m pytest tests -p no:cacheprovider

test-verbose:  ## Ugyanaz, részletes kimenettel
	$(RUN_IN_REPO) python -m pytest tests -vv -ra -p no:cacheprovider

verify:  ## A SZÁLLÍTOTT image önellenőrzése, mount nélkül (AC-0.2…AC-0.5)
	@echo "── AC-0.2: Python-verzió ───────────────────────────────"
	@docker run --rm $(IMAGE) python --version
	@echo "── AC-0.4: felhasználó (0 = root, hibás) ───────────────"
	@docker run --rm $(IMAGE) id -u
	@echo "── AC-0.5: PYTHONHASHSEED ──────────────────────────────"
	@docker run --rm $(IMAGE) printenv PYTHONHASHSEED
	@echo "── AC-0.3: a beépített tesztek a baked kódon ───────────"
	@docker run --rm -e VQEBD_IN_CONTAINER=1 $(IMAGE) \
		python -m pytest tests -ra -p no:cacheprovider

# --- Minőségi kapuk ----------------------------------------------------------

lint:  ## ruff check + formázás ellenőrzése (AC-0.9)
	$(RUN_IN_REPO) python -m ruff check .
	$(RUN_IN_REPO) python -m ruff format --check .

format:  ## Kód automatikus formázása (ez ÍR, ezért írható mounttal fut)
	docker run --rm -v "$(CURDIR)":/repo -w /repo $(IMAGE) python -m ruff format .
	docker run --rm -v "$(CURDIR)":/repo -w /repo $(IMAGE) python -m ruff check --fix .

typecheck:  ## mypy strict a src/vqebd felett (AC-0.9)
	$(RUN_IN_REPO) python -m mypy

check: lint typecheck test  ## Minden minőségi kapu egyben

ci: build check verify  ## Amit a CI futtat

# --- Segédparancsok ----------------------------------------------------------

shell:  ## Interaktív shell a konténerben
	docker run --rm -it -v "$(CURDIR)":/repo -e VQEBD_REPO_ROOT=/repo \
		-e PYTHONPATH=/repo/src -w /repo $(IMAGE) /bin/bash

compose-build:  ## Építés docker compose-zal (a compose útvonal tesztelése)
	$(COMPOSE) build

compose-run:  ## Futtatás docker compose-zal
	$(COMPOSE) run --rm app python --version

docs-refs:  ## A hivatkozásjegyzék újragenerálása (hálózatot igényel)
	docker run --rm -v "$(CURDIR)":/repo -w /repo $(IMAGE) \
		python scripts/gen_references.py

clean:  ## Helyi gyorsítótárak és image-ek törlése
	-docker rmi $(IMAGE) $(IMAGE_LATEST)
	-rm -rf .pytest_cache .ruff_cache .mypy_cache
	-find . -type d -name __pycache__ -prune -exec rm -rf {} +
