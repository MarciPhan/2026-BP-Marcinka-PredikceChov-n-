# Administrátorský průvodce (Instance Manager)

Průvodce pro správce, kteří provozují vlastní instanci Metricord — konfigurace, škálování, Redis údržba, monitoring a optimalizace výkonu.

## 1. Konfigurace prostředí (.env)

Kompletní přehled všech environmentálních proměnných:

| Proměnná | Povinná | Výchozí | Popis |
| :--- | :---: | :---: | :--- |
| `BOT_TOKEN` | Ano | — | Discord bot token z Developer Portalu. |
| `DISCORD_CLIENT_SECRET` | Ano | — | OAuth2 Client Secret pro dashboard přihlášení. |
| `DASHBOARD_PORT` | — | `8092` | Port pro web dashboard. |
| `DASHBOARD_SECRET_KEY` | Ano | — | Klíč pro podpis session cookies. |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Redis connection string. |
| `SMTP_PASSWORD` | — | — | Heslo pro SMTP (e-mailový OTP). |
| `BOT_LITE_MODE` | — | `0` | Nastavte na `1` pro sekundární bot instanci. |
| `DISCORD_REDIRECT_URI` | — | `http://localhost:{PORT}/auth/callback` | OAuth2 redirect URI. |

::: tip Generování SECRET_KEY
Použijte příkaz: `python3 -c "import secrets; print(secrets.token_hex(32))"`
:::

## 2. Škálování (Scaling Limits)

| Velikost serveru | RAM Redis | CPU | Poznámky |
| :--- | :--- | :--- | :--- |
| **< 5,000 členů** | 256 MB | 1 jádro | Výchozí konfigurace. |
| **5k – 50k členů** | 1 GB | 2 jádra | Zvažte zvýšení `maxmemory`. |
| **50k – 100k+ členů** | 4+ GB | 4+ jader | Redis replicas, event thinning. |

## 3. Redis Performance Tuning

| Parametr | Doporučená hodnota | Efekt |
| :--- | :--- | :--- |
| `tcp-keepalive` | 60 | Stabilnější bot↔Redis připojení. |
| `maxmemory` | 75% system RAM | Prevence swapování na disk. |
| `maxmemory-policy` | `noeviction` | Nikdy automaticky nemazat data. |
| `save` | `300 10` | RDB snapshot každých 5 minut. |
| `appendonly` | `yes` | AOF logging pro bezpečnost dat. |

```conf
# Příklad redis.conf
tcp-keepalive 60
maxmemory 1gb
maxmemory-policy noeviction
save 300 10
appendonly yes
```

## 4. Správa vah XP (za běhu)

XP pravidla lze měnit v reálném čase přes Redis nebo API:

```bash
# Přes redis-cli
redis-cli HSET config:xp:weights msg_short 1 msg_medium 5 msg_long 15

# Přes API (pokud máte access token)
curl -X POST http://localhost:8092/admin/config/weights \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"msg_short": 1, "msg_medium": 5}'
```

## 5. Logování a Monitoring

| Log | Obsah | Kde |
| :--- | :--- | :--- |
| `bot.log` | Discord eventy, chyby, Redis status. | Kořen projektu / Docker |
| `web.log` | HTTP requesty, OAuth flow, rendering. | Kořen projektu / Docker |

### Monitorovací příkazy
```bash
# Redis info
redis-cli INFO memory | grep used_memory_human
redis-cli DBSIZE

# Bot heartbeat (unix timestamp)
redis-cli GET bot:heartbeat

# Počet online členů
redis-cli GET presence:online:<guild_id>
```

::: danger Bezpečnost
Nikdy nesdílejte `.env` soubor ani `SECRET_KEY`. Kompromitace těchto klíčů umožňuje ovládat váš dashboard a přistupovat k datům všech uživatelů.
:::
