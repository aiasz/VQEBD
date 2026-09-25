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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=Path("docs/figures"), type=Path)
    parser.add_argument("--quick", action="store_true", help="a lassú skálázás kihagyása")
    parser.add_argument(
        "--only",
        default=None,
        help="csak a megnevezett mérés/ábra (pl. mitigacio); a többi adat érintetlen marad",
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
    ]
    if not args.quick:
        steps.append(("skalazas", measure_scaling, figure_scaling))
    if args.only is not None:
        steps = [step for step in steps if step[0] == args.only]
        if not steps:
            parser.error(f"ismeretlen mérés: {args.only!r}")

    for name, measure, draw in steps:
        print(f"[mérés] {name} …", flush=True)
        started = time.perf_counter()
        measured = measure()
        elapsed = time.perf_counter() - started
        (data_dir / f"{name}.json").write_text(
            json.dumps(measured, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n"
        )
        draw(measured, out)
        print(f"[ábra ] {name} kész ({elapsed:.1f} s)", flush=True)

    if args.only is None:
        print("[ábra ] gradiens_biztonsag …", flush=True)
        figure_gradient_safety(out)

    print(f"\nKész. Ábrák: {out}/  —  nyers adatok: {data_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
