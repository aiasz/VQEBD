"""A seed-származtatás egységtesztjei (ADR-0005).

A determinizmus a projekt egyik alapkövetelménye. Ezek a tesztek azt igazolják,
hogy a seed-származtatás **tiszta függvény**: környezettől, futástól és
platformtól független.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import dataclasses

import pytest

from vqebd.seeds import MAX_SEED, SeedSet, derive_seed

pytestmark = pytest.mark.unit

MASTER = 20260922


# --- Rögzített, „arany-érték" tesztek ----------------------------------------
#
# Az alábbi számok a BLAKE2b-alapú származtatás TÉNYLEGES kimenetei, beégetve.
# Szándékosan nem a `derive_seed` újrahívásával számoljuk őket: az tautologikus
# lenne, és bármilyen algoritmusváltozást csendben átengedne.
#
# Ha a származtatási algoritmus megváltozik, ezek a tesztek elbuknak — és ez a
# helyes viselkedés: egy ilyen változás MINDEN korábbi eredmény
# reprodukálhatóságát érvénytelenítené (a rögzített seedből más véletlensorozat
# születne). Ezért tudatos, verzióemeléssel és adatséma-migrációval járó
# döntésnek kell lennie, nem észrevétlen mellékhatásnak.
#
# Mérve: 2026-09-22, Python 3.11.16, linux/amd64.

GOLDEN_SEEDS: dict[str, int] = {
    "master": 20260922,
    "simulator": 1380152212,
    "transpiler": 710684171,
    "optimizer": 745637060,
    "mitigation": 930697387,
    "initial_point": 1974306394,
}

GOLDEN_DERIVATIONS: dict[tuple[int, str], int] = {
    (0, "simulator"): 1593055091,
    (1, "simulator"): 1694270369,
    (MASTER, "simulator"): 1380152212,
}


def test_derive_seed_is_deterministic() -> None:
    """Ugyanaz a bemenet mindig ugyanazt adja."""
    assert derive_seed(MASTER, "simulator") == derive_seed(MASTER, "simulator")


def test_derive_seed_depends_on_master() -> None:
    assert derive_seed(1, "simulator") != derive_seed(2, "simulator")


def test_derive_seed_depends_on_label() -> None:
    """Különböző komponensek különböző seedet kapnak — nincs korreláció."""
    assert derive_seed(MASTER, "simulator") != derive_seed(MASTER, "transpiler")


@pytest.mark.parametrize("master", [0, 1, 42, 20260922, 2**31 - 1, 2**63])
def test_derive_seed_is_in_range(master: int) -> None:
    """A származtatott seed belefér a NumPy/Qiskit/SciPy közös tartományába."""
    for label in ("simulator", "transpiler", "optimizer", "mitigation", "initial_point"):
        seed = derive_seed(master, label)
        assert 0 <= seed < MAX_SEED


# --- SeedSet -----------------------------------------------------------------


def test_seed_set_derive_is_deterministic() -> None:
    assert SeedSet.derive(MASTER) == SeedSet.derive(MASTER)


def test_seed_set_keeps_master() -> None:
    assert SeedSet.derive(MASTER).master == MASTER


def test_seed_set_components_are_distinct() -> None:
    """Az öt származtatott seed különbözik egymástól.

    Ütköző seedek rejtett korrelációt okoznának a komponensek között (pl. a
    szimulátor és a transzpiler ugyanazt a véletlensorozatot használná).
    """
    seeds = SeedSet.derive(MASTER)
    values = [
        seeds.simulator,
        seeds.transpiler,
        seeds.optimizer,
        seeds.mitigation,
        seeds.initial_point,
    ]
    assert len(set(values)) == len(values), f"ütköző seedek: {values}"


def test_seed_set_matches_golden_values() -> None:
    """A ``SeedSet`` a rögzített, beégetett értékeket adja.

    Ez a teszt a származtatási algoritmus **stabilitását** őrzi: ha bárki
    megváltoztatja (más hash, más címke, más modulus), ez azonnal jelez.
    """
    seeds = SeedSet.derive(MASTER)
    for label, expected in GOLDEN_SEEDS.items():
        actual = getattr(seeds, label)
        assert actual == expected, (
            f"a(z) '{label}' seed {actual}, a rögzített érték {expected}. "
            "Ha a származtatás szándékosan változott, ez MINDEN korábbi eredmény "
            "reprodukálhatóságát érinti — verzióemelés és migráció szükséges."
        )


@pytest.mark.parametrize(
    ("master", "label", "expected"),
    [(master, label, expected) for (master, label), expected in GOLDEN_DERIVATIONS.items()],
)
def test_derive_seed_matches_golden_values(master: int, label: str, expected: int) -> None:
    """A ``derive_seed`` rögzített bemenetekre rögzített kimenetet ad."""
    assert derive_seed(master, label) == expected


def test_seed_set_is_frozen() -> None:
    seeds = SeedSet.derive(MASTER)
    with pytest.raises(dataclasses.FrozenInstanceError):
        seeds.simulator = 0  # type: ignore[misc]


def test_seed_set_rejects_negative_master() -> None:
    with pytest.raises(ValueError, match="nem lehet negatív"):
        SeedSet.derive(-1)


def test_seed_set_to_dict_contains_every_field() -> None:
    """Az eredményrekordba **minden** seed bekerül, nem csak a mester."""
    data = SeedSet.derive(MASTER).to_dict()
    assert set(data) == {
        "master",
        "simulator",
        "transpiler",
        "optimizer",
        "mitigation",
        "initial_point",
    }
    assert all(isinstance(v, int) for v in data.values())
