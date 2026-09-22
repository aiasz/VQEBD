"""Spike 3. kor: ZNE strategiak osszehasonlitasa - sajat Qiskit-natv vs Mitiq."""
import sys, traceback, warnings
import numpy as np
warnings.filterwarnings("ignore")
G = {}


def step(name):
    def deco(fn):
        try:
            print("[OK]   " + name + ": " + str(fn()))
        except Exception as e:
            print("[FAIL] " + name + ": " + type(e).__name__ + ": " + str(e))
            traceback.print_exc(limit=5)
    return deco


# ---------------------------------------------------------------- setup
@step("S1 H2 problema + UCCSD + egzakt VQE parameterek")
def _():
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
                 np.zeros(ans.num_parameters), method="SLSQP",
                 options={"maxiter": 300, "ftol": 1e-12})
    G.update(OP=op, BOUND=ans.assign_parameters(r.x), E_NUC=p.nuclear_repulsion_energy,
             E_REF=float(r.fun) + p.nuclear_repulsion_energy)
    return "E_ref=%.8f" % G["E_REF"]


@step("S2 ISA aramkor + zajos szimulator")
def _():
    from qiskit import transpile
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    from qiskit_aer import AerSimulator
    be = FakeManilaV2()
    sim = AerSimulator.from_backend(be, seed_simulator=2024)
    isa = transpile(G["BOUND"], backend=be, optimization_level=3, seed_transpiler=42)
    G.update(BE=be, SIM=sim, ISA=isa, ISA_OP=G["OP"].apply_layout(isa.layout),
             BASIS=list(be.operation_names))
    return "ISA %dq d=%d ops=%s basis=%s" % (isa.num_qubits, isa.depth(),
                                             dict(isa.count_ops()), G["BASIS"])


def estimator(precision=0.002, seed=2024):
    from qiskit_aer.primitives import EstimatorV2 as AerEstimator
    return AerEstimator(options={
        "backend_options": {"noise_model": G["SIM"].options.noise_model,
                            "seed_simulator": seed},
        "default_precision": precision})


# ---------------------------------------------------------------- nativ folding
def qiskit_fold_global(qc, scale_factor):
    """Globalis unitaris hajtogatas: C -> C (C^dag C)^n, scale = 2n+1.
    Megorzi a qubit-szamot es a regisztereket -> ISA-biztos."""
    n, rem = divmod(int(round(scale_factor)) - 1, 2)
    if rem != 0:
        raise ValueError("csak paratlan egesz scale_factor (1,3,5,...)")
    base = qc.copy()
    inv = qc.inverse()
    out = qc.copy_empty_like()
    out.compose(base, inplace=True)
    for _ in range(n):
        out.compose(inv, inplace=True)
        out.compose(base, inplace=True)
    return out


@step("N1 nativ global folding ISA aramkoron (szelesseg megorzese)")
def _():
    from qiskit import transpile
    out = []
    for sf in (1, 3, 5):
        f = qiskit_fold_global(G["ISA"], sf)
        fb = transpile(f, basis_gates=G["BASIS"], optimization_level=0)
        out.append("sf=%d: %dq d=%d ops=%d -> basis d=%d ops=%d" % (
            sf, f.num_qubits, f.depth(), sum(f.count_ops().values()),
            fb.depth(), sum(fb.count_ops().values())))
    return " | ".join(out)


@step("N2 nativ ZNE: zajskalazas meresek (Richardson bemenet)")
def _():
    from qiskit import transpile
    est = estimator(precision=0.0015)
    pts = []
    for sf in (1, 3, 5):
        f = transpile(qiskit_fold_global(G["ISA"], sf), basis_gates=G["BASIS"],
                      optimization_level=0)
        ev = float(est.run([(f, G["ISA_OP"])]).result()[0].data.evs)
        pts.append((float(sf), ev))
    G["PTS"] = pts
    return " ".join("lam=%.0f -> E=%.6f" % (s, e + G["E_NUC"]) for s, e in pts)


def richardson(pts):
    """Lagrange-extrapolacio lambda=0-ra (Richardson)."""
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    tot = 0.0
    for i in range(len(xs)):
        w = 1.0
        for j in range(len(xs)):
            if i != j:
                w *= (0.0 - xs[j]) / (xs[i] - xs[j])
        tot += w * ys[i]
    return float(tot)


def polyfit_extrap(pts, deg):
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    return float(np.polyval(np.polyfit(xs, ys, deg), 0.0))


