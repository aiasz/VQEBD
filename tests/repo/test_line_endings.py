"""R0.2 — a verziózott szövegfájlok kizárólag LF sorvégűek lehetnek.

A fejlesztés Windowson is folyhat, a futtatás viszont mindig Linux-konténerben.
A CRLF sorvégek ott némán elronthatnak shell-szkripteket, heredocokat és
generált műtermékek diffjét (`docs/plan/phase_00.md`, R0.2 kockázat).

A ``.gitattributes`` (``* text=auto eol=lf``) ezt *commitoláskor* rendezi, de a
munkakönyvtárban lévő fájlokat nem javítja visszamenőleg — ezért kell ez a teszt.

**Ez a kockázat már bekövetkezett:** a Fázis 0 során hét fájl CRLF sorvéggel
keletkezett, mert Windowson a ``Path.write_text()`` alapértelmezésben ``os.linesep``-re
fordítja a ``\\n``-t. A javítás: minden generátor explicit ``newline="\\n"``-nel ír.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

CRLF = b"\r\n"

TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".cff", ".sql", ".json", ".example", ".sh"}
)
TEXT_NAMES: frozenset[str] = frozenset(
    {
        "Dockerfile",
        "Makefile",
        "VERSION",
        "LICENSE",
        ".gitignore",
        ".dockerignore",
        ".gitattributes",
        ".env.example",
    }
)
SKIPPED_DIRS: frozenset[str] = frozenset(
    {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".venv", "venv", "data"}
)


def _text_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIPPED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            found.append(path)
    return found


def test_no_crlf_in_tracked_text_files(repo_root: Path) -> None:
    files = _text_files(repo_root)
    assert files, "nem található vizsgálható szövegfájl — a gyűjtés hibás"
    offenders = [
        f"{p.relative_to(repo_root).as_posix()} ({p.read_bytes().count(CRLF)} CRLF)"
        for p in files
        if CRLF in p.read_bytes()
    ]
    assert not offenders, (
        "CRLF sorvégű fájl(ok) a repóban (lásd R0.2, docs/plan/phase_00.md): "
        f"{offenders}. Javítás: a fájlt LF-re kell konvertálni, a generátoroknak "
        'pedig explicit newline="\\n" paraméterrel kell írniuk.'
    )


def test_text_files_end_with_newline(repo_root: Path) -> None:
    """POSIX-konvenció: a szövegfájlok sortöréssel végződnek."""
    offenders = [
        p.relative_to(repo_root).as_posix()
        for p in _text_files(repo_root)
        if (data := p.read_bytes()) and not data.endswith(b"\n")
    ]
    assert not offenders, f"záró sortörés nélküli fájl(ok): {offenders}"


def test_gitattributes_enforces_lf(repo_root: Path) -> None:
    """A ``.gitattributes`` commitoláskor is kényszerítse az LF-et."""
    text = (repo_root / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in text, (
        "a .gitattributes-ből hiányzik a `* text=auto eol=lf` szabály (R0.2)"
    )
