"""AC-0.6 — a repó-szerkezet megfelel a Fázis 0 tervnek.

Specifikáció: ``docs/plan/phase_00.md``, 3.1. szakasz.

Ez a teszt szándékosan *konkrét* fájllistát ellenőriz, nem mintákat: a Fázis 0
terméke maga a szerkezet, így a szerkezet megváltozása tudatos döntés kell legyen,
nem véletlen mellékhatás.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REQUIRED_DIRS: tuple[str, ...] = (
    "src/vqebd",
    "src/vqebd/backends",
    "src/vqebd/chemistry",
    "src/vqebd/mitigation",
    "src/vqebd/storage",
    "src/vqebd/vqe",
    "tests/unit",
    "tests/integration",
    "tests/validation",
    "tests/repo",
    "docker",
    "docs",
    "docs/plan",
    "docs/adr",
    "docs/testing",
    "docs/figures",
    "dashboard",
    "data",
    "scripts",
)

REQUIRED_FILES: tuple[str, ...] = (
    ".dockerignore",
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE",
    "Makefile",
    "README.md",
    "VERSION",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
    "requirements.lock",
    "docker/Dockerfile",
    "docker/docker-compose.yml",
    "docs/00_setup.md",
    "docs/01_vqe_core.md",
    "docs/01m_multiplatform.md",
    "docs/01b_noisy_simulation.md",
    "docs/references.md",
    "docs/plan/00_master_plan.md",
    "docs/plan/phase_00.md",
    "docs/plan/phase_01.md",
    "docs/plan/phase_01m.md",
    "docs/plan/phase_01b.md",
    "docs/plan/phase_02.md",
    "docs/adr/ADR-0001-technologiai-stack.md",
    "docs/adr/ADR-0002-sajat-vqe-hurok.md",
    "docs/adr/ADR-0003-mitigacios-architektura.md",
    "docs/adr/ADR-0004-adattarolas.md",
    "docs/adr/ADR-0005-determinizmus.md",
    "docs/adr/ADR-0006-tobbplatformos-architektura.md",
    "docs/testing/TR-000_spike.md",
    "docs/testing/TP-F00_alapinfrastruktura.md",
    "docs/testing/TR-F00_alapinfrastruktura.md",
    "docs/testing/TP-F01_vqe_mag.md",
    "docs/testing/TR-F01_vqe_mag.md",
    "docs/testing/TP-F01M_tobbplatform.md",
    "docs/testing/TR-F01M_tobbplatform.md",
    "docs/testing/TP-F01B_noisy_simulation.md",
    "docs/testing/TR-F01B_noisy_simulation.md",
    "scripts/gen_references.py",
    "scripts/negative_test_harness.py",
    "scripts/check_ibm_access.py",
    "scripts/gen_report_figures.py",
    "src/vqebd/__init__.py",
    "src/vqebd/__main__.py",
    "src/vqebd/cli.py",
    "src/vqebd/config.py",
    "src/vqebd/seeds.py",
    "src/vqebd/versions.py",
    "src/vqebd/platforms.py",
    "src/vqebd/credentials.py",
    "src/vqebd/backends/conversion.py",
    "src/vqebd/backends/cirq_estimators.py",
    "src/vqebd/py.typed",
    "tests/conftest.py",
    "tests/repo/test_line_endings.py",
)

# Minden `src/vqebd` alkönyvtárnak valódi Python-csomagnak kell lennie.
PACKAGE_DIRS: tuple[str, ...] = (
    "src/vqebd",
    "src/vqebd/backends",
    "src/vqebd/chemistry",
    "src/vqebd/mitigation",
    "src/vqebd/storage",
    "src/vqebd/vqe",
)


@pytest.mark.parametrize("relative", REQUIRED_DIRS)
def test_required_directory_exists(repo_root: Path, relative: str) -> None:
    path = repo_root / relative
    assert path.is_dir(), f"hiányzó könyvtár: {relative} (lásd docs/plan/phase_00.md 3.1)"


# Jelölőfájlok, amelyek szabvány szerint ÜRESEK. A PEP 561 a `py.typed` esetében
# kifejezetten üres fájlt ír elő: a puszta létezése a jelzés.
INTENTIONALLY_EMPTY: frozenset[str] = frozenset({"src/vqebd/py.typed"})


@pytest.mark.parametrize("relative", REQUIRED_FILES)
def test_required_file_exists(repo_root: Path, relative: str) -> None:
    path = repo_root / relative
    assert path.is_file(), f"hiányzó fájl: {relative} (lásd docs/plan/phase_00.md 3.1)"
    if relative not in INTENTIONALLY_EMPTY:
        assert path.stat().st_size > 0, f"üres fájl: {relative}"


@pytest.mark.parametrize("relative", PACKAGE_DIRS)
def test_package_dir_has_init(repo_root: Path, relative: str) -> None:
    init = repo_root / relative / "__init__.py"
    assert init.is_file(), f"{relative} nem Python-csomag: hiányzik az __init__.py"


def test_no_stray_python_at_src_root(repo_root: Path) -> None:
    """A ``src/`` alatt csak a ``vqebd`` csomag lehet (src-layout tisztasága)."""
    entries = {p.name for p in (repo_root / "src").iterdir()}
    assert entries == {"vqebd"}, f"a src/ nem csak a vqebd csomagot tartalmazza: {sorted(entries)}"


def test_data_dir_is_not_tracked_content(repo_root: Path) -> None:
    """A ``data/`` futásidejű; a repóban nem lehet benne adatfájl."""
    data = repo_root / "data"
    offenders = [
        p.relative_to(repo_root).as_posix()
        for p in data.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    ]
    assert not offenders, f"a data/ alatt nem lehet verziózott adatfájl: {offenders}"
