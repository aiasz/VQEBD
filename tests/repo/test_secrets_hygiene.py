"""AC-0.8 — titokhigiénia: az IBM-token soha nem kerülhet a repóba vagy az image-be.

Ez a projekt legmagasabb kockázatú, legalacsonyabb költségű hibája (R0.4 kockázat,
``docs/plan/phase_00.md``). A védelem három rétegű, és mindhármat itt teszteljük:

1. ``.gitignore`` — a titkok nem kerülhetnek verziókezelésbe.
2. ``.dockerignore`` — a titkok nem kerülhetnek az image rétegeibe.
3. Tartalmi ellenőrzés — a verziózott fájlokban ne legyen tokennek látszó string.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# Mintáknak SZÓ SZERINT szerepelniük kell az ignore-fájlokban.
REQUIRED_IGNORE_PATTERNS: tuple[str, ...] = (".env", "*.token", "*.secret", "*.pem", "*.key")

# Csak a .gitignore-ra vonatkozó, futásidejű adatot érintő minták.
REQUIRED_GITIGNORE_ONLY: tuple[str, ...] = ("*.sqlite", "data/db/*", "__pycache__/")


def _patterns(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


@pytest.fixture(scope="module")
def gitignore_patterns(repo_root: Path) -> set[str]:
    return _patterns(repo_root / ".gitignore")


@pytest.fixture(scope="module")
def dockerignore_patterns(repo_root: Path) -> set[str]:
    return _patterns(repo_root / ".dockerignore")


@pytest.mark.parametrize("pattern", REQUIRED_IGNORE_PATTERNS)
def test_gitignore_covers_secret(gitignore_patterns: set[str], pattern: str) -> None:
    assert pattern in gitignore_patterns, (
        f"a .gitignore-ból hiányzik a titokminta: {pattern!r}. "
        "Ezt SOHA ne töröld — lásd docs/plan/phase_00.md, R0.4."
    )


@pytest.mark.parametrize("pattern", REQUIRED_IGNORE_PATTERNS)
def test_dockerignore_covers_secret(dockerignore_patterns: set[str], pattern: str) -> None:
    assert pattern in dockerignore_patterns, (
        f"a .dockerignore-ból hiányzik a titokminta: {pattern!r}. "
        "Enélkül a titok bekerülhet az image rétegeibe."
    )


@pytest.mark.parametrize("pattern", REQUIRED_GITIGNORE_ONLY)
def test_gitignore_covers_runtime_artifacts(gitignore_patterns: set[str], pattern: str) -> None:
    assert pattern in gitignore_patterns, f"a .gitignore-ból hiányzik: {pattern!r}"


def test_env_example_is_allowlisted(gitignore_patterns: set[str]) -> None:
    """A ``.env.example`` MINTA — ennek verziózva kell lennie a ``.env`` tiltása ellenére."""
    assert "!.env.example" in gitignore_patterns, (
        "a .gitignore-nak engedélyeznie kell a .env.example fájlt (`!.env.example`)"
    )


def test_real_env_file_absent(repo_root: Path) -> None:
    """A valódi ``.env`` nem lehet a repóban (akkor sem, ha nincs commitolva)."""
    assert not (repo_root / ".env").exists(), (
        "a repó gyökerében .env fájl található. Ez helyes fejlesztés közben, de "
        "ellenőrizd, hogy a .gitignore tényleg kizárja, mielőtt commitolsz."
    )


def test_env_example_has_no_real_token(repo_root: Path) -> None:
    """A minta fájl kulcsai legyenek üresek."""
    text = (repo_root / ".env.example").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if "TOKEN" in key.upper() or "SECRET" in key.upper() or "KEY" in key.upper():
            assert value.strip() == "", (
                f"a .env.example {key!r} kulcsa nem üres: {value!r}. "
                "MINTA fájlba soha ne kerüljön valódi titok."
            )


# Az IBM Quantum API-tokenek 40+ karakteres hexadecimális stringek.
TOKEN_LIKE = re.compile(r"\b[0-9a-f]{40,}\b")

SCANNED_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".cff", ".sql", ".example"}
SKIPPED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "data",
}
# A Docker-image digest szándékosan 64 hexa karakter — ez nem titok.
ALLOWED_CONTEXTS = ("sha256:", "digest", "Digest")


def test_no_token_like_strings_in_tracked_files(repo_root: Path) -> None:
    """Nincs tokennek látszó hexadecimális string a verziózott szövegfájlokban."""
    offenders: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        if any(part in SKIPPED_DIRS for part in path.relative_to(repo_root).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover — bináris fájl
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if TOKEN_LIKE.search(line) and not any(ctx in line for ctx in ALLOWED_CONTEXTS):
                offenders.append(f"{path.relative_to(repo_root).as_posix()}:{lineno}")
    assert not offenders, (
        "tokennek látszó hexadecimális string(ek) találhatók verziózott fájlokban: "
        f"{offenders}. Ha ez jogos (pl. hash), vedd fel az ALLOWED_CONTEXTS listába."
    )
