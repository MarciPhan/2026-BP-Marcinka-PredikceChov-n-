# Instalace a konfigurace

Tento průvodce vás provede kompletním procesem od přípravy prostředí až po spuštění všech komponent systému Metricord.

## Systémové požadavky

| Komponenta | Minimum | Doporučeno |
| :--- | :--- | :--- |
| **Python** | 3.9 | 3.11+ |
| **Node.js** | 18 | 20 LTS |
| **Redis / Valkey** | 6.0 | 7.0+ |
| **Docker** *(volitelné)* | 20.10 | 24.0+ s Compose v2 |
| **RAM** | 1 GB | 2+ GB (Redis je in-memory) |
| **OS** | Linux / macOS / WSL2 | Ubuntu 22.04 LTS |

## Příprava Discord aplikace

### 1. Vytvoření aplikace a bota

1.  Přejděte na [Discord Developer Portal](https://discord.com/developers/applications).
2.  Klikněte na **New Application**, zadejte název (např. „Metricord") a potvrďte.
3.  V sekci **Bot** klikněte na **Reset Token** a bezpečně si zkopírujte `BOT_TOKEN`.
4.  V sekci **Bot → Privileged Gateway Intents** zapněte všechny tři:
    - **Presence Intent**
    - **Server Members Intent**
    - **Message Content Intent**

> [!IMPORTANT]
> Bez **Message Content Intent** bot neuvidí délku zpráv a XP systém nebude fungovat. Bez **Server Members Intent** nelze sledovat příchody a odchody.

### 2. Pozvání bota na server

1.  V sekci **OAuth2 → URL Generator** zaškrtněte:
    - Scopes: `bot`, `applications.commands`
    - Bot Permissions: `View Channels`, `Read Message History`, `Send Messages`, `Connect`, `Use Application Commands`, `Manage Roles` *(volitelné)*
2.  Zkopírujte vygenerovanou URL a otevřete ji v prohlížeči.
3.  Vyberte cílový server a potvrďte oprávnění.

### 3. OAuth2 pro dashboard *(volitelné)*

Pokud chcete používat webový dashboard s přihlášením přes Discord:

1.  V sekci **OAuth2 → General** zkopírujte `CLIENT_ID` a `CLIENT_SECRET`.
2.  V **Redirects** přidejte callback URL:
    - Lokální vývoj: `http://localhost:8092/auth/callback`
    - Produkce: `https://vase-domena.com/auth/callback`

## Konfigurace proměnných prostředí

Vytvořte soubor `.env` z šablony:

```bash
cp .env.example .env
```

Vyplňte povinné hodnoty:

```bash
# Discord (povinné)
BOT_TOKEN=<VÁŠ_BOT_TOKEN_Z_DEVELOPER_PORTALU>
DISCORD_CLIENT_SECRET=abcdefghijklmnopqrstuvwxyz123456

# Web Dashboard
DASHBOARD_PORT=8092
DASHBOARD_SECRET_KEY=           # min 32 znaků (viz generování níže)
DASHBOARD_ACCESS_TOKEN=         # Bearer token pro REST API

# Infrastruktura
REDIS_URL=redis://localhost:6379/0

# SMTP / Email (volitelné - pro OTP ověření)
SMTP_PASSWORD=
```

### Generování bezpečnostních klíčů

```bash
# Klíč pro podepisování session cookies
python3 -c "import secrets; print(secrets.token_hex(32))"

# Token pro REST API
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

> [!CAUTION]
> Soubor `.env` nikdy nenahrávejte do Git repozitáře. Ujistěte se, že je uveden v `.gitignore`. Kompromitace `BOT_TOKEN` umožňuje útočníkovi plný přístup k vašemu Discord botu.

## Instalace a spuštění

### Varianta A: Lokální spuštění (vývoj)

Skript `start.sh` automaticky vytvoří virtuální prostředí, nainstaluje závislosti a spustí všechny tři služby:

```bash
# 1. Klonování repozitáře
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Konfigurace (viz výše)
cp .env.example .env

# 3. Spuštění
chmod +x start.sh
./start.sh
```

Co `start.sh` udělá:
1. Vytvoří `.venv` a nainstaluje Python závislosti.
2. Zkontroluje existenci `.env` a přítomnost `BOT_TOKEN`.
3. Spustí Redis/Valkey server (pokud neběží).
4. Spustí **Discord bota** → ukládá eventy do Redisu.
5. Spustí **FastAPI dashboard** na portu `8092`.
6. Spustí **VitePress dokumentaci** na portu `5173`.

### Varianta B: Docker Compose (produkce)

```bash
# 1. Vytvoření Docker sítě (pouze poprvé)
docker network create botnet

# 2. Build a spuštění
docker-compose up -d --build

# 3. Ověření
docker-compose ps
```

Docker Compose spustí 4 kontejnery:

| Kontejner | Funkce |
| :--- | :--- |
| `discord-redis` | Redis databáze |
| `discord-bot-primary` | Hlavní bot — příkazy, tracking, backfill |
| `discord-bot-dashboard` | Lite Mode bot — záložní sběr dat |
| `web-dashboard` | FastAPI backend s OAuth2 |

## Ověření instalace

Po spuštění proveďte tyto kontroly:

```bash
# 1. Redis odpovídá?
redis-cli ping
# Očekávaná odpověď: PONG

# 2. Bot běží?
redis-cli GET bot:heartbeat
# Měl by vrátit aktuální UNIX timestamp

# 3. Dashboard je dostupný?
curl -s http://localhost:8092/health
```

Na Discord serveru ověřte, že bot je **online** (zelená tečka). Pokud nereaguje na příkazy, zaregistrujte slash příkazy:

```
*sync
```

## Nastavení e-mailového ověření (OTP)

Pokud chcete používat dvoufázové ověření přes e-mail pro citlivá nastavení dashboardu:

1.  V `.env` vyplňte SMTP údaje:
    - `SMTP_HOST`: např. `smtp.gmail.com`
    - `SMTP_PORT`: `587`
    - `SMTP_USER`: váš e-mail
    - `SMTP_PASSWORD`: heslo k aplikaci (App Password)

> [!WARNING]
> Pro Gmail musíte vygenerovat **App Password** v nastavení Google účtu (Security → 2-Step Verification → App passwords). Běžné heslo neprojde.

## Další kroky

- **[Rychlý start](/quickstart)** — 5minutový průvodce prvním použitím.
- **[Správa instance](/admin-guide)** — Redis údržba, škálování, logování.
- **[Nasazení do produkce](/deployment)** — Nginx, SSL, vysoká dostupnost.
- **[Vývojářský průvodce](/dev-guide)** — Lokální vývoj a úpravy kódu.
