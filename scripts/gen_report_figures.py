#!/usr/bin/env python3
"""VQEBD — mérési ábrák generálása a TÉNYLEGES mérési adatokból.

Alapelv
-------
Az ábrák **generáltak, nem rajzoltak**. A szkript maga futtatja le a méréseket,
elmenti a nyers adatokat JSON-ba (provenance), és abból rajzol. Így az ábra és a
valóság nem csúszhat el egymástól: ha a kód változik, az ábra is változik.

Kimenet
-------
``docs/figures/*.png``       — az ábrák
``docs/figures/data/*.json`` — a nyers mérési adatok

Használat
---------
    python scripts/gen_report_figures.py [--out docs/figures] [--quick]

A ``--quick`` kihagyja a leglassabb méréseket (skálázás), így ~1 perc alatt lefut.

Színek
------
A paletta CVD-validált (colorblind-safe): a három platform a kategorikus paletta
első három slotját kapja, amelyek minden párban tisztán elkülönülnek. A
státuszszínek szándékosan eltérnek a sorozatszínektől, és mindig **ikonnal vagy
felirattal együtt** jelennek meg — a szín soha nem hordoz önmagában jelentést.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- paletta
# CVD-validált kategorikus paletta, első három slot (világos mód).
SERIES = {
    "qiskit_statevector": "#2a78d6",  # slot 1 — kék
    "cirq_simulator": "#eb6834",  # slot 2 — narancs
    "qsim": "#1baf7a",  # slot 3 — aqua
}
LABELS = {
    "qiskit_statevector": "Qiskit (complex128)",
    "cirq_simulator": "Cirq (complex128)",
    "qsim": "qsim (complex64)",
}

STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Kék szekvenciális rampa (világos → sötét) a hőtérképhez.
BLUE_RAMP = [
    "#cde2fb",
    "#b7d3f6",
    "#9ec5f4",
    "#86b6ef",
    "#6da7ec",
    "#5598e7",
    "#3987e5",
    "#2a78d6",
    "#256abf",
    "#1c5cab",
    "#184f95",
    "#104281",
    "#0d366b",
]

CHEMICAL_ACCURACY_HA = 1.5936e-3
BACKENDS = ("qiskit_statevector", "cirq_simulator", "qsim")
GRADIENT_OPTIMIZERS = ("SLSQP", "L-BFGS-B", "BFGS", "CG", "TNC")
DERIVATIVE_FREE_OPTIMIZERS = ("COBYLA", "Powell", "Nelder-Mead")


def style_axes(ax: Any, *, grid_axis: str = "y") -> None:
    """Recessszív tengely és rács — a márkák dominálnak, nem a kréta."""
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_MUTED, labelsize=9, length=3, width=0.8)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)


def title(ax: Any, text: str, subtitle: str = "") -> None:
    """Cím + alcím, ütközésmentes térközzel.

    A cím a tengely fölé kerül (``pad``), az alcím közvetlenül alá — a két
    érték együtt hangolt, hogy nagy betűmérettel se érjenek össze.
    """
    ax.set_title(
        text,
        color=INK,
        fontsize=12,
        fontweight="600",
        loc="left",
        pad=30 if subtitle else 10,
    )
    if subtitle:
        ax.text(
            0.0,
            1.035,
            subtitle,
            transform=ax.transAxes,
            color=INK_SECONDARY,
            fontsize=9.5,
            va="bottom",
            ha="left",
        )


# ================================================================= mérések
def measure_reference_chain() -> dict[str, Any]:
    """L0 → L1 → L2 hibalánc mindhárom platformon."""
    from vqebd.chemistry.molecule import h2
    from vqebd.config import OptimizerSpec, VQEConfig
    from vqebd.platforms import platform_of
    from vqebd.vqe.runner import run_vqe

    rows = {}
    for backend in BACKENDS:
        result = run_vqe(
            VQEConfig(
                molecule=h2(0.735),
                backend=backend,
                optimizer=OptimizerSpec(
                    method=platform_of(backend).recommended_optimizer, maxiter=2000
                ),
            )
        )
        reference = result.reference
        rows[backend] = {
            "hartree_fock": reference.hartree_fock,
            "l0_full_ci": reference.full_ci,
            "l1_exact": reference.exact_diagonalization,
            "l2_vqe": result.energy,
            "mapping_error": abs(reference.mapping_error or 0.0),
            "ansatz_error": abs(result.error_vs_exact_diagonalization or 0.0),
            "total_error": abs(result.error_vs_reference),
            "optimizer": result.config.optimizer.method,
            "n_evaluations": result.n_function_evaluations,
            "precision": result.precision,
        }
    return rows


def measure_optimizer_matrix() -> dict[str, dict[str, float]]:
    """Platform × optimalizáló hibamátrix — a Fázis 1M központi eredménye."""
    from vqebd.chemistry.molecule import h2
    from vqebd.config import OptimizerSpec, VQEConfig
    from vqebd.vqe.runner import run_vqe

    matrix: dict[str, dict[str, float]] = {}
    for backend in BACKENDS:
        matrix[backend] = {}
        for method in GRADIENT_OPTIMIZERS + DERIVATIVE_FREE_OPTIMIZERS:
            try:
                result = run_vqe(
                    VQEConfig(
                        molecule=h2(0.735),
                        backend=backend,
                        optimizer=OptimizerSpec(method=method, maxiter=2000),
                    )
                )
                matrix[backend][method] = abs(result.error_vs_reference)
            except Exception:
                matrix[backend][method] = float("nan")
    return matrix


def measure_dissociation() -> dict[str, Any]:
    """Disszociációs görbe mindhárom platformon + a klasszikus Full CI."""
    from vqebd.chemistry.molecule import h2
    from vqebd.chemistry.reference import fci_energy
    from vqebd.config import OptimizerSpec, VQEConfig
    from vqebd.platforms import platform_of
    from vqebd.vqe.runner import run_vqe

    distances = [0.4, 0.5, 0.6, 0.7, 0.735, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0, 2.5]
    curves: dict[str, list[float]] = {b: [] for b in BACKENDS}
    exact: list[float] = []
    for distance in distances:
        molecule = h2(distance)
        exact.append(fci_energy(molecule))
        for backend in BACKENDS:
            result = run_vqe(
                VQEConfig(
                    molecule=molecule,
                    backend=backend,
                    optimizer=OptimizerSpec(
                        method=platform_of(backend).recommended_optimizer, maxiter=2000
                    ),
                ),
                compute_fci=False,
            )
            curves[backend].append(result.energy)
    return {"distances": distances, "curves": curves, "full_ci": exact}


SCALING_REPEATS = 3
"""Hányszor ismételjük az időmérést.

Az időmérés zajos: a konténer ütemezése, a CPU-gyorsítótár állapota és a
háttérfolyamatok mind **hozzáadnak** a mért időhöz, elvenni viszont nem tudnak.
Ezért a **minimum** a torzítatlan becslés, nem az átlag — ez a mikrobenchmarkok
bevett gyakorlata. Az átlag a lassú kiugrásokat is beszámítaná.
"""


def measure_scaling() -> dict[str, Any]:
    """cirq.Simulator vs qsim futásidő qubitszám szerint.

    Minden mérés :data:`SCALING_REPEATS` ismétlésből a legrövidebb időt veszi.
    """
    import cirq
    import numpy as np
    import qsimcirq

    def best_of(simulate: Any, circuit: Any, observable: Any) -> float:
        """A legrövidebb futásidő :data:`SCALING_REPEATS` ismétlésből.

        Az áramkört és az observable-t **paraméterként** kapja, nem a külső
        hatókörből — így a mérőfüggvény nem függ a ciklusváltozók késleltetett
        kötésétől (ruff B023), és önmagában is tesztelhető marad.
        """
        times = []
        for _ in range(SCALING_REPEATS):
            start = time.perf_counter()
            simulate(circuit, observable)
            times.append(time.perf_counter() - start)
        return min(times)

    rows = []
    for n in (12, 14, 16, 18, 20, 22, 24):
        qubits = cirq.LineQubit.range(n)
        circuit = cirq.Circuit(
            [cirq.H(q) for q in qubits]
            + [cirq.CNOT(qubits[i], qubits[i + 1]) for i in range(n - 1)]
            + [cirq.rz(0.1 * i).on(qubits[i]) for i in range(n)]
        )
        observable = cirq.PauliString({qubits[0]: cirq.Z, qubits[n - 1]: cirq.Z})

        cirq_time = best_of(
            lambda c, o: cirq.Simulator(dtype=np.complex128).simulate_expectation_values(
                c, observables=[o]
            ),
            circuit,
            observable,
        )
        qsim_time = best_of(
            lambda c, o: qsimcirq.QSimSimulator(
                qsim_options=qsimcirq.QSimOptions(cpu_threads=1)
            ).simulate_expectation_values(c, observables=[o]),
            circuit,
            observable,
        )
        rows.append(
            {
                "qubits": n,
                "cirq_s": cirq_time,
                "qsim_s": qsim_time,
                "speedup": cirq_time / qsim_time,
                "repeats": SCALING_REPEATS,
            }
        )
    return {"rows": rows, "aggregation": "min", "repeats": SCALING_REPEATS}


MITIGATION_ENSEMBLE = 50
"""A seed-ensemble mérete a ZNE statisztikus szórásának becsléséhez.

