"""Adatbázis-rekordok csoportosítása és statisztikai összegzése (G3, G5).

Egy **csoport** = azonos konfiguráció, különböző seed. A csoportkulcs a rekord
olvasható mezőiből áll (molekula, kötéshossz, aktív tér, backend, optimalizáló,
hibaenyhítés), nem a ``config_hash``-ből, mert az a seedet is tartalmazza.

A végső energia zajos szinten az újramintavételezett átlag (``reestimate_mean_ha``),
ha van; különben a futás ``energy_ha`` értéke (``phase_05.md`` 5.5).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from vqebd.config import BackendKind
from vqebd.platforms import platform_of
from vqebd.stats import (
    AccuracyClass,
    ErrorBudget,
    SampleSummary,
    classify_chemical_accuracy,
    error_budget,
    rmse,
    summarize,
)

__all__ = ["GroupKey", "GroupStatistics", "aggregate_rows", "final_energy", "group_key"]

GroupKey = tuple[str, float, int | None, int | None, str, str, str, str | None]
"""(molekula, kötéshossz, aktív e, aktív o, backend, optimalizáló, mitigáció, extrapolátor)."""


def final_energy(row: Mapping[str, Any]) -> float:
    """Egy rekord végső teljes energiája (Ha): újramintavételezett átlag, ha van."""
    value = row.get("reestimate_mean_ha")
    return float(value if value is not None else row["energy_ha"])


def group_key(row: Mapping[str, Any]) -> GroupKey:
    """A rekord csoportkulcsa."""
    strategy = str(row["mitigation_strategy"])
    return (
        str(row["molecule_name"]),
        round(float(row["bond_length"]), 6),
        row.get("active_electrons"),
        row.get("active_orbitals"),
        str(row["backend"]),
        str(row["optimizer_method"]),
        strategy,
        row.get("mitigation_extrapolator") if strategy != "none" else None,
    )


@dataclass(frozen=True, slots=True)
class GroupStatistics:
    """Egy csoport (azonos konfiguráció, N seed) összegzése.

    Attributes:
        key: A csoportkulcs.
        n: A futások száma.
        energy: A végső energiák összegzése (Ha).
        error_vs_fci: A Full CI-hez mért hibák összegzése (Ha) — **fizikai** hiba.
        error_vs_exact: Az L1-hez mért hibák összegzése (Ha) — **módszer**hiba.
        rmse_vs_fci: Négyzetes középhiba a Full CI-hez (Ha).
        accuracy: Háromállapotú kémiai pontossági besorolás (az FCI-hez).
        selection_bias: Előzmény-minimum − újramintavételezett átlag, átlagolva
            (Ha) — a „minimumot jelentő” stratégia torzítása. ``None``, ha nem volt
            újramintavételezés, vagy hibaenyhített a csoport (ott az előzmény nyers,
            az átlag mitigált érték: nem összemérhetők).
        full_ci, casci, exact_diagonalization: A referenciák (Ha).
        budget: Hibaköltségvetés; zajos csoportnál az L2 pár alapján.
    """

    key: GroupKey
    n: int
    energy: SampleSummary
    error_vs_fci: SampleSummary | None
    error_vs_exact: SampleSummary | None
    rmse_vs_fci: float | None
    accuracy: AccuracyClass
    selection_bias: float | None
    full_ci: float | None
    casci: float | None
    exact_diagonalization: float | None
    budget: ErrorBudget | None = None

    @property
    def molecule(self) -> str:
        return self.key[0]

    @property
    def bond_length(self) -> float:
        return self.key[1]

    @property
    def active_space_label(self) -> str:
        e, o = self.key[2], self.key[3]
        return "teljes" if e is None else f"({e}e,{o}o)"

    @property
    def backend(self) -> str:
        return self.key[4]

    @property
    def mitigation_label(self) -> str:
        return self.key[6] if self.key[7] is None else f"{self.key[6]}/{self.key[7]}"

    def to_dict(self) -> dict[str, Any]:
        """Lapos szótár-alak az exporthoz (JSON)."""
        return {
            "molecule": self.molecule,
            "bond_length": self.bond_length,
            "active_space": self.active_space_label,
            "backend": self.backend,
            "optimizer": self.key[5],
            "mitigation": self.mitigation_label,
            "n": self.n,
            "energy": self.energy.to_dict(),
            "error_vs_fci": self.error_vs_fci.to_dict() if self.error_vs_fci else None,
            "error_vs_exact": self.error_vs_exact.to_dict() if self.error_vs_exact else None,
            "rmse_vs_fci": self.rmse_vs_fci,
            "accuracy": self.accuracy,
            "selection_bias": self.selection_bias,
            "full_ci": self.full_ci,
            "casci": self.casci,
            "exact_diagonalization": self.exact_diagonalization,
            "budget": self.budget.to_dict() if self.budget else None,
        }


def _is_exact(key: GroupKey) -> bool:
    """Egzakt (zajmentes) backend-e a csoporté."""
    return platform_of(cast(BackendKind, key[4])).exact


def _one_value(rows: list[Mapping[str, Any]], field_name: str) -> float | None:
    """Egy csoporton belül állandó referenciamező értéke, ellenőrzéssel.

    A referenciák (FCI, CASCI, L1) a seedtől függetlenek; ha egy csoporton belül
    1e-9 Ha-nél jobban eltérnek, a csoportosítás hibás — ezt nem nyeljük el.
    """
    values = sorted(float(row[field_name]) for row in rows if row.get(field_name) is not None)
    if not values:
        return None
    if values[-1] - values[0] > 1e-9:
        raise ValueError(f"a(z) {field_name} egy csoporton belül eltér: {values}")
    return values[0]


def aggregate_rows(rows: Iterable[Mapping[str, Any]]) -> list[GroupStatistics]:
    """Rekordok csoportosítása és összegzése, hibaköltségvetéssel.

    A zajos csoportok hibaköltségvetéséhez az azonos molekula/geometria/aktív tér
    ``qiskit_statevector`` csoportját keresi L2-referenciaként; ha nincs, a
    ``noise_bias`` ``None`` marad.
    """
    groups: dict[GroupKey, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(row)

    stats: dict[GroupKey, GroupStatistics] = {}
    for key, members in sorted(groups.items(), key=lambda kv: tuple(str(k) for k in kv[0])):
        energies = [final_energy(r) for r in members]
        full_ci = _one_value(members, "full_ci_ha")
        casci = _one_value(members, "casci_ha")
        exact = _one_value(members, "exact_diag_ha")
        err_fci = summarize([e - full_ci for e in energies]) if full_ci is not None else None
        err_exact = summarize([e - exact for e in energies]) if exact is not None else None
        accuracy: AccuracyClass = (
            classify_chemical_accuracy(err_fci, exact=_is_exact(key))
            if err_fci is not None
            else "undetermined"
        )
        biases = (
            [
                float(r["optimizer_history_min_ha"]) - float(r["reestimate_mean_ha"])
                for r in members
                if r.get("optimizer_history_min_ha") is not None
                and r.get("reestimate_mean_ha") is not None
            ]
            if key[6] == "none"
            else []
        )
        stats[key] = GroupStatistics(
            key=key,
            n=len(members),
            energy=summarize(energies),
            error_vs_fci=err_fci,
            error_vs_exact=err_exact,
            rmse_vs_fci=rmse([e - full_ci for e in energies]) if full_ci is not None else None,
            accuracy=accuracy,
            selection_bias=sum(biases) / len(biases) if biases else None,
            full_ci=full_ci,
            casci=casci,
            exact_diagonalization=exact,
        )

    # Hibaköltségvetés: L2 pár keresése a zajos csoportokhoz.
    result: list[GroupStatistics] = []
    for key, group in stats.items():
        if _is_exact(key):
            statevector: float | None = group.energy.mean
            noisy: SampleSummary | None = None
        else:
            l2_key: GroupKey = (*key[:4], "qiskit_statevector", "SLSQP", "none", None)
            l2 = stats.get(l2_key)
            statevector = l2.energy.mean if l2 is not None else None
            noisy = group.energy
        budget = error_budget(
            full_ci=group.full_ci,
            casci=group.casci,
            exact_diagonalization=group.exact_diagonalization,
            statevector=statevector,
            noisy=noisy,
        )
        result.append(
            GroupStatistics(
                key=group.key,
                n=group.n,
                energy=group.energy,
                error_vs_fci=group.error_vs_fci,
                error_vs_exact=group.error_vs_exact,
                rmse_vs_fci=group.rmse_vs_fci,
                accuracy=group.accuracy,
                selection_bias=group.selection_bias,
                full_ci=group.full_ci,
                casci=group.casci,
                exact_diagonalization=group.exact_diagonalization,
                budget=budget,
            )
        )
    return result
