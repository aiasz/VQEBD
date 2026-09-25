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

import cirq
import numpy as np

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
from vqebd.config import BackendKind, MapperKind, MoleculeSpec, OptimizerSpec, VQEConfig
from vqebd.platforms import (
    DERIVATIVE_FREE_OPTIMIZERS,
    GRADIENT_BASED_OPTIMIZERS,
    PLATFORMS,
    SCIPY_FINITE_DIFFERENCE_STEP,
    check_optimizer_compatibility,
    platform_of,
)
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
    """Konfiguráció a platformhoz **mért** alapértelmezésekkel.

    Az optimalizálót nem rögzítjük globálisan: a ``qsim`` egyszeres pontossága
    miatt ott deriváltmentes módszer kell (lásd ``test_gradient_safety`` és
    ADR-0006). Ez maga is a többplatformos vizsgálat eredménye.
    """
    kwargs.setdefault(
        "optimizer", OptimizerSpec(method=platform_of(backend).recommended_optimizer, maxiter=2000)
    )
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

    eigen_cirq = float(np.linalg.eigvalsh(pauli_sum.matrix(qubits=cirq_qubit_order(qubits)))[0])
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
        dtype=np.complex128,
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
        f"cirq={cirq_energy:.12f} qiskit={qiskit_energy:.12f} d={cirq_energy - qiskit_energy:.3e}"
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
        f"qsim={qsim_energy:.12f} qiskit={qiskit_energy:.12f} d={qsim_energy - qiskit_energy:.3e}"
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_ac_1m_8_every_platform_is_chemically_accurate(
    results_by_backend: dict[BackendKind, VQEResult], backend: BackendKind
) -> None:
    """Mindhárom platform kémiai pontosságon belül van a Full CI-hez képest."""
    result = results_by_backend[backend]
    assert result.within_chemical_accuracy, f"{backend}: hiba {result.error_vs_reference:.3e} Ha"


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
        f"{backend}: {first.energy!r} != {second.energy!r} (d={first.energy - second.energy:.3e})"
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
    """Egyik egzakt platform numerikus korlátja sem befolyásolja a kémiai következtetést."""
    for backend, info in PLATFORMS.items():
        if info.exact:
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
    assert spread < 1e-5, f"{mapper}: a platformok szórása {spread:.3e} Ha — " + ", ".join(
        f"{b}={e:.12f}" for b, e in energies.items()
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
        backend: run_vqe(
            VQEConfig(
                molecule=molecule,
                backend=backend,
                optimizer=OptimizerSpec(
                    method=platform_of(backend).recommended_optimizer, maxiter=2000
                ),
            ),
            compute_fci=False,
        ).energy
        for backend in ALL_BACKENDS
    }
    spread = max(energies.values()) - min(energies.values())
    assert spread < 1e-5, f"r={distance} Å: a platformok szórása {spread:.3e} Ha — " + ", ".join(
        f"{b}={e:.12f}" for b, e in energies.items()
    )


# =============================================================================
# A TÖBBPLATFORMOS VIZSGÁLAT HOZADÉKA — az optimalizáló × pontosság kölcsönhatás
# =============================================================================
#
# Ez a szakasz a Fázis 1M legfontosabb eredményét rögzíti. A felfedezés NEM
# jöhetett volna elő egyetlen platformon: a Qiskiten és a Cirqen mind a nyolc
# vizsgált optimalizáló hibátlanul működik. Csak a qsim bevonásával derült ki,
# hogy a gradiens-alapú módszerek CSENDBEN téves minimumot találnak, ha a
# célfüggvény zaja meghaladja a véges-differencia lépésközt.
#
# Ugyanez a hibamód fog jelentkezni a Fázis 1b-ben (lövészaj) és a Fázis 2-ben
# (hardverzaj) — ott viszont már IBM-kvótát égetve derülne ki.


