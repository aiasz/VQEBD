"""A konfigurációs réteg egységtesztjei.

Ezek a tesztek **nem igénylik a kvantum-stacket**: a ``vqebd.config`` modul
szándékosan függőségmentes, hogy a konfiguráció bárhol validálható legyen.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from vqebd.config import AnsatzSpec, MoleculeSpec, OptimizerSpec, VQEConfig

pytestmark = pytest.mark.unit


def _molecule() -> MoleculeSpec:
    return MoleculeSpec(name="H2", atom="H 0 0 0; H 0 0 0.735", bond_length=0.735)


# --- Validálás ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"name": ""}, "neve nem lehet üres"),
        ({"atom": "   "}, "geometria"),
        ({"spin": -1}, "spin"),
        ({"bond_length": 0.0}, "kötéshossznak"),
        ({"bond_length": -1.0}, "kötéshossznak"),
    ],
)
def test_molecule_spec_rejects_invalid_input(kwargs: dict[str, object], fragment: str) -> None:
    """Az érvénytelen bemenet beszédes hibát ad, nem csendes rossz eredményt."""
    base = {"name": "H2", "atom": "H 0 0 0; H 0 0 0.735"}
    with pytest.raises(ValueError, match=fragment):
        MoleculeSpec(**{**base, **kwargs})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [("maxiter", 0), ("maxiter", -5), ("tol", 0.0), ("tol", -1e-3)],
)
def test_optimizer_spec_rejects_invalid_input(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=field):
        OptimizerSpec(**{field: value})  # type: ignore[arg-type]


# --- Immutabilitás -----------------------------------------------------------


def test_config_is_frozen() -> None:
    """A konfiguráció futás közben nem módosítható."""
    config = VQEConfig(molecule=_molecule())
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.mapper = "jordan_wigner"  # type: ignore[misc]


def test_molecule_spec_is_frozen() -> None:
    molecule = _molecule()
    with pytest.raises(dataclasses.FrozenInstanceError):
        molecule.basis = "6-31g"  # type: ignore[misc]


def test_config_is_hashable() -> None:
    """Hash-elhetőség: a konfiguráció használható szótárkulcsként és halmazelemként.

    Ez azt is bizonyítja, hogy nincs benne módosítható (``list``, ``dict``) mező.
    """
    config = VQEConfig(molecule=_molecule())
    assert hash(config) == hash(VQEConfig(molecule=_molecule()))
    assert len({config, VQEConfig(molecule=_molecule())}) == 1


# --- Ujjlenyomat -------------------------------------------------------------


def test_fingerprint_is_deterministic() -> None:
    """Azonos konfiguráció → azonos ujjlenyomat, futásról futásra."""
    assert VQEConfig(molecule=_molecule()).fingerprint() == (
        VQEConfig(molecule=_molecule()).fingerprint()
    )


def test_fingerprint_is_a_sha256_hex_digest() -> None:
    fingerprint = VQEConfig(molecule=_molecule()).fingerprint()
    assert len(fingerprint) == 64
    assert all(ch in "0123456789abcdef" for ch in fingerprint)


@pytest.mark.parametrize(
    "change",
    [
        {"mapper": "jordan_wigner"},
        {"two_qubit_reduction": False},
        {"seed": 1},
        {"ansatz": AnsatzSpec(initial_point="random")},
        {"optimizer": OptimizerSpec(method="COBYLA")},
        {"backend": "qiskit_aer_shot"},
        {"backend": "qiskit_aer_noisy"},
    ],
)
def test_fingerprint_changes_with_configuration(change: dict[str, object]) -> None:
    """Bármely érdemi módosítás megváltoztatja az ujjlenyomatot.

    Enélkül két különböző futás azonos azonosítót kapna az adatbázisban, és az
    eredmények összekeverednének.
    """
    base = VQEConfig(molecule=_molecule())
    modified = dataclasses.replace(base, **change)  # type: ignore[arg-type]
    assert modified.fingerprint() != base.fingerprint()


def test_fingerprint_changes_with_geometry() -> None:
    """Eltérő kötéshossz → eltérő ujjlenyomat (a disszociációs görbe pontjai)."""
    a = VQEConfig(molecule=MoleculeSpec(name="H2", atom="H 0 0 0; H 0 0 0.735"))
    b = VQEConfig(molecule=MoleculeSpec(name="H2", atom="H 0 0 0; H 0 0 0.740"))
    assert a.fingerprint() != b.fingerprint()


def test_short_fingerprint_is_a_prefix() -> None:
    config = VQEConfig(molecule=_molecule())
    assert config.fingerprint().startswith(config.short_fingerprint())
    assert len(config.short_fingerprint()) == 12


# --- Szerializálás -----------------------------------------------------------


def test_canonical_json_is_sorted_and_compact() -> None:
    """A kanonikus JSON rendezett kulcsú — különben az ujjlenyomat ingadozna."""
    raw = VQEConfig(molecule=_molecule()).canonical_json()
    parsed = json.loads(raw)
    assert list(parsed) == sorted(parsed)
    assert ", " not in raw, "a kanonikus alak kompakt elválasztókat használ"


def test_to_dict_round_trips_through_json() -> None:
    """A szótár-alak JSON-ba szerializálható (a Fázis 4 tárolásának feltétele)."""
    data = VQEConfig(molecule=_molecule()).to_dict()
    assert json.loads(json.dumps(data)) == data
