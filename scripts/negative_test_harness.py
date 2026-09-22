#!/usr/bin/env python3
"""VQEBD — negatív teszt harness: bizonyítja, hogy a tesztek tudnak pirosat jelezni.

Miért kell ez?
--------------
Egy zöld teszt önmagában semmit nem bizonyít: lehet, hogy sosem fut le, vagy hogy
az állítása triviálisan igaz. A ``TP-F00`` tesztterv 4.2 szakasza ezért előírja,
hogy minden védelmi tesztet **szándékosan el kell rontani**, és igazolni kell, hogy
az elvárt teszt — és lehetőleg csak az — elbukik.

Hogyan működik?
---------------
A harness **nem nyúl az eredeti repóhoz**. Minden esethez készít egy izolált
másolatot egy ideiglenes könyvtárban, ott hajtja végre a rontást, majd a másolat
ellen futtatja a pytestet ``VQEBD_REPO_ROOT`` és ``PYTHONPATH`` átirányítással.
A másolat a futás végén törlődik, így a rontás visszaállítása nem emberi
fegyelem kérdése (T0.3 kockázat).

Használat
---------
    python scripts/negative_test_harness.py [--repo /repo] [-v]

Kilépési kód: 0, ha minden negatív eset az elvárt módon elbukott.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

EXCLUDE = shutil.ignore_patterns(
    ".git", "__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".venv", "venv"
)


@dataclass(frozen=True)
class NegativeCase:
    """Egy szándékos rontás és a hozzá tartozó elvárás."""

    code: str
    description: str
    break_it: Callable[[Path], None]
    expected_failing: str
    """A teszt-azonosító (vagy annak egyértelmű részlete), amelynek buknia KELL."""


# --------------------------------------------------------------------------- rontások
def _break_version(root: Path) -> None:
    (root / "VERSION").write_text("9.9.9\n", encoding="utf-8", newline="\n")


def _break_env_example(root: Path) -> None:
    path = root / ".env.example"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("IBM_QUANTUM_TOKEN=", "IBM_QUANTUM_TOKEN=nem-valodi-de-nem-is-ures"),
        encoding="utf-8",
        newline="\n",
    )


def _break_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    kept = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() != ".env"]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")


def _break_structure(root: Path) -> None:
    (root / "docs" / "adr").rename(root / "docs" / "adr_atnevezve")


def _break_token_scan(root: Path) -> None:
    # 64 hexa karakteres álkulcs — tokennek látszik, de nem az.
    fake = "0" * 20 + "1234567890abcdef" * 2 + "a" * 12
    path = root / "src" / "vqebd" / "chemistry" / "__init__.py"
    path.write_text(
        path.read_text(encoding="utf-8") + f'\n_ALKULCS = "{fake}"\n',
        encoding="utf-8",
        newline="\n",
    )


def _break_forbidden_import(root: Path) -> None:
    path = root / "src" / "vqebd" / "vqe" / "__init__.py"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nimport qiskit_algorithms  # ADR-0002 megsértése\n",
        encoding="utf-8",
        newline="\n",
    )


def _break_line_endings(root: Path) -> None:
    path = root / "docs" / "00_setup.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))


def _break_changelog(root: Path) -> None:
    """A CHANGELOG legfelső *kiadási* szakaszcímének átírása.

    A rontásnak verziófüggetlennek kell lennie: egy konkrét verziószámra
    (pl. ``## [0.1.0]``) kódolt csere a következő verzióemelés után csendben
    hatástalanná válna, és a negatív eset tévesen jelezne hibát. Ezért a
    *mintát* keressük, nem a konkrét számot.
    """
    path = root / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s*\[(?!Unreleased\b)([^\]]+)\]", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        raise RuntimeError("a CHANGELOG.md nem tartalmaz kiadási szakaszcímet")
    broken = text[: match.start()] + "## [9.9.9]" + text[match.end() :]
    path.write_text(broken, encoding="utf-8", newline="\n")


def _break_requirements_pin(root: Path) -> None:
    path = root / "requirements.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("numpy==1.26.4", "numpy==1.26.3"),
        encoding="utf-8",
        newline="\n",
    )


def _break_license_separation(root: Path) -> None:
    path = root / "requirements.txt"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nmitiq==0.47.0\n",
        encoding="utf-8",
        newline="\n",
    )


def _break_seed_derivation(root: Path) -> None:
    path = root / "src" / "vqebd" / "seeds.py"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'f"{master}:{label}".encode()', 'f"{master}|{label}".encode()'
        ),
        encoding="utf-8",
        newline="\n",
    )


CASES: tuple[NegativeCase, ...] = (
    NegativeCase(
        "TC-N1",
        "A VERSION fájl 9.9.9-re írása",
        _break_version,
        "test_changelog_top_entry_matches",
    ),
    NegativeCase(
        "TC-N2",
        "A .env.example tokenmezőjének kitöltése",
        _break_env_example,
        "test_env_example_has_no_real_token",
    ),
    NegativeCase(
        "TC-N3",
        "A .env sor törlése a .gitignore-ból",
        _break_gitignore,
        "test_gitignore_covers_secret",
    ),
    NegativeCase(
        "TC-N4",
        "A docs/adr könyvtár átnevezése",
        _break_structure,
        "test_required_directory_exists",
    ),
    NegativeCase(
        "TC-N5",
        "64 hexa karakteres álkulcs beszúrása forrásfájlba",
        _break_token_scan,
        "test_no_token_like_strings_in_tracked_files",
    ),
    NegativeCase(
        "TC-N6",
        "qiskit_algorithms import beszúrása (ADR-0002 sértése)",
        _break_forbidden_import,
        "test_no_qiskit_algorithms_import_in_source",
    ),
    NegativeCase(
        "TC-N7",
        "CRLF sorvégek bevezetése egy dokumentumba",
        _break_line_endings,
        "test_no_crlf_in_tracked_text_files",
    ),
    NegativeCase(
        "TC-N8",
        "A CHANGELOG legfelső kiadásának átírása",
        _break_changelog,
        "test_changelog_top_entry_matches",
    ),
    NegativeCase(
        "TC-N9",
        "A requirements.txt numpy-pinjének átírása",
        _break_requirements_pin,
        "test_required_package_is_pinned",
    ),
    NegativeCase(
        "TC-N10",
        "A GPL-3.0 licencű mitiq felvétele közvetlen függőségként",
        _break_license_separation,
        "test_gpl_package_is_not_a_direct_dependency",
    ),
    NegativeCase(
        "TC-N11",
        "A seed-származtatás elválasztójának megváltoztatása",
        _break_seed_derivation,
        "test_seed_set_matches_golden_values",
    ),
)


# --------------------------------------------------------------------------- futtatás
def run_pytest(root: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env["VQEBD_REPO_ROOT"] = str(root)
    env["PYTHONPATH"] = str(root / "src")
    env["VQEBD_IN_CONTAINER"] = "1"
    # A parancs rögzített lista (nem shell, nem felhasználói bemenet), így a
    # `subprocess` használata itt biztonságos.
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--no-header"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def check_case(case: NegativeCase, source: Path, verbose: bool) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"vqebd-neg-{case.code}-") as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(source, work, ignore=EXCLUDE, symlinks=True)
        case.break_it(work)
        code, output = run_pytest(work)

    failed_as_expected = code != 0 and case.expected_failing in output
    status = "OK  " if failed_as_expected else "HIBA"
    print(f"[{status}] {case.code}: {case.description}")
    if failed_as_expected:
        failing = sorted(
            {
                line.split("::")[-1].split()[0]
                for line in output.splitlines()
                if line.startswith("FAILED")
            }
        )
        print(f"         elbukott: {', '.join(failing)}")
    else:
        print(f"         ELVÁRT bukás: {case.expected_failing}")
        print(f"         pytest kilépési kód: {code}")
        if verbose:
            print("         --- kimenet ---")
            for line in output.splitlines()[-25:]:
                print("         " + line)
    return failed_as_expected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", type=Path, help="a vizsgálandó repó gyökere")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    source = args.repo.resolve()
    if not (source / "pyproject.toml").is_file():
        print(f"HIBA: {source} nem tűnik a repó gyökerének", file=sys.stderr)
        return 2

    print("=" * 72)
    print("VQEBD — negatív teszt harness (TP-F00, 4.2 szakasz)")
    print(f"Forrás: {source}")
    print("Minden eset izolált másolaton fut; az eredeti repó változatlan marad.")
    print("=" * 72)

    # Előfeltétel: a sértetlen repón MINDEN tesztnek zöldnek kell lennie.
    print("\n[ELŐ ] Alapállapot ellenőrzése (sértetlen repó)...")
    with tempfile.TemporaryDirectory(prefix="vqebd-neg-base-") as tmp:
        base = Path(tmp) / "repo"
        shutil.copytree(source, base, ignore=EXCLUDE, symlinks=True)
        code, output = run_pytest(base)
    if code != 0:
        print("[HIBA] A sértetlen repón is bukik teszt — a negatív körnek nincs értelme.")
        print(output[-2000:])
        return 1
    print("[OK  ] A sértetlen repón minden teszt zöld.\n")

    results = [check_case(case, source, args.verbose) for case in CASES]

    print("\n" + "=" * 72)
    passed = sum(results)
    print(f"Eredmény: {passed}/{len(results)} negatív eset bukott el az elvárt módon.")
    if passed != len(results):
        print("FIGYELEM: van olyan védelem, amely NEM működik.")
        return 1
    print("Minden védelmi teszt bizonyítottan képes hibát jelezni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
