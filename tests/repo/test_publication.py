"""Fázis 9 — a publikálási készség védőtesztjei (a repó-checkoutot tesztelik).

Őrzik, hogy a GitHub felismerje a licencet, a közösségi fájlok megvannak, a README bejárata és a
verziótáblázata egyezik a lockkal, a hivatkozások nem törnek el, és a ``CITATION.cff`` a
``VERSION``-nel konzisztens (AC-9.2 … AC-9.7, AC-9.9).

Szerző: Kormos Attila · Megvalósítás MI-eszközzel: Claude (Anthropic) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# A szabványos (SPDX) MIT-szöveg törzse: a GitHub licenc-felismerése ehhez hasonlít.
_CANONICAL_MIT_BODY = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_SKIP_DIRS = frozenset(
    {".git", ".venv", "node_modules", ".pytest_cache", ".ruff_cache", ".mypy_cache", "__pycache__"}
)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _read(repo_root: Path, name: str) -> str:
    return (repo_root / name).read_text(encoding="utf-8")


# --- licenc (AC-9.2) -----------------------------------------------------------------------


def test_license_is_the_canonical_mit_text(repo_root: Path) -> None:
    """A ``LICENSE`` szabványos MIT (csak így ismeri fel a GitHub): cím, szerzői sor, törzs."""
    lines = _read(repo_root, "LICENSE").strip().splitlines()
    assert lines[0] == "MIT License"
    assert lines[2].startswith("Copyright (c) ")
    body = "\n".join(lines[3:])
    assert _squash(body) == _squash(_CANONICAL_MIT_BODY)


def test_license_has_no_third_party_appendix(repo_root: Path) -> None:
    """A függelék a ``NOTICE``-ban van; a ``LICENSE``-ben a GPL említése elrontaná a felismerést."""
    license_text = _read(repo_root, "LICENSE")
    for word in ("GPL", "Mitiq", "THIRD-PARTY", "HARMADIK"):
        assert word not in license_text, word


def test_notice_carries_the_third_party_and_mitiq_notes(repo_root: Path) -> None:
    notice = _read(repo_root, "NOTICE")
    for required in (
        "Mitiq",
        "GPL-3.0",
        "src/vqebd/mitigation/mitiq_zne.py",
        "requirements.lock",
        "docs/references.md",
        "ADR-0003",
    ):
        assert required in notice, required
    assert (repo_root / "src/vqebd/mitigation/mitiq_zne.py").is_file()


# --- közösségi fájlok (AC-9.4) -------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/config.yml",
    ],
)
def test_community_file_exists(repo_root: Path, name: str) -> None:
    assert (repo_root / name).is_file(), name


def test_readme_links_the_community_files_in_both_languages(repo_root: Path) -> None:
    readme = _read(repo_root, "README.md")
    for target in ("CONTRIBUTING.md", "SECURITY.md", "NOTICE"):
        assert readme.count(f"]({target})") >= 2 or readme.count(f"`{target}`](") >= 2, target


def test_security_policy_names_the_token_rules_and_a_contact(repo_root: Path) -> None:
    security = _read(repo_root, "SECURITY.md")
    assert "IBM_QUANTUM_TOKEN" in security and "IBM.token" in security
    assert re.search(r"[\w.]+@[\w.]+\.\w+", security), "nincs elérhetőség"
    assert "127.0.0.1" in security  # a dashboard hitelesítés nélküli: loopback-kötés


def test_contributing_describes_the_real_quality_gates(repo_root: Path) -> None:
    contributing = _read(repo_root, "CONTRIBUTING.md")
    for gate in ("ruff check", "ruff format --check", "mypy", "pytest"):
        assert gate in contributing, gate
    assert "Conventional Commits" in contributing


# --- README bejárata (AC-9.5, AC-9.7) -----------------------------------------------------------


def test_readme_has_the_ci_badge(repo_root: Path) -> None:
    readme = _read(repo_root, "README.md")
    assert "actions/workflows/ci.yml/badge.svg" in readme
    assert (repo_root / ".github" / "workflows" / "ci.yml").is_file()


_QUICK_START = (
    "docker compose -f docker/docker-compose.yml build app",
    "docker compose -f docker/docker-compose.yml run --rm app python -m vqebd",
    "docker compose -f docker/docker-compose.yml up -d dashboard",
)


def test_readme_has_the_same_three_command_quick_start_in_both_languages(repo_root: Path) -> None:
    readme = _read(repo_root, "README.md")
    assert "### Röviden" in readme and "### In short" in readme
    for command in _QUICK_START:
        assert readme.count(command) >= 2, command  # magyar és angol szakasz is


def test_quick_start_commands_use_services_that_exist(repo_root: Path) -> None:
    compose = _read(repo_root, "docker/docker-compose.yml")
    for service in ("app", "dashboard"):
        assert re.search(rf"^  {service}:\n", compose, re.M), service


def _version_tables(readme: str) -> list[dict[str, str]]:
    tables = []
    for block in re.findall(r"<!-- versions:start -->(.*?)<!-- versions:end -->", readme, re.S):
        rows = re.findall(r"^\| `([^`]+)` \| ([^|\s]+) \|$", block, re.M)
        tables.append(dict(rows))
    return tables


def _lock(repo_root: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in _read(repo_root, "requirements.lock").splitlines():
        match = re.match(r"^([A-Za-z0-9._-]+)==(\S+)$", line.strip())
        if match:
            pins[re.sub(r"[-_.]+", "-", match.group(1)).lower()] = match.group(2)
    return pins


def test_readme_version_tables_equal_the_lock(repo_root: Path) -> None:
    """AC-9.7: a README rögzített-verzió táblázata (HU és EN) pontosan a lockot tükrözi."""
    tables = _version_tables(_read(repo_root, "README.md"))
    assert len(tables) == 2, f"magyar és angol táblázat egyaránt kell, van: {len(tables)}"
    assert tables[0] == tables[1], "a két nyelvi táblázat eltér"
    lock = _lock(repo_root)
    assert len(tables[0]) >= 10
    for name, version in tables[0].items():
        assert lock.get(name) == version, f"{name}: README {version}, lock {lock.get(name)}"


# --- hivatkozások (AC-9.6) ----------------------------------------------------------------------


def test_every_relative_markdown_link_resolves(repo_root: Path) -> None:
    """AC-9.6: minden Markdown-fájl minden relatív hivatkozása létező fájlra vagy mappára mutat."""
    link = re.compile(r"\]\(([^)\s]+)\)")
    broken: list[str] = []
    checked = 0
    for path in sorted(repo_root.rglob("*.md")):
        if any(part in _SKIP_DIRS for part in path.relative_to(repo_root).parts):
            continue
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for match in link.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            checked += 1
            if not (path.parent / target.split("#")[0]).resolve().exists():
                broken.append(f"{path.relative_to(repo_root).as_posix()} -> {target}")
    assert checked > 100, f"gyanúsan kevés ellenőrzött hivatkozás: {checked}"
    assert not broken, "törött relatív hivatkozások:\n" + "\n".join(broken)


# --- CITATION.cff és a kiadás konzisztenciája (AC-9.3, AC-9.9) -----------------------------


def _cff_field(cff: str, key: str) -> str:
    match = re.search(rf'^{key}:\s*"?([^"\n]+)"?\s*$', cff, re.M)
    assert match, f"a CITATION.cff-ből hiányzik: {key}"
    return match.group(1).strip()


def test_citation_matches_the_version_and_the_changelog_date(repo_root: Path) -> None:
    cff = _read(repo_root, "CITATION.cff")
    version = _read(repo_root, "VERSION").strip()
    assert _cff_field(cff, "cff-version") == "1.2.0"
    assert _cff_field(cff, "version") == version
    assert _cff_field(cff, "license") == "MIT"
    changelog = _read(repo_root, "CHANGELOG.md")
    released = re.search(
        rf"^## \[{re.escape(version)}\] — (\d{{4}}-\d{{2}}-\d{{2}})", changelog, re.M
    )
    assert released, f"a CHANGELOG-ban nincs [{version}] kiadás"
    assert _cff_field(cff, "date-released") == released.group(1)


def test_citation_has_an_english_abstract_and_the_required_fields(repo_root: Path) -> None:
    cff = _read(repo_root, "CITATION.cff")
    for key in (
        "cff-version",
        "title",
        "message",
        "authors",
        "abstract",
        "keywords",
        "repository-code",
    ):
        assert re.search(rf"^{key}:", cff, re.M), key
    abstract = cff[cff.index("abstract:") : cff.index("\nkeywords:")]
    assert "reproducible benchmark" in abstract  # angol leírás (nemzetközi felfedezhetőség)


def test_readme_bibtex_version_matches_the_version(repo_root: Path) -> None:
    version = _read(repo_root, "VERSION").strip()
    entries = re.findall(
        r"@software\{vqebd,.*?version\s*=\s*\{([^}]+)\}", _read(repo_root, "README.md"), re.S
    )
    assert len(entries) == 2, f"a BibTeX-bejegyzés HU és EN részben is kell, van: {len(entries)}"
    assert set(entries) == {version}


def test_publishing_guide_exists_and_names_the_zenodo_prerequisite(repo_root: Path) -> None:
    guide = _read(repo_root, "docs/09_publishing.md")
    assert (
        "Zenodo" in guide and "release előtt" in guide
    )  # a kapcsolót a release ELŐTT kell bekapcsolni
