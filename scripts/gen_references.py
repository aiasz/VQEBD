#!/usr/bin/env python3
"""VQEBD — a ``docs/references.md`` hivatkozásjegyzék generálása.

Cél
---
A bibliográfiai adatokat (szerzők, cím, év, kötet, oldalszám) **nem kézzel írjuk**,
hanem a DOI-ból oldjuk fel a Crossref (``api.crossref.org``), illetve arXiv-DOI esetén
a DataCite (``api.datacite.org``) REST API-val. Ezzel a hivatkozás-halucináció
kizárható: ami a jegyzékben szerepel, az a kiadó által regisztrált metaadat.

Használat
---------
    python scripts/gen_references.py [--out docs/references.md]

Hálózati hozzáférést igényel. A nyers API-válaszokat a
``docs/testing/refs_crossref_raw.json`` fájlba menti provenance céljából.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, TypeAlias, cast

# A REST API-k szabad szerkezetű JSON-t adnak vissza, és a séma kiadónként eltér.
# A ténylegesen használt mezőket futásidőben ellenőrizzük (lásd `apply_overrides`),
# ezért az `Any` itt tudatos döntés, nem lazaság.
JsonDict: TypeAlias = dict[str, Any]
"""Nyers, a Crossref vagy a DataCite API-tól kapott JSON-objektum."""

Record: TypeAlias = dict[str, Any]
"""Egy normalizált bibliográfiai tétel, a jegyzék generálásához előkészítve."""

MAILTO = "kormosa@gmail.com"
UA = {"User-Agent": f"VQEBD-refgen/1.0 (mailto:{MAILTO})"}
TIMEOUT = 45

# (kulcs, DOI vagy None, kategória, felhasználás a projektben)
ENTRIES: list[tuple[str, str | None, str, str]] = [
    # --- VQE elmélet és alapok ---
    (
        "peruzzo2014",
        "10.1038/ncomms5213",
        "VQE elmélet és alapok",
        "A VQE algoritmus eredeti közleménye.",
    ),
    (
        "mcclean2016",
        "10.1088/1367-2630/18/2/023023",
        "VQE elmélet és alapok",
        "A variációs hibrid algoritmusok elméleti kerete; a lövésszám-becslés alapja.",
    ),
    (
        "omalley2016",
        "10.1103/PhysRevX.6.031007",
        "VQE elmélet és alapok",
        "H2 alapállapot szupravezető qubiteken — a Fázis 2 hardveres mérés irodalmi előzménye.",
    ),
    (
        "kandala2017",
        "10.1038/nature23879",
        "VQE elmélet és alapok",
        "Hardware-efficient ansatz; a LiH és BeH2 választásunk irodalmi előzménye.",
    ),
    (
        "hempel2018",
        "10.1103/PhysRevX.8.031022",
        "VQE elmélet és alapok",
        "Független hardverplatform (csapdázott ion) ugyanezekre a molekulákra — kereszthivatkozás.",
    ),
    (
        "barkoutsos2018",
        "10.1103/PhysRevA.98.022322",
        "VQE elmélet és alapok",
        "Particle-hole Hamilton-operátor és optimalizált hullámfüggvény-kifejtések.",
    ),
    (
        "romero2019",
        "10.1088/2058-9565/aad3e4",
        "VQE elmélet és alapok",
        "UCCSD ansatz-stratégiák — a Fázis 1 ansatz-választásának indoklása.",
    ),
    (
        "tilly2022",
        "10.1016/j.physrep.2022.08.003",
        "VQE elmélet és alapok",
        "VQE összefoglaló review; best-practice forrás a teljes projektre.",
    ),
    # --- Kvantumkémia ---
    (
        "hehre1969",
        "10.1063/1.1672392",
        "Kvantumkémia",
        "Az STO-3G bázis eredeti definíciója — a projekt alapértelmezett bázisa.",
    ),
    (
        "cao2019",
        "10.1021/acs.chemrev.8b00803",
        "Kvantumkémia",
        "Kvantumkémia a kvantumszámítás korában — átfogó review.",
    ),
    (
        "mcardle2020",
        "10.1103/RevModPhys.92.015003",
        "Kvantumkémia",
        "Kvantumszámításos kémia review (Reviews of Modern Physics).",
    ),
    (
        "sun2018",
        "10.1002/wcms.1340",
        "Kvantumkémia",
        "PySCF — a klasszikus referenciaszint (L0: Hartree–Fock, FCI) számítómotorja.",
    ),
    (
        "sun2020",
        "10.1063/5.0006074",
        "Kvantumkémia",
        "PySCF újabb fejlesztések — a 2.x ág hivatkozása.",
    ),
    # --- Fermion → qubit leképezések ---
    (
        "jordan1928",
        "10.1007/BF01331938",
        "Fermion → qubit leképezések",
        "A Jordan–Wigner transzformáció eredeti közleménye.",
    ),
    (
        "bravyi2002",
        "10.1006/aphy.2002.6254",
        "Fermion → qubit leképezések",
        "A Bravyi–Kitaev leképezés.",
    ),
    (
        "seeley2012",
        "10.1063/1.4768229",
        "Fermion → qubit leképezések",
        "A Bravyi–Kitaev transzformáció elektronszerkezeti alkalmazása.",
    ),
    # --- Hibaenyhítés ---
    (
        "temme2017",
        "10.1103/PhysRevLett.119.180509",
        "Hibaenyhítés",
        "A ZNE eredeti közleménye (Temme–Bravyi–Gambetta).",
    ),
    (
        "li2017",
        "10.1103/PhysRevX.7.021050",
        "Hibaenyhítés",
        "Aktív hibaminimalizálás — a ZNE független, egyidejű felfedezése.",
    ),
    (
        "endo2018",
        "10.1103/PhysRevX.8.031027",
        "Hibaenyhítés",
        "Gyakorlati hibaenyhítés; a kvázi-valószínűségi módszer (PEC) alapja.",
    ),
    (
        "giurgicatiron2020",
        "10.1109/QCE49297.2020.00045",
        "Hibaenyhítés",
        "Digitális ZNE: unitáris hajtogatás (unitary folding) — a saját implementációnk alapja.",
    ),
    (
        "nation2021",
        "10.1103/PRXQuantum.2.040326",
        "Hibaenyhítés",
        "Skálázható mérési hibaenyhítés (M3) — válasz az M5 megállapításra (readout-hiba).",
    ),
    (
        "larose2022",
        "10.22331/q-2022-08-11-774",
        "Hibaenyhítés",
        "A Mitiq szoftvercsomag — a ZNE referencia-implementációja a keresztvalidációhoz.",
    ),
    (
        "vandenberg2023",
        "10.1038/s41567-023-02042-2",
        "Hibaenyhítés",
        "PEC ritka Pauli–Lindblad modellel — az IBM Runtime PEC opciójának háttere.",
    ),
    (
        "cai2023",
        "10.1103/RevModPhys.95.045005",
        "Hibaenyhítés",
        "Hibaenyhítés összefoglaló review (Reviews of Modern Physics).",
    ),
    (
        "kim2023",
        "10.1038/s41586-023-06096-3",
        "Hibaenyhítés",
        "ZNE nagy skálán, valódi hardveren — a módszer gyakorlati határainak referenciája.",
    ),
    # --- Benchmarking ---
    (
        "cross2019",
        "10.1103/PhysRevA.100.032328",
        "Benchmarking",
        "Quantum Volume — a volumetrikus nézet (Fázis 7.4) előzménye.",
    ),
    (
        "blumekohout2020",
        "10.22331/q-2020-11-15-362",
        "Benchmarking",
        "Volumetrikus benchmark-keretrendszer — a Fázis 7.4 hőtérkép módszertani alapja.",
    ),
    (
        "lubinski2023",
        "10.1109/TQE.2023.3253761",
        "Benchmarking",
        "Alkalmazás-orientált benchmarkok — a projekt benchmark-módszertanának mintája.",
    ),
    # --- Optimalizálók ---
    ("nelder1965", "10.1093/comjnl/7.4.308", "Optimalizálók", "Nelder–Mead szimplex módszer."),
    (
        "spall1992",
        "10.1109/9.119632",
        "Optimalizálók",
        "SPSA — zajos célfüggvényhez ajánlott sztochasztikus optimalizáló.",
    ),
    (
        "powell1994",
        "10.1007/978-94-015-8330-5_4",
        "Optimalizálók",
        "COBYLA — deriváltmentes, korlátozásos optimalizáló.",
    ),
    # --- Szoftver ---
    (
        "javadiabhari2024",
        "10.48550/arXiv.2405.08810",
        "Szoftver",
        "A Qiskit hivatalos hivatkozása (arXiv-preprint, DataCite DOI).",
    ),
    ("harris2020", "10.1038/s41586-020-2649-2", "Szoftver", "NumPy — numerikus alapréteg."),
    (
        "virtanen2020",
        "10.1038/s41592-019-0686-2",
        "Szoftver",
        "SciPy — a VQE optimalizáló-hurok implementációja.",
    ),
    # --- Adatkezelés ---
    (
        "wilkinson2016",
        "10.1038/sdata.2016.18",
        "Adatkezelés",
        "FAIR alapelvek — a Fázis 4 adatséma és a Fázis 9 publikálás irányelve.",
    ),
    # --- Statisztika és mérési módszertan (Fázis 5) ---
    (
        "student1908",
        "10.2307/2331554",
        "Statisztika és mérési módszertan",
        "A t-eloszlás: kis mintás (N seed) konfidencia-intervallum (vqebd.stats, ADR-0007).",
    ),
    (
        "wecker2015",
        "10.1103/PhysRevA.92.042303",
        "Statisztika és mérési módszertan",
        "A VQE mérési költsége és a lövészaj skálázása; az ismétlés/lövésszám tervezés alapja.",
    ),
    # --- DOI nélküli tételek ---
    ("kraft1988", None, "Optimalizálók", "Az SLSQP algoritmus eredeti technikai jelentése."),
    (
        "helgaker2000",
        None,
        "Kvantumkémia",
        "A „kémiai pontosság” (1 kcal/mol) fogalmának standard tankönyvi forrása.",
    ),
]

# DOI nélküli, kézzel megadott, bibliográfiailag ellenőrzött tételek.
MANUAL: dict[str, Record] = {
    "kraft1988": {
        "authors": "Kraft, D.",
        "title": "A software package for sequential quadratic programming",
        "venue": (
            "Technical Report DFVLR-FB 88-28, Deutsche Forschungs- und Versuchsanstalt "
            "für Luft- und Raumfahrt (DFVLR), Köln"
        ),
        "year": 1988,
        "volume": None,
        "page": None,
        "doi": None,
        "source": "kézi (ellenőrzött)",
        "note": (
            "A Crossrefben nem regisztrált (technikai jelentés, nem folyóiratcikk). "
            'A SciPy `method="SLSQP"` ezt az algoritmust implementálja.'
        ),
    },
    "helgaker2000": {
        "authors": "Helgaker, T., Jørgensen, P., Olsen, J.",
        "title": "Molecular Electronic-Structure Theory",
        "venue": "John Wiley & Sons, Chichester. ISBN 978-0-471-96755-2",
        "year": 2000,
        "volume": None,
        "page": None,
        "doi": None,
        "source": "kézi (ellenőrzött)",
        "note": "A kémiai pontosság (1 kcal/mol = 1.5936 mHa) hivatkozási alapja.",
    },
}

# --- Sérült registry-metaadatok felülírása -----------------------------------
#
# Néhány régi rekord metaadata magánál a kiadónál/Crossrefnél sérült: a válasz
# U+FFFD (REPLACEMENT CHARACTER) karaktereket tartalmaz. Ilyenkor a generátor
# NEM propagálja tovább a romlott szöveget, hanem ebből a táblából veszi a helyes
# értéket — vagy ha itt sincs bejegyzés, hibával leáll (lásd `assert_clean`).
#
# Ellenőrizve: 2026-09-22, `docs/testing/refs_crossref_raw.json`.
OVERRIDES: dict[str, dict[str, str]] = {
    "jordan1928": {
        # Crossref-válasz: "�ber das Paulische �quivalenzverbot"
        "title": "Über das Paulische Äquivalenzverbot",
        # Crossref-válasz: "Zeitschrift f�r Physik"
        "venue": "Zeitschrift für Physik",
        "_reason": (
            "A Crossref által tárolt metaadat hibásan kódolt (U+FFFD). "
            "A helyes alak a folyóirat eredeti közleményéből, "
            "Z. Physik 47, 631–651 (1928)."
        ),
    },
}

SOFTWARE = [
    ("Qiskit", "1.4.6", "Apache-2.0", "[javadiabhari2024]"),
    ("Qiskit Aer", "0.17.2", "Apache-2.0", "[javadiabhari2024]"),
    ("Qiskit Nature", "0.7.2", "Apache-2.0", "[javadiabhari2024]"),
    ("Qiskit Algorithms", "0.3.1", "Apache-2.0", "[javadiabhari2024]"),
    ("Qiskit IBM Runtime", "0.41.1", "Apache-2.0", "[javadiabhari2024]"),
    ("Mitiq", "0.47.0", "**GPL-3.0**", "[larose2022]"),
    ("PySCF", "2.14.0", "Apache-2.0", "[sun2018], [sun2020]"),
    ("NumPy", "1.26.4", "BSD-3-Clause", "[harris2020]"),
    ("SciPy", "1.13.1", "BSD-3-Clause", "[virtanen2020]"),
    ("Cirq (core)", "1.4.1", "Apache-2.0", "— (a Mitiq tranzitív függősége)"),
    ("ply", "3.11", "BSD-3-Clause", "— (a Mitiq QASM-elemzőjének rejtett függősége)"),
]

ONLINE = [
    ("Qiskit dokumentáció", "https://quantum.cloud.ibm.com/docs"),
    ("Qiskit Nature dokumentáció", "https://qiskit-community.github.io/qiskit-nature/"),
    ("Mitiq dokumentáció", "https://mitiq.readthedocs.io/"),
    ("PySCF dokumentáció", "https://pyscf.org/"),
    ("Metriq benchmark-platform (Unitary Foundation)", "https://metriq.info/"),
    ("Unitary Foundation", "https://unitary.foundation/"),
    ("QOSF — Quantum Open Source Foundation", "https://qosf.org/"),
    ("Zenodo", "https://zenodo.org/"),
    ("Keep a Changelog 1.1.0", "https://keepachangelog.com/en/1.1.0/"),
    ("Semantic Versioning 2.0.0", "https://semver.org/"),
    ("Conventional Commits 1.0.0", "https://www.conventionalcommits.org/en/v1.0.0/"),
    ("Citation File Format (CFF)", "https://citation-file-format.github.io/"),
]


def _get(url: str) -> JsonDict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return cast(JsonDict, json.load(resp))


def fetch_crossref(doi: str) -> JsonDict:
    payload = _get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={MAILTO}")
    return cast(JsonDict, payload["message"])


def fetch_datacite(doi: str) -> JsonDict:
    payload = _get(f"https://api.datacite.org/dois/{urllib.parse.quote(doi)}")
    return cast(JsonDict, payload["data"]["attributes"])


def clean(text: str) -> str:
    """Crossref-címekben előforduló XML-markup eltávolítása.

    A Crossref a JATS inline-elemeket (``<scp>``, ``<i>``, ``<sub>``) gyakran
    behúzással és sortöréssel adja vissza, például::

        "P\\n            <scp>y</scp>\\n            SCF: the Python-based ..."

    A tagek *és a körülöttük lévő whitespace* együttes törlése adja vissza a helyes
    ``PySCF`` alakot; a puszta tag-törlés ``P y SCF``-et eredményezne.
    """
    return re.sub(r"\s+", " ", re.sub(r"\s*<[^>]+>\s*", "", text)).strip()


def fmt_authors(names: list[str], limit: int = 12) -> str:
    return ", ".join(names[:limit]) + (", et al." if len(names) > limit else "")


def resolve(key: str, doi: str | None) -> tuple[Record, JsonDict | None]:
    """Egy tétel feloldása. Visszaadja a (rekord, nyers_API_válasz) párt."""
    if doi is None:
        return dict(MANUAL[key]), None
    try:
        raw = fetch_crossref(doi)
        # Álnévnél (pl. „Student”, 1908) nincs utónév: ilyenkor csak a családnév.
        names = [
            f"{a.get('family', '?')}, {a['given'][:1]}." if a.get("given") else a.get("family", "?")
            for a in raw.get("author") or []
        ]
        # Az idézési év a lapszám éve (published-print), ha van; különben az issued dátum.
        dates = raw.get("published-print", {}).get("date-parts") or raw.get("issued", {}).get(
            "date-parts"
        )
        return {
            "authors": fmt_authors(names),
            "title": clean((raw.get("title") or ["—"])[0]),
            "venue": clean((raw.get("container-title") or ["—"])[0]),
            "year": dates[0][0],
            "volume": raw.get("volume"),
            "page": raw.get("page") or raw.get("article-number"),
            "doi": raw.get("DOI"),
            "source": "Crossref",
            "note": None,
        }, raw
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        raw = fetch_datacite(doi)  # arXiv-DOI-k a DataCite-nál vannak regisztrálva
        return {
            "authors": fmt_authors([c.get("name", "?") for c in raw.get("creators") or []]),
            "title": clean((raw.get("titles") or [{}])[0].get("title", "—")),
            "venue": raw.get("publisher") or "arXiv",
            "year": raw.get("publicationYear"),
            "volume": None,
            "page": None,
            "doi": doi,
            "source": "DataCite",
            "note": None,
        }, raw


REPLACEMENT_CHAR = "�"


def apply_overrides(key: str, rec: Record) -> Record:
    """Sérült registry-mezők felülírása és a maradék romlás kiszűrése.

    Ha a feloldott rekord U+FFFD-t tartalmaz és nincs hozzá ``OVERRIDES`` bejegyzés,
    ``ValueError``-t dob: inkább álljon le a generálás, mint hogy romlott
    bibliográfiai adat kerüljön a jegyzékbe.
    """
    for field, value in OVERRIDES.get(key, {}).items():
        if not field.startswith("_"):
            rec[field] = value
    broken = [f for f, v in rec.items() if isinstance(v, str) and REPLACEMENT_CHAR in v]
    if broken:
        raise ValueError(
            f"a(z) '{key}' tétel registry-metaadata sérült (U+FFFD) a következő "
            f"mezőkben: {broken}. Vegyél fel hozzá bejegyzést az OVERRIDES táblába."
        )
    return rec


def citation_line(rec: Record) -> str:
    parts = [rec["authors"], f"({rec['year']}).", rec["title"] + ".", f"*{rec['venue']}*"]
    if rec.get("volume"):
        parts.append(f"**{rec['volume']}**")
    if rec.get("page"):
        parts.append(str(rec["page"]))
    return " ".join(parts).replace("* **", "*, **").rstrip(".") + "."


DOC_VERSION = "1.1.0"
"""A jegyzék dokumentum-verziója; új tételnél lép (``00_master_plan.md`` 8.3)."""

CHANGELOG_ROWS: list[tuple[str, str, str]] = [
    ("1.0.0", "2026-09-22", "Első kiadás. 37 tétel, ebből 35 gépileg DOI-validált."),
    (
        "1.1.0",
        "2026-09-25",
        "Fázis 5: +2 tétel (student1908, wecker2015) — statisztika és mérési módszertan.",
    ),
]
"""A jegyzék változásnaplója. Kézzel vezetett: a generálás dátuma nem írja felül."""

ONLINE_CHECKED = "2026-09-22"
"""Az online források utolsó (kézi) ellenőrzésének napja. A generátor ezeket az
URL-eket NEM ellenőrzi, ezért a generálás napja itt félrevezető lenne."""


def render(records: dict[str, Record], today: str) -> str:
    notes = {k: n for k, _, _, n in ENTRIES}
    n_doi = sum(1 for _, d, _, _ in ENTRIES if d)
    lines: list[str] = []
    add = lines.append

    add("# VQEBD — Hivatkozásjegyzék\n")
    add("| | |\n|---|---|")
    add("| **Dokumentum** | `docs/references.md` |")
    add(f"| **Dokumentum-verzió** | {DOC_VERSION} |")
    add(f"| **Dátum** | {today} |")
    add("| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |")
    add("| **Generálta** | `scripts/gen_references.py` |")
    add(f"| **Tételek** | {len(ENTRIES)} db, ebből **{n_doi}** gépileg DOI-validált |\n")
    add("---\n")
    add("## Módszertani megjegyzés\n")
    add("Ebben a jegyzékben a szerzőlistákat, címeket, évszámokat, kötet- és oldalszámokat")
    add("**nem kézzel írtuk**: a DOI-ból oldottuk fel őket a Crossref (`api.crossref.org`),")
    add("illetve arXiv-DOI esetén a DataCite (`api.datacite.org`) REST API-val. Ami itt")
    add("szerepel, az a kiadó által regisztrált metaadat — ez kizárja a")
    add("hivatkozás-halucinációt.")
    add("A generálás megismételhető: `python scripts/gen_references.py`. A nyers API-válaszok")
    add("provenance céljából a `docs/testing/refs_crossref_raw.json` fájlban vannak.\n")
    add("Két tételnek nincs regisztrált DOI-ja; ezek forrása kézi, de bibliográfiailag")
    add("ellenőrzött,")
    add("és a *Megjegyzés* sor jelzi őket.\n")
    add("A generátor a beolvasott metaadatban **kiszűri a U+FFFD (replacement character)**")
    add("karaktereket: ha egy registry-rekord sérült, a generálás hibával leáll, hacsak nincs")
    add("hozzá kézzel ellenőrzött javítás. Az ilyen tételeket a *Metaadat-javítás* sor jelzi.\n")
    add("Az idézési év a **lapszám** éve (`published-print`), nem az online-first dátum")
    add("(pl. [romero2019] online 2018-10-19, lapszám 2019-01-01 → **2019**).\n")
    add("---\n")

    seen: list[str] = []
    for _, _, cat, _ in ENTRIES:
        if cat not in seen:
            seen.append(cat)

    for cat in seen:
        add(f"## {cat}\n")
        for key, _, c, _ in ENTRIES:
            if c != cat:
                continue
            rec = records[key]
            add(f"**[{key}]** {citation_line(rec)}")
            if rec.get("doi"):
                add(f"  DOI: [{rec['doi']}](https://doi.org/{rec['doi']})")
            add(f"  *Felhasználás:* {notes[key]}")
            if rec.get("note"):
                add(f"  *Megjegyzés:* {rec['note']}")
            if key in OVERRIDES:
                add(f"  *Metaadat-javítás:* {OVERRIDES[key]['_reason']}")
            add("")
        add("")

    add("---\n")
    add("## Felhasznált szoftverek\n")
    add("A futásidőben ténylegesen betöltött verziókat a `requirements.lock` és minden")
    add("eredményrekord `*_version` mezői rögzítik. Az indoklást lásd:")
    add("[`docs/plan/00_master_plan.md`](plan/00_master_plan.md), 4. fejezet.\n")
    add("| Szoftver | Verzió | Licenc | Hivatkozás |")
    add("|---|---|---|---|")
    for row in SOFTWARE:
        add("| " + " | ".join(row) + " |")
    add("")
    add("> **Licencfigyelem.** A Mitiq **GPL-3.0** licencű, a VQEBD viszont MIT. Ezért a Mitiq")
    add("> **opcionális, futásidőben betöltött** komponens: nem linkeljük be és nem terjesztjük")
    add("> újra. A Mitiq-függő kódút egyetlen modulba, a `src/vqebd/mitigation/mitiq_zne.py`-be")
    add("> van zárva, és a `mitiq` extra nélkül a rendszer teljes funkcionalitással működik.")
    add(
        "> Részletek: [`docs/adr/ADR-0003-mitigacios-architektura.md`]"
        "(adr/ADR-0003-mitigacios-architektura.md).\n"
    )
    add("---\n")
    add("## Online források\n")
    add("| Forrás | URL | Utolsó ellenőrzés |")
    add("|---|---|---|")
    for name, url in ONLINE:
        add(f"| {name} | <{url}> | {ONLINE_CHECKED} |")
    add("")
    add("---\n")
    add("## Változásnapló\n")
    add("| Verzió | Dátum | Változás |")
    add("|---|---|---|")
    for version, date, change in CHANGELOG_ROWS:
        add(f"| {version} | {date} | {change} |")
    add("")
    add("*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="docs/references.md", type=Path)
    ap.add_argument("--raw", default="docs/testing/refs_crossref_raw.json", type=Path)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    records: dict[str, Record] = {}
    raws: dict[str, JsonDict] = {}
    failures: list[str] = []
    for key, doi, _, _ in ENTRIES:
        try:
            rec, raw = resolve(key, doi)
        except Exception as exc:  # a hibát jelentjük, nem nyeljük el
            failures.append(f"{key} ({doi}): {type(exc).__name__}: {exc}")
            continue
        try:
            rec = apply_overrides(key, rec)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        records[key] = rec
        if raw is not None:
            raws[key] = raw
        src = rec.get("source", "?")
        flag = " [felülírva]" if key in OVERRIDES else ""
        print(f"[{src:>9}] {key:<18} {rec['year']}  {rec['title'][:60]}{flag}")

    if failures:
        print("\nHIBÁS TÉTELEK (a jegyzék NEM készült el):", file=sys.stderr)
        for f in failures:
            print("  - " + f, file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.raw.parent.mkdir(parents=True, exist_ok=True)
    # `newline="\n"` kötelező: alapértelmezésben a Python szövegmódban a `\n`-t
    # `os.linesep`-re fordítja, így Windowson CRLF, Linuxon LF sorvégű fájl születne
    # UGYANABBÓL a bemenetből. A generátor kimenete viszont verziózott műtermék,
    # amelynek platformfüggetlenül azonosnak kell lennie (.gitattributes: `eol=lf`).
    args.out.write_text(render(records, args.date), encoding="utf-8", newline="\n")
    args.raw.write_text(
        json.dumps(raws, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"\nOK — {len(records)} tétel → {args.out}")
    print(f"     nyers metaadat → {args.raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
