"""Spike 2. kor: Mitiq + valodi kemiai aramkor + FakeBackend zajmodell."""
import sys, traceback, warnings
warnings.filterwarnings("ignore")
G = {}


def step(name):
    def deco(fn):
        try:
            print("[OK]   " + name + ": " + str(fn()))
        except Exception as e:
            print("[FAIL] " + name + ": " + type(e).__name__ + ": " + str(e))
            traceback.print_exc(limit=4)
    return deco


@step("A ply jelen van")
def _():
    import ply
    return "ply=" + ply.__version__


@step("B H2 problema + parity mapping + UCCSD + egzakt VQE parameterek")
def _():
    import numpy as np
    from qiskit_nature.units import DistanceUnit
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import ParityMapper
    from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
    from qiskit.primitives import StatevectorEstimator
    from scipy.optimize import minimize

    p = PySCFDriver(atom="H 0 0 0; H 0 0 0.735", basis="sto3g", charge=0, spin=0,
                    unit=DistanceUnit.ANGSTROM).run()
    mapper = ParityMapper(num_particles=p.num_particles)
    op = mapper.map(p.hamiltonian.second_q_op())
    hf = HartreeFock(p.num_spatial_orbitals, p.num_particles, mapper)
    ans = UCCSD(p.num_spatial_orbitals, p.num_particles, mapper, initial_state=hf)
    sv = StatevectorEstimator()
    r = minimize(lambda x: float(sv.run([(ans, op, x)]).result()[0].data.evs),
                 np.zeros(ans.num_parameters), method="SLSQP", options={"maxiter": 300, "ftol": 1e-12})
    G.update(P=p, OP=op, ANS=ans, X=r.x, E_REF=float(r.fun) + p.nuclear_repulsion_energy,
             E_NUC=p.nuclear_repulsion_energy)
    return "E_ref=%.8f  params=%s" % (G["E_REF"], np.round(r.x, 6).tolist())


@step("C bound UCCSD -> ISA aramkor FakeBackend-re")
def _():
    from qiskit import transpile
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    be = FakeManilaV2()
    bound = G["ANS"].assign_parameters(G["X"])
    isa = transpile(bound, backend=be, optimization_level=3, seed_transpiler=42)
    isa_op = G["OP"].apply_layout(isa.layout)
    G.update(BE=be, ISA=isa, ISA_OP=isa_op)
    return "ISA: %dq depth=%d ops=%s | obs qubits=%d terms=%d" % (
        isa.num_qubits, isa.depth(), dict(isa.count_ops()), isa_op.num_qubits, len(isa_op))


@step("D zajos referencia: Aer.from_backend(FakeManilaV2) EstimatorV2")
def _():
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator
    from qiskit import transpile
    sim = AerSimulator.from_backend(G["BE"], seed_simulator=1234)
    isa = transpile(G["ANS"].assign_parameters(G["X"]), backend=sim,
                    optimization_level=3, seed_transpiler=42)
    op = G["OP"].apply_layout(isa.layout)
    est = AerEstimator(options={"backend_options": {"noise_model": sim.options.noise_model,
                                                    "seed_simulator": 1234},
                                "default_precision": 0.002})
    ev = float(est.run([(isa, op)]).result()[0].data.evs)
    e = ev + G["E_NUC"]
    G["E_NOISY"] = e
    return "E_noisy=%.6f  E_ref=%.6f  hiba=%+.4f Ha" % (e, G["E_REF"], e - G["E_REF"])


@step("E Mitiq: valodi UCCSD ISA aramkor -> cirq konverzio")
def _():
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit, to_qiskit
    isa = G["ISA"]
    c = from_qiskit(isa)
    back = to_qiskit(c)
    return "qiskit(%dq,d=%d) -> cirq(%d ops, %d qubits) -> qiskit(%dq)" % (
        isa.num_qubits, isa.depth(), len(list(c.all_operations())),
        len(c.all_qubits()), back.num_qubits)


@step("F Mitiq fold_global skalazasi faktorok")
def _():
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit
    from mitiq.zne.scaling import fold_global, fold_gates_at_random
    c = from_qiskit(G["ISA"])
    n0 = len(list(c.all_operations()))
    out = []
    for sf in (1.0, 2.0, 3.0):
        out.append("g%.0fx=%d" % (sf, len(list(fold_global(c, sf).all_operations()))))
        out.append("r%.0fx=%d" % (sf, len(list(fold_gates_at_random(c, sf, seed=1).all_operations()))))
    return "base=%d | %s" % (n0, " ".join(out))


@step("G Mitiq ZNE teljes hurok zajos H2-VQE-n (FakeManilaV2 zaj)")
def _():
    import numpy as np
    from mitiq import zne
    from mitiq.zne.inference import RichardsonFactory, LinearFactory, ExpFactory
    from mitiq.zne.scaling import fold_global
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit, to_qiskit
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator

    sim = AerSimulator.from_backend(G["BE"], seed_simulator=2024)
    noise = sim.options.noise_model
    base_isa = transpile(G["ANS"].assign_parameters(G["X"]), backend=sim,
                         optimization_level=3, seed_transpiler=42)
    obs = G["OP"].apply_layout(base_isa.layout)
    est = AerEstimator(options={"backend_options": {"noise_model": noise, "seed_simulator": 2024},
                                "default_precision": 0.003})

    def executor(circuit):
        qc = to_qiskit(circuit)
        # a foldolt aramkor mar ISA-ban van; ugyanaz a qubit-szam
        return float(est.run([(qc, obs)]).result()[0].data.evs)

    c = from_qiskit(base_isa)
    raw = executor(c)
    res = {"raw": raw + G["E_NUC"]}
    for nm, fac in (("richardson", RichardsonFactory([1.0, 2.0, 3.0])),
                    ("linear", LinearFactory([1.0, 2.0, 3.0])),
                    ("exp", ExpFactory([1.0, 2.0, 3.0], asymptote=0.0))):
        try:
            v = zne.execute_with_zne(c, executor, scale_noise=fold_global, factory=fac)
            res[nm] = v + G["E_NUC"]
        except Exception as e:
            res[nm] = "ERR:" + type(e).__name__ + ":" + str(e)[:60]
    ref = G["E_REF"]
    line = "E_ref=%.6f | " % ref
    for k, v in res.items():
        line += "%s=%s " % (k, ("%.6f(d=%+.4f)" % (v, v - ref)) if isinstance(v, float) else v)
    return line


@step("H Mitiq observable/Executor API (batch)")
def _():
    from mitiq import Executor, Observable, PauliString
    import inspect
    from mitiq.zne import execute_with_zne
    return "execute_with_zne sig=%s | Observable OK" % list(
        inspect.signature(execute_with_zne).parameters)


print("\n=== SPIKE-2 VEGE ===")
