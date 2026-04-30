# Správa instance

Příručka pro správce, kteří provozují vlastní instanci Metricord. Pokrývá konfiguraci, Redis údržbu, škálování a každodenní provoz.

## Konfigurace prostředí

Všechny konfigurační hodnoty se nastavují přes proměnné prostředí v souboru `.env`. Soubor musí být v kořenovém adresáři projektu.

### Povinné proměnné

| Proměnná | Popis |
| :--- | :--- |
| `BOT_TOKEN` | Token Discord bota z [Developer Portal](https://discord.com/developers). |
| `DISCORD_CLIENT_ID` | OAuth2 Client ID pro přihlášení do dashboardu. |
| `DISCORD_CLIENT_SECRET` | OAuth2 Client Secret. |
| `DASHBOARD_SECRET_KEY` | Kryptografický klíč pro podpis session cookies (min. 32 znaků). |
| `REDIS_URL` | Connection string pro Redis (výchozí: `redis://localhost:6379/0`). |

Generování bezpečného klíče:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Volitelné proměnné

| Proměnná | Výchozí | Popis |
| :--- | :--- | :--- |
| `DASHBOARD_PORT` | `8092` | Port webového dashboardu. |
| `DISCORD_REDIRECT_URI` | `http://localhost:8092/auth/callback` | OAuth2 callback URL. |
| `BOT_LITE_MODE` | `0` | `1` pro sekundární instanci bez slash příkazů. |
| `API_ACCESS_TOKEN` | - | Bearer token pro REST API (pokud není nastaven, API je veřejné). |
| `SMTP_HOST` | - | SMTP server pro e-mailový OTP. |
| `SMTP_PORT` | `587` | Port SMTP serveru. |
| `SMTP_USER` | - | Uživatelské jméno pro SMTP. |
| `SMTP_PASSWORD` | - | Heslo pro SMTP. |

::: danger Bezpečnostní upozornění
Nikdy nahrávejte soubor `.env` do Git repozitáře. Soubor `.gitignore` musí obsahovat řádek `.env`. Kompromitace `BOT_TOKEN` nebo `DASHBOARD_SECRET_KEY` umožňuje útočníkovi plný přístup k vašemu systému a datům uživatelů.
:::

## Zabezpečení instance (Security Hardening)

Pro produkční nasazení doporučujeme provést následující kroky pro zvýšení zabezpečení:

1.  **Omezení přístupu k Redis:** Ujistěte se, že Redis není přístupný z veřejného internetu. V `redis.conf` nastavte `bind 127.0.0.1` a vždy používejte silné heslo přes `requirepass`.
2.  **HTTPS:** Vždy provozujte dashboard za reverzní proxy (např. Nginx) s platným SSL certifikátem (Let's Encrypt).
3.  **API Tokeny:** Pokud nevyužíváte veřejné API, nastavte `API_ACCESS_TOKEN`. Bez něj jsou statistiky serveru přístupné komukoliv, kdo zná `guild_id`.
4.  **Minimalizace oprávnění:** Botovi přidělte pouze nezbytná oprávnění v Discord Portalu. Vyhněte se přidělování role `Administrator`, pokud to není nezbytně nutné pro jiné moduly.

### Příklad `.env`

```bash
# Discord
BOT_TOKEN=<VÁŠ_BOT_TOKEN_Z_DEVELOPER_PORTALU>
DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=abcdefghijklmnopqrstuvwxyz123456
DISCORD_REDIRECT_URI=https://dashboard.example.com/auth/callback

# Security
DASHBOARD_SECRET_KEY=a1b2c3d4e5f6...  # min 32 znaků

# Redis
REDIS_URL=redis://default:heslo@localhost:6379/0

# Volitelné
DASHBOARD_PORT=8092
BOT_LITE_MODE=0
```

## Správa Redis

### Doporučená konfigurace

Přidejte do `redis.conf` nebo `docker-compose.yml`:

```conf
# Paměť
maxmemory 1gb
maxmemory-policy noeviction

# Perzistence
save 300 10
appendonly yes
appendfsync everysec

# Síť
tcp-keepalive 60
timeout 0
bind 127.0.0.1
protected-mode yes
requirepass VašeHeslo
```

### Vysvětlení parametrů

| Parametr | Doporučená hodnota | Důvod |
| :--- | :--- | :--- |
| `maxmemory` | 75 % systémové RAM | Prevence swapování na disk. |
| `maxmemory-policy` | `noeviction` | Redis nikdy automaticky nesmaže data - při plné paměti vrátí chybu. |
| `save` | `300 10` | RDB snapshot každých 5 minut, pokud se změnilo alespoň 10 klíčů. |
| `appendonly` | `yes` | AOF log zajišťuje trvanlivost dat i při nečekaném výpadku. |
| `tcp-keepalive` | `60` | Detekce mrtvých připojení každých 60 sekund. |
| `requirepass` | silné heslo | Ochrana před neautorizovaným přístupem. |

### Pravidelná údržba

Provádějte tyto kroky, abyste zajistili stabilitu systému a předešli ztrátě dat:

1.  **Kontrola zaplnění paměti:** Redis je in-memory databáze. Pokud se paměť zaplní, bot přestane ukládat data.
    `redis-cli INFO memory | grep used_memory_human`
2.  **Zálohování databáze:** Každý den zkopírujte soubor `dump.rdb` na externí úložiště.
3.  **Monitoring logů:** Pravidelně kontrolujte, zda bot nevykazuje chyby `429 Too Many Requests` (Rate limiting od Discordu).
4.  **Aktualizace:** Před aktualizací Metricord na novou verzi vždy vytvořte snapshot Redis databáze příkazem `SAVE`.

### Obnova ze zálohy

Postup obnovy Redis dat ze zálohy:

1. Zastavte Redis: `systemctl stop redis` nebo `docker-compose stop redis`.
2. Zkopírujte zálohu `dump.rdb` do Redis datového adresáře (výchozí: `/var/lib/redis/`).
3. Spusťte Redis: `systemctl start redis`.
4. Ověřte: `redis-cli DBSIZE` - počet klíčů odpovídá očekávání.

Pokud používáte AOF:
1. Zkopírujte `appendonly.aof` do datového adresáře.
2. Spusťte `redis-check-aof --fix appendonly.aof` pro opravu nekonzistencí.
3. Spusťte Redis.

## Škálování

### Orientační nároky

| Velikost serveru | RAM Redis | CPU | Doporučená konfigurace |
| :--- | :--- | :--- | :--- |
| < 5 000 členů | 256 MB | 1 jádro | Výchozí konfigurace, žádné úpravy. |
| 5 000–50 000 členů | 1 GB | 2 jádra | Zvyšte `maxmemory`, aktivujte AOF. |
| 50 000–100 000+ členů | 4+ GB | 4+ jader | Redis repliky, event thinning, load balancer. |

### Event thinning

Pro servery s > 50 000 členy doporučujeme event thinning - automatické prořezávání starých eventů:

```bash
# Smazání eventů starších než 30 dní pro celý server
redis-cli EVAL "
  local keys = redis.call('KEYS', 'events:msg:' .. ARGV[1] .. ':*')
  local cutoff = tonumber(ARGV[2])
  for _, key in ipairs(keys) do
    redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
  end
  return #keys
" 0 GUILD_ID $(date -d '30 days ago' +%s)
```

## Správa vah aktivity za běhu

Váhy moderátorských akcí lze měnit bez restartu bota:

```bash
# Aktuální váhy
redis-cli HGETALL config:action_weights

# Změna váhy banu na 300 sekund
redis-cli HSET config:action_weights bans 300

# Výchozí váhy (z kódu activity.py):
# bans: 300, kicks: 180, timeouts: 180, unbans: 120
# verifications: 120, msg_deleted: 60, role_updates: 30
# chat_time: 1, voice_time: 1
```

Po změně vah zvyšte verzi konfigurace, aby se denní statistiky přepočítaly:

```bash
redis-cli INCR config:weights_version
```

## Logování

| Soubor | Obsah |
| :--- | :--- |
| stdout bota (Docker) | Discord eventy, chyby, Redis status, backfill progress. |
| stdout dashboardu (Docker) | HTTP requesty, OAuth flow, chyby renderingu. |

Zobrazení logů v Docker Compose:

```bash
# Všechny služby
docker-compose logs -f

# Pouze bot (posledních 200 řádků)
docker-compose logs --tail=200 discord-bot-primary

# Pouze dashboard
docker-compose logs --tail=200 web-dashboard
```

## Dual-bot režim (Lite Mode)

Metricord podporuje provoz dvou instancí bota současně:

| Instance | `BOT_LITE_MODE` | Funkce |
| :--- | :--- | :--- |
| Primary | `0` | Plná funkčnost - příkazy, event tracking, backfill. |
| Secondary | `1` | Pouze event tracking - žádné slash příkazy. |

Důvod: Discord API neumožňuje dvěma instancím registrovat stejné slash příkazy. Secondary instance slouží jako záloha pro sběr dat v případě výpadku primary instance. Data obou instancí se ukládají do stejné Redis databáze.