50 minta mellett a szórásbecslés relatív hibája ≈ 1/sqrt(2·49) ≈ 10%.
"""


def measure_mitigation() -> dict[str, Any]:
    """ZNE hibaenyhítés: a TORZÍTÁS és a SZÓRÁS külön mérve (TR-F03, 1. javítási kör).

    Módszertan — mind a θ* (zajmentes optimum) pontban, ahol a hardveres L5 is mért:

    1. **Torzítás** — ``precision=0``: az Aer a FakeManilaV2 zajmodell szerinti
       EGZAKT várható értéket adja; a ZNE rendszeres hibája így determinisztikus.
       ``zne_local`` (ISA-szintű hajtogatás) és — ha telepítve — ``zne_mitiq``
       (logikai szintű hajtogatás), mint független keresztvalidáció.
    2. **Szórás** — ``MITIGATION_ENSEMBLE`` különböző seed, alapértelmezett
       precision (1/sqrt(8192)), független zajhúzás λ-nként: így látszik, mennyit
       erősít a zajon az extrapoláció (Richardson (1,3,5): sqrt(Σw²) ≈ 2.28×).
    3. **L5** — a hardveres mérés a bizonytalanságával együtt (TR-F02 v1.1.0).
    """
    import statistics

    from vqebd.backends.estimators import AerNoisyEnergyEvaluator
    from vqebd.chemistry.mapping import map_to_qubits
    from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
    from vqebd.chemistry.problem import build_electronic_structure
    from vqebd.config import AnsatzSpec, OptimizerSpec, VQEConfig
    from vqebd.mitigation import get_mitigation_strategy
    from vqebd.mitigation.extrapolation import extrapolate
    from vqebd.seeds import SeedSet
    from vqebd.vqe.ansatz import build_ansatz
    from vqebd.vqe.runner import run_vqe

    mol = h2(H2_REFERENCE_BOND_LENGTH)
    cfg = VQEConfig(
        molecule=mol, backend="qiskit_statevector", optimizer=OptimizerSpec(method="SLSQP")
    )
    res = run_vqe(cfg)
    theta = list(res.optimal_parameters)
    seeds = SeedSet.derive(cfg.seed)
    structure = build_electronic_structure(mol)
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(kind="uccsd"), seeds)
    e_nuc = hamiltonian.nuclear_repulsion_energy
    fci = res.reference.full_ci
    assert fci is not None

    def err_mha(electronic: float) -> float:
        return 1e3 * (electronic + e_nuc - fci)

    scales = (1, 3, 5)
    extrapolators = ("richardson", "linear", "exponential")

    def bias_block(strategy: str) -> dict[str, Any]:
        evaluator = AerNoisyEnergyEvaluator(
            ansatz.circuit, hamiltonian.operator, seeds, precision=0.0
        )
        result = get_mitigation_strategy(
            strategy, scale_factors=scales, extrapolator="richardson"
        ).execute(ansatz.circuit, hamiltonian.operator, evaluator, theta, seeds)
        energies = list(result.scaled_energies)
        return {
            "scales": list(result.scale_factors),
            "scaled_errors_mha": [err_mha(e) for e in energies],
            "extrapolated_errors_mha": {
                ex: err_mha(extrapolate(ex, list(result.scale_factors), energies)[0])
                for ex in extrapolators
            },
            "two_qubit_gate_counts": result.metadata.get("two_qubit_gate_counts"),
            "folding_level": result.metadata.get("folding_level"),
        }

    bias_local = bias_block("zne_local")
    try:
        import mitiq  # noqa: F401

        bias_mitiq: dict[str, Any] | None = bias_block("zne_mitiq")
    except ImportError:
        bias_mitiq = None

    ensemble: dict[str, list[float]] = {"raw": [], **{ex: [] for ex in extrapolators}}
    for k in range(MITIGATION_ENSEMBLE):
        member_seeds = SeedSet.derive(cfg.seed + 1 + k)
        evaluator = AerNoisyEnergyEvaluator(ansatz.circuit, hamiltonian.operator, member_seeds)
        result = get_mitigation_strategy(
            "zne_local", scale_factors=scales, extrapolator="richardson"
        ).execute(ansatz.circuit, hamiltonian.operator, evaluator, theta, member_seeds)
        energies = list(result.scaled_energies)
        ensemble["raw"].append(err_mha(result.raw_energy))
        for ex in extrapolators:
            ensemble[ex].append(err_mha(extrapolate(ex, list(result.scale_factors), energies)[0]))

    def summary(values: list[float]) -> dict[str, float]:
        q = statistics.quantiles(values, n=4)
        sd = statistics.stdev(values)
        return {
            "mean": statistics.fmean(values),
            "sd": sd,
            "sem": sd / len(values) ** 0.5,
            "median": statistics.median(values),
            "q1": q[0],
            "q3": q[2],
        }

    hw_file = Path("docs/figures/data/hardware_h2_kingston.json")
    hw = json.loads(hw_file.read_text(encoding="utf-8")) if hw_file.is_file() else {}
    hw_unc = hw.get("uncertainty_ha", {})

    return {
        "method": "theta_star_single_point",
        "molecule": "H2",
        "bond_length_angstrom": H2_REFERENCE_BOND_LENGTH,
        "noise_model": "FakeManilaV2",
        "l0_full_ci": fci,
        "l2_statevector": res.energy,
        "theta_star": theta,
        "precision_per_evaluation_ha": 1.0 / 8192**0.5,
        "bias_zne_local": bias_local,
        "bias_zne_mitiq": bias_mitiq,
        "ensemble_size": MITIGATION_ENSEMBLE,
        "ensemble_seeds": [cfg.seed + 1, cfg.seed + MITIGATION_ENSEMBLE],
        "ensemble_errors_mha": ensemble,
        "ensemble_summary_mha": {k: summary(v) for k, v in ensemble.items()},
        "l5_hardware": {
            "job_id": hw.get("job_id"),
            "backend": hw.get("ibm_backend_name"),
            "error_mha": 1e3 * hw["errors_ha"]["error_vs_l0_ha"] if hw else None,
            "stds_mha": 1e3 * hw_unc["stds"] if hw_unc.get("stds") is not None else None,
            "ensemble_standard_error_mha": (
                1e3 * hw_unc["ensemble_standard_error"]
                if hw_unc.get("ensemble_standard_error") is not None
                else None
            ),
            "resilience": "TREX (szerver-alapértelmezés, resilience_level=1)",
        },
    }


# ================================================================= ábrák
def figure_reference_chain(data: dict[str, Any], out: Path) -> None:
    """A hibalánc: hol keletkezik a hiba, és mekkora."""
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=SURFACE)
    stages = ["Leképezés\n(L1 − L0)", "Ansatz\n(L2 − L1)", "Teljes\n(L2 − L0)"]
    keys = ["mapping_error", "ansatz_error", "total_error"]
    positions = np.arange(len(stages))
    width = 0.26

    for index, backend in enumerate(BACKENDS):
        values = [max(data[backend][k], 1e-17) for k in keys]
        offset = (index - 1) * (width + 0.02)
        bars = ax.bar(
            positions + offset,
            values,
            width,
            color=SERIES[backend],
            label=LABELS[backend],
            zorder=3,
            edgecolor=SURFACE,
            linewidth=2,
        )
        for rect, value in zip(bars, values, strict=True):
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                value * 1.5,
                f"{value:.0e}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=INK_SECONDARY,
                rotation=90,
            )

    ax.axhline(
        CHEMICAL_ACCURACY_HA, color=STATUS["critical"], linewidth=1.6, linestyle="--", zorder=4
    )
    ax.text(
        len(stages) - 0.45,
        CHEMICAL_ACCURACY_HA * 1.4,
        "kémiai pontosság  1.6 mHa",
        color=STATUS["critical"],
        fontsize=9,
        ha="right",
        va="bottom",
        fontweight="600",
    )

    ax.set_yscale("log")
    ax.set_ylim(1e-17, 1e-1)
    ax.set_xticks(positions)
    ax.set_xticklabels(stages, fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("abszolút hiba (Hartree, log skála)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax)
    title(
        ax,
        "A hibalánc szétbontása platformonként",
        "H2, 0.735 Å, STO-3G — minden platform a hozzá mért optimalizálóval",
    )
    legend = ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=3)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.84, bottom=0.12)
    fig.savefig(out / "fig01_hibalanc.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_optimizer_matrix(matrix: dict[str, dict[str, float]], out: Path) -> None:
    """A Fázis 1M központi eredménye: az optimalizáló × pontosság kölcsönhatás."""
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    import numpy as np

    methods = list(GRADIENT_OPTIMIZERS + DERIVATIVE_FREE_OPTIMIZERS)
    grid = np.array([[matrix[b][m] for m in methods] for b in BACKENDS])
    plotted = np.log10(np.clip(grid, 1e-16, None))

    cmap = mcolors.LinearSegmentedColormap.from_list("vqebd_blue", BLUE_RAMP)
    fig, ax = plt.subplots(figsize=(11, 4.4), facecolor=SURFACE)
    mesh = ax.imshow(plotted, cmap=cmap, aspect="auto", vmin=-16, vmax=-1)

    for row in range(len(BACKENDS)):
        for column in range(len(methods)):
            value = grid[row, column]
            ok = value < CHEMICAL_ACCURACY_HA
            # A cella sötétsége adja a kontrasztot; a szöveg ehhez igazodik.
            text_color = "#ffffff" if plotted[row, column] > -6 else INK
            ax.text(
                column,
                row - 0.13,
                f"{value:.0e}",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
                fontweight="600",
            )
            ax.text(
                column,
                row + 0.22,
                "✓ OK" if ok else "✗ BUKÁS",
                ha="center",
                va="center",
                fontsize=8,
                color=text_color if ok else "#ffffff",
                fontweight="700" if not ok else "400",
            )
            if not ok:
                ax.add_patch(
                    plt.Rectangle(
                        (column - 0.5, row - 0.5),
                        1,
                        1,
                        fill=False,
                        edgecolor=STATUS["critical"],
                        linewidth=2.5,
                        zorder=5,
                    )
                )

    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, fontsize=9, color=INK_SECONDARY)
    ax.set_yticks(range(len(BACKENDS)))
    ax.set_yticklabels([LABELS[b] for b in BACKENDS], fontsize=9.5, color=INK_SECONDARY)
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    # A két optimalizáló-család elválasztása. A csoportfeliratok a tengely ALÁ
    # kerülnek (axes-koordinátában), hogy ne ütközzenek a címmel.
    split = len(GRADIENT_OPTIMIZERS) - 0.5
    ax.axvline(split, color=INK, linewidth=2)
    centre = (split + 0.5) / len(methods)
    ax.text(
        centre / 2,
        -0.30,
        "GRADIENS-ALAPÚ  (véges differenciás gradiens)",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color=INK_SECONDARY,
        fontweight="600",
    )
    ax.text(
        centre + (1 - centre) / 2,
        -0.30,
        "DERIVÁLTMENTES",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color=INK_SECONDARY,
        fontweight="600",
    )
    ax.plot(
        [0.0, centre - 0.01],
        [-0.22, -0.22],
        transform=ax.transAxes,
        color=AXIS,
        linewidth=1.2,
        clip_on=False,
    )
    ax.plot(
        [centre + 0.01, 1.0],
        [-0.22, -0.22],
        transform=ax.transAxes,
        color=AXIS,
        linewidth=1.2,
        clip_on=False,
    )

    bar = fig.colorbar(mesh, ax=ax, pad=0.015, fraction=0.025)
    bar.set_label("log₁₀(hiba / Ha)", color=INK_SECONDARY, fontsize=9)
    bar.ax.tick_params(colors=INK_MUTED, labelsize=8)
    bar.outline.set_visible(False)

    title(
        ax,
        "Optimalizáló × platform: hol bukik meg a gradiens-becslés",
        "Piros keret = kémiai pontosság (1.6 mHa) fölötti hiba. "
        "A qsim egyszeres pontossága csak a gradiens-alapú módszereket rontja el.",
    )
    fig.subplots_adjust(left=0.16, right=0.95, top=0.80, bottom=0.22)
    fig.savefig(out / "fig02_optimalizalo_matrix.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_gradient_safety(out: Path) -> None:
    """Miért bukik meg a gradiens: zajszint vs véges-differencia lépésköz."""
    import matplotlib.pyplot as plt
    import numpy as np

    from vqebd.platforms import PLATFORMS, SCIPY_FINITE_DIFFERENCE_STEP

    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=SURFACE)
    positions = np.arange(len(BACKENDS))
    noise = [PLATFORMS[b].noise_floor_ha for b in BACKENDS]

    bars = ax.bar(
        positions,
        noise,
        0.5,
        color=[SERIES[b] for b in BACKENDS],
        zorder=3,
        edgecolor=SURFACE,
        linewidth=2,
    )
    for rect, backend, value in zip(bars, BACKENDS, noise, strict=True):
        info = PLATFORMS[backend]
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            value * 2.2,
            f"{value:.0e} Ha",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK_SECONDARY,
            fontweight="600",
        )
        verdict = "gradiens OK" if info.gradient_safe else "gradiens NEM"
        colour = STATUS["good"] if info.gradient_safe else STATUS["critical"]
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            3e-18,
            f"{'✓' if info.gradient_safe else '✗'} {verdict}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=colour,
            fontweight="700",
        )

    ax.axhline(SCIPY_FINITE_DIFFERENCE_STEP, color=INK, linewidth=1.8, linestyle="--", zorder=4)
    ax.text(
        -0.42,
        SCIPY_FINITE_DIFFERENCE_STEP * 2.0,
        f"SciPy véges-differencia lépésköz  √ε = {SCIPY_FINITE_DIFFERENCE_STEP:.1e}",
        color=INK,
        fontsize=9,
        ha="left",
        va="bottom",
        fontweight="600",
    )

    ax.set_yscale("log")
    ax.set_ylim(1e-18, 1e-4)
    ax.set_xticks(positions)
    ax.set_xticklabels([LABELS[b] for b in BACKENDS], fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("célfüggvény-zaj (Hartree, log skála)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax)
    title(
        ax,
        "Miért bukik meg a gradiens-becslés a qsimen",
        "Ha a zaj a lépésköz FÖLÖTT van, a becsült gradiens zajból származik, nem a függvényből.",
    )
    fig.subplots_adjust(left=0.11, right=0.97, top=0.82, bottom=0.12)
    fig.savefig(out / "fig03_gradiens_biztonsag.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_dissociation(data: dict[str, Any], out: Path) -> None:
    """Disszociációs görbe — fizikai helyesség három platformon."""
    import matplotlib.pyplot as plt

    distances = data["distances"]
    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(9, 6.6),
        facecolor=SURFACE,
        sharex=True,
        gridspec_kw={"height_ratios": [2.1, 1], "hspace": 0.12},
    )

    ax_top.plot(
        distances,
        data["full_ci"],
        color=INK_MUTED,
        linewidth=2.4,
        linestyle="--",
        label="Full CI (klasszikus egzakt)",
        zorder=2,
    )
    for backend in BACKENDS:
        ax_top.plot(
            distances,
            data["curves"][backend],
            color=SERIES[backend],
            linewidth=2,
            marker="o",
            markersize=5,
            markeredgecolor=SURFACE,
            markeredgewidth=1.5,
            label=LABELS[backend],
            zorder=3,
        )
    ax_top.set_ylabel("alapállapoti energia (Ha)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax_top)
    title(
        ax_top,
        "H2 disszociációs görbe — három platform, egyetlen görbe",
        "A három platform vonala fedi egymást; az eltérés csak az alsó panelen látszik.",
    )
    legend = ax_top.legend(frameon=False, fontsize=9.5, loc="lower right")
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    for backend in BACKENDS:
        deviations = [
            max(abs(value - exact), 1e-17)
            for value, exact in zip(data["curves"][backend], data["full_ci"], strict=True)
        ]
        ax_bottom.plot(
            distances,
            deviations,
            color=SERIES[backend],
            linewidth=2,
            marker="o",
            markersize=4.5,
            markeredgecolor=SURFACE,
            markeredgewidth=1.2,
            label=LABELS[backend],
            zorder=3,
        )
    ax_bottom.axhline(
        CHEMICAL_ACCURACY_HA, color=STATUS["critical"], linewidth=1.6, linestyle="--", zorder=4
    )
    ax_bottom.text(
        distances[-1],
        CHEMICAL_ACCURACY_HA * 1.5,
        "kémiai pontosság",
        color=STATUS["critical"],
        fontsize=8.5,
        ha="right",
        va="bottom",
        fontweight="600",
    )
    ax_bottom.set_yscale("log")
    ax_bottom.set_ylim(1e-17, 1e-1)
    ax_bottom.set_xlabel("kötéshossz (Å)", color=INK_SECONDARY, fontsize=10)
    ax_bottom.set_ylabel("eltérés a Full CI-től (Ha)", color=INK_SECONDARY, fontsize=9.5)
    style_axes(ax_bottom)

    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.09)
    fig.savefig(out / "fig04_disszociacio.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_scaling(data: dict[str, Any], out: Path) -> None:
    """A qsim ára és haszna: pontosság kontra sebesség."""
    import matplotlib.pyplot as plt

    rows = data["rows"]
    qubits = [r["qubits"] for r in rows]

    fig, (ax_time, ax_speedup) = plt.subplots(
        1, 2, figsize=(11, 4.3), facecolor=SURFACE, gridspec_kw={"wspace": 0.24}
    )

    ax_time.plot(
        qubits,
        [r["cirq_s"] for r in rows],
        color=SERIES["cirq_simulator"],
        linewidth=2,
        marker="o",
        markersize=6,
        markeredgecolor=SURFACE,
        markeredgewidth=1.5,
        label=LABELS["cirq_simulator"],
        zorder=3,
    )
    ax_time.plot(
        qubits,
        [r["qsim_s"] for r in rows],
        color=SERIES["qsim"],
        linewidth=2,
        marker="o",
        markersize=6,
        markeredgecolor=SURFACE,
        markeredgewidth=1.5,
        label=LABELS["qsim"],
        zorder=3,
    )
    ax_time.set_yscale("log")
    ax_time.set_xlabel("qubitek száma", color=INK_SECONDARY, fontsize=10)
    ax_time.set_ylabel("futásidő (s, log skála)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax_time)
    title(ax_time, "Futásidő", "GHZ-lánc + forgatások, egy szálon")
    legend = ax_time.legend(frameon=False, fontsize=9.5, loc="upper left")
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    speedups = [r["speedup"] for r in rows]
    bars = ax_speedup.bar(
        qubits,
        speedups,
        1.3,
        color=SERIES["qsim"],
        zorder=3,
        edgecolor=SURFACE,
        linewidth=2,
    )
    for rect, value in zip(bars, speedups, strict=True):
        ax_speedup.text(
            rect.get_x() + rect.get_width() / 2,
            value * 1.03,
            f"{value:.0f}×",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK_SECONDARY,
            fontweight="600",
        )
    ax_speedup.axhline(1.0, color=AXIS, linewidth=1.2, zorder=2)
    ax_speedup.set_xlabel("qubitek száma", color=INK_SECONDARY, fontsize=10)
    ax_speedup.set_ylabel("qsim gyorsulás (×)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax_speedup)
    title(ax_speedup, "A qsim gyorsulása", "Az ár: complex64 → ~10⁻⁷ Ha hiba")

    fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.13, wspace=0.26)
    fig.savefig(out / "fig05_skalazas.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_mitigation(data: dict[str, Any], out: Path) -> None:
    """ZNE: torzítás (bal) és szórás (jobb), a hardveres L5-tel együtt.

    Minden érték a θ* pontban, hiba a Full CI-hez képest, mHa-ben. A bal panel
    a módszer RENDSZERES hibáját mutatja (egzakt zajos várható érték), a jobb a
    VÉGES MINTAVÉTEL mellett ténylegesen várható eloszlást (seed-ensemble).
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, (ax_bias, ax_dist) = plt.subplots(
        1,
        2,
        figsize=(12.5, 5.6),
        facecolor=SURFACE,
        gridspec_kw={"wspace": 0.26, "width_ratios": [1.0, 1.15]},
    )
    chem = CHEMICAL_ACCURACY_HA * 1e3

    # ---------------------------------------------------------------- bal: torzítás
    local = data["bias_zne_local"]
    lam = np.asarray(local["scales"])
    y = np.asarray(local["scaled_errors_mha"])
    grid = np.linspace(0.0, 5.3, 200)

    ax_bias.axhspan(-chem, chem, color=STATUS["good"], alpha=0.14, zorder=1)
    ax_bias.axhline(0.0, color=INK, linewidth=1.0, zorder=2)

    quad = np.polyfit(lam, y, deg=2)
    lin = np.polyfit(lam, y, deg=1)
    ex = local["extrapolated_errors_mha"]
    ax_bias.plot(
        grid,
        np.polyval(quad, grid),
        color=SERIES["qiskit_statevector"],
        lw=2.0,
        zorder=3,
        label=f"Richardson (λ→0: {ex['richardson']:+.2f} mHa)",
    )
    ax_bias.plot(
        grid,
        np.polyval(lin, grid),
        color=SERIES["cirq_simulator"],
        lw=1.6,
        ls="--",
        zorder=3,
        label=f"lineáris (λ→0: {ex['linear']:+.2f} mHa)",
    )
    ax_bias.scatter(
        lam,
        y,
        s=60,
        color=SERIES["qiskit_statevector"],
        edgecolor=INK,
        lw=1.0,
        zorder=5,
        label="zne_local — ISA-hajtogatás (mért)",
    )
    ax_bias.scatter(
        [0.0],
        [ex["richardson"]],
        marker="*",
        s=200,
        color=STATUS["good"],
        edgecolor=INK,
        lw=1.0,
        zorder=6,
    )

    mitiq_block = data.get("bias_zne_mitiq")
    if mitiq_block is not None:
        mx = mitiq_block["extrapolated_errors_mha"]
        ax_bias.scatter(
            mitiq_block["scales"],
            mitiq_block["scaled_errors_mha"],
            s=55,
            marker="D",
            facecolor="none",
            edgecolor=SERIES["qsim"],
            lw=1.6,
            zorder=5,
            label=f"zne_mitiq — logikai hajtogatás (λ→0: {mx['richardson']:+.2f} mHa)",
        )
        mquad = np.polyfit(mitiq_block["scales"], mitiq_block["scaled_errors_mha"], deg=2)
        ax_bias.plot(grid, np.polyval(mquad, grid), color=SERIES["qsim"], lw=1.0, ls=":", zorder=3)

    # Nagyító betét: a λ→0 extrapolált értékek a kémiai pontossági sávhoz mérve.
    inset = ax_bias.inset_axes((0.68, 0.14, 0.30, 0.26))
    rows: list[tuple[str, float]] = [
        (f"local {short}", local["extrapolated_errors_mha"][name])
        for name, short in (("richardson", "Rich."), ("exponential", "exp."), ("linear", "lin."))
    ]
    if mitiq_block is not None:
        rows += [
            (f"mitiq {short}", mitiq_block["extrapolated_errors_mha"][name])
            for name, short in (
                ("richardson", "Rich."),
                ("exponential", "exp."),
                ("linear", "lin."),
            )
        ]
    inset.axvspan(-chem, chem, color=STATUS["good"], alpha=0.18, zorder=1)
    inset.axvline(0.0, color=INK, lw=0.8, zorder=2)
    for idx, (_name, val) in enumerate(rows):
        ok = abs(val) < chem
        inset.scatter(
            [val],
            [idx],
            s=26,
            marker="o" if ok else "X",
            color=STATUS["good"] if ok else STATUS["critical"],
            edgecolor=INK,
            lw=0.6,
            zorder=3,
        )
        inset.text(
            val + 0.25,
            idx,
            f"{val:+.2f} {'✓' if ok else '✗'}",
            fontsize=7,
            va="center",
            color=INK_SECONDARY,
        )
    inset.set_yticks(range(len(rows)))
    inset.set_yticklabels([r[0] for r in rows], fontsize=7, color=INK_SECONDARY)
    inset.invert_yaxis()
    inset.set_xlim(-2.5, 8.5)
    inset.set_xlabel("torzítás (mHa)", fontsize=7.5, color=INK_SECONDARY, labelpad=1)
    inset.set_title(
        "λ→0 nagyítva · zöld = ±1.6 mHa",
        fontsize=7.5,
        color=STATUS["good"],
        loc="left",
        pad=4,
    )
    style_axes(inset, grid_axis="x")
    inset.tick_params(labelsize=7)

    for xi, yi, cnt in zip(lam, y, local["two_qubit_gate_counts"], strict=True):
        ax_bias.annotate(
            f"{cnt} CX",
            (xi, yi),
            textcoords="offset points",
            xytext=(-10, 8),
            ha="right",
            fontsize=8,
            color=INK_MUTED,
        )

    ax_bias.set_xlim(-0.3, 5.4)
    ax_bias.set_xlabel("Zajszorzó λ (ISA-szinten pontos)", color=INK_SECONDARY, fontsize=10)
    ax_bias.set_ylabel("Hiba a Full CI-hez (mHa)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax_bias)
    title(
        ax_bias,
        "1 · A ZNE torzítása",
        "egzakt zajos várható érték (precision = 0), H₂ θ*, FakeManilaV2",
    )
    leg = ax_bias.legend(frameon=False, fontsize=8.3, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK_SECONDARY)

    # ---------------------------------------------------------------- jobb: szórás
    ens = data["ensemble_errors_mha"]
    summ = data["ensemble_summary_mha"]
    cats = [
        ("raw", "nyers\n(λ=1)"),
        ("richardson", "ZNE\nRichardson"),
        ("exponential", "ZNE\nexponenciális"),
        ("linear", "ZNE\nlineáris"),
    ]
    rng = np.random.default_rng(0)  # csak a pontok vízszintes szórásához (jitter)

    y_lo, y_hi = -120.0, 95.0  # a kiugró exponenciális illesztések ne nyomják össze
    ax_dist.axhspan(-chem, chem, color=STATUS["good"], alpha=0.14, zorder=1)
    ax_dist.axhline(0.0, color=INK, linewidth=1.0, zorder=2)
    for i, (key, _) in enumerate(cats):
        vals = np.asarray(ens[key])
        inside = (vals >= y_lo) & (vals <= y_hi)
        ax_dist.scatter(
            i - 0.08 + rng.uniform(-0.14, 0.14, int(inside.sum())),
            vals[inside],
            s=14,
            color=SERIES["qiskit_statevector"],
            alpha=0.45,
            lw=0,
            zorder=3,
        )
        n_out = int((~inside).sum())
        if n_out:
            ax_dist.annotate(
                f"▼ {n_out} pont\n< {y_lo:.0f}",
                (i - 0.08, y_lo),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=STATUS["critical"],
            )
        m, sd = summ[key]["mean"], summ[key]["sd"]
        ax_dist.errorbar(
            [i + 0.22],
            [m],
            yerr=[sd],
            fmt="o",
            color=INK,
            ms=5,
            capsize=4,
            lw=1.4,
            zorder=5,
        )
        rmse = float(np.sqrt(np.mean(vals**2)))
        ax_dist.text(
            i,
            y_hi - 2,
            f"{m:+.1f} ± {sd:.1f}\nRMSE {rmse:.1f}",
            fontsize=8,
            color=INK_SECONDARY,
            va="top",
            ha="center",
        )

    hw = data.get("l5_hardware") or {}
    labels = [c[1] for c in cats]
    if hw.get("error_mha") is not None and hw.get("stds_mha") is not None:
        x_hw = len(cats)
        labels.append("L5 ibm_kingston\n(TREX, 1 mérés)")
        ax_dist.errorbar(
            [x_hw],
            [hw["error_mha"]],
            yerr=[hw["stds_mha"]],
            fmt="none",
            ecolor="#8a3ffc",
            elinewidth=1.2,
            capsize=5,
            alpha=0.6,
            zorder=4,
        )
        ax_dist.errorbar(
            [x_hw],
            [hw["error_mha"]],
            yerr=[hw["ensemble_standard_error_mha"]],
            fmt="s",
            color="#8a3ffc",
            ms=7,
            elinewidth=2.4,
            capsize=0,
            zorder=5,
        )
        ax_dist.text(
            x_hw,
            y_hi - 2,
            f"{hw['error_mha']:+.1f} ± {hw['ensemble_standard_error_mha']:.1f} (ens.)"
            f"\n± {hw['stds_mha']:.1f} (stds)",
            fontsize=8,
            color=INK_SECONDARY,
            va="top",
            ha="center",
        )

    ax_dist.set_xticks(range(len(labels)))
    ax_dist.set_xticklabels(labels, fontsize=8.8, color=INK_SECONDARY)
    ax_dist.set_xlim(-0.55, len(labels) - 0.45)
    ax_dist.set_ylim(y_lo, y_hi + 20)
    ax_dist.set_ylabel("Hiba a Full CI-hez (mHa)", color=INK_SECONDARY, fontsize=10)
    style_axes(ax_dist)
    title(
        ax_dist,
        f"2 · A ZNE szórása — {data['ensemble_size']} független seed",
        f"precision {data['precision_per_evaluation_ha'] * 1e3:.1f} mHa/kiértékelés · "
        "pont = egy futás · fekete = átlag ± szórás",
    )

    fig.subplots_adjust(left=0.065, right=0.985, top=0.85, bottom=0.14)
    fig.savefig(out / "fig06_mitigacio.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


# ================================================================= Fázis 5
F5_DATA = Path("docs/figures/data")
REPETITION_SAMPLES = 1024
"""Az ismétlés-kísérlet mintaszáma (fig08). 1024 = 2¹⁰: a legnagyobb (N = 32)
blokkméret is 32 blokkot ad, így a blokkátlagok szórásbecslésének relatív hibája
~1/√(2·31) ≈ 13%. (256 mintával ez 8 blokk és ~27% volt — mérve: a meredekség
−0.41-re szórt.)"""


def _load_batch(name: str) -> dict[str, Any]:
    path = F5_DATA / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} hiányzik — előbb: python scripts/run_batch.py --preset "
            f"{name.replace('_', '-')} --export {path}"
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def measure_active_space() -> dict[str, Any]:
    """fig07 adatai az ``f5_deterministic`` exportból (mérés nélkül, származtatott)."""
    batch = _load_batch("f5_deterministic")
    points = [
        {
            "molecule": r["molecule_name"],
            "bond_length": r["bond_length"],
            "active_space": (
                "teljes"
                if r["active_electrons"] is None
                else f"({r['active_electrons']}e,{r['active_orbitals']}o)"
            ),
            "backend": r["backend"],
            "energy_ha": r["energy_ha"],
            "full_ci_ha": r["full_ci_ha"],
            "casci_ha": r["casci_ha"],
            "exact_diag_ha": r["exact_diag_ha"],
            "hartree_fock_ha": r["hartree_fock_ha"],
            "n_function_evaluations": r["n_function_evaluations"],
            "wall_time_s": r["wall_time_s"],
        }
        for r in batch["rows"]
    ]
    return {
        "source": "f5_deterministic.json",
        "vqebd_version": batch["vqebd_version"],
        "points": points,
    }


def measure_repetition() -> dict[str, Any]:
    """fig08: az ismétlés hatása — SEM ∝ N^−½, és a torzítás-padló (AC-5.6).

    H₂ θ*-ban, rögzített seeddel: 256 független kiértékelés (1) lövészajjal,
    (2) FakeManilaV2 zajjal nyersen, (3) ugyanazzal ZNE-Richardsonnal. A
    referenciák: L2 (zajmentes), és a zajmodell szerinti egzakt várható érték
    (``precision = 0``) nyersen és ZNE-vel — ezek a „padlók”.
    """
    from vqebd.backends.estimators import AerNoisyEnergyEvaluator, AerShotEnergyEvaluator
    from vqebd.chemistry.mapping import map_to_qubits
    from vqebd.chemistry.molecule import h2
    from vqebd.chemistry.problem import build_electronic_structure
    from vqebd.config import AnsatzSpec, VQEConfig
    from vqebd.mitigation import get_mitigation_strategy
    from vqebd.seeds import SeedSet
    from vqebd.stats import block_mean_spread, loglog_slope
    from vqebd.vqe.ansatz import build_ansatz
    from vqebd.vqe.runner import run_vqe

    l2 = run_vqe(VQEConfig(molecule=h2()))
    theta = list(l2.optimal_parameters)
    structure = build_electronic_structure(h2())
    hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
    seeds = SeedSet.derive(20260925)
    ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(), seeds)
    offset = hamiltonian.energy_offset
    circuit, observable = ansatz.circuit, hamiltonian.operator

    def err_mha(electronic: float) -> float:
        return 1e3 * (electronic + offset - l2.energy)

    # Külön seed a két sorozatnak: azonos seeddel ugyanazt a Gauss-sorozatot húznák
    # (közös véletlen számok), és a két görbe bitre fedné egymást. Az azonos σ
    # ettől még a `precision`-modell konvenciója: σ = 1/sqrt(8192) Ha, zajmodelltől
    # függetlenül (ADR-0007, felülvizsgálati feltétel).
    shot = AerShotEnergyEvaluator(circuit, observable, SeedSet.derive(20260926))
    noisy = AerNoisyEnergyEvaluator(circuit, observable, seeds)
    zne = get_mitigation_strategy("zne_local", scale_factors=(1, 3, 5), extrapolator="richardson")
    samples = {
        "shot": [err_mha(shot.evaluate(theta)) for _ in range(REPETITION_SAMPLES)],
        "noisy_raw": [err_mha(noisy.evaluate(theta)) for _ in range(REPETITION_SAMPLES)],
        "noisy_zne": [
            err_mha(zne.execute(circuit, observable, noisy, theta, seeds).mitigated_energy)
            for _ in range(REPETITION_SAMPLES)
        ],
    }
    exact_noisy = AerNoisyEnergyEvaluator(circuit, observable, seeds, precision=0.0)
    floors = {
        "shot": 0.0,
        "noisy_raw": err_mha(exact_noisy.evaluate(theta)),
        "noisy_zne": err_mha(
            zne.execute(circuit, observable, exact_noisy, theta, seeds).mitigated_energy
        ),
    }
    sizes = [1, 2, 4, 8, 16, 32]
    spread = {k: block_mean_spread(v, sizes) for k, v in samples.items()}
    slopes = {k: loglog_slope(sizes, [s[n] for n in sizes]) for k, s in spread.items()}
    return {
        "theta_star": theta,
        "l2_energy_ha": l2.energy,
        "precision_per_evaluation_ha": 1.0 / 8192**0.5,
        "n_samples": REPETITION_SAMPLES,
        "block_sizes": sizes,
        "samples_mha": samples,
        "bias_floor_mha": floors,
        "block_spread_mha": {k: {str(n): v for n, v in s.items()} for k, s in spread.items()},
        "loglog_slope": slopes,
    }


