# Nasazení a údržba (Produkční průvodce)

Kompletní průvodce pro nasazení Metricord do produkce — od lokálního testu po zabezpečený server s SSL a monitoringem.

## 1. Systémové požadavky

| Parametr | Minimální | Doporučeno (produkce) |
| :--- | :--- | :--- |
| **OS** | Linux (libovolná distribuce) | Ubuntu 22.04 LTS / Fedora 39+ |
| **CPU** | 1 jádro | 2+ jádra (pro servery s 10k+ členy) |
| **RAM** | 1 GB | 2+ GB (Redis je in-memory) |
| **Python** | 3.9 | 3.11+ |
| **Redis / Valkey** | 6.0 | 7.0+ (pro ACL podporu) |
| **Docker** | 20.10 | 24.0+ s Compose v2 |

## 2. Příprava prostředí

### 2.1 Discord Developer Portal
Než začnete s nasazením, potřebujete:
1. Jděte na [Discord Developer Portal](https://discord.com/developers/applications).
2. Vytvořte novou aplikaci → sekce **Bot** → **Reset Token** → zkopírujte `BOT_TOKEN`.
3. Zapněte **všechny Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent`
4. V sekci **OAuth2**:
   - Přidejte Redirect URI: `http://localhost:8092/auth/callback` (pro vývoj).
   - Zkopírujte `DISCORD_CLIENT_ID` a `DISCORD_CLIENT_SECRET`.
5. Pozvěte bota na server s oprávněním `Administrator`.

### 2.2 Generování secret klíčů
```bash
# Generování bezpečného secret klíče pro dashboard session
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generování access tokenu pro API
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 3. Metoda A: Lokální nasazení (start.sh)

Ideální pro vývoj a testování. Spustí všechny služby na jednom stroji.

::: info Krok 1: Klonování a příprava
```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-
cp .env.example .env
```
:::

::: info Krok 2: Konfigurace .env
Vyplňte všechny povinné proměnné (Tokeny, Secret klíče, Redis URL).
:::

::: info Krok 3: Spuštění
```bash
chmod +x start.sh
./start.sh
```
Dashboard bude dostupný na **http://localhost:8092**.
:::

## 4. Metoda B: Docker Compose (doporučeno pro produkci)

```bash
cp .env.example .env
nano .env    # vyplňte všechny proměnné
docker-compose up -d --build
```

**Docker Compose spustí 4 služby:**
- `redis`: In-memory databáze.
- `discord-bot-primary`: Hlavní bot — zpracovává příkazy a trackuje aktivitu.
- `discord-bot-dashboard`: Sekundární bot v Lite Mode pro data dashboardu.
- `web-dashboard`: FastAPI dashboard.

## 5. Produkční nasazení s Nginx a SSL

### 5.1 Nginx reverse proxy
Příklad konfigurace (`/etc/nginx/sites-available/metricord`):
```nginx
server {
    listen 80;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5.2 SSL s Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.example.com
```

::: warning Důležité
Po nastavení SSL změňte Redirect URI v Discord Portalu na `https://dashboard.example.com/auth/callback` a nastavte `DISCORD_REDIRECT_URI` v `.env`.
:::

## 6. Údržba a monitoring

### 6.1 Logy
- **Bot logy:** `tail -f bot.log`
- **Dashboard logy:** `tail -f web.log`
- **Docker:** `docker-compose logs -f`

### 6.2 Health check
Bot zapisuje heartbeat do Redisu každých 60 sekund.
```bash
redis-cli GET bot:heartbeat
```

### 6.3 Záloha Redis dat
```bash
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/metricord-$(date +%Y%m%d).rdb
```

## 7. Hardening & Security

Pro produkční prostředí je kritické minimalizovat útočnou plochu:
- **Isolace:** Aplikace běží pod neprivilegovaným uživatelem.
- **Redis ACL:** V produkci vypněte nebezpečné příkazy pro bot uživatele.
- **Firewall:** Povolte pouze porty 22, 80, 443.

## 8. Škálování pro velké servery (100k+ členů)

Díky bezstavové architektuře dashboardu můžete systém škálovat horizontálně:
- **Load Balancing:** Spusťte více instancí dashboardu za Load Balancerem.
- **Redis Sharding:** Pokud data přesáhnou RAM limit, využijte Redis Cluster.

## 9. Production Checklist

- [ ] `BOT_TOKEN` vyplněn a validní
- [ ] `DASHBOARD_SECRET_KEY` vygenerován (32+ znaků)
- [ ] Privileged Intents zapnuty v Discord Portalu
- [ ] Nginx s SSL certifikátem (Let's Encrypt)
- [ ] Redis není vystaven na veřejnou síť
- [ ] Záloha Redis dat nastavena (cron)
- [ ] Firewall aktivní (UFW/iptables)
