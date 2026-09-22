"""Fázis 1M validációs tesztek — Qiskit ↔ Cirq ↔ qsim.

Ez a modul a **platform-dimenzió** helyességét igazolja
(``docs/plan/phase_01m.md``, 6. fejezet).

A legfontosabb állítás nem az, hogy a három platform ugyanazt az energiát adja —
hanem hogy a **konverzió mátrixszinten egzakt**. Egy szimmetrikus
Hamilton-operátoron a rossz qubit-sorrend véletlenül helyes energiát is adhat, és
csak egy aszimmetrikus rendszernél (LiH, BeH2 — Fázis 5) bukna ki, amikor már a
teljes batch-infrastruktúra rá épül.

Ezért itt **mátrixot és állapotvektort** hasonlítunk össze, nem csak energiát.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

pytest.importorskip("qiskit_nature", reason="a Fázis 1 kvantum-stackjét igényli")
pytest.importorskip("pyscf", reason="a Fázis 1 kvantum-stackjét igényli")
pytest.importorskip("cirq", reason="a Fázis 1M Cirq-platformját igényli")
pytest.importorskip("qsimcirq", reason="a Fázis 1M qsim-platformját igényli")

import numpy as np

import cirq

from vqebd.backends.conversion import (
    CIRQ_BASIS_GATES,
    cirq_qubit_order,
    to_cirq_circuit,
    to_cirq_pauli_sum,
    transpile_for_cirq,
)
from vqebd.chemistry.mapping import map_to_qubits
from vqebd.chemistry.molecule import h2
from vqebd.chemistry.problem import build_electronic_structure
from vqebd.config import BackendKind, MapperKind, MoleculeSpec, VQEConfig
from vqebd.platforms import PLATFORMS, platform_of
from vqebd.seeds import SeedSet
from vqebd.vqe.ansatz import build_ansatz
from vqebd.vqe.result import VQEResult
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation

ALL_BACKENDS: tuple[BackendKind, ...] = ("qiskit_statevector", "cirq_simulator", "qsim")
ALL_MAPPERS: tuple[MapperKind, ...] = ("jordan_wigner", "parity", "bravyi_kitaev")

MATRIX_TOLERANCE = 1e-12
"""A konverziónak **egzaktnak** kell lennie: azonos számokból azonos mátrix."""


def _config(backend: BackendKind = "qiskit_statevector", **kwargs: object) -> VQEConfig:
    return VQEConfig(molecule=h2(0.735), backend=backend, **kwargs)  # type: ignore[arg-type]


@pytest.fixture(scope="module")
def hamiltonian() -> object:
    structure = build_electronic_structure(h2(0.735))
    return map_to_qubits(structure, "parity", two_qubit_reduction=True)


@pytest.fixture(scope="module")
def results_by_backend() -> dict[BackendKind, VQEResult]:
    """Ugyanaz a feladat mindhárom platformon."""
    return {backend: run_vqe(_config(backend)) for backend in ALL_BACKENDS}


# =============================================================================
# AC-1M.2 / AC-1M.3 — a Hamilton-konverzió mátrixszinten egzakt
# =============================================================================


def test_ac_1m_2_hamiltonian_conversion_matches_matrix(hamiltonian: object) -> None:
    """A konvertált ``cirq.PauliSum`` mátrixa **bitre** megegyezik a Qiskitével.

    Ez a Fázis 1M központi állítása. Energiaszintű összehasonlítás nem lenne
    elég: szimmetrikus operátoron a hibás qubit-sorrend is helyes energiát adhat.
    """
    operator = hamiltonian.operator  # type: ignore[attr-defined]
    qubits = cirq.LineQubit.range(operator.num_qubits)
    pauli_sum = to_cirq_pauli_sum(operator, qubits)

    matrix_cirq = pauli_sum.matrix(qubits=cirq_qubit_order(qubits))
    matrix_qiskit = operator.to_matrix()

    deviation = float(np.max(np.abs(matrix_cirq - matrix_qiskit)))
    assert deviation < MATRIX_TOLERANCE, (
        f"a konvertált Hamilton-operátor mátrixa eltér: max|ΔM| = {deviation:.3e}. "
        "Ez majdnem biztosan qubit-sorrend (endianness) hiba."
    )


def test_ac_1m_3_wrong_qubit_order_is_detectably_different(hamiltonian: object) -> None:
    """A **rossz** qubit-sorrend kimutathatóan hibás mátrixot ad.

    Ez fordított irányú állítás: azt igazolja, hogy az előző teszt nem triviálisan
    teljesül. Ha a két sorrend ugyanazt adná, a teszt semmit nem bizonyítana.
    """
    operator = hamiltonian.operator  # type: ignore[attr-defined]
    qubits = cirq.LineQubit.range(operator.num_qubits)
    pauli_sum = to_cirq_pauli_sum(operator, qubits)

    wrong = pauli_sum.matrix(qubits=list(qubits))  # szándékosan NEM fordított
    deviation = float(np.max(np.abs(wrong - operator.to_matrix())))
    assert deviation > 1e-6, (
        "az egyenes és a fordított qubit-sorrend ugyanazt a mátrixot adja, ezért a "
        "helyességi teszt nem bizonyít semmit. Válassz aszimmetrikusabb tesztesetet."
    )


@pytest.mark.parametrize("mapper", ALL_MAPPERS)
def test_hamiltonian_conversion_for_every_mapper(mapper: MapperKind) -> None:
    """A konverzió mindhárom leképezésre egzakt — eltérő qubit-számokkal is."""
    structure = build_electronic_structure(h2(0.735))
    qubit_hamiltonian = map_to_qubits(structure, mapper, two_qubit_reduction=True)
    operator = qubit_hamiltonian.operator
    qubits = cirq.LineQubit.range(operator.num_qubits)
    pauli_sum = to_cirq_pauli_sum(operator, qubits)

    deviation = float(
        np.max(np.abs(pauli_sum.matrix(qubits=cirq_qubit_order(qubits)) - operator.to_matrix()))
    )
    assert deviation < MATRIX_TOLERANCE, f"{mapper}: max|ΔM| = {deviation:.3e}"


def test_converted_hamiltonian_has_the_same_ground_state(hamiltonian: object) -> None:
    """A konvertált operátor legkisebb sajátértéke megegyezik — L1 két úton."""
    operator = hamiltonian.operator  # type: ignore[attr-defined]
    qubits = cirq.LineQubit.range(operator.num_qubits)
    pauli_sum = to_cirq_pauli_sum(operator, qubits)

    eigen_cirq = float(
        np.linalg.eigvalsh(pauli_sum.matrix(qubits=cirq_qubit_order(qubits)))[0]
    )
    eigen_qiskit = float(np.linalg.eigvalsh(operator.to_matrix())[0])
    assert eigen_cirq == pytest.approx(eigen_qiskit, abs=1e-12)


# =============================================================================
# AC-1M.4 / AC-1M.5 — áramkör-konverzió
# =============================================================================


def test_ac_1m_4_circuit_conversion_preserves_the_state(hamiltonian: object) -> None:
    """A konvertált áramkör ugyanazt az állapotot állítja elő.

    Globális fázistól eltekintve: az energia fázisinvariáns, ezért **abszolút
    átfedést** hasonlítunk össze, nem elemenkénti egyenlőséget.
    """
    from qiskit.quantum_info import Statevector

    structure = build_electronic_structure(h2(0.735))
    seeds = SeedSet.derive(20260922)
    bundle = build_ansatz(structure, hamiltonian, _config().ansatz, seeds)  # type: ignore[arg-type]

    parameters = [0.11, -0.23, 0.37][: bundle.num_parameters]
    bound = bundle.circuit.assign_parameters(parameters)
    transpiled = transpile_for_cirq(bound, seed_transpiler=seeds.transpiler)

    qubits = cirq.LineQubit.range(transpiled.num_qubits)
    converted = to_cirq_circuit(transpiled, qubits)

    state_qiskit = np.asarray(Statevector(transpiled).data)
    state_cirq = np.asarray(
        cirq.Simulator(dtype=np.complex128)
        .simulate(converted, qubit_order=cirq_qubit_order(qubits))
        .final_state_vector,
        dtype=complex,
    )

    overlap = abs(complex(np.vdot(state_cirq, state_qiskit)))
    assert overlap == pytest.approx(1.0, abs=1e-9), (
        f"|⟨ψ_cirq|ψ_qiskit⟩| = {overlap:.12f}, nem 1.0 — az áramkör-konverzió hibás"
    )


def test_ac_1m_4_circuit_conversion_preserves_width() -> None:
    """Az inaktív qubitek sem vesznek el (a Mitiq QASM-konverziójának hibája)."""
    from qiskit import QuantumCircuit

    circuit = QuantumCircuit(4)
    circuit.h(0)
    circuit.cx(0, 1)  # a 2. és 3. qubiten NINCS művelet

    qubits = cirq.LineQubit.range(4)
    converted = to_cirq_circuit(circuit, qubits)
    assert len(converted.all_qubits()) == 4, (
        f"a konverzió {len(converted.all_qubits())} qubitet tartott meg 4 helyett"
    )


def test_ac_1m_5_unknown_gate_raises_with_its_name() -> None:
    """Ismeretlen kapu esetén azonnali, beszédes hiba — nem néma kihagyás."""
    from qiskit import QuantumCircuit

    circuit = QuantumCircuit(2)
    circuit.swap(0, 1)  # nincs a CIRQ_BASIS_GATES készletben

    with pytest.raises(ValueError, match="swap"):
        to_cirq_circuit(circuit, cirq.LineQubit.range(2))


def test_transpiled_circuit_uses_only_known_gates(hamiltonian: object) -> None:
    """A transzpilálás után minden kapu szerepel a konverter leképezésében."""
    structure = build_electronic_structure(h2(0.735))
    seeds = SeedSet.derive(20260922)
    bundle = build_ansatz(structure, hamiltonian, _config().ansatz, seeds)  # type: ignore[arg-type]
    bound = bundle.circuit.assign_parameters([0.1] * bundle.num_parameters)
    transpiled = transpile_for_cirq(bound, seed_transpiler=seeds.transpiler)

    unknown = set(transpiled.count_ops()) - set(CIRQ_BASIS_GATES) - {"barrier", "id", "delay"}
    assert not unknown, f"a transzpilált áramkörben ismeretlen kapu van: {sorted(unknown)}"


# =============================================================================
# AC-1M.6 … AC-1M.8 — energia-egyezés
# =============================================================================


def test_ac_1m_6_cirq_agrees_with_qiskit(
    results_by_backend: dict[BackendKind, VQEResult],
) -> None:
    """A Cirq (``complex128``) a Qiskittől 1e-9 Ha-on belül van."""
    qiskit_energy = results_by_backend["qiskit_statevector"].energy
    cirq_energy = results_by_backend["cirq_simulator"].energy
    assert cirq_energy == pytest.approx(qiskit_energy, abs=1e-9), (
        f"cirq={cirq_energy:.12f} qiskit={qiskit_energy:.12f} "
        f"d={cirq_energy - qiskit_energy:.3e}"
    )


def test_ac_1m_7_qsim_agrees_with_qiskit(
    results_by_backend: dict[BackendKind, VQEResult],
) -> None:
    """A qsim (``complex64``) a Qiskittől 1e-5 Ha-on belül van.

    A lazább tolerancia **nem engedmény**, hanem a 32 bites aritmetika
    következménye: a qsim gépi epszilonja 1.19e-7 (lásd ADR-0006).
    """
    qiskit_energy = results_by_backend["qiskit_statevector"].energy
    qsim_energy = results_by_backend["qsim"].energy
    assert qsim_energy == pytest.approx(qiskit_energy, abs=1e-5), (
        f"qsim={qsim_energy:.12f} qiskit={qiskit_energy:.12f} "
        f"d={qsim_energy - qiskit_energy:.3e}"
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_ac_1m_8_every_platform_is_chemically_accurate(
    results_by_backend: dict[BackendKind, VQEResult], backend: BackendKind
) -> None:
    """Mindhárom platform kémiai pontosságon belül van a Full CI-hez képest."""
    result = results_by_backend[backend]
    assert result.within_chemical_accuracy, (
        f"{backend}: hiba {result.error_vs_reference:.3e} Ha"
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_every_platform_is_within_its_own_tolerance(
    results_by_backend: dict[BackendKind, VQEResult], backend: BackendKind
) -> None:
    """Minden platform a **saját**, számábrázolásból levezetett toleranciáján belül van."""
    result = results_by_backend[backend]
    assert result.within_backend_tolerance, (
        f"{backend} ({result.precision}): hiba {result.error_vs_reference:.3e} Ha, "
        f"tolerancia {result.backend_tolerance_ha:.3e} Ha"
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_ac_1m_10_variational_principle_on_every_platform(
    results_by_backend: dict[BackendKind, VQEResult], backend: BackendKind
) -> None:
    """A variációs elv mindhárom platformon teljesül."""
    result = results_by_backend[backend]
    tolerance = platform_of(backend).tolerance_ha
    assert result.error_vs_reference > -tolerance, (
        f"{backend}: a variációs elv sérül, eltérés {result.error_vs_reference:.3e} Ha"
    )


# =============================================================================
# AC-1M.9 — determinizmus platformonként
# =============================================================================


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_ac_1m_9_determinism_per_platform(backend: BackendKind) -> None:
    """Minden platform bitre azonos eredményt ad kétszeri futtatásra.

    A qsim esetében ez azért nem magától értetődő, mert a C++ oldal többszálú
    is lehetne; ezért rögzítjük a ``cpu_threads = 1`` beállítást (ADR-0006).
    """
    config = _config(backend)
    first = run_vqe(config)
    second = run_vqe(config)
    assert first.energy == second.energy, (
        f"{backend}: {first.energy!r} != {second.energy!r} "
        f"(d={first.energy - second.energy:.3e})"
    )


# =============================================================================
# AC-1M.11 — a qsim egyszeres pontossága
# =============================================================================


def test_ac_1m_11_qsim_uses_single_precision() -> None:
    """A qsim állapotvektora ``complex64``, a Cirqé ``complex128``.

    Ez nem hiba, hanem a qsim tervezési döntése — a ~1e-7 Ha eltérés **mért
    magyarázata**. A ``QSimOptions`` nem kínál pontosság-kapcsolót.
    """
    import qsimcirq

    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit([cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1])])

    state_cirq = np.asarray(
        cirq.Simulator(dtype=np.complex128).simulate(circuit).final_state_vector
    )
    state_qsim = np.asarray(qsimcirq.QSimSimulator().simulate(circuit).final_state_vector)

    assert state_cirq.dtype == np.complex128
    assert state_qsim.dtype == np.complex64, (
        f"a qsim dtype-ja {state_qsim.dtype}, nem complex64 — az ADR-0006 "
        "pontossági indoklása felülvizsgálandó"
    )


def test_platform_tolerances_are_far_below_chemical_accuracy() -> None:
    """Egyik platform numerikus korlátja sem befolyásolja a kémiai következtetést."""
    for backend, info in PLATFORMS.items():
        assert info.chemical_accuracy_margin > 100.0, (
            f"{backend}: a tolerancia ({info.tolerance_ha:.1e} Ha) csak "
            f"{info.chemical_accuracy_margin:.1f}x van a kémiai pontosság alatt"
        )


# =============================================================================
# AC-1M.12 — a rekord tartalmazza a platform-információt
# =============================================================================


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_ac_1m_12_result_records_the_platform(
    results_by_backend: dict[BackendKind, VQEResult], backend: BackendKind
) -> None:
    """A rekord önmagában elegendő a platform utólagos azonosításához."""
    result = results_by_backend[backend]
    info = platform_of(backend)
    assert result.platform == info.platform
    assert result.precision == info.precision
    assert result.backend_tolerance_ha == info.tolerance_ha

    payload = result.to_dict()
    assert payload["backend"] == backend
    assert payload["platform"] == info.platform
    assert payload["precision"] == info.precision


# =============================================================================
# Keresztvalidáció: 3 platform × 3 leképezés, és a disszociációs görbe
# =============================================================================


@pytest.mark.parametrize("mapper", ALL_MAPPERS)
def test_x1m1_all_platforms_agree_for_every_mapper(mapper: MapperKind) -> None:
    """3 platform × 3 leképezés — kilenc kombináció, egyetlen energia."""
    energies = {
        backend: run_vqe(_config(backend, mapper=mapper)).energy for backend in ALL_BACKENDS
    }
    spread = max(energies.values()) - min(energies.values())
    assert spread < 1e-5, (
        f"{mapper}: a platformok szórása {spread:.3e} Ha — "
        + ", ".join(f"{b}={e:.12f}" for b, e in energies.items())
    )


@pytest.mark.parametrize("distance", [0.5, 1.0, 2.0])
def test_x1m4_platforms_agree_along_the_dissociation_curve(distance: float) -> None:
    """A platformok eltérő geometriákon is egyeznek.

    A 0.735 Å-ös H2 Hamilton-operátora viszonylag szimmetrikus. Más kötéshosszak
    **eltérő szerkezetű** operátort adnak, így egy esetleges qubit-sorrend-hiba
    nagyobb eséllyel bukik ki.
    """
    molecule = MoleculeSpec(name="H2", atom=f"H 0 0 0; H 0 0 {distance}", bond_length=distance)
    energies = {
        backend: run_vqe(VQEConfig(molecule=molecule, backend=backend), compute_fci=False).energy
        for backend in ALL_BACKENDS
    }
    spread = max(energies.values()) - min(energies.values())
    assert spread < 1e-5, (
        f"r={distance} Å: a platformok szórása {spread:.3e} Ha — "
        + ", ".join(f"{b}={e:.12f}" for b, e in energies.items())
    )