# A hibaköltségvetés ábrájának sorai: (címke, export, molekula, R, aktív tér, backend, mitigáció)
_BUDGET_ROWS: tuple[tuple[str, str, str, float, str, str, str], ...] = (
    ("H₂ 0.735 Å · L2", "f5_deterministic", "H2", 0.735, "teljes", "qiskit_statevector", "none"),
    ("H₂ 0.735 Å · lövészaj", "f5_statistical", "H2", 0.735, "teljes", "qiskit_aer_shot", "none"),
    ("H₂ 0.735 Å · zajos", "f5_statistical", "H2", 0.735, "teljes", "qiskit_aer_noisy", "none"),
    (
        "H₂ 0.735 Å · ZNE lin.",
        "f5_statistical",
        "H2",
        0.735,
        "teljes",
        "qiskit_aer_noisy",
        "zne_local/linear",
    ),
    (
        "H₂ 0.735 Å · ZNE Rich.",
        "f5_statistical",
        "H2",
        0.735,
        "teljes",
        "qiskit_aer_noisy",
        "zne_local/richardson",
    ),
    ("H₂ 1.5 Å · L2", "f5_deterministic", "H2", 1.5, "teljes", "qiskit_statevector", "none"),
    ("H₂ 1.5 Å · zajos", "f5_statistical", "H2", 1.5, "teljes", "qiskit_aer_noisy", "none"),
    (
        "H₂ 1.5 Å · ZNE Rich.",
        "f5_statistical",
        "H2",
        1.5,
        "teljes",
        "qiskit_aer_noisy",
        "zne_local/richardson",
    ),
    ("LiH (2e,3o) · L2", "f5_deterministic", "LiH", 1.595, "(2e,3o)", "qiskit_statevector", "none"),
    ("LiH (2e,3o) · zajos", "f5_statistical", "LiH", 1.595, "(2e,3o)", "qiskit_aer_noisy", "none"),
    ("LiH (2e,5o) · L2", "f5_deterministic", "LiH", 1.595, "(2e,5o)", "qiskit_statevector", "none"),
    (
        "BeH₂ (2e,3o) · L2",
        "f5_deterministic",
        "BeH2",
        1.33,
        "(2e,3o)",
        "qiskit_statevector",
        "none",
    ),
    (
        "BeH₂ (4e,6o) · L2",
        "f5_deterministic",
        "BeH2",
        1.33,
        "(4e,6o)",
        "qiskit_statevector",
        "none",
    ),
)


