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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=Path("docs/figures"), type=Path)
    parser.add_argument("--quick", action="store_true", help="a lassú skálázás kihagyása")
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
    ]
    if not args.quick:
        steps.append(("skalazas", measure_scaling, figure_scaling))

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

    print("[ábra ] gradiens_biztonsag …", flush=True)
    figure_gradient_safety(out)

    print(f"\nKész. Ábrák: {out}/  —  nyers adatok: {data_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
