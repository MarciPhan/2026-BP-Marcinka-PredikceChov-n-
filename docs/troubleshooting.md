# Řešení potíží (Troubleshooting)

Tento průvodce vám pomůže identifikovat a vyřešit nejčastější problémy, se kterými se můžete při provozu CommunityMetrics setkat.

## Rychlá diagnostika

Před detailním zkoumáním chyb proveďte tyto základní prověrky:

```bash
# 1. Redis dostupnost
redis-cli ping
# Očekávaná odpověď: PONG

# 2. Heartbeat bota
redis-cli GET bot:heartbeat
# Pokud je timestamp starší než 120 sekund, bot neběží.

# 3. Paměť Redis
redis-cli INFO memory | grep used_memory_human

# 4. Dashboard dostupnost (aplikace nemá samostatný /health endpoint,
#    ověřte přímo hlavní stránku nebo OpenAPI schéma)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8093/
curl -s http://localhost:8093/api/openapi.json | head -c 100

# 5. Docker kontejnery (pokud používáte Docker)
docker-compose ps
```

## Problémy s instalací

### Bot se nespustí (chybí závislosti)

```bash
# Ověřte Python verzi
python3 --version  # Vyžaduje 3.11+

# Přeinstalujte závislosti
pip install -r requirements.txt

# Ověřte PYTHONPATH
export PYTHONPATH=$PWD
python3 bot/main.py
```

### Redis se nepřipojí

| Příčina | Řešení |
| :--- | :--- |
| Redis neběží | `redis-server --daemonize yes` nebo `systemctl start redis` |
| Špatná URL | Ověřte `REDIS_URL` v `.env` (výchozí: `redis://localhost:6379/0`) |
| Blokovaný port | `lsof -i :6379` — ověřte, kdo port používá |
| Docker síť | Ověřte, že síť `botnet` existuje: `docker network ls` |

### Port 8093 je obsazený

```bash
# Zjistěte, co port používá
lsof -i :8093

# Ukončete proces
lsof -t -i :8093 | xargs kill -9

# Nebo změňte port v .env
# DASHBOARD_PORT=8093
```

## Problémy s botem

### 1. Bot je online, ale nereaguje na příkazy

- **Příčina:** Slash příkazy nejsou zaregistrovány nebo chybí oprávnění.
- **Řešení:**
  1. V Discord chatu napište `*sync` pro vynucenou synchronizaci příkazů.
  2. Ujistěte se, že bot má v kanálu oprávnění `Use Application Commands`.
  3. Ověřte, že jsou aktivní **Privileged Gateway Intents** v Developer Portalu.
  4. Pokud nic nepomáhá, pozvěte bota znovu s oprávněním `Administrator`.

### 2. Bot spadne po spuštění

Zkontrolujte logy:

```bash
# Lokální spuštění
tail -f bot.log

# Docker
docker-compose logs --tail=100 discord-bot-primary
```

| Chybová zpráva | Příčina | Řešení |
| :--- | :--- | :--- |
| `LoginFailure: Improper token` | Neplatný `BOT_TOKEN` | Vygenerujte nový token v Developer Portalu |
| `PrivilegedIntentsRequired` | Chybí Intents | Zapněte všechna 3 Privileged Intents |
| `ConnectionRefusedError` | Redis neběží | Spusťte Redis server |

### 3. XP se nepřidělují

- Ověřte, že **Message Content Intent** je zapnutý.
- Zkontrolujte cooldown (výchozí 60 s) — uživatel nemusí získat XP za každou zprávu.

## Problémy s dashboardem

### 1. Grafy v dashboardu jsou prázdné

- **Příčina:** Nedostatek nasbíraných dat nebo špatně nastavené časové pásmo.
- **Řešení:**
  1. Ověřte, že bot vidí zprávy v kanálech (vyžaduje `View Channels` a `Read Message History`).
  2. Spusťte backfill: `/activity backfill days:30`.
  3. Počkejte alespoň 1 hodinu na první agregované heatmapy.

### 2. Chyba „Invalid Redirect URI" při přihlášení

1. Otevřete [Discord Developer Portal](https://discord.com/developers/applications).
2. V sekci **OAuth2 → Redirects** přidejte přesnou URL z `.env`:
   - Lokální: `http://localhost:8093/auth/callback`
   - Produkce: `https://vase-domena.com/auth/callback`

> [!WARNING]
> URL musí přesně odpovídat — včetně protokolu (`http` vs `https`), portu a cesty.

### 3. Dashboard vrací 500 Internal Server Error

```bash
# Zkontrolujte logy
docker-compose logs --tail=50 web-dashboard

# Nejčastější příčiny:
# - Chybí DASHBOARD_SECRET_KEY v .env
# - Redis není dostupný
# - Chybí DISCORD_CLIENT_SECRET
```

## Problémy s predikcemi

### Predikce (Markov, Kaplan-Meier) se nezobrazují

- **Příčina:** Model nemá dostatek historických dat. Markovova predikce vyžaduje alespoň 5 pozorovaných přechodů mezi stavy; Kaplan-Meierova křivka se počítá až při dostupné historii aktivity alespoň 30 dní. Pokud podmínka není splněná, aplikace odhad záměrně nezobrazí (místo aby dopočítala nespolehlivý výsledek) — nejde o chybu.
- **Řešení:**
  1. Nechte bota běžet déle (ideálně 30+ dní pro Kaplan-Meier).
  2. Zkontrolujte, zda nedošlo k výpadku sběru dat v minulosti.
  3. Spusťte backfill pro doplnění chybějících dat.

## Časté chyby v logu

Aplikace v současné verzi negeneruje formální chybové kódy (`ERR_*`) — chyby se logují jako běžné Python výjimky. Nejčastější příčiny podle textu chybové hlášky:

| Text v logu / chování | Příčina | Doporučená akce |
| :--- | :--- | :--- |
| `redis.exceptions.ConnectionError` | Nelze se připojit k Redis databázi. | Prověřte `REDIS_URL` a dostupnost portu 6379. |
| HTTP 429 od Discordu | Narazili jste na Discord rate limit. | Snižte frekvenci backfillu nebo omezte počet kanálů. |
| Predikce se nezobrazí, žádná chyba v konzoli | Nedostatek dat pro Markov/Kaplan-Meier (viz výše). | Počkejte na více dat nebo spusťte backfill. |
| `discord.errors.LoginFailure` / chyba OAuth2 přihlášení | Neplatný `BOT_TOKEN`, `DISCORD_CLIENT_SECRET` nebo Redirect URI. | Ověřte hodnoty v `.env` a nastavení v Discord Developer Portalu. |

## Diagnostika Docker prostředí

```bash
# Stav všech kontejnerů
docker-compose ps

# Logy konkrétní služby
docker-compose logs --tail=200 discord-bot-primary
docker-compose logs --tail=200 web-dashboard

# Restart jedné služby
docker-compose restart discord-bot-primary

# Kompletní rebuild
docker-compose down
docker-compose up -d --build

# Vstup do kontejneru
docker exec -it discord-bot-primary /bin/bash
```

::: tip Podpora
Pokud problém přetrvává, nahlédněte do logů (`docker-compose logs --tail=100`) a pošlete výstup na náš [Support Server](https://discord.gg/35yeT32Knf).
:::