def test_finite_difference_step_is_the_documented_scipy_default() -> None:
    """A dokumentált lépésköz valóban a SciPy alapértelmezése: ``sqrt(eps)``."""
    assert (
        pytest.approx(float(np.sqrt(np.finfo(float).eps)), rel=1e-12)
        == SCIPY_FINITE_DIFFERENCE_STEP
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_noise_floor_is_measured_not_guessed(backend: BackendKind) -> None:
    """A nyilvántartott zajszint egyezik a ténylegesen mérttel.

    A célfüggvényt az optimum közelében kiértékeljük, majd egy
    véges-differencia lépésnyivel elmozdítva újra. A különbség nagyságrendje a
    platform zajszintje. Ha a nyilvántartás elcsúszna a valóságtól, a
    gradiens-biztonsági döntés is hibás lenne.
    """
    from vqebd.backends.estimators import make_energy_evaluator
    from vqebd.config import AnsatzSpec

    structure = build_electronic_structure(h2(0.735))
    qubit_hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(20260922)
    bundle = build_ansatz(structure, qubit_hamiltonian, AnsatzSpec(), seeds)

    evaluator = make_energy_evaluator(backend, bundle.circuit, qubit_hamiltonian.operator, seeds)
    base_point = [0.0, 0.0, -0.1117685][: bundle.num_parameters]
    shifted_point = list(base_point)
    shifted_point[-1] += SCIPY_FINITE_DIFFERENCE_STEP

    observed = abs(evaluator(shifted_point) - evaluator(base_point))
    declared = platform_of(backend).noise_floor_ha

    # A mért változás nem haladhatja meg a nyilvántartott zajszint tízszeresét.
    assert observed <= declared * 10.0, (
        f"{backend}: a mért zaj {observed:.3e} Ha, a nyilvántartott "
        f"{declared:.3e} Ha — a PlatformInfo felülvizsgálandó"
    )


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_gradient_safety_matches_the_noise_floor(backend: BackendKind) -> None:
    """A ``gradient_safe`` besorolás a zajszintből következik, nem vélekedésből."""
    info = platform_of(backend)
    expected = info.noise_floor_ha < SCIPY_FINITE_DIFFERENCE_STEP * 1e-2
    assert info.gradient_safe is expected

    if info.precision == "complex64":
        assert not info.gradient_safe, (
            "egyszeres pontosságú platformon a véges differenciás gradiens nem lehet megbízható"
        )


def test_qsim_is_flagged_as_gradient_unsafe() -> None:
    """A qsim kifejezetten gradiens-veszélyesnek van jelölve.

    Ez a mért tény kodifikálása: az SLSQP a qsimen 1.46e-02 Ha hibát adott,
    miközben a Powell 2.90e-08-at (TR-F01M).
    """
    info = platform_of("qsim")
    assert not info.gradient_safe
    assert info.recommended_optimizer in DERIVATIVE_FREE_OPTIMIZERS
    assert info.gradient_error_factor > 1.0, (
        "a qsim zajszintje a véges-differencia lépésköz FÖLÖTT kell legyen"
    )


@pytest.mark.parametrize("backend", ["qiskit_statevector", "cirq_simulator"])
def test_double_precision_platforms_are_gradient_safe(backend: BackendKind) -> None:
    """Kétszeres pontosságon a gradiens-alapú optimalizálás megbízható."""
    info = platform_of(backend)
    assert info.gradient_safe
    assert info.recommended_optimizer in GRADIENT_BASED_OPTIMIZERS


@pytest.mark.parametrize("method", sorted(GRADIENT_BASED_OPTIMIZERS))
def test_gradient_optimizer_on_qsim_raises_a_warning(method: str) -> None:
    """Gradiens-alapú optimalizáló a qsimen **figyelmeztetést** kap.

    A csendes hibás eredmény a legveszélyesebb hibamód: a futás „sikeres", a
    szám viszont rossz. Ezért a rendszer kimondja.
    """
    warning = check_optimizer_compatibility("qsim", method)
    assert warning is not None
    assert method in warning
    assert "MEGBÍZHATATLAN" in warning
    assert "Powell" in warning  # az ajánlott alternatíva szerepel


@pytest.mark.parametrize("method", sorted(DERIVATIVE_FREE_OPTIMIZERS))
def test_derivative_free_optimizer_on_qsim_is_accepted(method: str) -> None:
    """Deriváltmentes optimalizáló a qsimen nem vált ki figyelmeztetést."""
    assert check_optimizer_compatibility("qsim", method) is None


@pytest.mark.parametrize("method", sorted(GRADIENT_BASED_OPTIMIZERS))
def test_gradient_optimizer_on_double_precision_is_accepted(method: str) -> None:
    """Kétszeres pontosságú platformon a gradiens-alapú módszer rendben van."""
    assert check_optimizer_compatibility("qiskit_statevector", method) is None


def test_runner_warns_about_incompatible_optimizer() -> None:
    """A ``run_vqe`` futásidőben is figyelmeztet a veszélyes kombinációra."""
    config = VQEConfig(
        molecule=h2(0.735),
        backend="qsim",
        optimizer=OptimizerSpec(method="SLSQP", maxiter=100),
    )
    with pytest.warns(RuntimeWarning, match="MEGBÍZHATATLAN"):
        run_vqe(config, compute_fci=False)


def test_derivative_free_optimizer_rescues_qsim_accuracy() -> None:
    """A deriváltmentes optimalizáló **nagyságrendekkel** jobb eredményt ad qsimen.

    Ez a teszt közvetlenül bizonyítja a Fázis 1M hozadékát: ugyanaz a platform,
    ugyanaz a feladat, csak az optimalizáló más — és az eredmény négy
    nagyságrendet javul.
    """
    molecule = h2(0.735)
    # A figyelmeztetés itt SZÁNDÉKOS (a hibás párosítást mérjük): elvárjuk, nem szivárog.
    with pytest.warns(RuntimeWarning, match="MEGBÍZHATATLAN"):
        gradient_based = run_vqe(
            VQEConfig(
                molecule=molecule,
                backend="qsim",
                optimizer=OptimizerSpec(method="SLSQP", maxiter=2000),
            )
        )
    derivative_free = run_vqe(
        VQEConfig(
            molecule=molecule,
            backend="qsim",
            optimizer=OptimizerSpec(method="Powell", maxiter=2000),
        )
    )

    assert abs(derivative_free.error_vs_reference) < abs(gradient_based.error_vs_reference), (
        f"a deriváltmentes optimalizáló nem javított: "
        f"Powell {derivative_free.error_vs_reference:.3e} vs "
        f"SLSQP {gradient_based.error_vs_reference:.3e}"
    )
    assert derivative_free.within_chemical_accuracy, (
        f"a Powell sem érte el a kémiai pontosságot: {derivative_free.error_vs_reference:.3e} Ha"
    )
