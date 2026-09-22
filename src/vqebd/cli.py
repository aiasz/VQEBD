"""Parancssori felület.

Az alapterv előírja, hogy a kvantummodul **kézzel is futtatható és ellenőrizhető**
legyen (AC-1.9). Használat::

    python -m vqebd                                  # H2, 0.735 Å, STO-3G
    python -m vqebd --bond-length 1.2                # másik geometria
    python -m vqebd --mapper jordan_wigner           # másik leképezés
    python -m vqebd --optimizer COBYLA               # másik optimalizáló
    python -m vqebd --backend cirq_simulator         # másik platform (ADR-0006)
    python -m vqebd --backend qsim                   # C++ szimulátor, complex64
    python -m vqebd --json                           # gépi feldolgozáshoz

A CLI szándékosan **külön modulban** van, nem a :mod:`vqebd.vqe.runner`-ben:
így a runner importálható anélkül, hogy egyszerre ``__main__``-ként is futna
(ami a Python ``runpy`` figyelmeztetését váltaná ki).

Kilépési kód
------------
``0`` akkor és csak akkor, ha az eredmény kémiai pontosságon belül van **és** a
variációs elv teljesül. Így a parancs gépi ellenőrzésre (CI, dry run) is alkalmas.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import json
import sys

from vqebd import __version__
from vqebd.chemistry.molecule import H2_REFERENCE_BOND_LENGTH, h2
from vqebd.config import AnsatzSpec, OptimizerSpec, VQEConfig
from vqebd.vqe.runner import run_vqe

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Az argumentum-elemző felépítése (külön függvényben a tesztelhetőségért)."""
    parser = argparse.ArgumentParser(
        prog="python -m vqebd",
        description=(
            "VQE-alapú alapállapoti energia kis molekulákra. "
            "Fázis 1: H2, zajmentes állapotvektor-szimulátor."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"vqebd {__version__}")
    parser.add_argument(
        "--bond-length",
        type=float,
        default=H2_REFERENCE_BOND_LENGTH,
        help="H2 kötéshossz ångströmben",
    )
    parser.add_argument("--basis", default="sto3g", help="bázis neve")
    parser.add_argument(
        "--mapper",
        default="parity",
        choices=["jordan_wigner", "parity", "bravyi_kitaev"],
        help="fermion → qubit leképezés",
    )
    parser.add_argument(
        "--no-two-qubit-reduction",
        action="store_true",
        help="a kétqubites redukció kikapcsolása (csak parity esetén hat)",
    )
    parser.add_argument(
        "--backend",
        default="qiskit_statevector",
        choices=["qiskit_statevector", "cirq_simulator", "qsim"],
        help="platform-backend: melyik szimulátor végezze a kiértékelést (ADR-0006)",
    )
    parser.add_argument("--optimizer", default="SLSQP", help="SciPy optimalizáló-metódus")
    parser.add_argument("--maxiter", type=int, default=300, help="iterációs felső korlát")
    parser.add_argument("--seed", type=int, default=20260922, help="mester-seed")
    parser.add_argument(
        "--initial-point",
        default="zeros",
        choices=["zeros", "random"],
        help="a variációs paraméterek kezdőértéke",
    )
    parser.add_argument(
        "--no-fci",
        action="store_true",
        help="a Full CI referencia (L0) kihagyása — nagy rendszereknél drága",
    )
    parser.add_argument("--json", action="store_true", help="JSON kimenet")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont.

    Args:
        argv: Argumentumok; ``None`` esetén a ``sys.argv``.

    Returns:
        ``0``, ha az eredmény kémiai pontosságon belül van és a variációs elv
        teljesül; ``1`` egyébként; ``2`` hiba esetén.
    """
    args = build_parser().parse_args(argv)

    config = VQEConfig(
        molecule=h2(args.bond_length, basis=args.basis),
        mapper=args.mapper,
        two_qubit_reduction=not args.no_two_qubit_reduction,
        ansatz=AnsatzSpec(initial_point=args.initial_point),
        optimizer=OptimizerSpec(method=args.optimizer, maxiter=args.maxiter),
        backend=args.backend,
        seed=args.seed,
    )

    try:
        result = run_vqe(config, compute_fci=not args.no_fci)
    except (RuntimeError, ValueError) as exc:
        print(f"HIBA: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) if args.json else result.report()
    )

    return 0 if (result.within_chemical_accuracy and result.satisfies_variational_principle) else 1
