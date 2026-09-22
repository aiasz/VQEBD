"""Funkcionalis kompatibilitasi proba - VQEBD stack."""
import sys, traceback, warnings
warnings.filterwarnings("ignore")

G = {}

def step(name):
    def deco(fn):
        try:
            r = fn()
            print("[OK]   " + name + ": " + str(r))
            return r
        except Exception as e:
            print("[FAIL] " + name + ": " + type(e).__name__ + ": " + str(e))
            traceback.print_exc(limit=4)
            return None
    return deco


@step("1 verziok")
def _():
    import qiskit, qiskit_aer, qiskit_nature, qiskit_algorithms, mitiq, pyscf, numpy, scipy
    import qiskit_ibm_runtime, cirq
    return ("qiskit=%s aer=%s nature=%s algos=%s runtime=%s mitiq=%s pyscf=%s cirq=%s np=%s sp=%s py=%s" % (
        qiskit.__version__, qiskit_aer.__version__, qiskit_nature.__version__,
        qiskit_algorithms.__version__, qiskit_ibm_runtime.__version__, mitiq.__version__,
        pyscf.__version__, cirq.__version__, numpy.__version__, scipy.__version__,
        sys.version.split()[0]))


@step("2 pyscf HF+FCI H2 0.735A sto-3g")
def _():
    from pyscf import gto, scf, fci
    mol = gto.M(atom="H 0 0 0; H 0 0 0.735", basis="sto-3g", unit="Angstrom", verbose=0)
    mf = scf.RHF(mol).run()
    e_fci = fci.FCI(mf).kernel()[0]
    G["E_HF"], G["E_FCI"], G["E_NUC"] = mf.e_tot, e_fci, mol.energy_nuc()
    return "E_HF=%.8f E_FCI=%.8f E_nuc=%.8f" % (mf.e_tot, e_fci, mol.energy_nuc())


@step("3 qiskit-nature PySCFDriver")
def _():
    from qiskit_nature.units import DistanceUnit
    from qiskit_nature.second_q.drivers import PySCFDriver
    d = PySCFDriver(atom="H 0 0 0; H 0 0 0.735", basis="sto3g", charge=0, spin=0,
                    unit=DistanceUnit.ANGSTROM)
    p = d.run()
    G["PROBLEM"] = p
    return "n_spatial=%s n_particles=%s E_nuc=%.8f ref=%.8f" % (
        p.num_spatial_orbitals, p.num_particles, p.nuclear_repulsion_energy, p.reference_energy)


@step("4 JW + Parity(2q-reduction) mapping")
def _():
    from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper
    p = G["PROBLEM"]
    h = p.hamiltonian.second_q_op()
    jw = JordanWignerMapper().map(h)
    par = ParityMapper(num_particles=p.num_particles).map(h)
    G["QOP_JW"], G["QOP_PAR"] = jw, par
    return "JW: %dq/%d terms | Parity-2qr: %dq/%d terms" % (
        jw.num_qubits, len(jw), par.num_qubits, len(par))


@step("5 egzakt diagonalizacio (numpy eigh)")
def _():
    import numpy as np
    p = G["PROBLEM"]
    out = []
    for tag in ("QOP_JW", "QOP_PAR"):
        m = G[tag].to_matrix()
        e = float(np.linalg.eigvalsh(m)[0]) + p.nuclear_repulsion_energy
        G["E_EXACT_" + tag] = e
        out.append("%s=%.8f (dFCI=%+.2e)" % (tag, e, e - G["E_FCI"]))
    return " | ".join(out)


@step("6 UCCSD + HartreeFock ansatz")
def _():
    from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
    from qiskit_nature.second_q.mappers import ParityMapper
    p = G["PROBLEM"]
    mapper = ParityMapper(num_particles=p.num_particles)
    hf = HartreeFock(p.num_spatial_orbitals, p.num_particles, mapper)
    ans = UCCSD(p.num_spatial_orbitals, p.num_particles, mapper, initial_state=hf)
    G["ANSATZ"] = ans
    return "%dq, %d param, decomposed depth=%d" % (
        ans.num_qubits, ans.num_parameters, ans.decompose(reps=4).depth())


@step("7 sajat VQE: StatevectorEstimator(V2) + scipy SLSQP")
def _():
    import numpy as np
    from qiskit.primitives import StatevectorEstimator
    from scipy.optimize import minimize
    p, ans, op = G["PROBLEM"], G["ANSATZ"], G["QOP_PAR"]
    est = StatevectorEstimator()
    calls = {"n": 0}

    def cost(x):
        calls["n"] += 1
        return float(est.run([(ans, op, x)]).result()[0].data.evs)

    res = minimize(cost, np.zeros(ans.num_parameters), method="SLSQP",
                   options={"maxiter": 300, "ftol": 1e-12})
    e_tot = float(res.fun) + p.nuclear_repulsion_energy
    G["E_VQE_SV"] = e_tot
    return "E_VQE=%.8f (dFCI=%+.2e) iter=%d evals=%d" % (
        e_tot, e_tot - G["E_FCI"], res.nit, calls["n"])


