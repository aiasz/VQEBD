"""IBM Quantum hitelesítő adatok biztonságos betöltése.

Ez a modul **kizárólag** a hitelesítő adatok beolvasásáért felel. A tényleges
QPU-futtatás a Fázis 2 feladata, és külön biztonsági kapcsoló
(``VQEBD_ALLOW_HARDWARE``) védi.

Biztonsági alapelvek
--------------------
1. **A token soha nem kerül naplóba, kivételüzenetbe, ``repr()``-be vagy
   eredményrekordba.** A :class:`IbmCredentials` maszkolt ``__repr__``-t ad.
2. A token csak a :meth:`IbmCredentials.reveal` metóduson keresztül érhető el —
   ez a hívás helyén **láthatóvá teszi a szándékot** a kódolvasó számára.
3. A forrásfájlokat a ``.gitignore`` (``*.token``, ``.env``) és a
   ``.dockerignore`` egyaránt kizárja; ezt automatikus teszt őrzi
   (``tests/repo/test_secrets_hygiene.py``).

Betöltési sorrend
-----------------
1. ``IBM_QUANTUM_TOKEN`` környezeti változó — CI és konténer.
2. ``.env`` fájl a repó gyökerében — fejlesztői gép.
3. ``IBM.token`` JSON-fájl a repó gyökerében — az IBM Cloud konzol letöltési
   formátuma (``{"name":…, "description":…, "createdAt":…, "apikey":…}``).

Az első találat nyer; a sorrend szándékos, mert a környezeti változó a
legszűkebb hatókörű és a legkönnyebben felülírható.

Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5)
Licenc: MIT
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

__all__ = [
    "DEFAULT_CHANNEL",
    "CredentialsNotFoundError",
    "IbmCredentials",
    "load_ibm_credentials",
    "mask_secret",
]

DEFAULT_CHANNEL: Final[str] = "ibm_quantum_platform"
"""Az IBM Quantum Platform alapértelmezett csatornája.

