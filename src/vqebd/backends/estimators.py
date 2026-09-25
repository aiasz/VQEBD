"""Energiakiértékelők — a VQE kvantumos oldala.

A VQE klasszikus optimalizáló-hurka egyetlen dolgot kér a kvantumos rétegtől:

.. code-block::

    θ  →  ⟨ψ(θ)| H |ψ(θ)⟩

Ez a modul ezt a leképezést csomagolja egy **hívható objektumba**. Az absztrakció
haszna, hogy a VQE-hurok kódja azonos marad, akárhol fut a kiértékelés:

=====================  =========================================  ============  =====
``BackendKind``        Kiértékelés                                Pontosság     Fázis
=====================  =========================================  ============  =====
``qiskit_statevector`` Qiskit, egzakt állapotvektor                complex128    1
``cirq_simulator``     Google Cirq, egzakt állapotvektor           complex128    1M
``qsim``               Google qsim, C++-ban optimalizált           complex64     1M
``qiskit_aer_shot``    Véges lövésszám, zaj nélkül                 —             1b
``qiskit_aer_noisy``   Zajos szimuláció valós kalibrációval        —             1b
``ibm_qpu``            Valódi IBM kvantumprocesszor                —             2
=====================  =========================================  ============  =====

A Fázis 1M három egzakt platformot valósít meg; a zajos és hardveres változatok
a megfelelő fázisban kerülnek ide, **változatlan interfésszel**.

A platformonkénti tolerancia és a gradiens-biztonság a :mod:`vqebd.platforms`
modulban van nyilvántartva — a ``qsim`` egyszeres pontossága miatt ott
deriváltmentes optimalizáló kell (ADR-0006).

Miért V2 primitív?
------------------
A Qiskit 2.0 eltávolította a V1 primitíveket. A V2 primitívek (``StatevectorEstimator``,
``BackendEstimatorV2``, ``EstimatorV2``) a Qiskit 1.4-ben és 2.x-ben egyaránt
léteznek, így az itt írt kód **előre-hordozható** (ADR-0002).

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from vqebd.config import BackendKind
from vqebd.seeds import SeedSet

__all__ = [
    "EnergyEvaluator",
    "IsaEnergyEvaluator",
    "StatevectorEnergyEvaluator",
    "make_energy_evaluator",
]


def known_backends() -> list[str]:
    """Az ismert platform-backend azonosítók, hibaüzenetekhez.

    Késleltetett import a :mod:`vqebd.platforms` modulból, hogy a
    modulbetöltési sorrend ne számítson.
    """
    from vqebd.platforms import PLATFORMS

    return sorted(PLATFORMS)


class EnergyEvaluator(ABC):
    """Egy paraméter-vektorhoz energiát rendelő, hívható objektum.

    A hívások számát magában tartja nyilván (``call_count``), mert a
    célfüggvény-kiértékelések száma a VQE egyik legfontosabb költségmutatója —
    valódi hardveren ez fordul le közvetlenül QPU-időre.
    """

    def __init__(self, num_qubits: int) -> None:
        self.num_qubits = num_qubits
        self.call_count = 0

    def __call__(self, parameters: Sequence[float]) -> float:
        """Az elektronos energia várható értéke a megadott paramétereknél (Ha).

        A magtaszítási energiát **nem** tartalmazza: azt a hívó adja hozzá.
        """
        self.call_count += 1
        return self.evaluate(parameters)

    @abstractmethod
    def evaluate(self, parameters: Sequence[float]) -> float:
        """A tényleges kiértékelés. Leszármazottak ezt írják felül."""

    @property
    @abstractmethod
    def kind(self) -> BackendKind:
        """A backend azonosítója az adatsémához."""

    def describe(self) -> dict[str, Any]:
        """A kiértékelő paraméterei az eredményrekordhoz."""
        return {"backend": self.kind, "num_qubits": self.num_qubits}


class StatevectorEnergyEvaluator(EnergyEvaluator):
    """Qiskit: zajmentes, egzakt kiértékelés állapotvektorral (``complex128``).

    Nincs sem lövészaj, sem hardverzaj: a várható érték a gépi pontosság határáig
    egzakt. Ez az **L2 referenciaszint** — az ansatz korlátait mutatja meg, minden
    más hibaforrás nélkül.
    """

    def __init__(self, circuit: Any, observable: Any) -> None:
        from qiskit.primitives import StatevectorEstimator

        super().__init__(num_qubits=int(circuit.num_qubits))
        if int(observable.num_qubits) != self.num_qubits:
            raise ValueError(
                f"az áramkör ({self.num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )
        self._circuit = circuit
        self._observable = observable
        self._estimator = StatevectorEstimator()

    @property
    def kind(self) -> BackendKind:
        return "qiskit_statevector"

    def evaluate(self, parameters: Sequence[float]) -> float:
        # A V2 primitív „PUB" formátuma: (áramkör, observable, paraméterek);
        # kötött (paraméter nélküli) áramkörnél a harmadik elem elmarad.
        pub = (
            (self._circuit, self._observable, list(parameters))
            if len(parameters)
            else (self._circuit, self._observable)
        )
        job = self._estimator.run([pub])
        return float(job.result()[0].data.evs)


class IsaEnergyEvaluator(EnergyEvaluator):
    """Közös alap a **transzpiláló** (ISA-áramkört futtató) kiértékelőkhöz.

    A zajos és hardveres kiértékelők a logikai áramkört egyszer, a konstruktorban
    transzpilálják a célhardverre (ISA). A hibaenyhítéshez (ZNE) két további
    művelet kell, amelyek **nem** optimalizálhatnak újra:

    - :meth:`to_isa_unoptimized`: egy (pl. hajtogatott) áramkört
      ``optimization_level=0``-val fordít a célhardver kapukészletére. Magasabb
      szinten a transzpiler az U·U† párokat részben kiejti, és a
      tényleges zajszorzó eltér a névlegestől. Ezt a TR-F03 1. javítási köre
      mérte: ``optimization_level=3`` mellett λ = 1/3/5-re 4/10/16 CX, vagyis a
      tényleges szorzó 1/2.5/4 volt.
    - :meth:`evaluate_isa`: egy már ISA-szintű áramkör kiértékelése a tárolt,
      layouthoz igazított observable-lel.

    A leszármazottak a konstruktorban beállítják: ``_target`` (a transzpilálás
    célja), ``_isa_circuit``, ``_isa_observable``, ``_logical_observable``,
    ``_estimator``, ``_seeds``.
    """

    _target: Any
    _isa_circuit: Any
    _isa_observable: Any
    _logical_observable: Any
    _estimator: Any
    _seeds: SeedSet

    @property
    def isa_circuit(self) -> Any:
        """A célhardverre fordított (paraméterezett) áramkör."""
        return self._isa_circuit

    def to_isa_unoptimized(self, circuit: Any) -> Any:
        """Áramkör fordítása a célhardverre **optimalizálás nélkül** (``level=0``).

        Egy már ISA-szintű (fizikai qubiteken futó) áramkörnél a triviális layout
        az identitás, útvonalválasztás nem kell, így csak a kapukészletre fordít
        (pl. ``sxdg`` → ``rz``/``sx``), kapukat nem ejt ki.
        """
        from qiskit import transpile

        return transpile(
            circuit,
            backend=self._target,
            optimization_level=0,
            seed_transpiler=self._seeds.transpiler,
        )

    def _run_pub(self, circuit: Any, observable: Any, parameters: Sequence[float]) -> float:
        """Egyetlen PUB futtatása; a hardveres leszármazott felülírja."""
        pub = (circuit, observable, list(parameters)) if len(parameters) else (circuit, observable)
        return float(self._estimator.run([pub]).result()[0].data.evs)

    def evaluate(self, parameters: Sequence[float]) -> float:
        return self._run_pub(self._isa_circuit, self._isa_observable, parameters)

    def evaluate_isa(self, isa_circuit: Any, parameters: Sequence[float]) -> float:
        """Egy ISA-szintű áramkör energiája a konstruktorbeli layouttal.

        A hívónak kell garantálnia, hogy az áramkör ugyanazokon a fizikai
        qubiteken fut, mint :attr:`isa_circuit` (pl. annak hajtogatottja).
        """
        if int(isa_circuit.num_qubits) != int(self._isa_circuit.num_qubits):
            raise ValueError(
                f"az ISA-áramkör szélessége ({isa_circuit.num_qubits}) eltér a "
                f"kiértékelőétől ({self._isa_circuit.num_qubits})"
            )
        return self._run_pub(isa_circuit, self._isa_observable, parameters)

    def evaluate_logical(self, circuit: Any, parameters: Sequence[float] = ()) -> float:
        """Logikai áramkör kiértékelése **optimalizálás nélküli** fordítással.

        A külső hajtogató könyvtárak (Mitiq) logikai áramkört adnak; ezt a
        célhardverre kell fordítani úgy, hogy a hajtogatás megmaradjon.
        """
        isa = self.to_isa_unoptimized(circuit)
        observable = (
            self._logical_observable.apply_layout(isa.layout)
            if isa.layout is not None
            else self._logical_observable
        )
        return self._run_pub(isa, observable, parameters)


class _AerIsaEnergyEvaluator(IsaEnergyEvaluator):
    """Aer-alapú ISA-kiértékelők közös mintavételi modellje.

    **Miért nem az Aer saját ``default_precision``-je?** Az Aer ``EstimatorV2``
    minden ``run()`` hívásnál ``numpy.random.default_rng(seed_simulator)``-t hoz
    létre, és abból húz ``N(evs, precision)``-t (``qiskit_aer/primitives/
    estimator_v2.py``). Rögzített seed mellett tehát **minden kiértékelés ugyanazt a
    z·σ eltolást kapja**: a „lövészaj” valójában állandó torzítás, a VQE egy
    eltolt, zajmentes felületet optimalizál, a ZNE-ben pedig közös módusként kiesik.
    (Mérve: TR-F03 1. javítási kör — minden L3a-futás ≈ +16 mHa, 20 seed
    szórása 10.3 mHa ≈ σ = 11.05 mHa.)

    **Javítás (v0.7.1):** az Aer az egzakt, zajmodell szerinti várható értéket adja
    (``precision=0``), a véges mintavétel szórását pedig egy **saját, hívásonként
    továbblépő**, ``seeds.simulator``-ból indított generátor adja hozzá. Így a
    futás továbbra is bitre determinisztikus, de az egymást követő kiértékelések
    zaja **független** — ahogy valódi hardveren.
    """

    _precision: float
    _rng: Any

    def _run_pub(self, circuit: Any, observable: Any, parameters: Sequence[float]) -> float:
        exact = super()._run_pub(circuit, observable, parameters)
        if self._precision == 0.0:
            return exact
        return exact + float(self._rng.normal(0.0, self._precision))


class AerShotEnergyEvaluator(_AerIsaEnergyEvaluator):
    """Qiskit Aer: véges lövésszámú, zajmentes kiértékelés (L3a)."""

    def __init__(
        self,
        circuit: Any,
        observable: Any,
        seeds: SeedSet,
        *,
        precision: float | None = None,
    ) -> None:
        """
        Args:
            precision: Az Aer ``EstimatorV2`` célpontossága (Ha). Alapértelmezés
                ``1/sqrt(8192)``. Az Aer ennél **nem mintavételez lövéseket**, hanem
                az egzakt várható értékhez ekkora szórású Gauss-zajt ad; ``0.0``
                az egzakt (zajmodell szerinti) várható értéket adja — ezzel
                választható szét a torzítás és a szórás (TR-F03, 1. javítási kör).
        """
        import numpy as np
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        from qiskit_aer.primitives import EstimatorV2 as AerEstimator

        super().__init__(num_qubits=int(circuit.num_qubits))
        if int(observable.num_qubits) != self.num_qubits:
            raise ValueError(
                f"az áramkör ({self.num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )

        self._shots = 8192
        if precision is not None and precision < 0:
            raise ValueError(f"a precision nem lehet negatív, kapott: {precision}")
        self._precision = float(1.0 / np.sqrt(self._shots)) if precision is None else precision
        self._rng = np.random.default_rng(seeds.simulator)
        self._seeds = seeds

        simulator = AerSimulator(seed_simulator=seeds.simulator)
        self._target = simulator
        self._logical_observable = observable
        self._isa_circuit = transpile(
            circuit, simulator, optimization_level=1, seed_transpiler=seeds.transpiler
        )
        self._isa_observable = (
            observable.apply_layout(self._isa_circuit.layout)
            if self._isa_circuit.layout is not None
            else observable
        )

        self._estimator = AerEstimator(
            options={
                "default_precision": 0.0,  # egzakt; a zajt _run_pub adja (lásd fent)
                "run_options": {"seed_simulator": seeds.simulator},
            }
        )

    @property
    def kind(self) -> BackendKind:
        return "qiskit_aer_shot"

    def describe(self) -> dict[str, Any]:
        desc = super().describe()
        desc.update(
            {
                "shots": self._shots,
                "precision": self._precision,
                "sampling_model": "exact+gaussian_independent",
                "optimization_level": 1,
            }
        )
        return desc


class AerNoisyEnergyEvaluator(_AerIsaEnergyEvaluator):
    """Qiskit Aer: zajos kiértékelés FakeBackend kalibrációval (L3b)."""

    def __init__(
        self,
        circuit: Any,
        observable: Any,
        seeds: SeedSet,
        *,
        precision: float | None = None,
    ) -> None:
        """
        Args:
            precision: Lásd :class:`AerShotEnergyEvaluator`. ``0.0`` mellett a
                zajmodell szerinti egzakt várható érték (a ZNE torzításának mérése).
        """
        import numpy as np
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        from qiskit_aer.primitives import EstimatorV2 as AerEstimator
        from qiskit_ibm_runtime.fake_provider import FakeManilaV2

        super().__init__(num_qubits=int(circuit.num_qubits))
        if int(observable.num_qubits) != self.num_qubits:
            raise ValueError(
                f"az áramkör ({self.num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )

        self._shots = 8192
        if precision is not None and precision < 0:
            raise ValueError(f"a precision nem lehet negatív, kapott: {precision}")
        self._precision = float(1.0 / np.sqrt(self._shots)) if precision is None else precision
        self._rng = np.random.default_rng(seeds.simulator)
        self._seeds = seeds
        self._backend_name = "FakeManilaV2"

        backend = FakeManilaV2()
        simulator = AerSimulator.from_backend(backend, seed_simulator=seeds.simulator)
        self._target = simulator
        self._logical_observable = observable
        self._isa_circuit = transpile(
            circuit, simulator, optimization_level=3, seed_transpiler=seeds.transpiler
        )
        self._isa_observable = (
            observable.apply_layout(self._isa_circuit.layout)
            if self._isa_circuit.layout is not None
            else observable
        )

        self._estimator = AerEstimator(
            options={
                "default_precision": 0.0,  # egzakt; a zajt _run_pub adja (lásd fent)
                "backend_options": {
                    "noise_model": simulator.options.noise_model,
                    "seed_simulator": seeds.simulator,
                },
                "run_options": {"seed_simulator": seeds.simulator},
            }
        )

    @property
    def kind(self) -> BackendKind:
        return "qiskit_aer_noisy"

    def describe(self) -> dict[str, Any]:
        desc = super().describe()
        desc.update(
            {
                "shots": self._shots,
                "precision": self._precision,
                "sampling_model": "exact+gaussian_independent",
                "optimization_level": 3,
                "fake_backend": self._backend_name,
            }
        )
        return desc


IBM_DEFAULT_RESILIENCE_LEVEL = 1
"""Az IBM Runtime ``EstimatorV2`` szerveroldali alapértelmezett mitigációs szintje.