def _statevector_energy_at(
    molecule: str, bond: float, space: str, theta: list[float], cache: dict[Any, Any]
) -> float:
    """Zajmentes (állapotvektoros) teljes energia egy adott θ-ban — a θ_opt minősítéséhez."""
    from vqebd.backends.estimators import StatevectorEnergyEvaluator
    from vqebd.chemistry.mapping import map_to_qubits
    from vqebd.chemistry.molecule import beh2, h2, lih
    from vqebd.chemistry.problem import build_electronic_structure
    from vqebd.config import ActiveSpaceSpec, AnsatzSpec
    from vqebd.seeds import SeedSet
    from vqebd.vqe.ansatz import build_ansatz

    key = (molecule, bond, space)
    if key not in cache:
        factory = {"H2": h2, "LiH": lih, "BeH2": beh2}[molecule]
        active = None
        if space != "teljes":
            e, o = space.strip("()").replace("e", "").replace("o", "").split(",")
            active = ActiveSpaceSpec(int(e), int(o))
        structure = build_electronic_structure(factory(bond), active)
        hamiltonian = map_to_qubits(structure, "parity", two_qubit_reduction=True)
        ansatz = build_ansatz(structure, hamiltonian, AnsatzSpec(), SeedSet.derive(0))
        cache[key] = (
            StatevectorEnergyEvaluator(ansatz.circuit, hamiltonian.operator),
            hamiltonian.energy_offset,
        )
    evaluator, offset = cache[key]
    return float(evaluator.evaluate(theta)) + float(offset)