@step("8 Aer EstimatorV2 shot-alapu (8192 shot)")
def _():
    import numpy as np
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit.primitives import StatevectorEstimator
    from scipy.optimize import minimize
    p, ans, op = G["PROBLEM"], G["ANSATZ"], G["QOP_PAR"]
    sv = StatevectorEstimator()
    r = minimize(lambda x: float(sv.run([(ans, op, x)]).result()[0].data.evs),
                 np.zeros(ans.num_parameters), method="SLSQP", options={"maxiter": 300})
    sim = AerSimulator(seed_simulator=42)
    isa = transpile(ans, sim, optimization_level=1)
    isa_op = op.apply_layout(isa.layout) if isa.layout is not None else op
    est = AerEstimator(options={"default_precision": 1.0 / np.sqrt(8192),
                                "run_options": {"seed": 42}})
    ev = float(est.run([(isa, isa_op, r.x)]).result()[0].data.evs)
    e = ev + p.nuclear_repulsion_energy
    return "E_shot=%.6f  E_exactVQE=%.6f  shot-zaj=%+.2e" % (e, G["E_VQE_SV"], e - G["E_VQE_SV"])


@step("9 Mitiq qiskit->cirq konverzio + fold_global")
def _():
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit
    from mitiq.zne.scaling import fold_global
    from qiskit import QuantumCircuit, transpile
    qc = QuantumCircuit(2)
    qc.h(0); qc.cx(0, 1); qc.rz(0.3, 1)
    basis = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)
    c = from_qiskit(basis)
    folded = fold_global(c, scale_factor=3.0)
    return "cirq ops %d -> folded(3x) %d" % (
        len(list(c.all_operations())), len(list(folded.all_operations())))


@step("10 Mitiq execute_with_zne zajos AerSimulator-on")
def _():
    from mitiq import zne
    from mitiq.zne.inference import RichardsonFactory
    from mitiq.zne.scaling import fold_global
    from mitiq.interface.mitiq_qiskit.conversions import to_qiskit, from_qiskit
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit.quantum_info import SparsePauliOp

    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(0.005, 1), ["sx", "x"])
    nm.add_all_qubit_quantum_error(depolarizing_error(0.03, 2), ["cx"])
    sim = AerSimulator(noise_model=nm, seed_simulator=7)
    obs = SparsePauliOp("ZZ")

    def executor(circuit):
        qc = to_qiskit(circuit)
        qc.save_expectation_value(obs, list(range(qc.num_qubits)))
        tqc = transpile(qc, sim, optimization_level=0)
        return float(sim.run(tqc, shots=20000).result().data()["expectation_value"])

    qc = QuantumCircuit(2)
    qc.h(0); qc.cx(0, 1)
    base = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)
    c = from_qiskit(base)
    raw = executor(c)
    mit = zne.execute_with_zne(c, executor, scale_noise=fold_global,
                               factory=RichardsonFactory(scale_factors=[1.0, 2.0, 3.0]))
    return "ideal=1.0 raw=%.4f zne=%.4f javulas=%+.4f" % (
        raw, mit, abs(1 - raw) - abs(1 - mit))


@step("11 qiskit-ibm-runtime csatorna-tamogatas")
def _():
    import inspect
    from qiskit_ibm_runtime import QiskitRuntimeService
    src = inspect.getsource(QiskitRuntimeService)
    chans = [c for c in ("ibm_quantum_platform", "ibm_cloud", "ibm_quantum") if '"%s"' % c in src or "'%s'" % c in src]
    sig = list(inspect.signature(QiskitRuntimeService.__init__).parameters)
    return "channels=%s | init params=%s" % (chans, sig)


@step("12 Runtime EstimatorV2 beepitett ZNE opciok")
def _():
    from qiskit_ibm_runtime.options import ZneOptions, ResilienceOptionsV2
    zf = [x for x in getattr(ZneOptions, "__dataclass_fields__", {})]
    rf = [x for x in getattr(ResilienceOptionsV2, "__dataclass_fields__", {})]
    return "ZneOptions=%s | Resilience=%s" % (zf, rf)


@step("13 Aer noise model NoiseModel.from_backend + FakeBackend")
def _():
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2, FakeSherbrooke
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    b = FakeManilaV2()
    nm = NoiseModel.from_backend(b)
    sim = AerSimulator.from_backend(b)
    return "FakeManilaV2 %dq, noise ops=%d, AerSimulator.from_backend OK, FakeSherbrooke=%dq" % (
        b.num_qubits, len(nm.noise_instructions), FakeSherbrooke().num_qubits)


print("\n=== SPIKE VEGE ===")
