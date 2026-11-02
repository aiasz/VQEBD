"""A szakirodalmi pozicionálás, az MI-felhasználási nyilatkozat és a Fázis 11 terv védőtesztjei.

Őrzik, hogy (1) a pozicionálásban hivatkozott minden ``[kulcs]`` létezik a gépileg generált
jegyzékben, és a dokumentum kimondja a saját korlátait; (2) az MI-használat a README-ban,
a ``CITATION.cff``-ben és a kiadási útmutatóban jelölve van, a nyilatkozat pedig kétnyelvű és
kimondja, mi nem ellenőrzött; (3) a Fázis 11 hardveres ütemezése a rögzített keretszabályon belül
marad.

Készítők: Kormos Attila, Claude AI (Anthropic) — MIT licenc
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_QUOTA_SECONDS = 600.0
_MAX_USED_FRACTION = 0.80


def _read(repo_root: Path, name: str) -> str:
    return (repo_root / name).read_text(encoding="utf-8")


def _reference_keys(repo_root: Path) -> set[str]:
    return set(
        re.findall(r"^\*\*\[([a-z0-9]+)\]\*\*", _read(repo_root, "docs/references.md"), re.M)
    )


# --- szakirodalmi pozicionálás -----------------------------------------------------------------


def test_every_cited_key_in_the_positioning_exists_in_the_reference_list(repo_root: Path) -> None:
    text = _read(repo_root, "docs/10_literature_positioning.md")
    cited = set(re.findall(r"`\[([a-z0-9]+)\]`", text))
    assert len(cited) >= 25, "a pozicionálás feltűnően kevés művet idéz"
    missing = sorted(cited - _reference_keys(repo_root))
    assert not missing, f"nem létező hivatkozáskulcsok: {missing}"


def test_every_positioning_reference_is_actually_cited(repo_root: Path) -> None:
    """A „Szakirodalmi pozicionálás" kategóriák tételeit a dokumentumnak fel kell használnia."""
    refs = _read(repo_root, "docs/references.md")
    positioning_part = refs.split("## Szakirodalmi pozicionálás", 1)[1].split(
        "## Felhasznált szoftverek", 1
    )[0]
    keys = set(re.findall(r"^\*\*\[([a-z0-9]+)\]\*\*", positioning_part, re.M))
    assert len(keys) == 20
    text = _read(repo_root, "docs/10_literature_positioning.md")
    unused = sorted(k for k in keys if f"[{k}]" not in text)
    assert not unused, f"jegyzékben van, de a pozicionálás nem használja: {unused}"


def test_positioning_states_its_own_limits(repo_root: Path) -> None:
    text = _read(repo_root, "docs/10_literature_positioning.md")
    assert "Nem szisztematikus áttekintés" in text
    for code in ("S1", "S2", "S3", "S4", "S5", "S6"):
        assert f"| {code} |" in text, code
    assert "nem lektorált" in text
    assert "Publikálás előtt kötelező" in text


def test_reference_list_counts_match_the_readme(repo_root: Path) -> None:
    refs = _read(repo_root, "docs/references.md")
    m = re.search(r"\*\*Tételek\*\* \| (\d+) db, ebből \*\*(\d+)\*\* gépileg DOI-validált", refs)
    assert m is not None
    total, validated = m.group(1), m.group(2)
    assert len(_reference_keys(repo_root)) == int(total)
    readme = _read(repo_root, "README.md")
    assert f"**{total} hivatkozás, {validated} gépileg DOI-validálva**" in readme
    assert f"**{total} references, {validated} machine DOI-validated**" in readme


# --- MI-felhasználási nyilatkozat ----------------------------------------------------------------


def test_ai_disclosure_is_bilingual_and_states_what_was_not_verified(repo_root: Path) -> None:
    text = _read(repo_root, "AI_DISCLOSURE.md")
    assert "## Magyar" in text and "## English" in text
    for required in (
        "mesterséges intelligenciával (MI) készített kísérlet",
        "AI-assisted experiment",
        "független szakértői lektorálás",
        "independent expert review",
        "Claude Sonnet 5.5",
        "Claude Opus 5",
        "nem tartalmaz ilyen sort",  # nem állítja, hogy minden commit hordoz modell-jelölést
        "no such trailer",
    ):
        assert required in text, required


