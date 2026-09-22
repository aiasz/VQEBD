"""Fázis 1 validációs tesztek — H2-VQE szimulátoron.

Ez a modul a Fázis 1 **fizikai** elfogadási kritériumait ellenőrzi
(``docs/plan/phase_01.md``, 6. fejezet). A hangsúly nem azon van, hogy a kód
lefut-e, hanem hogy a **helyes számot** adja-e — három, egymástól független
referenciához mérve.

A validálás logikája
--------------------
=====  ==================================  ==========================
Szint  Mit ad                              Mit igazol az egyezés
=====  ==================================  ==========================
L0     Full CI (PySCF, független kód)      a fizikai igazság
L1     a qubit-Hamiltoni egzakt sajátért.  a leképezés helyes
L2     VQE zajmentes állapotvektoron       az ansatz és az optimalizáló jó
=====  ==================================  ==========================

Ha L2 eltér L0-tól, a lánc megmondja, **hol** a hiba: ha már L1 is eltér, a
leképezés a bűnös; ha csak L2, akkor az ansatz vagy az optimalizáló.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import pytest

pytest.importorskip("qiskit_nature", reason="a Fázis 1 kvantum-stackjét igényli")
pytest.importorskip("pyscf", reason="a Fázis 1 kvantum-stackjét igényli")

from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA
from vqebd.config import AnsatzSpec, MapperKind, OptimizerSpec, VQEConfig
from vqebd.vqe.result import VQEResult
from vqebd.vqe.runner import run_vqe

pytestmark = pytest.mark.validation

# --- Toleranciák -------------------------------------------------------------

NUMERICAL_TOLERANCE_HA = 1e-9
"""Numerikus tűrés azonos mennyiségek összehasonlításához.

