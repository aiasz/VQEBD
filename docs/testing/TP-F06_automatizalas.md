# TP-F06 — Fázis 6 tesztterv (automatizálás, hibatárolás, ütemezés)

| | |
|---|---|
| **Azonosító** | TP-F06 |
| **Dokumentum-verzió** | 1.0.0 |
| **Dátum** | 2026-11-02 |
| **Fázis** | 6 — Automatizálás, strukturált hibatárolás, újrapróbálkozás |
| **Terv** | [`phase_06.md`](../plan/phase_06.md) |
| **Döntés** | [`ADR-0008`](../adr/ADR-0008-hibakezeles-es-utemezes.md) |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |

---

## 1. Mit kell igazolni

1. **A hiba nem vész el:** minden sikertelen próbálkozás sorként tárolódik, és a
   folyamat összeomlása után is megvan.
2. **Az újrapróbálkozás korlátos és biztonságos:** csak átmeneti hibát próbál újra,
   a korlát újraindítás után is érvényes, hardveren 1 próbálkozás.
3. **Az ütemezett működés nem fogyaszthat kvótát és nem szivárogtathat titkot.**

## 2. Tesztesetek

| Eset | AC | Ellenőrzés | Fájl |
|---|---|---|---|
| **TC-601** | AC-6.1 | Hibás futás (érvénytelen aktív tér) sorként tárolódik (típus, osztály, próbálkozás, üzenet); a batch folytatódik; az export `failed` listája is tartalmazza | `tests/integration/test_pipeline.py` |
| **TC-602** | AC-6.2 | Az osztályozás táblázata: kvóta, átmeneti (hálózat, idő, HTTP 429/5xx), tartós (HTTP 4xx, `InvalidAccountError`, belső hibák); ismeretlen = `permanent`; a státuszkód az osztálynevet felülírja. A visszalépés a képlet és a felső korlát szerinti | `tests/unit/test_pipeline_errors.py`, `tests/unit/test_retry.py` |
| **TC-603** | AC-6.3 | Tartós és kvótahiba nem újrapróbált; átmeneti hiba legfeljebb `max_attempts`-szor, a várakozások `[5, 10]` s (injektált alvással) | `tests/unit/test_retry.py` |
| **TC-604** | AC-6.4 | A próbálkozásszám újraindítás után is érvényes; a feladott futást a pipeline kihagyja (nem jön új hibasor); `--retry-abandoned` megbocsát, a történet megmarad | `tests/unit/test_retry.py`, `tests/integration/test_pipeline.py` |
| **TC-605** | AC-6.5 | Hardveres futás 1 próbálkozás; a `hardware_evaluation_budget` a végső becsléseket és a ZNE-szorzókat számolja; a batch szintű kapu a teljes batchre, +20% tartalékkal kérdez; engedély nélkül nincs hálózati hívás | `tests/integration/test_pipeline.py`, `tests/unit/test_hardware_guard.py` |
| **TC-606** | AC-6.6 | Dry run: `f5-smoke` végigfut, 0 kilépési kód, napló és export; a második indítás mind az 5 futást kihagyja | `tests/integration/test_pipeline.py` + konténeres futtatás |
| **TC-607** | AC-6.7 | Hibainjektálás: a pipeline nem omlik össze, kilépési kód 1, naplózott `partial` összegzés | `tests/integration/test_pipeline.py` |
| **TC-608** | AC-6.8 | A token és a CRN a hibaüzenetből sem az adatbázisba, sem a naplóba, sem a jelentésbe, sem az exportba nem jut | `tests/unit/test_retry.py`, `tests/integration/test_pipeline.py`, `tests/unit/test_pipeline_errors.py` |
| **TC-609** | AC-6.9 | v2 → v3 migráció: a v2 rekord bitre változatlan; második megnyitás nem migrál újra; friss és migrált séma azonos (`results` és `run_failures`) | `tests/unit/test_storage_v3.py`, `tests/unit/test_storage.py` |
| **TC-610** | AC-6.10 | Zár: kizárólagos birtoklás, elavulás a határon, sérült zár, idegen zár nem törlődik; az ütemezési hurok injektált órával, kivételnél is elengedi a zárat | `tests/unit/test_scheduler.py` |
| **TC-611** | AC-6.11 | A `scheduler` szolgáltatás érvényes, titok és `--allow-hardware` nélkül; `--allow-hardware` + `--every` elutasított; hardveres batch engedély nélkül elutasított | `tests/unit/test_scheduler.py`, `tests/integration/test_pipeline.py` + `docker compose config` |

## 3. Negatív és robusztussági ellenőrzések

- `RetryPolicy` érvénytelen paraméterekkel (0 próbálkozás, negatív várakozás, `factor < 1`,
  `max_delay < base_delay`): `ValueError`.
- Érvénytelen intervallum (`""`, `"6"`, `"-1h"`, `"0s"`, `"1 hour"`): `ValueError`, a CLI-n
  használati hiba (2-es kilépési kód).
- Ismeretlen preset, hiányzó preset és spec: végzetes (2), a kivétel nem jut a hívóig.
- `KeyboardInterrupt` nem kerül elnyelésre; a zár ilyenkor sem marad.
- Érvénytelen `error_class` a séma `CHECK` megszorításán elbukik.
- 2000 karakternél hosszabb hibaüzenet csonkolt.
- `forgive_failures` pontosan egy kiválasztót fogad.
- Csak olvasható adatbázis lekérdezheti a hibákat.
- Titok nélküli környezet: `known_secrets()` üres, nem kivétel.

## 4. Keresztvalidációk

| Mit | Mivel | Várt |
|---|---|---|
| Pipeline eredménye | a Fázis 5 `run_batch` | `run_id`, energia, `config_hash`, paraméterek bitre azonosak |
| Export formátuma | a Fázis 5 `f5_*.json` | azonos kulcsok és sorrend |
| Migrált v3 | friss v3 adatbázis | azonos oszlopok (sorrenddel, típussal) |
| Konténeres futás | helyi futás | azonos kilépési kód, naplólépések, a volume-jogosultság rendben |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
