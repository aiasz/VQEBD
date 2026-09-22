# =============================================================================
# VQEBD — Fázis 0 alap-image
# Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
# =============================================================================
# Terv: docs/plan/phase_00.md (3.2), docs/plan/phase_01.md (5.)
#
# A Fázis 0-ban ez az image szándékosan nem tartalmazott kvantumkönyvtárat, hogy
# az infrastruktúra önmagában igazolható legyen. A Fázis 1-től a teljes, az
# ADR-0001-ben rögzített és a TR-000 spike-ban funkcionálisan igazolt stack benne van.
# =============================================================================

# Az alap-image DIGEST-tel rögzítve: a tag idővel más image-re mutathat, a digest
# soha. Ez a reprodukálhatóság alapja (docs/plan/00_master_plan.md, 4.4).
#   tag   : python:3.11-slim
#   digest: sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9
#   python: 3.11.16     (ellenőrizve: 2026-09-22)
#
# Miért `slim` és nem `alpine`? Az Alpine musl libc-t használ, a numpy/scipy/pyscf/
# qiskit-aer bináris wheel-jei viszont manylinux (glibc) alapúak — Alpine-on
# forrásból fordulnának, eltérő numerikával. Lásd: docs/plan/phase_00.md, 3.2.
FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9

# --- OCI címkék (Open Containers Initiative szabvány) ------------------------
LABEL org.opencontainers.image.title="VQEBD" \
      org.opencontainers.image.description="VQE-alapú kvantumkémiai benchmark & dashboard" \
      org.opencontainers.image.authors="Kormos Attila, Claude AI (Anthropic, Claude Opus 5)" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/aiasz/VQEBD" \
      org.opencontainers.image.documentation="https://github.com/aiasz/VQEBD/tree/main/docs"

# --- Rendszerszintű függőségek ----------------------------------------------
# libgomp1: a PySCF és a NumPy/SciPy OpenMP-futásideje. A csomagok mind
# manylinux wheel-ként települnek, ezért fordítóra (build-essential) nincs
# szükség — ez ~250 MB-tal kisebb image-et ad.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# --- Környezeti változók -----------------------------------------------------
ENV PYTHONHASHSEED=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1
# PYTHONHASHSEED=0   : determinizmus — a Python hash-randomizáció kikapcsolása
#                      (ADR-0005, 5. véletlenforrás)
# PYTHONPATH         : src-layout importálhatósága `pip install` nélkül is
# *_NUM_THREADS=1    : a többszálú BLAS/OpenMP redukciók összegzési sorrendje
#                      futásonként eltérhet, ami az utolsó bitekben ingadozó
#                      energiát adna. Egyetlen szálon a lebegőpontos összegzés
#                      determinisztikus — ez az AC-1.6 (bitre azonosság) feltétele.
#                      (R1.2 kockázat, docs/plan/phase_01.md)

# --- Nem-root felhasználó ----------------------------------------------------
# Indok: biztonság, és hogy a bind-mountolt fájlok ne kerüljenek root tulajdonba
# (R0.3 kockázat, docs/plan/phase_00.md).
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "${APP_GID}" vqebd \
 && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --shell /bin/bash vqebd

WORKDIR /app

# --- Függőségek (külön réteg a cache-hatékonyságért) -------------------------
# Előbb CSAK a requirements fájlokat másoljuk: így a forráskód változása nem
# invalidálja a pip-réteget.
COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r requirements.txt \
 && python -m pip install -r requirements-dev.txt

# --- Forrás ------------------------------------------------------------------
COPY --chown=vqebd:vqebd VERSION pyproject.toml ./
COPY --chown=vqebd:vqebd src/ ./src/
COPY --chown=vqebd:vqebd tests/ ./tests/
COPY --chown=vqebd:vqebd scripts/ ./scripts/

# --- Futásidejű adatkönyvtárak (a compose volume ide csatol) -----------------
RUN mkdir -p /app/data/db /app/data/raw /app/data/exports \
 && chown -R vqebd:vqebd /app/data

USER vqebd

# --- Egészségellenőrzés ------------------------------------------------------
# A Fázis 0 elfogadási kritériuma (AC-0.2) magában az image-ben is kódolva.
HEALTHCHECK --interval=30s --timeout=5s --start-period=2s --retries=3 \
    CMD python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"

# Alapértelmezett parancs: a verzió kiírása (AC-0.2 kézi ellenőrzéséhez).
CMD ["python", "--version"]
