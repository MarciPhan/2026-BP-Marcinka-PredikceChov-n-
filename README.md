# 📊 Metricord

Discord bot s pokročilou analytikou, prediktivními modely a interaktivním dashboardem pro správu a rozvoj komunit.

Projekt vznikl jako součást bakalářské práce zaměřené na **predikci chování uživatelů na Discord serverech**.

---

## � Obsah
1. [Příprava (Před instalací)](#-příprava-před-instalací)
2. [Instalace (Krok za krokem)](#-instalace-krok-za-krokem)
3. [Používání systému](#-používání-systému)
4. [Údržba a Monitoring](#-údržba-a-monitoring)
5. [Odstranění systému](#-odstranění-systému)

---

## 🛠 1. Příprava (Před instalací)

Před samotným spuštěním bota musíte připravit externí služby:

### A. Discord Developer Portal
1. Jděte na [Discord Developer Portal](https://discord.com/developers/applications).
2. Vytvořte novou aplikaci (**New Application**) a pojmenujte ji (např. "Metricord").
3. V sekci **Bot**:
    - Vygenerujte si token (**Reset Token**) a bezpečně si ho uložte.
    - Zapněte všechny **Privileged Gateway Intents** (Presence, Server Members, Message Content).
4. V sekci **OAuth2**:
    - Vytvořte si URL pro pozvání bota s oprávněním `Administrator` (pro testování) nebo minimálně `Manage Server`, `View Audit Log` a `Read Messages/View Channels`.

### B. Redis Database
Metricord využívá Redis pro real-time analytiku.
- **Linux (Ubuntu/Debian)**: `sudo apt install redis-server`
- **Ostatní**: Doporučujeme využít Docker (viz níže).

---

## 🚀 2. Instalace (Krok za krokem)

### Krok 1: Klonování a příprava složky
```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd Discord-bot-main
```

### Krok 2: Virtuální prostředí
Vždy doporučujeme používat virtuální prostředí, aby nedošlo ke konfliktům v balíčcích:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Krok 3: Instalace závislostí
```bash
pip install -r requirements.txt
```

### Krok 4: Konfigurace `.env`
Vytvořte v root složce soubor `.env` a vložte do něj:
```env
BOT_TOKEN=váš_discord_token_z_portálu
DASHBOARD_TOKEN=náhodný_dlouhý_string_pro_zabezpečení
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
```

---

## 🕹 3. Používání systému

### Spuštění
Nejjednodušší způsob je použít přiložený startovací skript:
```bash
./start.sh
```
Tento skript:
1. Zkontroluje, zda běží Redis (pokud ne, pokusí se ho spustit).
2. Aktivuje virtuální prostředí.
3. Spustí bota i dashboard jako procesy na pozadí.

### Dashboard (Webové rozhraní)
Po spuštění je dashboard dostupný na: `http://localhost:8092`
- **Demo režim**: Pokud se nechcete přihlašovat, stačí v URL použít `?guild_id=demo-guild` nebo kliknout na "Demo" v přihlašovací obrazovce.
- **Interaktivní prvky**: Widgety na dashboardu můžete přesouvat nebo měnit jejich velikost (změny se ukládají v prohlížeči).

### Bot Příkazy
- `/stats`: Zobrazí aktuální rychlý přehled serveru (členové, aktivita).
- `/verify`: Spustí process verifikace nového uživatele.
- `/report`: Vygeneruje podrobný měsíční report (pouze pro administrátory).
- `/help`: Zobrazí nápovědu ke všem dostupným funkcím.

---

## � 4. Údržba a Monitoring

### Sledování logů
Pokud systém nefunguje podle představ, zkontrolujte logy:
- **Bot**: `tail -f bot_std.log`
- **Dashboard**: `tail -f dashboard_std.log`

### Záloha dat
Veškerá data jsou v Redisu. Pro zálohu stačí zkopírovat soubor `dump.rdb` (obvykle v `/var/lib/redis/` nebo v lokální složce, pokud spouštíte Redis ručně).

---

## 🗑 5. Odstranění systému

Pokud si přejete Metricord kompletně odstranit ze svého stroje, postupujte takto:

### Krok 1: Zastavení procesů
Nejprve ukončete běžící bota a dashboard:
```bash
pkill -f "bot/main.py"
pkill -f "uvicorn"
```

### Krok 2: Odstranění dat z Redisu
Pokud chcete smazat i nashromážděné statistiky:
```bash
redis-cli FLUSHALL
```

### Krok 3: Smazání souborů
```bash
cd ..
rm -rf Discord-bot-main
```

### Krok 4: Odstranění z Discordu
V Discord aplikaci stačí bota "vyhodit" (Kick) ze serveru a na [Developer Portalu](https://discord.com/developers/applications) aplikaci smazat v sekci **Settings** -> **Delete Application**.

---

## 📝 Licence & Autor
Projekt Metricord je proprietární software vytvořený jako součást bakalářské práce v roce 2026.
Všechna práva vyhrazena.
