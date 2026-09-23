"""SQLite adatbáziskezelő — kanonikus perzisztens tároló (ADR-0004).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from vqebd.storage.schema import CURRENT_SCHEMA_VERSION, SCHEMA_V1_DDL
from vqebd.vqe.result import VQEResult

__all__ = ["DEFAULT_DB_PATH", "Database"]

DEFAULT_DB_PATH = Path("data/db/vqebd.sqlite")


class Database:
    """Kanonikus SQLite adatbáziskezelő WAL móddal és sémaverziózással."""

    def __init__(
        self,
        path: Path | str = DEFAULT_DB_PATH,
        *,
        read_only: bool = False,
    ) -> None:
        self.path = Path(path) if isinstance(path, str) and path != ":memory:" else path
        self.read_only = read_only

        if isinstance(self.path, Path) and not self.read_only and self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)

        conn_str = f"file:{self.path}?mode=ro" if (read_only and self.path != ":memory:") else str(self.path)
        uri = bool(read_only and self.path != ":memory:")

        self._conn = sqlite3.connect(conn_str, uri=uri)
        self._conn.row_factory = sqlite3.Row

        if not read_only and self.path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")

        if not read_only:
            self._init_schema()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Adatbázis-kapcsolat lezárása."""
        self._conn.close()

    def _init_schema(self) -> None:
        """Séma inicializálása és verzióellenőrzés."""
        with self._conn:
            self._conn.executescript(SCHEMA_V1_DDL)
            cur = self._conn.cursor()
            cur.execute("SELECT value FROM meta WHERE key = 'schema_version'")
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
                    (str(CURRENT_SCHEMA_VERSION),),
                )
                cur.execute(
                    "INSERT INTO meta (key, value) VALUES ('created_at', ?)",
                    (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),),
                )
            else:
                db_ver = int(row["value"])
                if db_ver != CURRENT_SCHEMA_VERSION:
                    raise ValueError(
                        f"adatbázis sémaverzió eltérés: várt={CURRENT_SCHEMA_VERSION}, "
                        f"talált={db_ver}. Migráció szükséges."
                    )

    def insert_result(self, result: VQEResult, *, run_id: str | None = None) -> str:
        """Egy VQEResult objektum mentése az adatbázisba."""
        rid = run_id or str(uuid.uuid4())
        ref = result.reference
        cfg = result.config
        mit = result.mitigation

        record: dict[str, Any] = {
            "run_id": rid,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "schema_version": CURRENT_SCHEMA_VERSION,
            "molecule_name": cfg.molecule.name,
            "geometry": cfg.molecule.atom,
            "bond_length": cfg.molecule.bond_length,
            "basis": cfg.molecule.basis,
            "charge": cfg.molecule.charge,
            "spin": cfg.molecule.spin,
            "mapper": result.mapper,
            "two_qubit_reduction": 1 if result.two_qubit_reduction else 0,
            "ansatz_kind": cfg.ansatz.kind,
            "initial_point": cfg.ansatz.initial_point,
            "optimizer_method": cfg.optimizer.method,
            "optimizer_maxiter": cfg.optimizer.maxiter,
            "n_iterations": result.n_iterations,
            "n_function_evaluations": result.n_function_evaluations,
            "converged": 1 if result.converged else 0,
            "optimizer_message": result.optimizer_message,
            "backend": cfg.backend,
            "platform": result.platform,
            "precision": result.precision,
            "shots": 8192 if "shot" in cfg.backend or "noisy" in cfg.backend or cfg.backend == "ibm_qpu" else None,
            "optimization_level": 3 if cfg.backend in ("qiskit_aer_noisy", "ibm_qpu") else (1 if cfg.backend == "qiskit_aer_shot" else None),
            "hardware_backend_name": "ibm_kingston" if cfg.backend == "ibm_qpu" else None,
            "hardware_job_id": None,
            "mitigation_strategy": mit.strategy_name if mit else "none",
            "mitigation_extrapolator": mit.extrapolator_name if mit else None,
            "scale_factors_json": json.dumps(list(mit.scale_factors)) if mit else None,
            "scaled_energies_json": json.dumps(list(mit.scaled_energies)) if mit else None,
            "energy_ha": result.energy,
            "electronic_energy_ha": result.electronic_energy,
            "nuclear_repulsion_ha": result.nuclear_repulsion_energy,
            "raw_energy_ha": (mit.raw_energy + result.nuclear_repulsion_energy) if mit else result.energy,
            "hartree_fock_ha": ref.hartree_fock,
            "full_ci_ha": ref.full_ci,
            "exact_diag_ha": ref.exact_diagonalization,
            "error_vs_fci_ha": (result.energy - ref.full_ci) if ref.full_ci is not None else None,
            "error_vs_exact_diag_ha": (result.energy - ref.exact_diagonalization) if ref.exact_diagonalization is not None else None,
            "correlation_recovered": result.correlation_energy_recovered,
            "within_chemical_accuracy": 1 if result.within_chemical_accuracy else 0,
            "satisfies_variational_principle": 1 if result.satisfies_variational_principle else 0,
            "master_seed": result.seeds.master,
            "seeds_json": json.dumps(result.seeds.to_dict()),
            "config_hash": cfg.fingerprint(),
            "environment_fingerprint": result.environment_fingerprint,
            "versions_json": json.dumps(dict(result.versions)),
            "wall_time_s": result.wall_time_s,
            "optimal_parameters_json": json.dumps(list(result.optimal_parameters)),
            "metadata_json": json.dumps(mit.metadata if mit else {}),
        }
        return self.insert_record(record)

    def insert_record(self, record: dict[str, Any]) -> str:
        """Nyers szótárrekord közvetlen beszúrása."""
        keys = list(record.keys())
        placeholders = [f":{k}" for k in keys]
        sql = f"INSERT INTO results ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
        with self._conn:
            self._conn.execute(sql, record)
        return str(record["run_id"])

    def get_result(self, run_id: str) -> dict[str, Any] | None:
        """Egy rekord lekérdezése run_id alapján."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM results WHERE run_id = ?", (run_id,))
        row = cur.fetchone()
        return dict(row) if row is not None else None

    def query_results(
        self,
        *,
        molecule: str | None = None,
        backend: str | None = None,
        mitigation: str | None = None,
        within_chemical_accuracy: bool | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Eredmények lekérdezése szűrőkkel."""
        query = "SELECT * FROM results WHERE 1=1"
        params: list[Any] = []

        if molecule is not None:
            query += " AND molecule_name = ?"
            params.append(molecule)
        if backend is not None:
            query += " AND backend = ?"
            params.append(backend)
        if mitigation is not None:
            query += " AND mitigation_strategy = ?"
            params.append(mitigation)
        if within_chemical_accuracy is not None:
            query += " AND within_chemical_accuracy = ?"
            params.append(1 if within_chemical_accuracy else 0)

        query += " ORDER BY timestamp DESC, id DESC"
        if limit is not None:
            query += f" LIMIT {int(limit)}"

        cur = self._conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def count(self) -> int:
        """A tárolt eredmények száma."""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM results")
        return int(cur.fetchone()["total"])
