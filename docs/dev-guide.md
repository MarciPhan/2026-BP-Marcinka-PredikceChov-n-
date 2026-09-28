# Vývojářský průvodce

Podrobný technický návod pro zprovoznění celého ekosystému CommunityMetrics na lokálním stroji a orientaci v kódu.

## Prerekvizity

Před začátkem se ujistěte, že máte nainstalované:

| Komponenta | Účel | Ověření |
| :--- | :--- | :--- |
| **Python 3.11** | Jádro bota a backendu | `python3 --version` |
| **Node.js 18+ & npm** | VitePress dokumentace | `node --version` |
| **Redis (nebo Valkey)** | In-memory databáze | `redis-cli ping` → `PONG` |
| **Git** | Verzování | `git --version` |

## Klonování a příprava prostředí

```bash
# 1. Klonování repozitáře
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Vytvoření virtuálního prostředí
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalace Python závislostí
pip install -r requirements.txt

# 4. Instalace Node.js závislostí
npm install
```

## Konfigurace prostředí

Vytvořte soubor `.env` z šablony:

```bash
cp .env.example .env
```

Minimální konfigurace pro lokální vývoj:

```bash
# Discord (povinné)
BOT_TOKEN=<váš bot token z Developer Portalu>
DISCORD_CLIENT_SECRET=<OAuth2 Client Secret>

# Web Dashboard
DASHBOARD_PORT=8093
DASHBOARD_SECRET_KEY=<vygenerujte: python3 -c "import secrets; print(secrets.token_hex(32))">
DASHBOARD_ACCESS_TOKEN=<interní přístupový token backendu; vygeneruje se automaticky, pokud chybí>

# Infrastruktura
REDIS_URL=redis://localhost:6379/0
```

> [!TIP]
> Pro vývoj bez Discord tokenu bot nastartuje v „idle mode" — dashboard a dokumentace budou fungovat, ale bot se nepřipojí k Discordu.

## Spuštění celého systému

### Varianta 1: Automatický skript (doporučeno)

```bash
chmod +x start.sh
./start.sh
```

### Varianta 2: Manuální spuštění jednotlivých komponent

```bash
# Terminál 1: Redis
redis-server

# Terminál 2: Bot
export PYTHONPATH=$PWD
python3 bot/main.py

# Terminál 3: Dashboard (FastAPI)
export PYTHONPATH=$PWD
uvicorn web.backend.main:app --host 0.0.0.0 --port 8093 --reload

# Terminál 4: Dokumentace (VitePress)
cd docs && npm run docs:dev
```

### Co běží po spuštění?

| Služba | Port | URL | Popis |
| :--- | :--- | :--- | :--- |
| **Discord Bot** | — | — | Připojí se k Discordu přes Gateway WebSocket |
| **FastAPI Backend** | 8093 | `http://localhost:8093` | Dashboard s OAuth2, REST API |
| **VitePress Docs** | 5173 | `http://localhost:5173` | Tato dokumentace |
| **Redis** | 6379 | `redis://localhost:6379` | In-memory databáze |

## Adresářová struktura projektu