def expfit_extrap(pts, asymptote=None):
    from scipy.optimize import curve_fit
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    if asymptote is None:
        f = lambda x, a, b, c: a + b * np.exp(-c * x)
        p0 = (ys[-1], ys[0] - ys[-1], 0.5)
        popt, _ = curve_fit(f, xs, ys, p0=p0, maxfev=20000)
        return float(f(0.0, *popt))
    f = lambda x, b, c: asymptote + b * np.exp(-c * x)
    popt, _ = curve_fit(f, xs, ys, p0=(ys[0] - asymptote, 0.5), maxfev=20000)
    return float(f(0.0, *popt))


@step("N3 nativ extrapolatorok eredmenye")
def _():
    ref, nuc = G["E_REF"], G["E_NUC"]
    raw = G["PTS"][0][1] + nuc
    out = ["raw=%.6f(d=%+.4f)" % (raw, raw - ref)]
    for nm, v in (("richardson", richardson(G["PTS"])),
                  ("linear", polyfit_extrap(G["PTS"], 1)),
                  ("quadratic", polyfit_extrap(G["PTS"], 2))):
        e = v + nuc
        out.append("%s=%.6f(d=%+.4f)" % (nm, e, e - ref))
    try:
        e = expfit_extrap(G["PTS"]) + nuc
        out.append("exp=%.6f(d=%+.4f)" % (e, e - ref))
    except Exception as ex:
        out.append("exp=ERR:" + type(ex).__name__)
    return "E_ref=%.6f | %s" % (ref, " ".join(out))


# ---------------------------------------------------------------- Mitiq logikai szinten
@step("M1 Mitiq ZNE LOGIKAI szinten (executor transpilal)")
def _():
    from mitiq import zne
    from mitiq.zne.inference import RichardsonFactory, LinearFactory
    from mitiq.zne.scaling import fold_global as mitiq_fold
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit, to_qiskit
    from qiskit import transpile

    logical = transpile(G["BOUND"], basis_gates=["rz", "sx", "x", "cx"],
                        optimization_level=1, seed_transpiler=42)
    logical_op = G["OP"]
    est = estimator(precision=0.0015)

    def executor(circuit):
        qc = to_qiskit(circuit)
        isa = transpile(qc, backend=G["BE"], optimization_level=0, seed_transpiler=42)
        obs = logical_op.apply_layout(isa.layout)
        return float(est.run([(isa, obs)]).result()[0].data.evs)

    c = from_qiskit(logical)
    raw = executor(c) + G["E_NUC"]
    ref = G["E_REF"]
    out = ["logical=%dq d=%d" % (logical.num_qubits, logical.depth()),
           "raw=%.6f(d=%+.4f)" % (raw, raw - ref)]
    for nm, fac in (("richardson", RichardsonFactory([1.0, 3.0, 5.0])),
                    ("linear", LinearFactory([1.0, 3.0, 5.0]))):
        v = zne.execute_with_zne(c, executor, scale_noise=mitiq_fold, factory=fac) + G["E_NUC"]
        out.append("mitiq_%s=%.6f(d=%+.4f)" % (nm, v, v - ref))
    return "E_ref=%.6f | %s" % (ref, " ".join(out))


@step("M2 kereszt-validacio: nativ vs Mitiq folding gate-szam")
def _():
    from mitiq.zne.scaling import fold_global as mitiq_fold
    from mitiq.interface.mitiq_qiskit.conversions import from_qiskit, to_qiskit
    from qiskit import transpile
    logical = transpile(G["BOUND"], basis_gates=["rz", "sx", "x", "cx"],
                        optimization_level=1, seed_transpiler=42)
    c = from_qiskit(logical)
    out = []
    for sf in (1.0, 3.0, 5.0):
        m = len(list(mitiq_fold(c, sf).all_operations()))
        q = sum(qiskit_fold_global(logical, sf).count_ops().values())
        out.append("sf=%.0f mitiq=%d nativ=%d %s" % (sf, m, q, "EGYEZIK" if m == q else "ELTER"))
    return " | ".join(out)


@step("M3 readout-hiba: ZNE-vel nem javithato komponens")
def _():
    from qiskit_aer.noise import NoiseModel
    nm = NoiseModel.from_backend(G["BE"])
    props = G["BE"].properties() if hasattr(G["BE"], "properties") else None
    ro = []
    for q in range(G["BE"].num_qubits):
        try:
            ro.append(G["BE"].target["measure"][(q,)].error)
        except Exception:
            pass
    return "noise instr=%s | readout hibak=%s" % (
        sorted(nm.noise_instructions), [round(x, 4) for x in ro])


print("\n=== SPIKE-3 VEGE ===")