def test_ai_disclosure_records_the_code_review_as_self_reported(repo_root: Path) -> None:
    """A szerző közlése (kb. 80% soronként átnézve) önbevallásként, korlátokkal szerepel."""
    text = _read(repo_root, "AI_DISCLOSURE.md")
    assert "80%" in text
    assert "önbevallás" in text and "self-reported" in text
    assert "nem állítja" in text  # HU: nem állítja, hogy a kód egésze átnézett
    assert "does not claim" in text  # EN


def test_ai_use_is_marked_in_readme_both_languages(repo_root: Path) -> None:
    readme = _read(repo_root, "README.md")
    assert "MI-vel készített kísérlet" in readme
    assert "AI-assisted experiment" in readme
    assert readme.count("AI_DISCLOSURE.md") >= 6
    assert "### MI-felhasználás" in readme
    assert "### AI Use" in readme


def test_ai_use_is_marked_in_the_citation_file(repo_root: Path) -> None:
    cff = _read(repo_root, "CITATION.cff")
    message = re.search(r'^message: "(.*)"$', cff, re.M)
    assert message is not None
    assert "AI" in message.group(1) and "MI" in message.group(1)
    assert "AI-assisted work" in cff


def test_publishing_checklist_requires_the_ai_marking(repo_root: Path) -> None:
    text = _read(repo_root, "docs/09_publishing.md")
    assert "Az MI-használat jelölve van" in text
    assert "AI_DISCLOSURE.md" in text


def test_the_zenodo_author_list_stays_attila_kormos_only(repo_root: Path) -> None:
    """Felhasználói döntés (D4): a Zenodo-rekord szerzője csak Kormos Attila."""
    cff = _read(repo_root, "CITATION.cff")
    authors = cff.split("authors:", 1)[1].split("abstract:", 1)[0]
    assert authors.count("family-names") == 1
    assert "Kormos" in authors


# --- Fázis 11 terv ---------------------------------------------------------------------------


def _cost(row_cost: str) -> float:
    return float(row_cost.replace(" s", "").replace(",", "."))


def test_phase_11_schedule_stays_within_the_quota_rule(repo_root: Path) -> None:
    text = _read(repo_root, "docs/plan/phase_11.md")
    assert "A B0 pilot lefutott" in text  # a hardveres futások állása a tervben naprakész
    rows = re.findall(r"^\| (B0 pilot|C\d) \| \d+ \| ([\d,]+ s) \|", text, re.M)
    assert [r[0] for r in rows] == ["B0 pilot"] + [f"C{i}" for i in range(1, 9)]
    existing = 57.0  # a meglévő 5.H használat (TR-F05 7.)
    total = existing + sum(_cost(c) for _, c in rows)
    assert total <= _MAX_USED_FRACTION * _QUOTA_SECONDS, total
    assert _QUOTA_SECONDS - total >= 0.20 * _QUOTA_SECONDS


def test_phase_11_costs_follow_from_the_measured_per_pub_rates(repo_root: Path) -> None:
    text = _read(repo_root, "docs/plan/phase_11.md")
    raw, trex = 4.8, 6.6
    assert f"{5 * (raw + trex):.0f} s" in text  # pilot: 5 geometria
    assert (
        f"{3 * (raw + trex):.1f}".replace(".", ",") + " s" in text
    )  # megerősítő blokk: 3 geometria


def test_phase_11_fixes_decision_rules_before_measuring(repo_root: Path) -> None:
    text = _read(repo_root, "docs/plan/phase_11.md")
    for required in (
        "protocol-f11-frozen",
        "δ = 3,0 mHa",
        "feltáró",
        "megerősítő",
        "TOST",
        "Nem szabad",
    ):
        assert required in text, required
    assert (
        "belső előzetes meghatározás" in text
    )  # nem állítja, hogy külső regiszterben előre regisztrált
