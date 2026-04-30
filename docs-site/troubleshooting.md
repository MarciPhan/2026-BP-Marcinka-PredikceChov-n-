# Řešení potíží (Troubleshooting)

Tento průvodce vám pomůže identifikovat a vyřešit nejčastější problémy, se kterými se můžete při provozu Metricord setkat.

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

# 4. Dashboard dostupnost
curl -s http://localhost:8092/health

# 5. Docker kontejnery (pokud používáte Docker)
docker-compose ps
```

## Problémy s instalací

### Bot se nespustí (chybí závislosti)

```bash
# Ověřte Python verzi
python3 --version  # Vyžaduje 3.9+

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

### Port 8092 je obsazený

```bash
# Zjistěte, co port používá
lsof -i :8092

# Ukončete proces
lsof -t -i :8092 | xargs kill -9

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
- Ověřte váhy: `redis-cli HGETALL config:xp:weights`

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
   - Lokální: `http://localhost:8092/auth/callback`
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

### Prediktivní modely nefungují (DQS < 0.5)

- **Příčina:** Model nemá dostatek historických dat pro sestavení matice přechodu.
- **Řešení:**
  1. Nechte bota běžet alespoň 7 dní.
  2. Zkontrolujte, zda nedošlo k výpadku sběru dat v minulosti.
  3. Spusťte backfill pro doplnění chybějících dat.

### Matice přechodu je singulární (ERR_ML_MATRIX)

- **Příčina:** Příliš málo uživatelů nebo příliš krátká historie.
- **Řešení:** Prodlužte časový rozsah analýzy nebo počkejte na více dat.

## Chybové kódy v logu

| Kód | Význam | Doporučená akce |
| :--- | :--- | :--- |
| `ERR_REDIS_CONN` | Nelze se připojit k Redis databázi. | Prověřte `REDIS_URL` a dostupnost portu 6379. |
| `ERR_DISCORD_429` | Narazili jste na Discord rate limit. | Snižte frekvenci backfillu nebo omezte počet kanálů. |
| `ERR_ML_MATRIX` | Matice přechodu je singulární. | Nedostatek uživatelů — zkuste delší časový rozsah. |
| `ERR_OAUTH_FAIL` | OAuth2 selhala. | Ověřte `DISCORD_CLIENT_SECRET` a Redirect URI. |
| `ERR_SMTP_FAIL` | Nelze odeslat OTP e-mail. | Ověřte SMTP údaje v `.env`. |

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
Pokud problém přetrvává, nahlédněte do logů (`docker-compose logs --tail=100`) a pošlete výstup na náš [Support Server](https://discord.gg/metricord).
:::