def measure_error_budget() -> dict[str, Any]:
    """fig09: hibaköltségvetés a **két batch uniójából**, a zajos tag szétbontásával.

    A könyvtári :class:`~vqebd.stats.ErrorBudget` a zajos szinten egyetlen tagot ad
    (``átlag − L2``). Ez két, fizikailag különböző hatást mos össze, ezért itt,
    a tárolt θ_opt-ok alapján, szétbontjuk:

    - **optimalizálás zajban** = ``E_sv(θ_opt) − L2``: a zajos célfüggvényen a COBYLA
      nem θ*-ban áll meg (a H₂ korrelációs energiája csak ~1.8σ);
    - **eszközzaj-torzítás** = ``átlag(újramintavétel) − E_sv(θ_opt)``: a zajmodell
      torzítása rögzített θ-ban (lövészajnál ez várhatóan 0).

    A tagok összege továbbra is a teljes hiba (teleszkópikus).
    """
    import statistics

    from vqebd.batch.aggregate import aggregate_rows, group_key

    exports = {name: _load_batch(name) for name in ("f5_deterministic", "f5_statistical")}
    rows_all = [row for batch in exports.values() for row in batch["rows"]]
    groups = aggregate_rows(rows_all)
    by_key = {g.key: g for g in groups}
    members: dict[Any, list[dict[str, Any]]] = {}
    for row in rows_all:
        members.setdefault(group_key(row), []).append(row)

    cache: dict[Any, Any] = {}
    out_rows = []
    for label, _export, molecule, bond, space, backend, mitigation in _BUDGET_ROWS:
        match = [
            g
            for g in groups
            if g.molecule == molecule
            and abs(g.bond_length - bond) < 1e-9
            and g.active_space_label == space
            and g.backend == backend
            and g.mitigation_label == mitigation
        ]
        if len(match) != 1:
            raise ValueError(f"a(z) '{label}' sorhoz {len(match)} csoport illeszkedik (1 kell)")
        g = match[0]
        budget = g.budget.to_dict() if g.budget is not None else {}
        entry: dict[str, Any] = {
            "label": label,
            "n": g.n,
            "accuracy": g.accuracy,
            "error_vs_fci": g.error_vs_fci.to_dict() if g.error_vs_fci else None,
            "selection_bias_ha": g.selection_bias,
            "truncation": budget.get("truncation"),
            "mapping": budget.get("mapping"),
            "ansatz": budget.get("ansatz"),
            "optimization": None,
            "device_bias": None,
            "statistical": budget.get("statistical"),
            "total": budget.get("total"),
        }
        l2_key = (*g.key[:4], "qiskit_statevector", "SLSQP", "none", None)
        l2 = by_key.get(l2_key)
        if backend != "qiskit_statevector" and l2 is not None:
            sv = [
                _statevector_energy_at(
                    molecule, bond, space, json.loads(r["optimal_parameters_json"]), cache
                )
                for r in members[g.key]
            ]
            sv_mean = statistics.fmean(sv)
            entry["optimization"] = sv_mean - l2.energy.mean
            entry["device_bias"] = g.energy.mean - sv_mean
        out_rows.append(entry)
    return {"sources": sorted(exports), "rows": out_rows}


