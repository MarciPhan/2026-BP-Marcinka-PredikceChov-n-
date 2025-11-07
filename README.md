# Metricord

Discord bot s analytikou a dashboardem pro správu serveru.

Projekt pro bakalářskou práci - predikce chování uživatelů na Discord serverech.

## Co to umí

- **Analytika**: Real-time sledování aktivity (DAU/MAU/WAU, online počty)
- **Moderace**: Logování všech událostí, verifikace, reporty
- **Dashboard**: Web rozhraní pro přehledy a grafy
- **Gamifikace**: XP systém, výzvy, emoji role
- **Predikce**: Analýza trendů a engagement score

## Struktura projektu

```
bot/           # Discord bot + příkazy
web/           # FastAPI dashboard
  backend/     # API endpoints
  frontend/    # Jinja2 templates + static
config/        # Konfigurace bota
shared/        # Sdílené utility (Redis client atd.)
scripts/       # Maintenance skripty
```

## Jak spustit

### Potřebujete
- Python 3.10+
- Redis server
- Discord bot token

### Instalace

```bash
# vytvoř venv
python3 -m venv .venv
source .venv/bin/activate

# nainstaluj závislosti
pip install -r requirements.txt
pip install fastapi uvicorn jinja2 python-multipart httpx itsdangerous
```

### Konfigurace

Vytvořte `.env` soubor v root složce:

```env
BOT_TOKEN=your_discord_bot_token_here
DASHBOARD_TOKEN=your_dashboard_bot_token
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost

# volitelné - pro OAuth login
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8092/auth/callback
```

### Spuštění

```bash
# 1. Spusť Redis
redis-server --daemonize yes

# 2. Spusť bota
export PYTHONPATH=$(pwd)
python bot/main.py

# 3. Spusť dashboard (v novém terminálu)
export PYTHONPATH=$(pwd)
cd web
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8092
```

Dashboard pak běží na: http://localhost:8092

## Docker

Nebo použij Docker Compose (jednodušší):

```bash
docker-compose up -d
```

## Funkce

### Bot příkazy
- `/ping` - latence bota
- `/help` - nápověda
- `/stats` - statistiky serveru
- `/verify` - verifikace uživatele
- `/purge` - čištění zpráv (admin)
- `/notify` - oznámení (admin)
- `/report` - generování reportů (admin)

### Analytics
- Real-time sledování aktivity (DAU/MAU/WAU)
- HyperLogLog pro efektivní counting
- Tracking user aktivity
- Historická data a trendy

### Dashboard
- Real-time metriky
- Grafy aktivity (Chart.js)
- Predikce chování uživatelů
- User profily
- OAuth přihlášení

## Poznámky

- Bot potřebuje všechny intents (privileged gateway intents v Discord Dev Portal)
- Redis musí běžet jinak bot spadne
- Pro production použij proper secrets v `config/dashboard_secrets.py`

## Licence

Proprietární. Všechna práva vyhrazena.

---

*Vytvořeno jako součást bakalářské práce 2026*
