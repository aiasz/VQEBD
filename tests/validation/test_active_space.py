"""Fázis 5 — aktív tér validáció (AC-5.1, AC-5.2, AC-5.3, TP-F05).

Az aktívtér-redukció két független kódúton számol:

- **Qiskit Nature** ``ActiveSpaceTransformer`` → leképezés → egzakt diagonalizáció (L1);
- **PySCF** ``mcscf.CASCI`` (L0′).

A kettő egyezése igazolja a redukciót és az energiaeltolás kezelését.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import beh2, h2, lih
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA, collect_references
from vqebd.config import ActiveSpaceSpec, BackendKind, OptimizerSpec, VQEConfig
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation

# A v0.7.1 kóddal, az új mezők bevezetése ELŐTT rögzített ujjlenyomatok (2026-09-25).
V071_H2_DEFAULT = "f365310d0350b2e45c616047246e9c36d00684e400ae962e20a38905fc102546"  # config_hash
V071_LIH_ZNE = "673a245104b004b814b595ade3aac072798081ff063646b302c6e90145d7c459"  # config_hash


@pytest.mark.parametrize(
    ("molecule", "active_space", "qubits"),
    [
        (lih(), ActiveSpaceSpec(2, 3), 4),
        (lih(), ActiveSpaceSpec(2, 5), 8),
        (beh2(), ActiveSpaceSpec(2, 3), 4),
    ],
    ids=["LiH(2e,3o)", "LiH(2e,5o)", "BeH2(2e,3o)"],
)
def test_ac_5_1_exact_diagonalization_matches_casci(
    molecule: object, active_space: ActiveSpaceSpec, qubits: int
) -> None:
    """AC-5.1: L1 (Qiskit Nature) = L0′ (PySCF CASCI), ≤ 1e-10 Ha."""
    structure = build_electronic_structure(molecule, active_space)  # type: ignore[arg-type]
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    refs = collect_references(structure, hamiltonian)
    assert hamiltonian.num_qubits == qubits
    assert refs.casci is not None and refs.exact_diagonalization is not None
    assert abs(refs.exact_diagonalization - refs.casci) < 1e-10
    assert refs.mapping_error is not None and abs(refs.mapping_error) < 1e-10
    # A csonkolás variációs: a CASCI nem lehet az FCI alatt.
    assert refs.truncation_error is not None and refs.truncation_error > -1e-10


def test_ac_5_2_full_space_offset_equals_nuclear_repulsion() -> None:
    """AC-5.2: teljes térben az energiaeltolás bitre a magtaszítás (Fázis 1–4 változatlan)."""
    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    assert structure.inactive_energy == 0.0
    assert structure.energy_offset == structure.nuclear_repulsion_energy
    assert hamiltonian.energy_offset == hamiltonian.nuclear_repulsion_energy
    result = run_vqe(VQEConfig(molecule=h2()))
    assert result.offset == result.nuclear_repulsion_energy
    assert result.reference.casci is None and result.reference.truncation_error is None


def test_ac_5_2_config_fingerprints_are_unchanged() -> None:
    """AC-5.2: az új mezők alapértéken nem változtatják a v0.7.x ujjlenyomatokat.

    A várt értékek a v0.7.1 kóddal rögzítve (2026-09-25), a mezők bevezetése előtt.
    """
    from vqebd.config import MitigationSpec

    assert VQEConfig(molecule=h2()).fingerprint() == V071_H2_DEFAULT
    lih_zne = VQEConfig(
        molecule=lih(),
        backend="qiskit_aer_noisy",
        optimizer=OptimizerSpec(method="COBYLA"),
        mitigation=MitigationSpec(strategy="zne_local"),
    )
    assert lih_zne.fingerprint() == V071_LIH_ZNE
    with_active = VQEConfig(molecule=lih(), active_space=ActiveSpaceSpec(2, 3))
    assert with_active.fingerprint() != VQEConfig(molecule=lih()).fingerprint()


def test_active_space_offset_includes_inactive_energy() -> None:
    """Aktív térben az eltolás = magtaszítás + inaktív energia (LiH: ~−7.8 Ha)."""
    structure = build_electronic_structure(lih(), ActiveSpaceSpec(2, 5))
    assert structure.inactive_energy < -7.0
    assert structure.energy_offset == pytest.approx(
        structure.nuclear_repulsion_energy + structure.inactive_energy
    )
    assert structure.num_spatial_orbitals == 5
    assert structure.num_particles == (1, 1)


@pytest.mark.parametrize(
    ("backend", "method"),
    [("qiskit_statevector", "SLSQP"), ("cirq_simulator", "SLSQP"), ("qsim", "Powell")],
)
def test_ac_5_3_active_space_vqe_on_all_platforms(backend: BackendKind, method: str) -> None:
    """AC-5.3: LiH (2e,3o) teljes energiája helyes mindhárom platformon (L2 − L1 < 1.6 mHa).

    A teljes energiához az aktív térben az inaktív energiát is hozzá kell adni —
    ha a futtató csak a magtaszítást adná hozzá, a hiba ~7.8 Ha lenne.
    """
    result = run_vqe(
        VQEConfig(
            molecule=lih(),
            active_space=ActiveSpaceSpec(2, 3),
            backend=backend,
            optimizer=OptimizerSpec(method=method, maxiter=2000),
        )
    )
    error = result.error_vs_exact_diagonalization
    assert error is not None
    assert -1e-9 < error < CHEMICAL_ACCURACY_HA
    assert result.within_backend_tolerance


@pytest.mark.parametrize(
    ("active_space", "message"),
    [
        (ActiveSpaceSpec(2, 9), "nem értelmezhető"),  # több pálya, mint amennyi van
        (ActiveSpaceSpec(3, 2), "nem értelmezhető"),  # páratlan elektronszám zárt héjon
    ],
)
def test_invalid_active_space_is_rejected(active_space: ActiveSpaceSpec, message: str) -> None:
    """Negatív: értelmetlen aktív tér beszédes ValueError-t ad, nem mély kivételt."""
    with pytest.raises(ValueError, match=message):
        build_electronic_structure(lih(), active_space)


@pytest.mark.parametrize(
    ("electrons", "orbitals", "message"),
    [(0, 3, "elektronok"), (2, 0, "pályák"), (7, 3, "nem fér el")],
)
def test_active_space_spec_validation(electrons: int, orbitals: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ActiveSpaceSpec(electrons, orbitals)


def test_active_space_label() -> None:
    assert ActiveSpaceSpec(4, 6).label == "(4e,6o)"