def figure_active_space(data: dict[str, Any], out: Path) -> None:
    """fig07: LiH és BeH₂ PES aktív térben — FCI, CASCI, VQE (3 platform) + csonkolás."""
    import matplotlib.pyplot as plt

    points = data["points"]
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12.5, 8.2),
        facecolor=SURFACE,
        gridspec_kw={"height_ratios": [1.6, 1.0], "hspace": 0.42, "wspace": 0.22},
    )
    chem = CHEMICAL_ACCURACY_HA * 1e3
    space_style = {
        "(2e,3o)": ("--", "o", "minimális"),
        "(2e,5o)": ("-", "s", "frozen core"),
        "(4e,6o)": ("-", "s", "frozen core"),
    }
    markers = {"qiskit_statevector": "o", "cirq_simulator": "x", "qsim": "^"}

    for col, molecule in enumerate(("LiH", "BeH2")):
        ax, ax_t = axes[0][col], axes[1][col]
        mol_pts = [p for p in points if p["molecule"] == molecule]
        bonds = sorted({p["bond_length"] for p in mol_pts})
        fci = {p["bond_length"]: p["full_ci_ha"] for p in mol_pts}
        hf = {p["bond_length"]: p["hartree_fock_ha"] for p in mol_pts}
        ax.plot(bonds, [fci[b] for b in bonds], color=INK, lw=2.0, label="L0 Full CI", zorder=3)
        ax.plot(
            bonds,
            [hf[b] for b in bonds],
            color=INK_MUTED,
            lw=1.0,
            ls=":",
            label="Hartree–Fock",
            zorder=2,
        )
        for space in sorted({p["active_space"] for p in mol_pts}):
            ls, _, name = space_style[space]
            sp = sorted({p["bond_length"] for p in mol_pts if p["active_space"] == space})
            cas = {p["bond_length"]: p["casci_ha"] for p in mol_pts if p["active_space"] == space}
            ax.plot(
                sp,
                [cas[b] for b in sp],
                color=INK_SECONDARY,
                lw=1.3,
                ls=ls,
                marker="." if len(sp) == 1 else None,
                label=f"L0′ CASCI {space} — {name}",
                zorder=2,
            )
            for backend, marker in markers.items():
                vq = sorted(
                    (p["bond_length"], p["energy_ha"])
                    for p in mol_pts
                    if p["active_space"] == space and p["backend"] == backend
                )
                if vq:
                    ax.scatter(
                        [b for b, _ in vq],
                        [e for _, e in vq],
                        marker=marker,
                        s=46,
                        color=SERIES[backend],
                        lw=1.4,
                        zorder=5,
                        facecolor="none" if marker == "o" else SERIES[backend],
                    )
            trunc = [1e3 * (cas[b] - fci[b]) for b in sp]
            ax_t.plot(
                sp, trunc, color=INK_SECONDARY, ls=ls, marker="o", ms=4, label=f"{space} — {name}"
            )
            for b, t in zip(sp, trunc, strict=True):
                ax_t.annotate(
                    f"{t:.2f}",
                    (b, t),
                    textcoords="offset points",
                    xytext=(4, 4),
                    fontsize=7.5,
                    color=INK_SECONDARY,
                )
        for backend, marker in markers.items():
            ax.scatter(
                [],
                [],
                marker=marker,
                color=SERIES[backend],
                facecolor="none" if marker == "o" else SERIES[backend],
                label=f"L2 VQE — {LABELS[backend]}",
            )
        ax.set_xlabel("Kötéshossz R (Å)", color=INK_SECONDARY, fontsize=9.5)
        ax.set_ylabel("Energia (Ha)", color=INK_SECONDARY, fontsize=9.5)
        style_axes(ax)
        name = "LiH" if molecule == "LiH" else "BeH₂"
        title(
            ax,
            f"{name} — aktív tér és referencialánc",
            "a VQE pontok a saját CASCI-görbéjükön; az FCI-től a csonkolás választja el őket",
        )
        leg = ax.legend(frameon=False, fontsize=7.8, loc="upper right")
        for t in leg.get_texts():
            t.set_color(INK_SECONDARY)

        ax_t.axhline(chem, color=STATUS["good"], lw=1.4, ls="--")
        ax_t.text(
            max(bonds),
            chem * 1.25,
            "kémiai pontosság (1.6 mHa)",
            color=STATUS["good"],
            fontsize=8,
            ha="right",
            va="bottom",
            fontweight="600",
        )
        ax_t.set_yscale("log")
        ax_t.set_ylim(0.05, 200)
        ax_t.set_xlabel("Kötéshossz R (Å)", color=INK_SECONDARY, fontsize=9.5)
        ax_t.set_ylabel("Csonkolás CASCI − FCI (mHa)", color=INK_SECONDARY, fontsize=9.5)
        style_axes(ax_t)
        title(ax_t, "Az aktív tér ára", "determinisztikus modellhiba — ismétléssel nem csökken")
        leg = ax_t.legend(frameon=False, fontsize=7.8, loc="lower right")
        for t in leg.get_texts():
            t.set_color(INK_SECONDARY)

    fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.07)
    fig.savefig(out / "fig07_aktiv_ter.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_repetition(data: dict[str, Any], out: Path) -> None:
    """fig08: az ismétlés a szórást csökkenti (N^−½), a torzítást nem."""
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import stats as sps

    series = {
        "shot": ("lövészaj (zajmentes eszköz)", SERIES["qiskit_statevector"]),
        "noisy_raw": ("FakeManilaV2, nyers", SERIES["cirq_simulator"]),
        "noisy_zne": ("FakeManilaV2 + ZNE Richardson", SERIES["qsim"]),
    }
    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(12.5, 5.4), facecolor=SURFACE, gridspec_kw={"wspace": 0.25}
    )
    sizes = data["block_sizes"]
    for key, (label, color) in series.items():
        spread = [data["block_spread_mha"][key][str(n)] for n in sizes]
        ax_a.plot(
            sizes,
            spread,
            "o",
            color=color,
            ms=6,
            zorder=4,
            label=f"{label} (meredekség {data['loglog_slope'][key]:+.2f})",
        )
        ref = spread[0] / np.sqrt(np.asarray(sizes, float))
        ax_a.plot(sizes, ref, color=color, lw=1.0, ls="--", zorder=3)
    ax_a.axhline(CHEMICAL_ACCURACY_HA * 1e3, color=STATUS["good"], lw=1.3, ls=":")
    ax_a.text(
        sizes[0],
        CHEMICAL_ACCURACY_HA * 1e3 * 1.08,
        "kémiai pontosság (1.6 mHa)",
        ha="left",
        va="bottom",
        fontsize=8,
        color=STATUS["good"],
        fontweight="600",
    )
    ax_a.set_xscale("log", base=2)
    ax_a.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

    ax_a.yaxis.set_major_locator(FixedLocator([1.5, 2, 3, 5, 10, 20, 30]))
    ax_a.yaxis.set_minor_locator(NullLocator())
    ax_a.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
    ax_a.xaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
    ax_a.set_xlabel(
        "Ismétlésszám N (átlagolt független kiértékelés)", color=INK_SECONDARY, fontsize=9.5
    )
    ax_a.set_ylabel("Az N-es átlag szórása (mHa)", color=INK_SECONDARY, fontsize=9.5)
    style_axes(ax_a, grid_axis="both")
    title(
        ax_a,
        "1 · Az ismétlés a PRECIZITÁST javítja",
        "szaggatott: elméleti σ/√N; mért meredekség ≈ −½ mindhárom zajra",
    )
    leg = ax_a.legend(frameon=False, fontsize=8, loc="upper right")
    for t in leg.get_texts():
        t.set_color(INK_SECONDARY)

    n_axis = np.arange(1, data["n_samples"] + 1)
    for key in ("noisy_raw", "noisy_zne"):
        label, color = series[key]
        vals = np.asarray(data["samples_mha"][key])
        mean = np.cumsum(vals) / n_axis
        sd = np.array([vals[: i + 1].std(ddof=1) if i else np.nan for i in range(vals.size)])
        tcrit = sps.t.ppf(0.975, np.maximum(n_axis - 1, 1))
        half = tcrit * sd / np.sqrt(n_axis)
        # A t-CI N = 2–3-nál (df = 1–2, t = 12.7 / 4.3) extrém széles; N ≥ 4-től ábrázoljuk.
        ax_b.fill_between(
            n_axis[3:], (mean - half)[3:], (mean + half)[3:], color=color, alpha=0.18, lw=0
        )
        ax_b.plot(n_axis, mean, color=color, lw=1.8, label=f"{label}: futó átlag ± 95% CI")
        floor = data["bias_floor_mha"][key]
        ax_b.axhline(floor, color=color, lw=1.0, ls="--")
        ax_b.text(
            n_axis[-1],
            floor,
            f" torzítás {floor:+.2f} mHa",
            color=color,
            fontsize=8,
            va="bottom",
            ha="right",
        )
    ax_b.axhspan(
        -CHEMICAL_ACCURACY_HA * 1e3,
        CHEMICAL_ACCURACY_HA * 1e3,
        color=STATUS["good"],
        alpha=0.15,
        lw=0,
    )
    ax_b.axhline(0.0, color=INK, lw=0.9)
    ax_b.set_xscale("log", base=2)
    ax_b.xaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
    ax_b.set_ylim(-40, 70)
    ax_b.set_xlabel("Ismétlésszám N", color=INK_SECONDARY, fontsize=9.5)
    ax_b.set_ylabel("Hiba a zajmentes L2-höz (mHa)", color=INK_SECONDARY, fontsize=9.5)
    style_axes(ax_b)
    title(
        ax_b,
        "2 · A TORZÍTÁST nem — azt a módszer (ZNE) javítja",
        "a nyers átlag a torzítás-padlóhoz tart, nem a nullához; zöld = kémiai pontosság",
    )
    leg = ax_b.legend(frameon=False, fontsize=8, loc="upper right")
    for t in leg.get_texts():
        t.set_color(INK_SECONDARY)

    fig.subplots_adjust(left=0.07, right=0.985, top=0.86, bottom=0.12)
    fig.savefig(out / "fig08_ismetles.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def figure_error_budget(data: dict[str, Any], out: Path) -> None:
    """fig09: hibaköltségvetés-táblázat — forrásonként, színezve a nagyság szerint."""
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, LogNorm

    columns = [
        ("truncation", "csonkolás\nCASCI−FCI"),
        ("mapping", "leképezés\nL1−CASCI"),
        ("ansatz", "ansatz\nL2−L1"),
        ("optimization", "optimalizálás\nzajban"),
        ("device_bias", "eszközzaj\nθ_opt-ban"),
        ("statistical", "statisztikus\n(SEM)"),
        ("total", "teljes\nátlag−FCI"),
    ]
    rows = data["rows"]
    cmap = LinearSegmentedColormap.from_list("vqebd_blue", BLUE_RAMP)
    norm = LogNorm(vmin=1e-3, vmax=1e2)  # mHa
    fig, ax = plt.subplots(figsize=(12.5, 0.52 * len(rows) + 2.2), facecolor=SURFACE)
    chem = CHEMICAL_ACCURACY_HA * 1e3
    for i, row in enumerate(rows):
        for j, (key, _) in enumerate(columns):
            value = row.get(key)
            if value is None:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, color=GRID, alpha=0.35, lw=0))
                ax.text(
                    j + 0.5, i + 0.5, "—", ha="center", va="center", color=INK_MUTED, fontsize=8.5
                )
                continue
            mha = 1e3 * value
            mag = max(abs(mha), 1e-3)
            face = cmap(norm(mag))
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=face, lw=0))
            dark = norm(mag) > 0.55
            over = abs(mha) >= chem and key != "statistical"
            text = f"{mha:+.2e}" if abs(mha) < 1e-2 else f"{mha:+.2f}"
            ax.text(
                j + 0.5,
                i + 0.5,
                text + (" ▲" if over else ""),
                ha="center",
                va="center",
                fontsize=8.3,
                color=SURFACE if dark else INK,
                fontweight="700" if over else "normal",
            )
        ax.text(
            len(columns) + 0.08,
            i + 0.5,
            f"n={row['n']} · {row['accuracy']}",
            va="center",
            fontsize=8.3,
            color=INK_SECONDARY,
        )
    ax.set_xlim(0, len(columns) + 1.6)
    ax.set_ylim(len(rows), 0)
    ax.set_xticks(np.arange(len(columns)) + 0.5)
    ax.set_xticklabels([c[1] for c in columns], fontsize=8.8, color=INK_SECONDARY)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(rows)) + 0.5)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=8.8, color=INK_SECONDARY)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(
        "Hibaköltségvetés (mHa) — ▲ = a kémiai pontosság (1.6 mHa) fölött; "
        "szín: |érték| log-skálán",
        color=INK,
        fontsize=11.5,
        fontweight="600",
        loc="left",
        pad=46,
    )
    fig.subplots_adjust(left=0.19, right=0.99, top=0.84, bottom=0.03)
    fig.savefig(out / "fig09_hibakoltsegvetes.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=Path("docs/figures"), type=Path)
    parser.add_argument("--quick", action="store_true", help="a lassú skálázás kihagyása")
    parser.add_argument(
        "--only",
        default=None,
        help="csak a megnevezett mérés/ábra (pl. mitigacio); a többi adat érintetlen marad",
    )
    parser.add_argument(
        "--replot",
        action="store_true",
        help="nincs újramérés: a mentett docs/figures/data/<név>.json-ból rajzol",
    )
    args = parser.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")

    out: Path = args.out
    data_dir = out / "data"
    out.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    steps: list[tuple[str, Any, Any]] = [
        ("hibalanc", measure_reference_chain, figure_reference_chain),
        ("optimalizalo_matrix", measure_optimizer_matrix, figure_optimizer_matrix),
        ("disszociacio", measure_dissociation, figure_dissociation),
        ("mitigacio", measure_mitigation, figure_mitigation),
        # Fázis 5 — az aktiv_ter és a hibakoltsegvetes a batch-exportokból dolgozik
        # (scripts/run_batch.py), az ismetles saját, rögzített seedű mérés.
        ("aktiv_ter", measure_active_space, figure_active_space),
        ("ismetles", measure_repetition, figure_repetition),
        ("hibakoltsegvetes", measure_error_budget, figure_error_budget),
    ]
    if not args.quick:
        steps.append(("skalazas", measure_scaling, figure_scaling))
    if args.only is not None:
        steps = [step for step in steps if step[0] == args.only]
        if not steps:
            parser.error(f"ismeretlen mérés: {args.only!r}")

    for name, measure, draw in steps:
        data_file = data_dir / f"{name}.json"
        started = time.perf_counter()
        if args.replot:
            print(f"[adat ] {name} ← {data_file}", flush=True)
            measured = json.loads(data_file.read_text(encoding="utf-8"))
        else:
            print(f"[mérés] {name} …", flush=True)
            measured = measure()
            data_file.write_text(
                json.dumps(measured, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n"
            )
        elapsed = time.perf_counter() - started
        draw(measured, out)
        print(f"[ábra ] {name} kész ({elapsed:.1f} s)", flush=True)

    if args.only is None:
        print("[ábra ] gradiens_biztonsag …", flush=True)
        figure_gradient_safety(out)

    print(f"\nKész. Ábrák: {out}/  —  nyers adatok: {data_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
