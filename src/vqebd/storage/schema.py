"""SQLite adatbázis-séma definíciók és sémamigrációk (ADR-0004).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc
"""

from __future__ import annotations

from typing import Final

__all__ = ["CURRENT_SCHEMA_VERSION", "SCHEMA_V1_DDL"]

CURRENT_SCHEMA_VERSION: Final[int] = 1

SCHEMA_V1_DDL: Final[str] = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    
    -- Molekula és fizikai feladat
    molecule_name TEXT NOT NULL,
    geometry TEXT NOT NULL,
    bond_length REAL NOT NULL,
    basis TEXT NOT NULL,
    charge INTEGER NOT NULL DEFAULT 0,
    spin INTEGER NOT NULL DEFAULT 0,
    
    -- Leképezés és ansatz
    mapper TEXT NOT NULL,
    two_qubit_reduction INTEGER NOT NULL,
    ansatz_kind TEXT NOT NULL,
    initial_point TEXT NOT NULL,
    
    -- Optimalizáló és konvergencia
    optimizer_method TEXT NOT NULL,
    optimizer_maxiter INTEGER NOT NULL,
    n_iterations INTEGER NOT NULL,
    n_function_evaluations INTEGER NOT NULL,
    converged INTEGER NOT NULL,
    optimizer_message TEXT NOT NULL,
    
    -- Platform és backend
    backend TEXT NOT NULL,
    platform TEXT NOT NULL,
    precision TEXT NOT NULL,
    shots INTEGER,
    optimization_level INTEGER,
    hardware_backend_name TEXT,
    hardware_job_id TEXT,
    
    -- Hibaenyhítés (ZNE)
    mitigation_strategy TEXT NOT NULL DEFAULT 'none',
    mitigation_extrapolator TEXT,
    scale_factors_json TEXT,
    scaled_energies_json TEXT,
    
    -- Energiák és hibák (Hartree)
    energy_ha REAL NOT NULL,
    electronic_energy_ha REAL NOT NULL,
    nuclear_repulsion_ha REAL NOT NULL,
    raw_energy_ha REAL,
    hartree_fock_ha REAL NOT NULL,
    full_ci_ha REAL,
    exact_diag_ha REAL,
    error_vs_fci_ha REAL,
    error_vs_exact_diag_ha REAL,
    correlation_recovered REAL,
    within_chemical_accuracy INTEGER NOT NULL,
    satisfies_variational_principle INTEGER NOT NULL,
    
    -- Reprodukálhatóság és Provenance (FAIR)
    master_seed INTEGER NOT NULL,
    seeds_json TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    environment_fingerprint TEXT NOT NULL,
    versions_json TEXT NOT NULL,
    wall_time_s REAL NOT NULL,
    optimal_parameters_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_results_molecule ON results(molecule_name, bond_length);
CREATE INDEX IF NOT EXISTS idx_results_backend ON results(backend, platform);
CREATE INDEX IF NOT EXISTS idx_results_mitigation ON results(mitigation_strategy);
CREATE INDEX IF NOT EXISTS idx_results_config_hash ON results(config_hash);
CREATE INDEX IF NOT EXISTS idx_results_timestamp ON results(timestamp);
"""