Nagyságrendekkel a gépi pontosság (~1e-15) fölött, de nagyságrendekkel a kémiai
pontosság (1.6e-3) alatt: elkap minden valódi implementációs hibát, de nem
érzékeny a lebegőpontos zajra.
"""

# Az alapterv eredeti kritériuma (Fázis 1): E ≈ −1.137 Ha, ±0.01 Ha toleranciával.
PLAN_TARGET_ENERGY_HA = -1.137
PLAN_TOLERANCE_HA = 0.01

ALL_MAPPERS: tuple[MapperKind, ...] = ("jordan_wigner", "parity", "bravyi_kitaev")

# Zajmentes esetben mindegyiknek ugyanoda kell konvergálnia.
DERIVATIVE_FREE_AND_GRADIENT_METHODS = ("SLSQP", "COBYLA", "Nelder-Mead", "L-BFGS-B", "Powell")


# --- Fixture-ök (drága számítások megosztása) --------------------------------


def _config(mapper: MapperKind = "parity", **kwargs: object) -> VQEConfig:
    return VQEConfig(molecule=h2(H2_REFERENCE_BOND_LENGTH), mapper=mapper, **kwargs)  # type: ignore[arg-type]


@pytest.fixture(scope="module")
def result() -> VQEResult:
    """A Fázis 1 referencia-futtatása: H2, 0.735 Å, STO-3G, paritás, SLSQP."""
    return run_vqe(_config())


@pytest.fixture(scope="module")
def results_by_mapper() -> dict[MapperKind, VQEResult]:
    """Ugyanaz a feladat mindhárom leképezéssel."""
    return {mapper: run_vqe(_config(mapper)) for mapper in ALL_MAPPERS}


# --- AC-1.4 — az ALAPTERV eredeti kritériuma ---------------------------------


def test_ac_1_4_plan_criterion(result: VQEResult) -> None:
    """Az alapterv kritériuma: E ≈ −1.137 Ha, ±0.01 Ha.

    Ez a projekt eredeti, szerződéses elvárása. A többi teszt ennél szigorúbb,
    de ez az, amire az alapterv hivatkozik.
    """
    assert result.energy == pytest.approx(PLAN_TARGET_ENERGY_HA, abs=PLAN_TOLERANCE_HA), (
        f"E_VQE = {result.energy:.10f} Ha kívül esik a tervezett "
        f"{PLAN_TARGET_ENERGY_HA} ± {PLAN_TOLERANCE_HA} Ha ablakon"
    )


# --- AC-1.2 — L0 ≡ L1: a leképezés helyes ------------------------------------


def test_ac_1_2_mapping_is_exact(result: VQEResult) -> None:
    """A qubit-Hamiltoni egzakt sajátértéke megegyezik a PySCF Full CI energiájával.

    Ez **két teljesen független implementáció** (PySCF determináns-CI, illetve
    Qiskit Pauli-operátor + NumPy diagonalizáció) egyezése. Ha eltérnek, a
    fermion → qubit leképezés hibás.
    """
    ref = result.reference
    assert ref.full_ci is not None, "a Full CI referencia hiányzik"
    assert ref.exact_diagonalization is not None, "az egzakt diagonalizáció hiányzik"
    assert ref.exact_diagonalization == pytest.approx(ref.full_ci, abs=NUMERICAL_TOLERANCE_HA), (
        f"leképezési hiba: L1 − L0 = {ref.mapping_error:.3e} Ha "
        f"(L0 = {ref.full_ci:.12f}, L1 = {ref.exact_diagonalization:.12f})"
    )


@pytest.mark.parametrize("mapper", ALL_MAPPERS)
def test_ac_1_2_all_mappers_are_exact(
    results_by_mapper: dict[MapperKind, VQEResult], mapper: MapperKind
) -> None:
    """Mindhárom leképezés ugyanazt a spektrumot adja."""
    ref = results_by_mapper[mapper].reference
    assert ref.mapping_error is not None
    assert abs(ref.mapping_error) < NUMERICAL_TOLERANCE_HA, (
        f"a(z) '{mapper}' leképezés hibája {ref.mapping_error:.3e} Ha"
    )


# --- AC-1.3 — L2 ≈ L1: kémiai pontosság --------------------------------------


def test_ac_1_3_within_chemical_accuracy(result: VQEResult) -> None:
    """A VQE energiája kémiai pontosságon belül van (|Δ| < 1.6 mHa).

    Ez az alapterv ±0.01 Ha kritériumánál **hatszor szigorúbb**, és a
    kvantumkémiában bevett hibahatár [helgaker2000].
    """
    assert result.within_chemical_accuracy, (
        f"a hiba {result.error_vs_reference:.3e} Ha, ami meghaladja a kémiai "
        f"pontosságot ({CHEMICAL_ACCURACY_HA:.3e} Ha)"
    )


def test_ac_1_3_uccsd_is_essentially_exact_for_h2(result: VQEResult) -> None:
    """H2-re az UCCSD ansatz gépi pontossággal egzakt.

    Ez erősebb állítás a kémiai pontosságnál, és H2 esetén elvárható: a 3
    paraméteres UCCSD a releváns alteret teljesen lefedi. Ha ez elbukik, az
    ansatz vagy az optimalizáló hibás — nem a modell korlátja.
    """
    ansatz_error = result.error_vs_exact_diagonalization
    assert ansatz_error is not None
    assert abs(ansatz_error) < 1e-7, (
        f"az ansatz hibája {ansatz_error:.3e} Ha, ami H2-re váratlanul nagy "
        "(az UCCSD itt egzakt kellene legyen)"
    )


def test_full_correlation_energy_recovered(result: VQEResult) -> None:
    """A VQE a teljes korrelációs energiát visszanyeri (100 %).

    Fizikailag beszédesebb mutató az abszolút hibánál: azt mondja meg, hogy a
    Hartree–Fock fölötti korrelációból mennyit sikerült megfogni.
    """
    recovered = result.correlation_energy_recovered
    assert recovered is not None
    assert recovered == pytest.approx(1.0, abs=1e-6), (
        f"a visszanyert korrelációs energia {recovered * 100:.4f} %, nem 100 %"
    )


# --- AC-1.5 — variációs elv --------------------------------------------------


def test_ac_1_5_variational_principle(result: VQEResult) -> None:
    """A VQE energiája nem lehet az egzakt alapállapot alatt.

    A variációs elv szerint bármely próbaállapot várható értéke felső korlátja
    az alapállapoti energiának. Ha ez sérül, az **biztosan hiba** — például
    rosszul normált állapot, hibás observable vagy hibás magtaszítás.
    """
    assert result.satisfies_variational_principle, (
        f"a variációs elv sérül: E_VQE = {result.energy:.12f} Ha, "
        f"E_ref = {result.reference.best:.12f} Ha, "
        f"eltérés = {result.error_vs_reference:.3e} Ha"
    )


def test_hartree_fock_is_an_upper_bound(result: VQEResult) -> None:
    """A Hartree–Fock energia a Full CI fölött van (korrelációs energia ≤ 0)."""
    correlation = result.reference.correlation_energy
    assert correlation is not None
    assert correlation <= NUMERICAL_TOLERANCE_HA, (
        f"a korrelációs energia pozitív ({correlation:.3e} Ha), ami lehetetlen"
    )


# --- AC-1.6 — determinizmus (D1 szint) ---------------------------------------


def test_ac_1_6_determinism_bit_for_bit() -> None:
    """Ugyanaz a konfiguráció kétszer futtatva **bitre azonos** energiát ad.

    Az alapterv így fogalmaz: „ne menj tovább, amíg ez nem megy stabilan, többször
    lefuttatva is ugyanazt az eredményt adja". Itt ezt gépi bizonyítékká tesszük,
    kézi megfigyelés helyett.

    Zajmentes állapotvektoron a bitre azonosság jogos elvárás (D1 szint,
    ADR-0005). A konténerben a ``*_NUM_THREADS=1`` beállítás biztosítja, hogy a
    BLAS-redukciók összegzési sorrendje se ingadozzon.
    """
    config = _config()
    first = run_vqe(config)
    second = run_vqe(config)

    assert first.energy == second.energy, (
        f"a két futás eltér: {first.energy!r} vs {second.energy!r} "
        f"(különbség {first.energy - second.energy:.3e} Ha)"
    )
    assert first.optimal_parameters == second.optimal_parameters
    assert first.n_function_evaluations == second.n_function_evaluations


def test_config_fingerprint_is_stable() -> None:
    """Azonos konfigurációhoz azonos ujjlenyomat; eltérőhöz eltérő."""
    assert _config().fingerprint() == _config().fingerprint()
    assert _config().fingerprint() != _config("jordan_wigner").fingerprint()


# --- AC-1.7 — leképezés-függetlenség -----------------------------------------


def test_ac_1_7_mappers_agree(results_by_mapper: dict[MapperKind, VQEResult]) -> None:
    """Mindhárom leképezés ugyanazt az energiát adja.

    Ez keresztvalidáció: három különböző algebrai konstrukció (Jordan–Wigner,
    paritás, Bravyi–Kitaev) ugyanazt a fizikai rendszert írja le, tehát ugyanazt
    a spektrumot kell adniuk. Az egyezés a leképezés-implementáció független
    ellenőrzése.
    """
    energies = {mapper: res.energy for mapper, res in results_by_mapper.items()}
    spread = max(energies.values()) - min(energies.values())
    assert spread < 1e-7, f"a leképezések energiái eltérnek (szórás {spread:.3e} Ha): " + ", ".join(
        f"{m}={e:.12f}" for m, e in energies.items()
    )


def test_two_qubit_reduction_saves_qubits(
    results_by_mapper: dict[MapperKind, VQEResult],
) -> None:
    """A paritás-leképezés kétqubites redukciója ténylegesen két qubitet spórol."""
    parity = results_by_mapper["parity"]
    jw = results_by_mapper["jordan_wigner"]
    assert parity.two_qubit_reduction is True
    assert parity.n_qubits == jw.n_qubits - 2, (
        f"a redukció nem működött: parity {parity.n_qubits} qubit, "
        f"Jordan–Wigner {jw.n_qubits} qubit"
    )
    assert parity.n_hamiltonian_terms < jw.n_hamiltonian_terms


def test_two_qubit_reduction_can_be_disabled() -> None:
    """Redukció nélkül a paritás-leképezés ugyanannyi qubitet használ, mint a JW."""
    reduced = run_vqe(_config("parity"))
    full = run_vqe(_config("parity", two_qubit_reduction=False))
    assert full.two_qubit_reduction is False
    assert full.n_qubits == reduced.n_qubits + 2
    assert full.energy == pytest.approx(reduced.energy, abs=1e-7)


# --- AC-1.8 — E(θ=0) ≡ E_HF ---------------------------------------------------


def test_ac_1_8_zero_parameters_give_hartree_fock() -> None:
    """A ``θ = 0`` kezdőpont pontosan a Hartree–Fock állapotot adja.

    Az UCCSD ansatz ``exp(0) = I`` miatt a kezdőállapotot hagyja változatlanul,
    az pedig a Hartree–Fock determináns. A VQE első célfüggvény-kiértékelésének
    tehát a PySCF SCF energiáját kell adnia — **két független úton** ugyanaz a szám.
    """
    config = _config(ansatz=AnsatzSpec(initial_point="zeros"))
    result = run_vqe(config)
    first_evaluation = result.history[0] + result.nuclear_repulsion_energy
    assert first_evaluation == pytest.approx(
        result.reference.hartree_fock, abs=NUMERICAL_TOLERANCE_HA
    ), f"E(θ=0) = {first_evaluation:.12f} Ha ≠ E_HF = {result.reference.hartree_fock:.12f} Ha"


# --- Keresztvalidáció: optimalizálók -----------------------------------------


@pytest.mark.parametrize("method", DERIVATIVE_FREE_AND_GRADIENT_METHODS)
def test_optimizers_agree(method: str) -> None:
    """Minden támogatott optimalizáló kémiai pontosságon belülre konvergál.

    Zajmentes célfüggvényen a gradiens-alapú és a deriváltmentes módszereknek
    egyaránt meg kell találniuk a minimumot. Ha valamelyik nem, az az
    optimalizáló-burkolat hibájára utal, nem a fizikára.
    """
    result = run_vqe(_config(optimizer=OptimizerSpec(method=method, maxiter=2000)))
    assert result.within_chemical_accuracy, (
        f"a(z) {method} optimalizáló hibája {result.error_vs_reference:.3e} Ha"
    )


# --- Keresztvalidáció: az estimator megkerülése ------------------------------


def test_estimator_matches_direct_linear_algebra(result: VQEResult) -> None:
    """Az energia a Qiskit primitív megkerülésével, tiszta lineáris algebrával is ugyanaz.

    A Qiskit ``StatevectorEstimator``-ának kimenetét itt **független úton**
    számoljuk újra: felépítjük az állapotvektort és a Hamilton-mátrixot, majd
    kiszámoljuk a ``⟨ψ|H|ψ⟩`` szorzatot. Ha a kettő eltér, a primitív-réteg
    használata hibás (pl. rossz paraméter-sorrend vagy illesztetlen observable).
    """
    import numpy as np
    from qiskit.quantum_info import Statevector

    from vqebd.chemistry.mapping import map_to_qubits
    from vqebd.chemistry.problem import build_electronic_structure
    from vqebd.seeds import SeedSet
    from vqebd.vqe.ansatz import build_ansatz

    config = result.config
    structure = build_electronic_structure(config.molecule)
    hamiltonian = map_to_qubits(
        structure, config.mapper, two_qubit_reduction=config.two_qubit_reduction
    )
    ansatz = build_ansatz(structure, hamiltonian, config.ansatz, SeedSet.derive(config.seed))

    bound = ansatz.circuit.assign_parameters(list(result.optimal_parameters))
    state = np.asarray(Statevector(bound).data)
    matrix = hamiltonian.operator.to_matrix()
    expectation = float(np.real(np.conjugate(state) @ matrix @ state))
    energy = expectation + hamiltonian.nuclear_repulsion_energy

    assert energy == pytest.approx(result.energy, abs=NUMERICAL_TOLERANCE_HA), (
        f"a primitív {result.energy:.12f} Ha-t adott, a közvetlen számítás "
        f"{energy:.12f} Ha-t (eltérés {energy - result.energy:.3e})"
    )


# --- Fizikai viselkedés: disszociációs görbe ---------------------------------


def test_dissociation_curve_has_a_minimum() -> None:
    """A H2 disszociációs görbe U-alakú, a minimummal az egyensúlyi távolság körül.

    Ez nem numerikus, hanem **fizikai** helyességi ellenőrzés: rövid távolságon a
    magtaszítás, nagy távolságon a kötés hiánya emeli az energiát.
    """
    distances = (0.4, 0.6, 0.735, 0.9, 1.5, 2.5)
    energies = [run_vqe(VQEConfig(molecule=h2(d)), compute_fci=False).energy for d in distances]

    minimum_index = energies.index(min(energies))
    assert 0 < minimum_index < len(energies) - 1, (
        "a minimum a vizsgált tartomány szélén van, tehát a görbe nem U-alakú: "
        + ", ".join(f"r={d}Å→{e:.6f}" for d, e in zip(distances, energies, strict=True))
    )
    assert distances[minimum_index] == pytest.approx(0.735, abs=0.2), (
        f"a minimum r = {distances[minimum_index]} Å-nél van, ami messze esik az "
        "egyensúlyi kötéshossztól (~0.74 Å)"
    )
