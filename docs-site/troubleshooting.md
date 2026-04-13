# Řešení potíží (Troubleshooting)

Systematický průvodce diagnostikou a opravou nejčastějších problémů s Metricord botem a dashboardem.

## Rychlá diagnostika

Spusťte tyto příkazy v terminálu pro základní prověření stavu:

```bash
# 1. Je Redis funkční?
redis-cli ping  # Očekávaná odpověď: PONG

# 2. Žije bot?
redis-cli GET bot:heartbeat  # unix timestamp (pokud > 120s starý -> bot spadl)

# 3. Kolik paměti Redis zabírá?
redis-cli INFO memory | grep used_memory_human

# 4. Běží procesy? (Docker)
docker-compose ps
```

## 1. Problémy s botem

| Chybová hláška | Příčina | Řešení |
| :--- | :--- | :--- |
| `LoginFailure` | Neplatný `BOT_TOKEN` | Vygenerujte nový token v Discord Portalu. |
| `PrivilegedIntentsRequired` | Chybí Intents | Zapněte Presence, Members a Message Content v Portalu. |
| `Error 113: No route to host` | Redis nedostupný | Zkontrolujte, zda Redis běží (docker-compose up). |

### Bot nereaguje na příkazy
1. Zkontrolujte, zda je bot online na serveru.
2. Spusťte `*sync` (prefix příkaz) pro synchronizaci slash příkazů.
3. Ověřte oprávnění bota: `View Channel`, `Send Messages`, `Use Slash Commands`.
4. Podívejte se do logů: `tail -20 bot.log`.

## 2. Problémy s dashboardem

### „Unauthorized" nebo „Invalid Redirect URI"
- **Session vypršela:** Vymažte cookies nebo zkuste Incognito režim.
- **Redirect URI nesedí:** V Discord Portalu (OAuth2) přidejte: `http://localhost:8092/auth/callback`.
- **Client Secret:** Ověřte `DISCORD_CLIENT_SECRET` v `.env`.

### Grafy jsou prázdné
- Počkejte 15–30 minut od přidání bota.
- Spusťte backfill pro historická data: `/activity backfill days:30`.
- Ověřte, že bot vidí kanály (oprávnění).

## 3. Chybové kódy

| Kód | Význam | Akce |
| :--- | :--- | :--- |
| `ERR_REDIS_CONN` | Chyba připojení k DB. | Je Redis spuštěný? Prověřte `REDIS_URL`. |
| `ERR_DISCORD_403` | Chybějící oprávnění. | Pozvěte bota znovu jako Administrator. |
| `ERR_DQS_LOW` | Málo dat pro predikci. | Sbírejte data déle nebo spusťte backfill. |
| `ERR_OAUTH_MISMATCH` | OAuth2 URI nesouhlasí. | Upravte Redirect URI v Discord Portalu. |

::: danger Stále nefunguje?
Zkontrolujte logy: `tail -100 bot.log web.log`. Výstup pošlete na náš [Support Server](https://discord.gg/metricord).
:::
