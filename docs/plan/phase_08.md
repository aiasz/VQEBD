# Fázis 8 — Konténerizáció összeszerelése: a dashboard egyparancsos indítása

| | |
|---|---|
| **Fázis** | 8 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Státusz** | **Megvalósítva és lezárva (2026-11-02)** — mind a 10 elfogadási kritérium teljesült: [`TR-F08`](../testing/TR-F08_konteneres_rendszer.md) |
| **Célverzió** | `v0.11.0` |
| **Előzmény** | [`phase_07.md`](phase_07.md), [`00_master_plan.md`](00_master_plan.md) 7. fejezet, v0.10.0 |
| **Új ADR** | nincs; a döntések a 5. fejezetben vannak (nem architektúra-szintűek) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Miért most, és mi a szűkített hatókör

Az alapterv Fázis 8-ja: „minden korábbi darab egyetlen `docker-compose` rendszerben, egymástól elszigetelt
szolgáltatásokként”, tiszta gépen `git clone` + `docker compose up` után elérhető a dashboard.

A felhasználó döntése (2026-11-02): **a dashboard a saját gépén, konténerben fusson**; távoli host nincs. Ezért a
fázis hatóköre a **tényleges szükséglet**: a `dashboard` szolgáltatás a már meglévő `app` és `scheduler` mellé,
biztonságos alapbeállításokkal, egyparancsos indítással, és annak igazolása, hogy ez egy **tiszta klónból** is
működik. Külön `db` szolgáltatás (valódi adatbázis-szerver) **nem** készül: az SQLite a mért igényt fedezi.

---

## 2. Előzetes mérés (2026-11-02, `vqebd:0.10.0`)

| # | Kérdés | Mérés | Következmény |
|---|---|---|---|
| M1 | Mennyi erőforrást kér a dashboard? | Üresjáratban **~65 MiB RAM**, 0.6–4% CPU; egy munkamenet csúcsa (3 nézet, 180 soros adat) **~170 MB**; egy kattintás 0.05–0.2 s | Bármely hétköznapi gépen elfér; nem kell host |
| M2 | Mekkora az image? | **2.19 GB** (a kvantumstack miatt) | Az első build letöltés- és időigényes; a dashboardnak nem kell a teljes stack, de egy image egyszerűbb (D1) |
| M3 | Van-e hitelesítés? | **Nincs** (a Streamlit alapértelmezése) | A port csak a gazdagép hurokcímére (`127.0.0.1`) legyen kötve (D2) |
| M4 | Olvasható-e a WAL módú SQLite csak olvasható mountról? | Az SQLite-olvasónak a `-shm` fájlhoz írási jog kellhet | A `vqebd-data` volume **nem** `:ro`; a dashboard a kódban `read_only=True`-val nyit (D3) |
| M5 | Hol van az adat egy konténerben? | A `vqebd-data` volume `db/*.sqlite` (az ütemező írja) és a repó verziózott `docs/figures/data/*.json` exportjai | Mindkettőt a dashboard automatikusan felderíti; az exportokat csak olvasható mountként adjuk át |
| M6 | A Docker-build reprodukálható-e tiszta klónból? | Lásd az AC-8.3-at (a v0.10.0 lockbetartatása óta) | — |

---

## 3. Célkitűzések

| # | Cél | Szállítandó |
|---|---|---|
| G1 | `dashboard` Compose-szolgáltatás | `docker/docker-compose.yml`, healthcheck-kel |
| G2 | Egyparancsos indítás | `docker compose -f docker/docker-compose.yml up -d --build dashboard`, `make dashboard` |
| G3 | Biztonságos alapbeállítás | loopback-port, token és hardver nélkül, csak olvasó kód- és export-mount |
| G4 | Igazolás tiszta klónból | `git clone` + gyorsítótár nélküli build + indítás + adatfelderítés |
| G5 | Tesztek | `tests/repo/test_compose.py` (a Compose-fájl épsége) |
| G6 | Dokumentáció | `docs/08_deployment.md`, TP-F08, TR-F08, **az összes README és dokumentum átvilágítása** |

---

## 4. Architektúra

