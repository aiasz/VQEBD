"""A VQE-futtatás strukturált eredménye.

Az alapterv egyetlen ``float``-ot kér a ``run_vqe()`` függvénytől. A
:attr:`VQEResult.energy` **pontosan ez a float**, tehát a követelmény teljesül —
de a futás kontextusát is megőrizzük.

Miért?
------
A Fázis 4 adatsémája minden eredményrekordhoz eltárolja a teljes futási
kontextust: a referenciaszinteket, az iterációszámot, a seedeket és a
csomagverziókat. Ha a Fázis 1 csak ``float``-ot adna vissza, a Fázis 4-ben a
teljes hívási láncot át kellene írni — ez pedig sértené az alapterv „nem lépünk
tovább félig működő alapokon" elvét.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from vqebd.chemistry.reference import CHEMICAL_ACCURACY_HA, ReferenceEnergies
from vqebd.config import VQEConfig
from vqebd.seeds import SeedSet

__all__ = ["VQEResult"]


@dataclass(frozen=True, slots=True)
class VQEResult:
    """Egyetlen VQE-futtatás teljes eredménye.

    Attributes:
        energy: A **teljes** alapállapoti energia (Ha), a magtaszítással együtt.
            Ez az alapterv által kért érték.
        electronic_energy: Az elektronos rész (Ha), magtaszítás nélkül.
        nuclear_repulsion_energy: A magtaszítási energia (Ha).
        optimal_parameters: Az optimális variációs paraméterek.
        reference: A klasszikus referenciaszintek (L0, L1, Hartree–Fock).
        n_qubits: Az áramkör qubit-száma.
        n_parameters: A variációs paraméterek száma.
        n_hamiltonian_terms: A Hamilton-operátor Pauli-tagjainak száma.
        mapper: A használt leképezés azonosítója.
        two_qubit_reduction: Alkalmaztunk-e kétqubites redukciót.
        platform: A kiértékelést végző szoftverplatform (``qiskit``/``cirq``/``qsim``).
        precision: Az állapotvektor számábrázolása (``complex128``/``complex64``).
        backend_tolerance_ha: Az adott platformtól elfogadható eltérés (Ha).
        n_iterations: Az optimalizáló iterációinak száma.
        n_function_evaluations: A célfüggvény-kiértékelések száma.
        converged: Konvergált-e az optimalizáló.
        optimizer_message: A SciPy állapotüzenete.
        history: Iterációnkénti energia (elektronos rész, Ha).
        wall_time_s: A teljes futásidő másodpercben.
        config: A futtatás konfigurációja.
        seeds: A használt seedek.
        versions: A futásidejű csomagverziók.
        environment_fingerprint: A környezet SHA-256 ujjlenyomata.
    """

    energy: float
    electronic_energy: float
    nuclear_repulsion_energy: float
    optimal_parameters: tuple[float, ...]
    reference: ReferenceEnergies
    n_qubits: int
    n_parameters: int
    n_hamiltonian_terms: int
    mapper: str
    two_qubit_reduction: bool
    platform: str
    precision: str
    backend_tolerance_ha: float
    n_iterations: int
    n_function_evaluations: int
    converged: bool
    optimizer_message: str
    history: tuple[float, ...]
    wall_time_s: float
    config: VQEConfig
    seeds: SeedSet
    versions: Mapping[str, str]
    environment_fingerprint: str

    # ---------------------------------------------------------------- hibák

    @property
    def error_vs_reference(self) -> float:
        """``E_VQE − E_ref`` (Ha), a legmegbízhatóbb elérhető referenciához mérve.

        A variációs elv miatt ez **nem lehet szignifikánsan negatív**: ha az, az
        implementációs vagy numerikus hibát jelez.
        """
        return self.energy - self.reference.best

    @property
    def error_vs_exact_diagonalization(self) -> float | None:
        """``E_VQE − E_L1`` (Ha) — tisztán az **ansatz** hibája.

        Az L1 ugyanazt a qubit-Hamilton-operátort diagonalizálja egzaktul, amelyen
        a VQE is dolgozik. A kettő különbsége ezért kizárólag az ansatz
        kifejezőképességéből ered — a leképezési hiba kiesik.
        """
        if self.reference.exact_diagonalization is None:
            return None
        return self.energy - self.reference.exact_diagonalization

    @property
    def correlation_energy_recovered(self) -> float | None:
        """A visszanyert korrelációs energia aránya (0–1).

        ``(E_HF − E_VQE) / (E_HF − E_FCI)``. Az 1.0 azt jelenti, hogy a VQE a
        teljes korrelációs energiát visszanyerte. Ez fizikailag beszédesebb
        mutató a puszta abszolút hibánál, mert molekulák között is összevethető.
        """
        correlation = self.reference.correlation_energy
        if correlation is None or abs(correlation) < 1e-12:
            return None
        return (self.reference.hartree_fock - self.energy) / (-correlation)

    @property
    def within_backend_tolerance(self) -> bool:
        """A platform saját, számábrázolásból levezetett toleranciáján belül van-e.

        Ez szigorúbb (vagy lazább) a kémiai pontosságnál, platformtól függően:
        a ``complex64`` qsimtől 1e-5 Ha-t fogadunk el, a ``complex128``
        platformoktól 1e-9 Ha-t. Lásd: :mod:`vqebd.platforms`.
        """
        return abs(self.error_vs_reference) < self.backend_tolerance_ha

    @property
    def within_chemical_accuracy(self) -> bool:
        """Kémiai pontosságon belül van-e az eredmény (\\|Δ\\| < 1.6 mHa)."""
        return abs(self.error_vs_reference) < CHEMICAL_ACCURACY_HA

    @property
    def satisfies_variational_principle(self) -> bool:
        """Teljesül-e a variációs elv: ``E_VQE ≥ E_exact``.

        Numerikus tűréssel: a lebegőpontos aritmetika miatt a gépi pontosság
        nagyságrendjében az alácsúszás megengedett.
        """
        return self.error_vs_reference > -1e-9

    # ---------------------------------------------------------------- kimenet

    def to_dict(self) -> dict[str, Any]:
        """Lapos szótár-alak — naplózáshoz és a Fázis 4 adatsémájához."""
        return {
            "energy_ha": self.energy,
            "electronic_energy_ha": self.electronic_energy,
            "nuclear_repulsion_energy_ha": self.nuclear_repulsion_energy,
            "optimal_parameters": list(self.optimal_parameters),
            "reference": self.reference.to_dict(),
            "error_vs_reference_ha": self.error_vs_reference,
            "error_vs_exact_diagonalization_ha": self.error_vs_exact_diagonalization,
            "correlation_energy_recovered": self.correlation_energy_recovered,
            "within_chemical_accuracy": self.within_chemical_accuracy,
            "n_qubits": self.n_qubits,
            "n_parameters": self.n_parameters,
            "n_hamiltonian_terms": self.n_hamiltonian_terms,
            "mapper": self.mapper,
            "two_qubit_reduction": self.two_qubit_reduction,
            "backend": self.config.backend,
            "platform": self.platform,
            "precision": self.precision,
            "backend_tolerance_ha": self.backend_tolerance_ha,
            "within_backend_tolerance": self.within_backend_tolerance,
            "n_iterations": self.n_iterations,
            "n_function_evaluations": self.n_function_evaluations,
            "converged": self.converged,
            "optimizer_message": self.optimizer_message,
            "wall_time_s": self.wall_time_s,
            "config": self.config.to_dict(),
            "config_hash": self.config.fingerprint(),
            "seeds": self.seeds.to_dict(),
            "versions": dict(self.versions),
            "environment_fingerprint": self.environment_fingerprint,
        }

    def report(self) -> str:
        """Ember által olvasható összefoglaló — a parancssori kimenethez."""
        ref = self.reference
        lines = [
            f"Molekula ............ {self.config.molecule.name} [{self.config.molecule.basis}]",
            f"Geometria ........... {self.config.molecule.atom}",
            f"Leképezés ........... {self.mapper}"
            + (" (2-qubit redukcióval)" if self.two_qubit_reduction else ""),
            f"Áramkör ............. {self.n_qubits} qubit, {self.n_parameters} paraméter, "
            f"{self.n_hamiltonian_terms} Pauli-tag",
            f"Backend ............. {self.config.backend} [{self.platform}, {self.precision}]",
            f"Optimalizáló ........ {self.config.optimizer.method} "
            f"({self.n_iterations} iteráció, {self.n_function_evaluations} kiértékelés)",
            "",
            "Energiák (Hartree):",
            f"  Hartree–Fock ...... {ref.hartree_fock:+.10f}",
        ]
        if ref.full_ci is not None:
            lines.append(f"  L0  Full CI ....... {ref.full_ci:+.10f}")
        if ref.exact_diagonalization is not None:
            lines.append(f"  L1  egzakt diag. .. {ref.exact_diagonalization:+.10f}")

        if self.config.backend == "qiskit_aer_shot":
            lines.append(f"  L3a VQE (shot) .... {self.energy:+.10f}")
        elif self.config.backend == "qiskit_aer_noisy":
            lines.append(f"  L3b VQE (noisy) ... {self.energy:+.10f}")
        else:
            lines.append(f"  L2  VQE ........... {self.energy:+.10f}")

        lines.append("")
        lines.append("Hibák:")
        if ref.mapping_error is not None:
            lines.append(f"  leképezés (L1−L0) . {ref.mapping_error:+.3e} Ha")
        if self.error_vs_exact_diagonalization is not None:
            if self.config.backend in ("qiskit_aer_shot", "qiskit_aer_noisy"):
                lines.append(f"  ansatz+zaj (L3−L1)  {self.error_vs_exact_diagonalization:+.3e} Ha")
            else:
                lines.append(f"  ansatz (L2−L1) .... {self.error_vs_exact_diagonalization:+.3e} Ha")
        lines.append(f"  referenciához ..... {self.error_vs_reference:+.3e} Ha")
        recovered = self.correlation_energy_recovered
        if recovered is not None:
            lines.append(f"  korreláció vissza . {recovered * 100:.4f} %")
        lines.append("")
        accuracy = "IGEN" if self.within_chemical_accuracy else "NEM"
        variational = "teljesül" if self.satisfies_variational_principle else "SÉRÜL"
        lines.append(f"Kémiai pontosságon belül (|Δ| < 1.6 mHa): {accuracy}")
        lines.append(f"Variációs elv (E_VQE ≥ E_egzakt): {variational}")
        lines.append(
            f"Konvergált: {'igen' if self.converged else 'NEM'} ({self.optimizer_message})"
        )
        lines.append(f"Futásidő: {self.wall_time_s:.3f} s")
        lines.append(f"Konfiguráció-ujjlenyomat: {self.config.short_fingerprint()}")
        return "\n".join(lines)
