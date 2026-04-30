# Architektura dat v databázi Redis

Metricord využívá Redis jako primární in-memory úložiště pro extrémní výkon analytiky. Tento dokument slouží jako technická reference pro správu datových struktur a optimalizaci paměti.

::: tip Konvence pojmenování
Všechny klíče definuj v centrálním souboru `shared/keys.py`. Dodržuj formát:
`{kategorie}:{subtyp}:{guild_id}:{identifikátor}`
:::

## Přehled datových struktur

### Analytické události (Time-Series)
Pro ukládání historických událostí využíváme **Sorted Sets**. Skóre prvku odpovídá UNIX timestampu události.

| Klíč (Pattern) | Datový typ | Význam dat |
| :--- | :--- | :--- |
| `events:msg:{gid}:{uid}` | Sorted Set | Metadata zpráv (hodnota = délka zprávy). |
| `events:voice:{gid}:{uid}` | Sorted Set | Voice sezení (hodnota = délka v sekundách). |
| `events:action:{gid}:{uid}` | Sorted Set | Moderátorské akce (hodnota = kód akce). |

### Agregované statistiky a HLL
Pro výpočet unikátních uživatelů a heatmap využíváme efektivní agregátory.

| Klíč (Pattern) | Datový typ | Účel |
| :--- | :--- | :--- |
| `hll:dau:{gid}:{date}` | HyperLogLog | Unikátní aktivita za den (fixních 12 KB). |
| `stats:hourly:{gid}:{date}` | Hash | Počet zpráv v každé hodině dne ("0"–"23"). |
| `stats:heatmap:{gid}` | Hash | Matice aktivity pro dashboard ("den:hodina"). |
| `stats:msglen:{gid}` | Hash | Distribuce délky zpráv do bucketů. |

### Runtime stav bota
Dynamické klíče pro sledování "zdraví" systému a přítomnosti na serverech.

| Klíč (Pattern) | Datový typ | TTL | Popis |
| :--- | :--- | :--- | :--- |
| `bot:heartbeat` | String | 60 s | Timestamp posledního cyklu bota. |
| `bot:guilds` | Set | - | Seznam ID všech serverů, kde bot běží. |
| `presence:online:{gid}` | String | 300 s | Počet aktuálně připojených členů. |

## Životnost dat (Retention Policy)

Aby nedošlo k přeplnění operační paměti (RAM), Metricord uplatňuje automatickou expiraci dat (TTL).

| Kategorie | Retence | Odůvodnění |
| :--- | :--- | :--- |
| **Surové eventy** | 30 dní | Nutné pro výpočet MAU a predikci odchodu (Churn). |
| **HLL Statistiky** | 90 dní | Pro dlouhodobý pohled na unikátní uživatele. |
| **Uživatelská cache** | 7 dní | Cachování jmen a avatarů z Discord API. |
| **Runtime status** | 60–300 s | Kritická data pro monitorování stavu bota. |

## Strategie paměťové optimalizace

Při vývoji jsme dbali na minimální "footprint" v paměti RAM:

1.  **Využití Redis Hashes:** Namísto tisíců samostatných String klíčů používáme Hashe. Redis interně optimalizuje Hashe pomocí `ziplist`, což snižuje režii paměti až o 80 %.
2.  **HyperLogLog (HLL):** Tato struktura nám umožňuje odhadnout miliony unikátních uživatelů s pevnou spotřebou **12 KB**, namísto megabajtů u klasických setů.
3.  **Pipelining:** Bot odesílá data k zápisu v batchích (pipelinách), což dramaticky snižuje zátěž sítě a procesoru.

> [!WARNING]
> Při manuální správě databáze nikdy nepoužívejte příkaz `KEYS *` v produkčním prostředí. Mohlo by dojít k zablokování Redis vlákna. Vždy využívejte příkaz `SCAN`.

## Diagnostika klíčů z CLI

```bash
# Vyhledání všech klíčů konkrétního serveru
redis-cli SCAN 0 MATCH "*:{guild_id}*" COUNT 100

# Zjištění paměťové náročnosti konkrétního uživatele
redis-cli MEMORY USAGE "events:msg:{guild_id}:{user_id}"

# Kontrola aktuálního počtu členů v DAU
redis-cli PFCOUNT "hll:dau:{guild_id}:{yyyymmdd}"
```
