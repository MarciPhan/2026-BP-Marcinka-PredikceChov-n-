# Monitoring systému

Průvodce sledováním stavu Metricord instance - Redis, bot procesy a webový dashboard.

## Rychlá diagnostika

Spusťte tyto příkazy pro ověření stavu:

```bash
# Redis dostupnost
redis-cli ping
# Očekávaná odpověď: PONG

# Bot heartbeat (UNIX timestamp poslední aktivity)
redis-cli GET bot:heartbeat
# Pokud je starší než 120 sekund, bot neběží.

# Spotřeba paměti
redis-cli INFO memory | grep used_memory_human

# Počet klíčů v databázi
redis-cli DBSIZE
```

## Klíčové metriky

| Metrika | Zdravý rozsah | Kritická hodnota |
| :--- | :--- | :--- |
| Redis Uptime | > 7 dní | < 1 hodina (opakované restarty) |
| Paměť | < 75 % RAM | > 90 % RAM |
| OPS/sec | 100–5 000 | > 10 000 |
| Bot Heartbeat | < 120 s | > 300 s (bot spadl) |
| Connected Clients | 2–5 | > 20 (únik spojení) |

## Služby v produkci

| Proces | Port | Funkce | Health Check |
| :--- | :--- | :--- | :--- |
| `redis` | 6379 | In-memory databáze | `redis-cli ping` |
| `discord-bot-primary` | - | Sběr událostí, příkazy | `bot:heartbeat` v Redis |
| `discord-bot-dashboard` | - | Lite Mode, dashboard sync | `bot:heartbeat:lite` |
| `web-dashboard` | 8092 | FastAPI backend | `curl localhost:8092/health` |

## Kontrola Docker kontejnerů

```bash
# Stav všech služeb
docker-compose ps

# Logy konkrétní služby (poslední 100 řádků)
docker-compose logs --tail=100 discord-bot-primary

# Restart jedné služby
docker-compose restart web-dashboard
```

## Automatický health check

Skript pro kontrolu heartbeatu (`/opt/metricord/check_health.sh`):

```bash
#!/bin/bash
HEARTBEAT=$(redis-cli GET bot:heartbeat)
NOW=$(date +%s)
DIFF=$((NOW - HEARTBEAT))

if [ "$DIFF" -gt 300 ]; then
  echo "[ALERT] Bot heartbeat is ${DIFF}s old - restarting..."
  docker-compose restart discord-bot-primary
fi
```

Přidání do crontabu:
```bash
*/5 * * * * /opt/metricord/check_health.sh >> /var/log/metricord-health.log 2>&1
```

## Interpretace `redis-cli INFO`

| Sekce | Důležité hodnoty |
| :--- | :--- |
| `memory` | `used_memory_human`, `mem_fragmentation_ratio` (ideálně 1,0–1,5) |
| `stats` | `total_commands_processed`, `instantaneous_ops_per_sec` |
| `keyspace` | `db0:keys=N` - celkový počet klíčů |
| `replication` | `role:master` nebo `role:slave` |

::: warning Fragmentace paměti
Pokud `mem_fragmentation_ratio` přesáhne 1,5, Redis spotřebovává více RAM než je nutné. Zapněte `activedefrag yes` v `redis.conf` nebo naplánujte restart.
:::
