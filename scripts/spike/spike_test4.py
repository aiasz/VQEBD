"""Spike 4: molekula-skalazas es futasido - Fazis 5 tervezeshez."""
import time, warnings, traceback
import numpy as np
warnings.filterwarnings("ignore")

from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper, JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer, FreezeCoreTransformer
from qiskit.primitives import StatevectorEstimator
from scipy.optimize import minimize

CASES = [
    ("H2",   "H 0 0 0; H 0 0 0.735",                      "sto3g", 0, 0, None),
    ("LiH",  "Li 0 0 0; H 0 0 1.595",                     "sto3g", 0, 0, None),
    ("LiH-as", "Li 0 0 0; H 0 0 1.595",                   "sto3g", 0, 0, (2, 3)),
    ("BeH2", "Be 0 0 0; H 0 0 1.330; H 0 0 -1.330",       "sto3g", 0, 0, None),
    ("BeH2-as", "Be 0 0 0; H 0 0 1.330; H 0 0 -1.330",    "sto3g", 0, 0, (2, 3)),
]

print("%-9s %-6s %-6s %-5s %-6s %-6s %-7s %-9s %-9s %s" % (
    "molekula", "spatO", "part", "JWq", "PARq", "terms", "UCCSDp", "E_HF", "E_exact", "t[s]"))

for name, atom, basis, charge, spin, act in CASES:
    try:
        t0 = time.time()
        p = PySCFDriver(atom=atom, basis=basis, charge=charge, spin=spin,
                        unit=DistanceUnit.ANGSTROM).run()
        e_hf = p.reference_energy
        if act is not None:
            p = ActiveSpaceTransformer(num_electrons=act[0], num_spatial_orbitals=act[1]).transform(p)
        h = p.hamiltonian.second_q_op()
        jw = JordanWignerMapper().map(h)
        mapper = ParityMapper(num_particles=p.num_particles)
        par = mapper.map(h)
        hf = HartreeFock(p.num_spatial_orbitals, p.num_particles, mapper)
        ans = UCCSD(p.num_spatial_orbitals, p.num_particles, mapper, initial_state=hf)
        e_exact = ""
        if par.num_qubits <= 12:
            m = par.to_matrix()
            e_exact = "%.6f" % (float(np.linalg.eigvalsh(m)[0])
                                + p.hamiltonian.constants.get("nuclear_repulsion_energy", 0.0)
                                + sum(v for k, v in p.hamiltonian.constants.items()
                                      if k != "nuclear_repulsion_energy"))
        print("%-9s %-6s %-6s %-5s %-6s %-6s %-7s %-9.5f %-9s %.1f" % (
            name, p.num_spatial_orbitals, str(p.num_particles), jw.num_qubits,
            par.num_qubits, len(par), ans.num_parameters, e_hf, e_exact, time.time() - t0))
    except Exception as e:
        print("%-9s FAIL %s: %s" % (name, type(e).__name__, str(e)[:90]))
        traceback.print_exc(limit=2)

# --- H2 disszociacios gorbe idozites (statevector VQE) ---
print("\n--- H2 disszociacios gorbe (statevector VQE) ---")
t0 = time.time()
dists = np.round(np.arange(0.3, 2.81, 0.1), 3)
res = []
for d in dists:
    p = PySCFDriver(atom="H 0 0 0; H 0 0 %.3f" % d, basis="sto3g",
                    unit=DistanceUnit.ANGSTROM).run()
    mapper = ParityMapper(num_particles=p.num_particles)
    op = mapper.map(p.hamiltonian.second_q_op())
    hf = HartreeFock(p.num_spatial_orbitals, p.num_particles, mapper)
    ans = UCCSD(p.num_spatial_orbitals, p.num_particles, mapper, initial_state=hf)
    sv = StatevectorEstimator()
    r = minimize(lambda x: float(sv.run([(ans, op, x)]).result()[0].data.evs),
                 np.zeros(ans.num_parameters), method="SLSQP",
                 options={"maxiter": 300, "ftol": 1e-12})
    res.append((float(d), float(r.fun) + p.nuclear_repulsion_energy))
dt = time.time() - t0
emin = min(res, key=lambda t: t[1])
print("%d pont %.1f s (%.2f s/pont)" % (len(res), dt, dt / len(res)))
print("minimum: r=%.2f A  E=%.6f Ha" % emin)
print("U-alak ellenorzes: E(0.3)=%.4f > E(min)=%.4f < E(2.8)=%.4f -> %s" % (
    res[0][1], emin[1], res[-1][1],
    "OK" if res[0][1] > emin[1] < res[-1][1] else "HIBA"))
print("\n=== SPIKE-4 VEGE ===")
