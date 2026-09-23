"""A parancssori felület integrációs tesztjei (AC-1.9).

Az alapterv előírja, hogy a kvantummodul **kézzel is futtatható és ellenőrizhető**
legyen. Ezek a tesztek a teljes láncot végigviszik a CLI-n keresztül: molekula →
Hamilton-operátor → VQE → kimenet → kilépési kód.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("qiskit_nature", reason="a Fázis 1 kvantum-stackjét igényli")
pytest.importorskip("pyscf", reason="a Fázis 1 kvantum-stackjét igényli")

from vqebd.cli import build_parser, main

pytestmark = pytest.mark.integration


# --- Argumentum-elemzés (gyors, kvantumszámítás nélkül) ----------------------


def test_parser_defaults_match_the_phase_1_reference_case() -> None:
    """Az alapértelmezés a Fázis 1 referencia-esete: H2, 0.735 Å, paritás, SLSQP."""
    args = build_parser().parse_args([])
    assert args.bond_length == pytest.approx(0.735)
    assert args.basis == "sto3g"
    assert args.mapper == "parity"
    assert args.optimizer == "SLSQP"
    assert args.initial_point == "zeros"
    assert args.json is False


def test_parser_rejects_unknown_mapper() -> None:
    """Az ismeretlen leképezés az argparse szintjén elbukik, nem futásidőben."""
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--mapper", "nincs_ilyen"])


def test_version_flag_reports_the_package_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import vqebd

    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["--version"])
    assert excinfo.value.code == 0
    assert vqebd.__version__ in capsys.readouterr().out


# --- Teljes futtatás ---------------------------------------------------------


def test_default_run_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    """Az alapértelmezett futtatás 0 kilépési kóddal és értelmes kimenettel zárul.

    A ``0`` kilépési kód **nem** azt jelenti, hogy „a program nem szállt el":
    a CLI csak akkor ad nullát, ha az eredmény kémiai pontosságon belül van ÉS a
    variációs elv teljesül. A parancs tehát gépi ellenőrzésre is alkalmas.
    """
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "H2" in output
    assert "L2  VQE" in output
    assert "-1.137" in output
    assert "Kémiai pontosságon belül (|Δ| < 1.6 mHa): IGEN" in output
    assert "Variációs elv (E_VQE ≥ E_egzakt): teljesül" in output


def test_json_output_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    """A ``--json`` kapcsoló feldolgozható JSON-t ad (a Fázis 4 előkészítése)."""
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["energy_ha"] == pytest.approx(-1.137306, abs=1e-5)
    assert payload["within_chemical_accuracy"] is True
    assert payload["n_qubits"] == 2
    assert payload["n_parameters"] == 3
    assert payload["mapper"] == "parity"
    assert payload["two_qubit_reduction"] is True

    # A reprodukálhatósági kontextus is benne van — enélkül az eredmény
    # később nem lenne értelmezhető.
    assert len(payload["config_hash"]) == 64
    assert len(payload["environment_fingerprint"]) == 64
    assert payload["versions"]["qiskit"]
    assert payload["versions"]["pyscf"]
    assert set(payload["seeds"]) >= {"master", "simulator", "transpiler"}


@pytest.mark.parametrize("mapper", ["jordan_wigner", "parity", "bravyi_kitaev"])
def test_every_mapper_runs_from_the_cli(mapper: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Mindhárom leképezés elérhető a parancssorból, és kémiai pontosságot ad."""
    assert main(["--mapper", mapper, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mapper"] == mapper


@pytest.mark.parametrize("backend", ["qiskit_aer_shot", "qiskit_aer_noisy"])
def test_aer_backends_run_from_the_cli(backend: str, capsys: pytest.CaptureFixture[str]) -> None:
    """A zajos Aer backendek futtathatók a CLI-ből."""
    code = main(["--backend", backend, "--optimizer", "COBYLA", "--maxiter", "5", "--json"])
    # 0 vagy 1 (a zaj miatt lehet kívül a kémiai pontosságon, de nem lehet 2-es hiba)
    assert code in (0, 1)
    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == backend
    assert payload["platform"] == "qiskit"
    assert "energy_ha" in payload


def test_jordan_wigner_uses_more_qubits(capsys: pytest.CaptureFixture[str]) -> None:
    """A CLI-n keresztül is látszik a kétqubites redukció haszna."""
    assert main(["--mapper", "jordan_wigner", "--json"]) == 0
    jw = json.loads(capsys.readouterr().out)
    assert main(["--mapper", "parity", "--json"]) == 0
    parity = json.loads(capsys.readouterr().out)
    assert parity["n_qubits"] == jw["n_qubits"] - 2


def test_custom_bond_length_changes_the_energy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Más geometria más energiát ad — a bemenet ténylegesen hat."""
    main(["--bond-length", "0.735", "--json", "--no-fci"])
    equilibrium = json.loads(capsys.readouterr().out)["energy_ha"]
    main(["--bond-length", "2.0", "--json", "--no-fci"])
    stretched = json.loads(capsys.readouterr().out)["energy_ha"]
    assert stretched > equilibrium, (
        f"a megnyújtott kötés ({stretched:.6f} Ha) nem magasabb energiájú az "
        f"egyensúlyinál ({equilibrium:.6f} Ha)"
    )


# --- Hibakezelés -------------------------------------------------------------


def test_invalid_basis_returns_error_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ismeretlen bázis: 2-es kilépési kód és beszédes üzenet a stderr-en.

    A robusztusság elvárása, hogy a hiba **azonosítható** legyen: ne egy mély
    könyvtárbeli ``IndexError`` bukjon ki, hanem a mi hibaüzenetünk.
    """
    assert main(["--basis", "nincs-ilyen-bazis"]) == 2
    captured = capsys.readouterr()
    assert "HIBA" in captured.err
    assert "nincs-ilyen-bazis" in captured.err


def test_invalid_optimizer_returns_error_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--optimizer", "NINCS_ILYEN"]) == 2
    assert "nem támogatott optimalizáló" in capsys.readouterr().err
