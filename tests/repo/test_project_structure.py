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
    "docs/02_hardware_run.md",
    "docs/03_mitigation_test.md",
    "docs/04_data_schema.md",
    "docs/references.md",
    "docs/plan/00_master_plan.md",
    "docs/plan/phase_00.md",
    "docs/plan/phase_01.md",
    "docs/plan/phase_01m.md",
    "docs/plan/phase_01b.md",
    "docs/plan/phase_02.md",
    "docs/plan/phase_03.md",
    "docs/plan/phase_04.md",
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
    "docs/testing/TP-F02_hardware_run.md",
    "docs/testing/TR-F02_hardware_run.md",
    "docs/testing/TP-F03_mitigation.md",
    "docs/testing/TR-F03_mitigation.md",
    "docs/testing/TP-F04_storage.md",
    "docs/testing/TR-F04_storage.md",
    "scripts/gen_references.py",
    "scripts/negative_test_harness.py",
    "scripts/check_ibm_access.py",
    "scripts/run_hardware_vqe.py",
    "scripts/export_results.py",
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
    "src/vqebd/mitigation/__init__.py",
    "src/vqebd/mitigation/base.py",
    "src/vqebd/mitigation/folding.py",
    "src/vqebd/mitigation/extrapolation.py",
    "src/vqebd/mitigation/none.py",
    "src/vqebd/mitigation/zne.py",
    "src/vqebd/mitigation/mitiq_zne.py",
    "src/vqebd/storage/__init__.py",
    "src/vqebd/storage/schema.py",
    "src/vqebd/storage/db.py",
    "src/vqebd/storage/export.py",
    "src/vqebd/py.typed",
    "tests/conftest.py",
    "tests/repo/test_line_endings.py",
    "tests/unit/test_hardware_evaluator.py",
    "tests/unit/test_folding.py",
    "tests/unit/test_extrapolation.py",
    "tests/unit/test_mitigation_strategies.py",
    "tests/unit/test_storage.py",
    "tests/validation/test_mitigation_validation.py",
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


RUNTIME_DATA_DIRS = ("data/db", "data/raw", "data/exports")
"""A futásidejű adat helye; tartalmukat a ``.gitignore`` kizárja (``dir/*``)."""


def test_data_dir_is_not_tracked_content(repo_root: Path) -> None:
    """A ``data/`` futásidejű; a repóban nem lehet benne **verziózott** adatfájl.

    A futásidejű fájlok (pl. egy batch SQLite-adatbázisa) a munkakönyvtárban
    megengedettek, de csak a ``.gitignore`` által kizárt könyvtárakban. A v0.8.0
    előtti változat minden helyi fájlt hibának vett, így rendeltetésszerű
    használat (``scripts/run_batch.py --db data/db/...``) után bukott.

    Ha a git elérhető (fejlesztői gép), a tényleges követést is ellenőrzi; a CI
    konténerében nincs git, ott a szabályalapú ellenőrzés fut.
    """
    import shutil
    import subprocess

    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
    for directory in RUNTIME_DATA_DIRS:
        assert f"{directory}/*" in gitignore, f"hiányzó .gitignore-szabály: {directory}/*"

    data = repo_root / "data"
    outside = [
        p.relative_to(repo_root).as_posix()
        for p in data.rglob("*")
        if p.is_file()
        and p.name != ".gitkeep"
        and not p.relative_to(repo_root)
        .as_posix()
        .startswith(tuple(d + "/" for d in RUNTIME_DATA_DIRS))
    ]
    assert not outside, f"a data/ alatt kizárt könyvtáron kívüli fájl: {outside}"

    git = shutil.which("git")
    if git is not None and (repo_root / ".git").exists():
        tracked = subprocess.run(
            [git, "-C", str(repo_root), "ls-files", "data"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        offenders = [t for t in tracked if not t.endswith("/.gitkeep")]
        assert not offenders, f"a data/ alatt nem lehet verziózott adatfájl: {offenders}"