Ha a kliens nem adja meg, a szerver ezt alkalmazza: TREX mérésmitigáció
(``measure_mitigation=True``) + mérés-twirling. Ezt a TR-F02 1. javítási köre a
``dapq25kak42c73cj1hu0`` job tárolt metaadataiból **mérte ki** (``result.metadata``).
A VQEBD ezért **explicit** adja meg — egy szerveroldali alapértelmezés-váltás így
nem tudja csendben megváltoztatni, mit jelent az L5 szint.
"""


class IBMQpuEnergyEvaluator(IsaEnergyEvaluator):
    """IBM Quantum: valódi hardveres kiértékelés Heron QPU-n (L5).

    **Mitigáció:** a ``resilience_level`` mindig explicit (alapértelmezés:
    :data:`IBM_DEFAULT_RESILIENCE_LEVEL` = 1, TREX). ``0`` a valóban nyers mérés.
    Az L5 érték tehát csak ``resilience_level=0`` mellett „nyers”; 1-es szinten
    már mérésmitigált (ADR-0003 értelmében az L4-hez hasonló, szerveroldali
    mitigáció).

    **Bizonytalanság:** az utolsó kiértékelés után elérhető a ``last_std``
    (``PubResult.data.stds``) és a ``last_ensemble_standard_error`` (a twirling-
    randomizációk szórásából becsült standard hiba), valamint a teljes
    szerveroldali metaadat (``last_metadata``). Ezek nélkül egy hardveres
    energia nem értelmezhető: egyetlen ~15 QPU-másodperces mérés szórása
    nagyságrendekkel nagyobb lehet a kémiai pontosságnál.
    """

    def __init__(
        self,
        circuit: Any,
        observable: Any,
        seeds: SeedSet,
        *,
        backend_name: str | None = None,
        shots: int = 8192,
        resilience_level: int = IBM_DEFAULT_RESILIENCE_LEVEL,
    ) -> None:
        import os

        import numpy as np
        from qiskit import transpile
        from qiskit_ibm_runtime import EstimatorV2 as IBMRuntimeEstimator
        from qiskit_ibm_runtime import QiskitRuntimeService

        from vqebd.credentials import load_ibm_credentials

        super().__init__(num_qubits=int(circuit.num_qubits))
        if int(observable.num_qubits) != self.num_qubits:
            raise ValueError(
                f"az áramkör ({self.num_qubits} qubit) és az observable "
                f"({observable.num_qubits} qubit) qubit-száma eltér"
            )

        if resilience_level not in (0, 1, 2):
            raise ValueError(f"resilience_level csak 0, 1 vagy 2 lehet, kapott: {resilience_level}")

        self._shots = shots
        self._precision = 1.0 / np.sqrt(self._shots)
        self._resilience_level = resilience_level
        self._seeds = seeds
        self._credentials = load_ibm_credentials()
        self._last_job_id: str | None = None
        self._last_std: float | None = None
        self._last_ensemble_standard_error: float | None = None
        self._last_metadata: dict[str, Any] = {}

        service_kwargs: dict[str, Any] = {
            "channel": self._credentials.channel,
            "token": self._credentials.reveal(),
        }
        if self._credentials.instance:
            service_kwargs["instance"] = self._credentials.instance

        service = QiskitRuntimeService(**service_kwargs)
        target_name = backend_name or os.environ.get("VQEBD_IBM_BACKEND", "ibm_kingston")
        self._backend = service.backend(target_name)
        self._backend_name = self._backend.name
        self._target = self._backend
        self._logical_observable = observable

        self._isa_circuit = transpile(
            circuit,
            backend=self._backend,
            optimization_level=3,
            seed_transpiler=seeds.transpiler,
        )
        self._isa_observable = (
            observable.apply_layout(self._isa_circuit.layout)
            if self._isa_circuit.layout is not None
            else observable
        )

        self._estimator = IBMRuntimeEstimator(
            mode=self._backend,
            options={
                "default_precision": self._precision,
                "resilience_level": self._resilience_level,
            },
        )

    @property
    def kind(self) -> BackendKind:
        return "ibm_qpu"

    @property
    def last_job_id(self) -> str | None:
        return self._last_job_id

    @property
    def last_std(self) -> float | None:
        """Az utolsó kiértékelés ``stds`` értéke (Ha), vagy ``None``."""
        return self._last_std

    @property
    def last_ensemble_standard_error(self) -> float | None:
        """A twirling-randomizációkból becsült standard hiba (Ha), ha a szerver adja."""
        return self._last_ensemble_standard_error

    @property
    def last_metadata(self) -> dict[str, Any]:
        """Az utolsó job PUB- és eredmény-metaadatai (mitigáció, twirling, shots)."""
        return dict(self._last_metadata)

    def describe(self) -> dict[str, Any]:
        desc = super().describe()
        desc.update(
            {
                "shots": self._shots,
                "precision": self._precision,
                "resilience_level": self._resilience_level,
                "optimization_level": 3,
                "ibm_backend": self._backend_name,
                "isa_qubits": self._isa_circuit.num_qubits,
                "last_job_id": self._last_job_id,
            }
        )
        return desc

    def _run_pub(self, circuit: Any, observable: Any, parameters: Sequence[float]) -> float:
        pub = (circuit, observable, list(parameters)) if len(parameters) else (circuit, observable)
        job = self._estimator.run([pub])
        self._last_job_id = job.job_id()
        result = job.result()
        pub_result = result[0]
        data = pub_result.data
        self._last_std = float(data.stds) if hasattr(data, "stds") else None
        self._last_ensemble_standard_error = (
            float(data.ensemble_standard_error)
            if hasattr(data, "ensemble_standard_error")
            else None
        )
        self._last_metadata = {
            "pub": dict(getattr(pub_result, "metadata", {}) or {}),
            "result": dict(getattr(result, "metadata", {}) or {}),
        }
        return float(data.evs)

    def evaluate_observables(
        self,
        observables: Sequence[Any],
        parameter_sets: Sequence[Sequence[float]],
    ) -> list[dict[str, Any]]:
        """Több PUB **egyetlen jobban**: azonos ISA-áramkör, más observable és paraméter.

        Kvótatakarékos pásztázáshoz (pl. H₂ disszociációs görbe): a H₂ UCCSD-áramköre
        minden kötéshossznál azonos, csak a θ*(R) és a Hamilton-operátor változik.
        Egy job 5 PUB-bal kevesebb QPU-időt és sorban állást igényel, mint 5 job.

        Args:
            observables: **Logikai** (layout nélküli) qubit-Hamilton-operátorok; a
                konstruktorbeli ISA-layoutra képezzük le őket.
            parameter_sets: A PUB-onkénti paraméterek (azonos hosszú lista).

        Returns:
            PUB-onként: ``evs``, ``stds``, ``ensemble_standard_error`` és ``metadata``
            (elektronos energia, Ha). A job azonosítója a :attr:`last_job_id`-ben.

        Raises:
            ValueError: Eltérő hosszú bemenet vagy eltérő qubit-számú observable esetén.
        """
        if len(observables) != len(parameter_sets) or not observables:
            raise ValueError(
                f"az observable-ök ({len(observables)}) és a paraméterkészletek "
                f"({len(parameter_sets)}) száma azonos és pozitív legyen"
            )
        layout = self._isa_circuit.layout
        pubs = []
        for observable, params in zip(observables, parameter_sets, strict=True):
            if int(observable.num_qubits) != self.num_qubits:
                raise ValueError(
                    f"az observable qubit-száma ({observable.num_qubits}) eltér az "
                    f"áramkörétől ({self.num_qubits})"
                )
            isa_observable = observable.apply_layout(layout) if layout is not None else observable
            pubs.append((self._isa_circuit, isa_observable, list(params)))
        job = self._estimator.run(pubs)
        self._last_job_id = job.job_id()
        result = job.result()
        out: list[dict[str, Any]] = []
        for pub_result in result:
            data = pub_result.data
            out.append(
                {
                    "evs": float(data.evs),
                    "stds": float(data.stds) if hasattr(data, "stds") else None,
                    "ensemble_standard_error": (
                        float(data.ensemble_standard_error)
                        if hasattr(data, "ensemble_standard_error")
                        else None
                    ),
                    "metadata": dict(getattr(pub_result, "metadata", {}) or {}),
                }
            )
        self._last_metadata = {"result": dict(getattr(result, "metadata", {}) or {})}
        return out


def make_energy_evaluator(
    kind: BackendKind,
    circuit: Any,
    observable: Any,
    seeds: SeedSet,
) -> EnergyEvaluator:
    """Energiakiértékelő létrehozása a kért platform-backendhez.

    A VQE-hurok szempontjából mindegy, melyiket kapja: az interfész azonos
    (ADR-0002). Ez teszi lehetővé, hogy ugyanaz a kód fusson mindhárom platformon.

    Args:
        kind: A platform-backend azonosítója.
        circuit: A paraméterezett ansatz-áramkör (Qiskit).
        observable: A qubit-Hamilton-operátor (Qiskit ``SparsePauliOp``).
        seeds: A seed-készlet. A ``qiskit_statevector`` kiértékelés egzakt és
            determinisztikus, ezért nem használ seedet; a Cirq-alapú backendek
            viszont **transzpilálnak**, és ahhoz kell a ``seed_transpiler``
            (ADR-0005: a SABRE-alapú lépések sztochasztikusak).

    Returns:
        A kiértékelő.

    Raises:
        ValueError: Ismeretlen backend esetén.
    """
    if kind == "qiskit_statevector":
        return StatevectorEnergyEvaluator(circuit, observable)

    if kind == "qiskit_aer_shot":
        return AerShotEnergyEvaluator(circuit, observable, seeds)

    if kind == "qiskit_aer_noisy":
        return AerNoisyEnergyEvaluator(circuit, observable, seeds)

    if kind == "ibm_qpu":
        return IBMQpuEnergyEvaluator(circuit, observable, seeds)

    # Késleltetett import: a Cirq-réteg csak akkor töltődik be, ha tényleg kell.
    if kind == "cirq_simulator":
        from vqebd.backends.cirq_estimators import CirqEnergyEvaluator

        return CirqEnergyEvaluator(circuit, observable, seed_transpiler=seeds.transpiler)

    if kind == "qsim":
        from vqebd.backends.cirq_estimators import QsimEnergyEvaluator

        return QsimEnergyEvaluator(circuit, observable, seed_transpiler=seeds.transpiler)

    # A típusellenőrző szerint ide nem juthatunk (a BackendKind kimerítő Literal),
    # de futásidőben érkezhet érvénytelen string is — ezért marad a védelem.
    raise ValueError(f"ismeretlen backend: {kind!r}. Ismert backendek: {known_backends()}")