```
 gazdagép                          konténerek (vqebd:<VERSION>, egy image)
 ────────                          ─────────────────────────────────────────
 http://localhost:8501  ◄── 127.0.0.1:8501 ──  dashboard  (streamlit, csak olvas)
                                                  │  ▲
 repó: src/, dashboard/,  ── csak olvasható ──────┘  │ read_only SQLite
       docs/figures/data/                            │
                                  vqebd-data (volume) ◄── scheduler (ír: db/, logs/)
                                                     ◄── app (futtatáshoz)
```

- **Három szolgáltatás, egy image, közös `vqebd-data` volume.** A `scheduler` ír, a `dashboard` olvas, az `app`
  parancssori futtatáshoz van.
- A `dashboard` nem kap `env_file`-t, tokent és hardverengedélyt: sosem ér el hálózatot vagy QPU-t.

---

## 5. Döntések

| # | Döntés | Indok |
|---|---|---|
| D1 | **Egy image** mindhárom szolgáltatáshoz | egyszerűbb build és verziókezelés; a kisebb dashboard-image a 2.19 GB miatt későbbi optimalizáció |
| D2 | A port **`127.0.0.1:8501`**-re kötött, `VQEBD_DASHBOARD_PORT`-tal módosítható | nincs hitelesítés (M3); a hálózaton kívülről nem érhető el |
| D3 | A `vqebd-data` volume **nem `:ro`** | WAL módú SQLite (M4); az olvasásra nyitást a kód garantálja (`AC-7.9` teszt) |
| D4 | `restart: unless-stopped` | a `docker compose stop` leállítja, a Docker újraindulása után visszajön; kézzel, `stop`-pal kikapcsolható |
| D5 | Nincs külön `db` szolgáltatás | az SQLite a mért igényt fedezi (egy író, kevés olvasó) |

---

## 6. Elfogadási kritériumok

| # | Kritérium | Ellenőrzés |
|---|---|---|
| **AC-8.1** | A `docker compose config` a három szolgáltatást (`app`, `scheduler`, `dashboard`) érvényesnek jelzi, minden image-címke a `VERSION` | teszt + végrehajtás |
| **AC-8.2** | **Tiszta klónból** `docker compose up -d dashboard` után a konténer `healthy`, a `/_stcore/health` `ok`, a főoldal HTTP 200 | végrehajtás |
| **AC-8.3** | A tiszta klónból, **gyorsítótár nélkül** épített image `pip freeze`-e a lockkal 0 eltérést mutat | végrehajtás |
| **AC-8.4** | A közzétett port csak `127.0.0.1`-re kötött (`docker port`) | teszt + végrehajtás |
| **AC-8.5** | A dashboard-szolgáltatás nem tartalmaz tokent, `env_file`-t, hardverengedélyt | teszt |
| **AC-8.6** | A konténerben a dashboard felderíti és betölti az ütemező adatbázisát és a verziózott exportokat; mind a négy nézet kivétel nélkül fut | végrehajtás |
| **AC-8.7** | A kód- és export-mountok a konténerben csak olvashatók | végrehajtás |
| **AC-8.8** | Az adat a konténer eltávolítása után megmarad (`vqebd-data`) | végrehajtás |
| **AC-8.9** | `make dashboard`, `dashboard-stop`, `dashboard-logs`; a Compose-teszt (9) zöld | teszt |
| **AC-8.10** | `docs/08_deployment.md`, TP-F08, TR-F08, README (HU/EN) és **minden dokumentum átvilágítva**, `v0.11.0`; kapuk zöldek | végrehajtás |

---

## 7. Amit ez a fázis NEM tartalmaz

- Távoli host telepítése, reverse proxy, hitelesítés, TLS — a felhasználó helyben futtat; a követelményeket a
  `docs/08_deployment.md` 7. pontja írja le.
- Külön, kisebb dashboard-image és külön lock (D1).
- Valódi adatbázis-szerver (D5).
- Egy **másik gépen vagy tiszta VM-en** végzett telepítés: a tiszta klónt ugyanezen a gépen, gyorsítótár nélkül
  építettük (lásd TR-F08 5.).

---

## 8. Kilépési feltétel

AC-8.1 … AC-8.10 teljesül; TP-F08 és TR-F08 elkészült; minden README és dokumentum naprakész; `v0.11.0`;
minőségi kapuk (ruff, mypy strict, teljes tesztkészlet) zöldek.

---

## 9. Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-11-02 | Első változat; a felhasználó helyi-gépes döntése és az erőforrás-mérés (2. fejezet) alapján, megvalósítással együtt |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
