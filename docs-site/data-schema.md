# Redis Datové schéma (Kompletní referenční mapa)

Metricord využívá Redis jako primární databázi pro in-memory analytiku. Tato stránka dokumentuje všechny klíče definované v `shared/keys.py` a runtime klíče vytvářené botem.

::: info Konvence pojmenování klíčů
Formát: `{kategorie}:{subtyp}:{guild_id}:{identifikátor}`. Všechny klíče jsou definovány centrálně v `shared/keys.py`. Nikdy nepoužívejte hardcoded klíče v kódu.
:::

## 1. Analytické eventy (Time-Series)

Data jednotlivých uživatelů jako **Sorted Sets** (score = UNIX timestamp).

| Klíč (Pattern) | Typ | Popis | Funkce v `keys.py` |
| :--- | :--- | :--- | :--- |
| `events:msg:{gid}:{uid}` | Sorted Set | Metadata zpráv uživatele (délka, kanál). | `K_EVENTS_MSG()` |
| `events:voice:{gid}:{uid}` | Sorted Set | Voice sezení (start/end, délka). | `K_EVENTS_VOICE()` |
| `events:action:{gid}:{uid}` | Sorted Set | Moderátorské akce (ban, kick, atd.). | `K_EVENTS_ACTION()` |

## 2. Agregované statistiky

| Klíč (Pattern) | Typ | Popis | Funkce v `keys.py` |
| :--- | :--- | :--- | :--- |
| `hll:dau:{gid}:{YYYYMMDD}` | HyperLogLog | Unikátní aktivní uživatelé za den. (~12 KB). | `K_DAU()` |
| `stats:hourly:{gid}:{YYYYMMDD}` | Hash | Počet zpráv za každou hodinu ("0"–"23"). | `K_HOURLY()` |
| `stats:heatmap:{gid}` | Hash | Aktivita po dnech a hodinách ("0:14"). | `K_HEATMAP()` |
| `stats:msglen:{gid}` | Hash | Distribuce délky zpráv (buckety). | `K_MSGLEN()` |
| `stats:total_msgs:{gid}` | String | Kumulativní celkový počet zpráv. | `K_TOTAL_MSGS()` |

## 3. Uživatelská data

| Klíč (Pattern) | Typ | TTL | Popis | Funkce v `keys.py` |
| :--- | :--- | :--- | :--- | :--- |
| `user:info:{uid}` | Hash | 7 dní | Cached: `name`, `avatar`, `roles`. | `K_USER_INFO()` |

## 4. Runtime klíče (bot/main.py)

Tyto klíče nejsou v `keys.py`, ale zapisuje je bot přímo:

| Klíč (Pattern) | Typ | Popis |
| :--- | :--- | :--- |
| `bot:heartbeat` | String | UNIX timestamp posledního heartbeatu. |
| `bot:guilds` | Set | ID všech serverů, kde je bot přítomen. |
| `presence:online:{gid}` | String | Aktuálně online členové (aktualizováno každých 10s). |
| `guild:verification_level:{gid}` | String | Úroveň verifikace serveru pro Security Score. |

## 5. Diagnostické příkazy

```bash
# Zobrazit všechny klíče pro guild
redis-cli SCAN 0 MATCH "*:{guild_id}*" COUNT 100

# Počet členů v DAU HLL
redis-cli PFCOUNT "hll:dau:{guild_id}:{yyyymmdd}"

# Počet zpráv uživatele
redis-cli ZCARD "events:msg:{guild_id}:{user_id}"

# Paměťová náročnost klíče
redis-cli MEMORY USAGE "events:msg:{guild_id}:{user_id}"
```

::: warning Výkon
Při přímém přístupu k Redisu doporučujeme `SCAN` místo `KEYS`, aby nedošlo k blokování databáze při velkém objemu dat.
:::
