"""A dashboard adatrétege: három forrás egy normalizált táblába (Fázis 7, ADR-0009).

Tiszta függvények (pandas), a Streamlittől függetlenek, ezért egység-szinten tesztelhetők.

Források (``docs/plan/phase_07.md`` 4.2):

- **SQLite** (``.sqlite`` / ``.db``): teljes rekord, és a ``run_failures`` tábla;
- **batch-export** (``.json``, szótár ``"rows"`` kulccsal): a ``scripts/run_batch.py`` exportja;
- **teljes rekordlista** (``.json``, lista): a Fázis 4 ``results_v1.json`` alakja.

Az adatbázist **csak olvasásra** nyitjuk. Hibás vagy hiányzó adatra :class:`DataLoadError`
(érthető, felhasználónak szánt üzenettel) a nyers kivétel helyett.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from vqebd.storage import Database

__all__ = [
    "CHEMICAL_ACCURACY_MHA",
    "COMPARISON_COLUMNS",
    "DEFAULT_BASIS",
    "DEFAULT_MAPPER",
    "FAILURE_COLUMNS",
    "METHOD_ORDER",
    "DataLoadError",
    "default_bond_length",
    "derive_columns",
    "derive_n_qubits",
    "load_failures",
    "load_results",
    "method_comparison_table",
    "method_label",
]

CHEMICAL_ACCURACY_MHA: Final[float] = 1.5936
"""A kémiai pontosság (1 kcal/mol) mHa-ban. A teszt egyezteti a ``vqebd.chemistry`` konstansával;
itt külön áll, hogy a dashboard ne húzza be a kvantumcsomagok importját."""

DEFAULT_MAPPER: Final[str] = "parity"
DEFAULT_BASIS: Final[str] = "sto3g"

_BASIS_ORBITALS: Final[dict[tuple[str, str], int]] = {
    ("H2", "sto3g"): 2,
    ("LiH", "sto3g"): 6,
    ("BeH2", "sto3g"): 7,
}
"""Térbeli pályák száma teljes térben (STO-3G). Ismeretlen pár: a qubitszám ``NaN``."""

METHOD_ORDER: Final[tuple[str, ...]] = (
    "egzakt",
    "lövészaj",
    "zajos (nyers)",
    "ZNE lineáris",
    "ZNE Richardson",
    "ZNE exponenciális",
    "QPU (nyers)",
    "QPU (TREX)",
    "QPU (resilience 2)",
)
"""A módszerek megjelenítési sorrendje (a nem szereplők utánuk, ábécében)."""

_EXACT_BACKENDS: Final[frozenset[str]] = frozenset({"qiskit_statevector", "cirq_simulator", "qsim"})
_EXTRAPOLATORS: Final[dict[str, str]] = {
    "linear": "lineáris",
    "richardson": "Richardson",
    "exponential": "exponenciális",
}

_NUMERIC: Final[tuple[str, ...]] = (
    "bond_length",
    "active_electrons",
    "active_orbitals",
    "energy_ha",
    "full_ci_ha",
    "hartree_fock_ha",
    "casci_ha",
    "repeat_index",
    "reestimate_sem_ha",
    "wall_time_s",
    "n_function_evaluations",
)
_TEXT: Final[tuple[str, ...]] = (
    "run_id",
    "batch_id",
    "molecule_name",
    "backend",
    "platform",
    "mitigation_strategy",
    "mitigation_extrapolator",
    "optimizer_method",
    "mapper",
    "basis",
    "config_hash",
)
_DERIVED: Final[tuple[str, ...]] = (
    "error_mha",
    "casci_error_mha",
    "chemically_accurate",
    "method",
    "active_space",
    "n_qubits",
    "size_assumed",
)
FAILURE_COLUMNS: Final[tuple[str, ...]] = (
    "run_id",
    "batch_id",
    "attempt",
    "timestamp",
    "error_type",
    "error_class",
    "error_message",
    "wall_time_s",
    "will_retry",
    "forgiven",
)
_SQLITE_SUFFIXES: Final[frozenset[str]] = frozenset({".sqlite", ".sqlite3", ".db"})


class DataLoadError(Exception):
    """Az adat nem tölthető be; az üzenet a felhasználónak szól (nem nyers kivétel)."""


# --- levezetett mennyiségek ----------------------------------------------------------


def method_label(backend: str | None, strategy: str | None, extrapolator: str | None) -> str:
    """A futás módszercímkéje a backendből és a hibaenyhítésből.

    A címkék a ``METHOD_ORDER`` elemei; ismeretlen backend a nevét kapja vissza.
    """
    backend = backend or ""
    strategy = (strategy or "none").strip() or "none"
    if backend in _EXACT_BACKENDS:
        return "egzakt"
    if backend == "qiskit_aer_shot":
        return "lövészaj"
    if backend == "qiskit_aer_noisy":
        if strategy == "none":
            return "zajos (nyers)"
        if strategy.startswith("zne"):
            name = _EXTRAPOLATORS.get(extrapolator or "", extrapolator or "?")
            return f"ZNE {name}"
        return f"zajos ({strategy})"
    if backend == "ibm_qpu":
        if strategy in ("none", "ibm_resilience_0"):
            return "QPU (nyers)"
        if strategy == "ibm_resilience_1":
            return "QPU (TREX)"
        if strategy == "ibm_resilience_2":
            return "QPU (resilience 2)"
        return f"QPU ({strategy})"
    return backend or "ismeretlen"


def derive_n_qubits(
    molecule_name: str | None,
    basis: str | None,
    active_orbitals: float | None,
    mapper: str | None,
    two_qubit_reduction: bool | None,
) -> float:
    """A qubitszám levezetése: ``2 · pályák`` (parity + kétqubites redukciónál ``− 2``).

    A pályák száma az aktív térből jön, teljes térben a bázisból (STO-3G). Ismeretlen
    molekula–bázis párnál ``NaN``: nem találgat (ADR-0009, 3. döntés). A képletet a mért
    építés igazolja (H₂ 2, (2e,3o) 4, LiH (2e,5o) 8, BeH₂ (4e,6o) 10 qubit).
    """
    if active_orbitals is not None and not np.isnan(active_orbitals):
        orbitals = int(active_orbitals)
    else:
        found = _BASIS_ORBITALS.get((molecule_name or "", (basis or DEFAULT_BASIS).lower()))
        if found is None:
            return float("nan")
        orbitals = found
    qubits = 2 * orbitals
    if (mapper or DEFAULT_MAPPER) == "parity" and two_qubit_reduction is not False:
        qubits -= 2
    return float(qubits)


def _text(value: Any) -> str | None:
    """Hiányzó érték (``None`` / ``NaN``) → ``None``, egyébként szöveg."""
    return None if value is None or pd.isna(value) else str(value)


def derive_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """A levezetett oszlopok hozzáadása (másolatot ad vissza).

    ``error_mha`` az energia és a Full CI különbsége mHa-ban; ``casci_error_mha`` az aktív
    tér saját (CASCI) referenciájához mért hiba, ``NaN`` teljes térben. A ``size_assumed``
    igaz, ha a qubitszámhoz a ``mapper`` vagy a ``basis`` hiányzott, és az alapértelmezés
    érvényesült.
    """
    out = frame.copy()
    out["error_mha"] = (out["energy_ha"] - out["full_ci_ha"]) * 1e3
    out["casci_error_mha"] = (out["energy_ha"] - out["casci_ha"]) * 1e3
    out["chemically_accurate"] = out["error_mha"].abs() < CHEMICAL_ACCURACY_MHA
    out["method"] = [
        method_label(_text(b), _text(s), _text(e))
        for b, s, e in zip(
            out["backend"], out["mitigation_strategy"], out["mitigation_extrapolator"], strict=True
        )
    ]
    out["active_space"] = [
        "teljes" if np.isnan(o) else f"({int(e) if not np.isnan(e) else '?'}e,{int(o)}o)"
        for e, o in zip(out["active_electrons"], out["active_orbitals"], strict=True)
    ]
    out["size_assumed"] = out["mapper"].isna() | out["basis"].isna()
    out["n_qubits"] = [
        derive_n_qubits(_text(m), _text(b), float(o), _text(mp), None if pd.isna(r) else bool(r))
        for m, b, o, mp, r in zip(
            out["molecule_name"],
            out["basis"],
            out["active_orbitals"],
            out["mapper"],
            out["two_qubit_reduction"],
            strict=True,
        )
    ]
    return out


# --- betöltés ------------------------------------------------------------------------


def _frame_from_rows(rows: list[Mapping[str, Any]], source: str) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows))
    for column in _TEXT:
        if column not in frame:
            frame[column] = None
    for column in _NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors="coerce") if column in frame else np.nan
    if "two_qubit_reduction" not in frame:
        frame["two_qubit_reduction"] = None
    frame["source"] = source
    frame = derive_columns(frame)
    leading = [*_TEXT, *_NUMERIC, "two_qubit_reduction", "source", *_DERIVED]
    rest = [c for c in frame.columns if c not in leading]
    return frame[[*leading, *rest]]


def _load_sqlite_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with Database(path, read_only=True) as db:
            return db.query_results()
    except sqlite3.DatabaseError as exc:
        raise DataLoadError(f"Az adatbázis nem olvasható ({path.name}): {exc}") from exc


def _load_json_rows(path: Path) -> list[Mapping[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DataLoadError(f"A JSON-fájl hibás ({path.name}): {exc}") from exc
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        batch_id = payload.get("batch_id")
        rows = [{"batch_id": batch_id, **row} for row in payload["rows"]]
    else:
        raise DataLoadError(
            f"Ismeretlen JSON-szerkezet ({path.name}): rekordlista vagy "
            "'rows' kulcsú batch-export várt."
        )
    if not all(isinstance(row, dict) for row in rows):
        raise DataLoadError(f"A JSON-fájl sorai nem szótárak ({path.name}).")
    return rows


def load_results(path: Path | str) -> pd.DataFrame:
    """Az eredmények betöltése egy forrásból, normalizált táblaként (levezetett oszlopokkal).

    Üres forrás (nulla rekord) **nem hiba**: üres, de teljes oszlopkészletű tábla.

    Raises:
        DataLoadError: Hiányzó fájl, ismeretlen típus, hibás JSON vagy nem olvasható adatbázis.
    """
    source = Path(path)
    if not source.is_file():
        raise DataLoadError(f"Az adatfájl nem található: {source}")
    suffix = source.suffix.lower()
    if suffix in _SQLITE_SUFFIXES:
        rows: list[Mapping[str, Any]] = list(_load_sqlite_rows(source))
    elif suffix == ".json":
        rows = _load_json_rows(source)
    else:
        raise DataLoadError(
            f"Ismeretlen adatforrás-típus: {source.suffix!r} (várt: .sqlite, .db vagy .json)."
        )
    return _frame_from_rows(rows, source.name)


def load_failures(path: Path | str) -> pd.DataFrame:
    """A ``run_failures`` tábla (csak SQLite-forrásból); más forrásnál üres tábla.

    Raises:
        DataLoadError: Hiányzó fájl vagy nem olvasható adatbázis.
    """
    source = Path(path)
    if not source.is_file():
        raise DataLoadError(f"Az adatfájl nem található: {source}")
    if source.suffix.lower() not in _SQLITE_SUFFIXES:
        return pd.DataFrame(columns=list(FAILURE_COLUMNS))
    try:
        with Database(source, read_only=True) as db:
            rows = db.failures()
    except sqlite3.DatabaseError as exc:
        # Egy v1/v2 adatbázisban a tábla még nem létezik: ez nem hiba, nincs hibatörténet.
        if "no such table" in str(exc):
            return pd.DataFrame(columns=list(FAILURE_COLUMNS))
        raise DataLoadError(f"Az adatbázis nem olvasható ({source.name}): {exc}") from exc
    return (
        pd.DataFrame(rows, columns=list(FAILURE_COLUMNS))
        if rows
        else pd.DataFrame(columns=list(FAILURE_COLUMNS))
    )


# --- módszer-összehasonlítás (7.3) ----------------------------------------------------------

COMPARISON_COLUMNS: Final[tuple[str, ...]] = (
    "method",
    "n",
    "mean_error_mha",
    "sd_mha",
    "sem_mha",
    "chemically_accurate",
)


def _select_point(
    frame: pd.DataFrame, molecule: str, bond_length: float, active_space: str | None
) -> pd.DataFrame:
    """Egy (molekula, kötéshossz[, aktív tér]) pont futásai, hibaértékkel."""
    mask = (frame["molecule_name"] == molecule) & np.isclose(
        frame["bond_length"].to_numpy(dtype=float), bond_length, rtol=0.0, atol=1e-9
    )
    if active_space is not None:
        mask &= frame["active_space"] == active_space
    return frame[mask].dropna(subset=["error_mha"])


def method_comparison_table(
    frame: pd.DataFrame,
    molecule: str,
    bond_length: float,
    *,
    active_space: str | None = None,
) -> pd.DataFrame:
    """Módszerenként összesítve az energiahiba (a Full CI-hez, mHa) egy kötéshosszra.

    Oszlopok: ``COMPARISON_COLUMNS``. ``sd_mha`` a mintaszórás (``ddof = 1``), egyetlen futásnál
    ``NaN``; ``sem_mha = sd / sqrt(n)``. ``chemically_accurate`` igaz, ha az **átlagos** hiba
    abszolút értéke a kémiai pontosságon belül van (a futásonkénti pontosság a ``results``
    táblában van). A sorok a ``METHOD_ORDER`` szerint rendezettek, a többi utánuk, ábécében.
    Adat nélkül üres tábla, teljes oszlopkészlettel.
    """
    point = _select_point(frame, molecule, bond_length, active_space)
    if point.empty:
        return pd.DataFrame(columns=list(COMPARISON_COLUMNS))
    rows: list[dict[str, Any]] = []
    for method, group in point.groupby("method", sort=False):
        errors = group["error_mha"].to_numpy(dtype=float)
        n = int(errors.size)
        mean = float(errors.mean())
        sd = float(errors.std(ddof=1)) if n > 1 else float("nan")
        rows.append(
            {
                "method": str(method),
                "n": n,
                "mean_error_mha": mean,
                "sd_mha": sd,
                "sem_mha": sd / float(np.sqrt(n)) if n > 1 else float("nan"),
                "chemically_accurate": abs(mean) < CHEMICAL_ACCURACY_MHA,
            }
        )
    order = {m: i for i, m in enumerate(METHOD_ORDER)}
    rows.sort(key=lambda r: (order.get(r["method"], len(order)), r["method"]))
    return pd.DataFrame(rows, columns=list(COMPARISON_COLUMNS))


def default_bond_length(
    frame: pd.DataFrame, molecule: str, *, active_space: str | None = None
) -> float | None:
    """A legtöbb különböző módszert tartalmazó kötéshossz (döntetlennél a legkisebb).

    Ez a legtanulságosabb alapértelmezés az összehasonlításhoz. ``None``, ha nincs adat.
    """
    subset = frame[frame["molecule_name"] == molecule].dropna(subset=["bond_length", "error_mha"])
    if active_space is not None:
        subset = subset[subset["active_space"] == active_space]
    if subset.empty:
        return None
    counts = {
        float(length): int(group["method"].nunique())
        for length, group in subset.groupby("bond_length")
    }
    return min(counts, key=lambda length: (-counts[length], length))
