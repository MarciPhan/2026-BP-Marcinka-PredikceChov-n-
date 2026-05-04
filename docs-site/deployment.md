# Průvodce produkčním nasazením

Tento dokument vás provede nasazením systému Metricord do produkčního prostředí. Pokrývá instalaci přes Docker, nastavení reverzní proxy (Nginx) a zajištění vysoké dostupnosti a bezpečnosti.

## Systémové požadavky

Před instalací ověřte, zda váš server splňuje tyto minimální a doporučené parametry:

| Parametr | Minimální | Doporučená produkce |
| :--- | :--- | :--- |
| **OS** | Linux (libovolná distribuce) | Ubuntu 22.04 LTS / Fedora 39+ |
| **CPU** | 1 jádro | 2+ jádra (pro servery s 10k+ členy) |
| **RAM** | 1 GB | 2+ GB (Redis je in-memory) |
| **Python** | 3.9 | 3.11+ |
| **Redis / Valkey** | 6.0 | 7.0+ (pro podporu ACL) |
| **Docker** | 20.10 | 24.0+ s Compose v2 |

## Příprava prostředí

### Konfigurace v Discord Portalu

1.  Otevřete [Discord Developer Portal](https://discord.com/developers/applications).
2.  Vytvořte novou aplikaci a v sekci **Bot** vygenerujte `BOT_TOKEN`.
3.  Aktivujte všechna **Privileged Gateway Intents** (Presence, Server Members, Message Content).
4.  V sekci **OAuth2** přidejte Redirect URI: `https://vase-domena.com/auth/callback`.
5.  Pozvěte bota na server s oprávněním `Administrator`.

### Generování bezpečnostních klíčů

Spusťte tyto příkazy pro vytvoření unikátních klíčů pro vaši instanci:

```bash
# Klíč pro podepisování session cookies (min. 32 znaků)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Statický token pro přístup k REST API
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Nasazení pomocí Docker Compose (Doporučeno)

Docker Compose automaticky spustí a propojí všechny potřebné služby: Redis, hlavního bota, dashboard a analytický engine.

1.  Klonujte repozitář: `git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-`
2.  Vytvořte konfigurační soubor: `cp .env.example .env`
3.  Upravte `.env` a vyplňte všechny povinné proměnné (viz Tabulka proměnných níže).
4.  Spusťte stack: `docker-compose up -d --build`

## Nastavení Nginx a SSL

Pro bezpečný přístup k dashboardu přes HTTPS využijte Nginx jako reverzní proxy.

### Konfigurace Nginx

Vytvořte konfigurační soubor `/etc/nginx/sites-available/metricord` s tímto obsahem:

```nginx
server {
    listen 80;
    server_name dashboard.vase-domena.com;

    location / {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Podpora pro WebSockety
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Zabezpečení pomocí SSL (Let's Encrypt)

> [!WARNING]
> Před spuštěním Certbotu se ujistěte, že vaše doména směřuje na IP adresu serveru a port 80 je otevřený ve firewallu.

Spusťte tyto příkazy pro vystavení a instalaci certifikátu:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.vase-domena.com
```

## Údržba a správa dat

### Zálohování Redis databáze
Pro minimalizaci rizika ztráty dat nastavte pravidelnou zálohu RDB souboru:

```bash
# Vynucení vytvoření snapshotu
redis-cli BGSAVE

# Kopírování zálohy (nastavte jako cron úlohu)
cp /var/lib/redis/dump.rdb /backup/metricord-$(date +%Y%m%d).rdb
```

### Strategie Disaster Recovery
Metricord podporuje dva režimy persistence v Redisu. Pro optimální výkon zvolte:
- **RDB (Snapshotting):** Vhodné pro analytická data. Nastavte interval na 15 minut.
- **AOF (Append-Only File):** Vhodné pro kritickou konfiguraci a XP body. Povolte v produkci pro maximální integritu.

## Přehled proměnných prostředí (`.env`)

| Proměnná | Povinná | Popis |
| :--- | :--- | :--- |
| `BOT_TOKEN` | Ano | Token z Discord Developer Portalu. |
| `DISCORD_CLIENT_ID` | Ano | OAuth2 Client ID. |
| `DISCORD_CLIENT_SECRET` | Ano | OAuth2 Client Secret. |
| `DISCORD_REDIRECT_URI` | Ano | Callback URL (musí přesně odpovídat nastavení v Portalu). |
| `DASHBOARD_SECRET_KEY` | Ano | Klíč pro šifrování session (vygenerujte pomocí `secrets`). |
| `REDIS_URL` | Ano | Adresa Redis serveru (např. `redis://redis:6379/0`). |

> [!CAUTION]
> Soubor `.env` nikdy neukládejte do verzovacího systému (Git). Vždy se ujistěte, že je uveden v `.gitignore`.

- [x] `BOT_TOKEN` vyplněn a validní
- [x] Privileged Intents zapnuty v Discord Portalu
- [x] Nginx s SSL certifikátem (Let's Encrypt)
- [x] Redis není vystaven na veřejnou síť
- [x] Záloha Redis dat nastavena (cron)
- [x] Firewall aktivní (UFW/iptables)