```text
communitymetrics/
 bot/
    main.py              # Entry point, event loop, background tasks
    commands/
        activity.py      # Hlavní tracking modul — XP, voice, zprávy
        stats_hll.py     # HyperLogLog statistiky — DAU/MAU
        gdpr.py          # GDPR příkazy — export, smazání dat
        health.py        # Zdravotní check — Redis ping, bot status
        help.py          # Interaktivní nápověda
        ping.py          # Měření latence k Discord API
        community_health.py    # Community Health příkazy
        analytics_tracking.py  # Event tracking pro dashboard
 web/
    backend/
        main.py          # FastAPI app — middleware, routery, error handling
        security.py      # CSRF ochrana (require_csrf)
        utils.py         # Analytické výpočty — Engagement, predikce
        routers/
            auth.py       # Discord OAuth2, demo login
            pages.py      # Server-side rendered HTML stránky
            api.py        # REST API endpointy (JSON)
            settings.py   # Konfigurace dashboardu
            community_health.py  # Community Health stránky
        services/
            analytics_service.py       # AnalyticsService — metriky
            community_health_service.py # CommunityHealthService
    frontend/
        templates/         # Jinja2 HTML šablony (22 souborů)
        static/            # CSS, JS, obrázky
 shared/
    models.py            # Matematické modely — Markov, Kaplan-Meier
    redis_client.py      # Redis connection pool (async + sync)
    config.py            # Pydantic Settings — prostředí, retence
    community_health.py  # Helper funkce pro Community Health
    analytics_config.py  # Výchozí váhy MII
    net_security.py      # SSRF/DNS-rebinding validace Discourse URL
 scripts/
    discourse_sync.py    # Konektor pro Discourse fórum
 docs/                    # Tato dokumentace (VitePress)
 config/                  # Konfigurace a tajemství
 docker-compose.yml       # Vývojové nasazení (5 kontejnerů, vč. lite bota)
 docker-compose.prod.yml  # Produkční nasazení (4 kontejnery, bez lite bota)
 Dockerfile               # Container image (python:3.11-slim)
 start.sh                 # Lokální spouštěč
 requirements.txt         # Python závislosti
 .env.example             # Šablona konfigurace
```

## Vývoj dokumentace

Dokumentace běží na VitePress s hot-reload (HMR):

- Soubory: `docs/*.md`
- Konfigurace navigace: `docs/.vitepress/config.js`
- Custom CSS: `docs/.vitepress/theme/custom.css`
- Změny se projeví okamžitě po uložení.

### Přidání nové stránky

1. Vytvořte nový `.md` soubor v `docs/`.
2. Přidejte odkaz do sidebaru v `.vitepress/config.js`:
   ```javascript
   { text: 'Název stránky', link: '/nazev-souboru' }
   ```
3. Uložte — VitePress automaticky načte novou stránku.

### Build pro produkci

```bash
cd docs
npm run docs:build
# Výstup: docs/.vitepress/dist/
```

## Vývoj bota

### Přidání nového příkazu (Cog)

1. Vytvořte nový soubor v `bot/commands/`:
   ```python
   from discord.ext import commands
   from discord import app_commands

   class MyCog(commands.Cog):
       def __init__(self, bot):
           self.bot = bot

       @app_commands.command(name="mycommand", description="Popis příkazu")
       async def my_command(self, interaction):
           await interaction.response.send_message("Hello!")

   async def setup(bot):
       await bot.add_cog(MyCog(bot))
   ```

2. Bot automaticky načte nový Cog při startu (pokud je v `bot/commands/`).
3. Zaregistrujte příkazy: `*sync`

### Práce s Redis

Pomocné funkce pro sestavení klíčů HyperLogLogu (`K_DAU`, `day_key`) jsou aktuálně definované v `bot/commands/stats_hll.py` a samostatně (duplicitně) také v `web/backend/utils.py` — projekt zatím nemá jeden centrální modul pro Redis klíčové schéma napříč botem a backendem. Pro Community Health klíče (poznámky, help požadavky, moderační eventy) existuje centralizovaná pomocná vrstva v `shared/community_health.py`. Při přidávání nového klíče se držte existující konvence (`{skupina}:{typ}:{guild_id}:{...}`) a pokud je pro danou oblast už pomocná funkce k dispozici, použijte ji místo ručně skládaného stringu.

## Řešení potíží

| Problém | Řešení |
| :--- | :--- |
| **Port 8093 je obsazen** | Změňte `DASHBOARD_PORT` v `.env` nebo ukončete proces: `lsof -t -i :8093 \| xargs kill` |
| **Bílá obrazovka v dokumentaci** | Ujistěte se, že běží NPM server (`cd docs && npm run docs:dev`). |
| **Redis Connection Error** | Zkontrolujte, zda běží Redis: `redis-cli ping`. Pokud ne: `redis-server --daemonize yes`. |
| **Bot nereaguje na příkazy** | Zaregistrujte slash příkazy: `*sync`. Ověřte, že bot má oprávnění `Use Application Commands`. |
| **Import Error** | Ověřte `PYTHONPATH`: `export PYTHONPATH=$PWD`. |

Podrobnější řešení najdete v [Troubleshooting](/troubleshooting).
