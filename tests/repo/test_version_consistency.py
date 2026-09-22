"""AC-0.7 — a verziószám minden előfordulása egyezik.

Igazságforrás: a repó gyökerében lévő ``VERSION`` fájl
(``docs/plan/00_master_plan.md``, 8.1).

Ellenőrzött helyek:

- ``VERSION``
- ``vqebd.__version__``
- ``CHANGELOG.md`` legfelső kiadási bejegyzése
- ``CITATION.cff`` ``version`` mezője
- ``docker/docker-compose.yml`` ``image:`` tagje

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# Semantic Versioning 2.0.0 — a hivatalos ajánlott reguláris kifejezés egyszerűsített,
# de szigorú változata (https://semver.org/).
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@pytest.fixture(scope="module")
def declared_version(repo_root: Path) -> str:
    return (repo_root / "VERSION").read_text(encoding="utf-8").strip()


def test_version_file_is_valid_semver(declared_version: str) -> None:
    assert SEMVER_RE.match(declared_version), (
        f"a VERSION nem érvényes Semantic Versioning 2.0.0 érték: {declared_version!r}"
    )


def test_version_file_has_single_line(repo_root: Path) -> None:
    raw = (repo_root / "VERSION").read_text(encoding="utf-8")
    assert raw.endswith("\n"), "a VERSION fájl záró sortöréssel végződjön"
    assert len(raw.strip().splitlines()) == 1, "a VERSION fájl pontosan egy sort tartalmazzon"


def test_package_version_matches(declared_version: str) -> None:
    import vqebd

    assert vqebd.__version__ == declared_version, (
        f"vqebd.__version__ ({vqebd.__version__}) != VERSION ({declared_version})"
    )


# A „Keep a Changelog" szerinti, még ki nem adott szakasz címkéi. Az angol
# `Unreleased` a szabványos, gépileg feldolgozható alak; a magyar változatot is
# elfogadjuk, hogy a dokumentáció nyelve ne kényszerítsen technikai kompromisszumot.
UNRELEASED_LABELS: frozenset[str] = frozenset({"unreleased", "nem kiadott"})


def test_changelog_top_entry_matches(repo_root: Path, declared_version: str) -> None:
    """A CHANGELOG legfelső *kiadási* bejegyzése a VERSION-nel egyezzen.

    A még ki nem adott (``Unreleased``) szakaszt átugorjuk.
    """
    text = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = re.findall(r"^##\s*\[([^\]]+)\]", text, flags=re.MULTILINE)
    released = [v for v in versions if v.strip().lower() not in UNRELEASED_LABELS]
    assert released, "a CHANGELOG.md nem tartalmaz kiadási bejegyzést"
    assert released[0] == declared_version, (
        f"a CHANGELOG legfelső kiadása ({released[0]}) != VERSION ({declared_version})"
    )


def test_citation_cff_version_matches(repo_root: Path, declared_version: str) -> None:
    text = (repo_root / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r"^version:\s*['\"]?([^'\"\s]+)['\"]?\s*$", text, flags=re.MULTILINE)
    assert match, "a CITATION.cff nem tartalmaz `version:` mezőt"
    assert match.group(1) == declared_version, (
        f"a CITATION.cff verziója ({match.group(1)}) != VERSION ({declared_version})"
    )


def test_compose_image_tag_matches(repo_root: Path, declared_version: str) -> None:
    text = (repo_root / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    match = re.search(r"^\s*image:\s*vqebd:([^\s]+)\s*$", text, flags=re.MULTILINE)
    assert match, "a docker-compose.yml nem tartalmaz `image: vqebd:<verzió>` sort"
    assert match.group(1) == declared_version, (
        f"a compose image tagje ({match.group(1)}) != VERSION ({declared_version})"
    )


def test_pyproject_declares_dynamic_version(repo_root: Path) -> None:
    """A pyproject a VERSION fájlból vegye a verziót — ne legyen második igazságforrás."""
    text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^dynamic\s*=\s*\[\s*"version"\s*\]', text, flags=re.MULTILINE), (
        "a pyproject.toml-ban a `version` legyen dynamic"
    )
    assert re.search(r'version\s*=\s*\{\s*file\s*=\s*"VERSION"\s*\}', text), (
        "a [tool.setuptools.dynamic] a VERSION fájlra hivatkozzon"
    )
    assert not re.search(r'^version\s*=\s*"', text, flags=re.MULTILINE), (
        'a pyproject.toml ne tartalmazzon statikus `version = "..."` sort'
    )