A korábbi ``ibm_quantum`` csatorna 2025 júliusában megszűnt. A
``qiskit-ibm-runtime 0.41.1`` a ``ibm_quantum_platform`` és az ``ibm_cloud``
csatornákat ismeri (mérve: TR-000, 1. kör / 11. lépés).
"""

TOKEN_FILENAME: Final[str] = "IBM.token"
ENV_FILENAME: Final[str] = ".env"

_ENV_TOKEN: Final[str] = "IBM_QUANTUM_TOKEN"
_ENV_CHANNEL: Final[str] = "IBM_QUANTUM_CHANNEL"
_ENV_INSTANCE: Final[str] = "IBM_QUANTUM_INSTANCE"

_MIN_TOKEN_LENGTH: Final[int] = 20
"""Az IBM Cloud API-kulcsok 44 karakteresek; ennél rövidebb érték elgépelés."""


class CredentialsNotFoundError(RuntimeError):
    """Nem található használható IBM-hitelesítő adat.

    A hibaüzenet felsorolja a megvizsgált forrásokat, de **soha nem tartalmaz**
    titkot.
    """


def mask_secret(secret: str, *, visible: int = 3) -> str:
    """Titok maszkolása naplózáshoz.

    Args:
        secret: A maszkolandó érték.
        visible: Hány karakter maradjon látható az elején és a végén.

    Returns:
        Maszkolt szöveg, például ``"C96***…***Rnz (44 karakter)"``.
        Rövid értékeknél semmi nem marad látható.
    """
    if not secret:
        return "<üres>"
    if len(secret) <= 2 * visible + 4:
        return f"{'*' * len(secret)} ({len(secret)} karakter)"
    return f"{secret[:visible]}{'*' * 6}{secret[-visible:]} ({len(secret)} karakter)"


@dataclass(frozen=True, slots=True)
class IbmCredentials:
    """IBM Quantum hitelesítő adatok.

    A ``token`` mező szándékosan **nem** jelenik meg a ``repr()``-ben. A
    kiolvasáshoz a :meth:`reveal` metódust kell hívni — így a kódban látható
    marad, hol kerül elő a titok.

    Attributes:
        token: Az IBM Cloud API-kulcs. Ne naplózd, ne add tovább.
        channel: A Runtime-csatorna neve.
        instance: A szolgáltatáspéldány azonosítója (CRN), ha meg van adva.
        source: Honnan töltöttük be — naplózható, mert nem titok.
    """

    token: str = field(repr=False)
    channel: str = DEFAULT_CHANNEL
    instance: str | None = None
    source: str = "ismeretlen"

    def __post_init__(self) -> None:
        if not self.token or not self.token.strip():
            raise ValueError("az IBM-token nem lehet üres")
        if len(self.token) < _MIN_TOKEN_LENGTH:
            raise ValueError(
                f"az IBM-token gyanúsan rövid ({len(self.token)} karakter, "
                f"legalább {_MIN_TOKEN_LENGTH} várt) — elgépelés vagy csonkolt érték?"
            )

    def __repr__(self) -> str:
        """Maszkolt ábrázolás — ez kerül naplóba és hibaüzenetbe."""
        return (
            f"IbmCredentials(token={mask_secret(self.token)!r}, "
            f"channel={self.channel!r}, instance={self.instance!r}, "
            f"source={self.source!r})"
        )

    __str__ = __repr__

    def reveal(self) -> str:
        """A nyers token kiolvasása.

        Csak a ``QiskitRuntimeService`` felé szabad továbbadni. A hívás
        szándékosan explicit, hogy a kódban látható legyen, hol kerül elő a titok.
        """
        return self.token

    def masked(self) -> str:
        """A token maszkolt alakja — naplózáshoz."""
        return mask_secret(self.token)


def _read_env_file(path: Path) -> dict[str, str]:
    """Egyszerű ``.env``-elemző (``KEY=VALUE`` sorok, ``#`` kommentekkel).

    Szándékosan nem használunk külső csomagot: a formátum triviális, és a
    függőségek számát a reprodukálhatóság miatt minimalizáljuk.
    """
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        cleaned = value.strip().strip("\"'")
        if cleaned:
            values[key.strip()] = cleaned
    return values


def _from_environment() -> IbmCredentials | None:
    token = os.environ.get(_ENV_TOKEN, "").strip()
    if not token:
        return None
    return IbmCredentials(
        token=token,
        channel=os.environ.get(_ENV_CHANNEL, DEFAULT_CHANNEL).strip() or DEFAULT_CHANNEL,
        instance=(os.environ.get(_ENV_INSTANCE, "").strip() or None),
        source=f"környezeti változó ({_ENV_TOKEN})",
    )


def _from_env_file(root: Path) -> IbmCredentials | None:
    path = root / ENV_FILENAME
    if not path.is_file():
        return None
    values = _read_env_file(path)
    token = values.get(_ENV_TOKEN, "").strip()
    if not token:
        return None
    return IbmCredentials(
        token=token,
        channel=values.get(_ENV_CHANNEL, DEFAULT_CHANNEL) or DEFAULT_CHANNEL,
        instance=values.get(_ENV_INSTANCE) or None,
        source=f"{ENV_FILENAME} fájl",
    )


def _from_token_file(root: Path) -> IbmCredentials | None:
    """Az IBM Cloud konzol által letöltött JSON-fájl beolvasása.

    Formátum::

        {"name": "...", "description": "...", "createdAt": "...", "apikey": "..."}

    Elfogadunk nyers, egysoros tokent is, ha a fájl nem JSON.
    """
    path = root / TOKEN_FILENAME
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # Nyers token egyetlen sorban.
        return IbmCredentials(
            token=text.splitlines()[0].strip(),
            source=f"{TOKEN_FILENAME} (nyers szöveg)",
        )

    if not isinstance(payload, dict):
        raise CredentialsNotFoundError(
            f"a(z) {TOKEN_FILENAME} JSON-tartalma nem objektum, hanem "
            f"{type(payload).__name__}"
        )

    for key in ("apikey", "api_key", "token"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return IbmCredentials(
                token=value.strip(),
                instance=(payload.get("crn") or payload.get("instance") or None),
                source=f"{TOKEN_FILENAME} (JSON, '{key}' kulcs)",
            )

    raise CredentialsNotFoundError(
        f"a(z) {TOKEN_FILENAME} JSON-ja nem tartalmaz 'apikey', 'api_key' vagy "
        f"'token' kulcsot. Megtalált kulcsok: {sorted(payload)}"
    )


def load_ibm_credentials(root: Path | None = None) -> IbmCredentials:
    """IBM-hitelesítő adatok betöltése a dokumentált prioritási sorrendben.

    Args:
        root: A repó gyökere; ``None`` esetén az aktuális munkakönyvtár.

    Returns:
        Az :class:`IbmCredentials`.

    Raises:
        CredentialsNotFoundError: Ha egyik forrásban sincs használható token.
            A hibaüzenet felsorolja a megvizsgált helyeket, de **titkot nem
            tartalmaz**.
    """
    base = Path.cwd() if root is None else Path(root)
    for loader in (_from_environment, lambda: _from_env_file(base), lambda: _from_token_file(base)):
        credentials = loader()
        if credentials is not None:
            return credentials

    raise CredentialsNotFoundError(
        "nem található IBM-hitelesítő adat. Megvizsgált források: "
        f"(1) {_ENV_TOKEN} környezeti változó, "
        f"(2) {base / ENV_FILENAME}, "
        f"(3) {base / TOKEN_FILENAME}. "
        f"Másold a mintát: cp .env.example .env — vagy helyezd el az IBM Cloud "
        f"konzolból letöltött {TOKEN_FILENAME} fájlt a repó gyökerébe."
    )
