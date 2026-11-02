# TP-F08 — Fázis 8 tesztterv (konténeres rendszer, a dashboard egyparancsos indítása)

| | |
|---|---|
| **Azonosító** | TP-F08 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 8 — Konténerizáció összeszerelése |
| **Terv** | [`phase_08.md`](../plan/phase_08.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Mit kell igazolni

1. **Egyparancsos indítás tiszta klónból:** `git clone` + `docker compose up -d dashboard` után a dashboard elérhető.
2. **Biztonságos alapbeállítás:** a port csak a hurokcímre kötött, a szolgáltatás nem kap titkot és hardvert, a
   kód- és export-mountok csak olvashatók.
3. **A dashboard a konténerben is látja az adatot** (az ütemező adatbázisát és a verziózott exportokat).

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl / mód |
|---|---|---|---|
| **TC-801** | AC-8.1 | minden szolgáltatás az aktuális `VERSION`-címkét használja; a három szolgáltatás létezik; `docker compose config` érvényes | `tests/repo/test_compose.py`, végrehajtás |
| **TC-802** | AC-8.2 | tiszta klónból `up -d dashboard`: `healthy`, `/_stcore/health` = `ok`, főoldal HTTP 200 | végrehajtás |
| **TC-803** | AC-8.3 | a klónból, `--no-cache` építéssel készült image `pip freeze`-e a lockkal 0 eltérés | végrehajtás |
| **TC-804** | AC-8.4 | a közzétett port minden bejegyzése `127.0.0.1:`-gyel kezdődik; `docker port` | `tests/repo/test_compose.py`, végrehajtás |
| **TC-805** | AC-8.5 | a dashboard-blokk nem tartalmaz `env_file`, `token`, `ibm_quantum`, `allow_hardware`, `.env` szót | `tests/repo/test_compose.py` |
| **TC-806** | AC-8.6 | a konténerben a felderítés 4 forrást talál; az alapnézet és a három további nézet kivétel nélkül fut | végrehajtás (konténeren belüli `AppTest`) |
| **TC-807** | AC-8.7 | a `/app/src`, `/app/dashboard`, `/app/docs/figures/data` írási kísérlete elbukik | végrehajtás |
| **TC-808** | AC-8.8 | `docker compose down` után a `vqebd-data` volume megvan | végrehajtás |
| **TC-809** | AC-8.9 | `make dashboard`, `dashboard-stop`, `dashboard-logs` léteznek és `up -d --build dashboard`-ot hívnak; healthcheck, mountok, belépési pont, a Dockerfile a `dashboard/`-t másolja | `tests/repo/test_compose.py` |

## 3. Negatív és robusztussági ellenőrzések

- A `0.0.0.0`-ra kötött port (a tesztben a közzétett port nem kezdődik `127.0.0.1:`-gyel) elbukik a TC-804-en.
- A tokent vagy `env_file`-t tartalmazó dashboard-blokk elbukik a TC-805-ön.
- A `scheduler` blokkja a dashboard-szakasztól elkülönítve vizsgált (a Fázis 6 tesztje nem keveredik).

## 4. Dokumentum-átvilágítás (AC-8.10)

A fázis része **minden README és dokumentum átvilágítása**: verziószámok, tesztszámok, fázis-állapotok, a
`Gyors indítás`, a dokumentumtáblák és az archív jegyzetek jelölése (TR-F08 3.).

## 5. Amit a terv nem fed

Másik gépen vagy tiszta VM-en végzett telepítés; Windows-specifikus útvonalkezelés (a fejlesztés Windowson, Docker
Desktoppal történt, de külön Windows-teszt nincs); hosszú távú (napokig tartó) futás.

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
