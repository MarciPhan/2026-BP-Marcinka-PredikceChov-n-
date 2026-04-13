# Developer Guide: Vývoj Metricord

Průvodce pro vývojáře, kteří chtějí nasadit, upravovat nebo rozšiřovat Metricord. Pokrývá lokální vývojové prostředí, strukturu modulů, coding conventions a testování.

## 1. Lokální vývojové prostředí

```bash
# Klonování a příprava
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Spuštění bota
export PYTHONPATH=$PWD
python3 bot/main.py

# Spuštění dashboardu (uvicorn)
python3 -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8092 --reload
```

::: info Uvicorn --reload
Flag `--reload` automaticky restartuje dashboard při změně souborů. Ideální pro vývoj frontend šablon.
:::

## 2. Struktura modulů

### Bot Commands (bot/commands/)
Každý soubor je Cog načítaný automaticky při startu:
- `activity.py`: Hlavní tracking engine, XP, leaderboard.
- `stats_hll.py`: HyperLogLog statistiky (DAU/MAU).
- `gdpr.py`: Export a mazání dat uživatelů.
- `health.py`: Diagnostika systému.

### Web Backend
- `web/backend/main.py`: FastAPI aplikace, routing, OAuth flow.
- `web/backend/utils.py`: Analytické výpočty, Engagement Score, predikce.
- `web/backend/demo_data.py`: Generátor dat pro ukázkový režim.

### Shared modul
Sdílený kód mezi botem a dashboardem:
- `shared/keys.py`: Centrální definice Redis klíčů. **Všechny klíče na jednom místě.**
- `shared/models.py`: Matematické modely (Markov, Kaplan-Meier).
- `shared/redis_client.py`: Singleton async Redis klient.

## 3. Přidání nového příkazu (Cog)

```python
# bot/commands/my_command.py
import discord
from discord.ext import commands

class MyCommand(commands.Cog):
    @discord.app_commands.command(name="ping_pong")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MyCommand(bot))
```

## 4. Coding Conventions

- **Async everywhere:** Vždy používejte `async/await` pro IO operace.
- **Klíče přes keys.py:** Nikdy nepoužívejte hardcoded Redis klíče.
- **.env pro secrets:** Žádné tokeny v kódu.
- **Error handling:** V příkazech vždy ošetřete chyby, aby uživatel neviděl traceback.

## 5. Testování

Spuštění unit testů vyžaduje běžící Redis na `localhost:6379`.

| Test | Účel |
| :--- | :--- |
| `test_math_extreme.py` | Stress test matematických modelů (10M events). |
| `test_advanced_models.py` | Unit testy pro Markov a Kaplan-Meier. |
| `test_redis_performance.py` | Benchmark propustnosti Redisu. |
| `test_insights_extreme.py` | Kvalita Smart Insights enginu. |
