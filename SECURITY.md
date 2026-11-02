# Biztonsági irányelvek / Security Policy

## Támogatott verziók

A projekt a `1.x` ágat támogatja (a legutóbbi kiadás). Régebbi, `0.x` verziókra biztonsági javítást nem adunk.

## Sebezhetőség jelentése

**Ne nyiss nyilvános issue-t** biztonsági problémához. Jelentsd az alábbi módok egyikén:

1. a GitHub **Security → Report a vulnerability** (privát sebezhetőség-jelentés) funkcióján keresztül, ha elérhető; vagy
2. e-mailben: **kormosa@gmail.com**, tárgy: `VQEBD security`.

Kérjük, add meg: az érintett verziót (`VERSION`), a lépéseket a reprodukáláshoz és a várt/tényleges viselkedést.
A projektet kis csapat tartja karban, ezért határidőt nem vállalunk; igyekszünk mielőbb visszajelezni, és a javítás
ütemét egyeztetni.

*Please do not open a public issue for a security problem. Use GitHub's private vulnerability reporting, or e-mail the
address above with the subject `VQEBD security`. The project is maintained by a small team, so we cannot promise a
response time, but we will reply as soon as we can.*

## Mi tartozik ide

A projekt kritikus biztonsági felülete az **IBM Quantum API-token** kezelése:

- A token **soha nem kerülhet** naplóba, kivételüzenetbe, `repr()`-be, eredményrekordba, hibatáblába vagy exportba.
  A betöltés és a titoktalanítás: `src/vqebd/credentials.py`, `src/vqebd/pipeline/errors.py` (ADR-0008).
- A token csak környezeti változóból (`IBM_QUANTUM_TOKEN`) vagy a gitignore-olt `IBM.token` / `.env` fájlból jöhet.
  A forrásfájlokat a `.gitignore` és a `.dockerignore` kizárja; ezt teszt őrzi (`tests/repo/test_secrets_hygiene.py`).
- **Ha véletlenül tokent commitoltál vagy tettél közzé:** azonnal **vond vissza** az IBM Cloud konzolon (IAM → API keys),
  és csak utána tisztítsd a történetet.

Ugyancsak ide tartozik:

- a **dashboard hitelesítés nélküli**; a Compose-beállítás ezért csak a gazdagép hurokcímére (`127.0.0.1`) köti a portot
  (`docs/08_deployment.md` 6.). Hitelesítés nélküli, nyilvános kitettség **nem támogatott** konfiguráció;
- a **valódi QPU használata** kvótát fogyaszt: az ütemező sosem indít hardvert, a kézi futtatás két kulcsot igényel
  (`--allow-hardware` és `VQEBD_ALLOW_HARDWARE=true`).

## Mi nem tartozik ide

Harmadik felek csomagjainak (Qiskit, Streamlit, …) sebezhetősége: azt a saját projektjüknél jelentsd. Ha az általunk
rögzített verzió érintett, jelezd nekünk is, hogy a lockot frissíthessük.
