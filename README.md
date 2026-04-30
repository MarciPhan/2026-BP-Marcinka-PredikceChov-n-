# Metricord

Discord bot s pokročilou analytikou, prediktivními modely a interaktivním dashboardem pro správu a rozvoj komunit.

Projekt vznikl jako součást bakalářské práce zaměřené na **predikci chování uživatelů na Discord serverech**.

---

## Rychlý start (3 kroky)

### 1. Klonování
```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-
```

### 2. Konfigurace
```bash
cp .env.example .env
nano .env          # vyplň BOT_TOKEN
```

> **Kde vzít BOT_TOKEN?**
> 1. Jdi na [Discord Developer Portal](https://discord.com/developers/applications)
> 2. Vytvořit novou aplikaci → sekce **Bot** → **Reset Token**
> 3. Zapni všechny **Privileged Gateway Intents** (Presence, Server Members, Message Content)
> 4. Pozvi bota na server s oprávněním `Administrator`

### 3. Spuštění
```bash
./start.sh
```

Skript automaticky:
-  Vytvoří virtuální prostředí (`.venv`)
-  Nainstaluje závislosti
-  Zkontroluje konfiguraci
-  Spustí Redis, Discord bota i Dashboard

Dashboard je po spuštění dostupný na **http://localhost:8092**

---

## Požadavky

- **Python 3.9+**
- **Redis** nebo **Valkey** (`sudo dnf install redis` / `sudo apt install redis-server`)

---

## Používání

### Dashboard (Webové rozhraní)
Po spuštění je dashboard dostupný na: `http://localhost:8092`
- **Demo režim**: Klikni na "Demo" v přihlašovací obrazovce
- **Interaktivní prvky**: Widgety můžeš přesouvat a měnit jejich velikost

### Bot Příkazy
- `/stats` – Přehled serveru (členové, aktivita)
- `/verify` – Verifikace nového uživatele
- `/report` – Měsíční report (pouze pro administrátory)
- `/help` – Nápověda

---

## Údržba

### Sledování logů
```bash
tail -f bot_std.log        # Bot
tail -f dashboard_std.log  # Dashboard
```

### Zastavení
```bash
pkill -f "bot/main.py"
pkill -f "uvicorn"
```

### Záloha dat
Zkopíruj soubor `dump.rdb` (obvykle `/var/lib/redis/`).

---

## Docker (alternativa)
```bash
cp .env.example .env
nano .env
docker-compose up -d
```

---

## Technická analýza a predikce

Metricord poskytuje:
- **Engagement Score** – Hodnocení zapojení komunity (0–100)
- **Security Audit** – Vyhodnocování bezpečnosti serveru
- **Prediktivní modely** – Odhady růstu pomocí lineární regrese a sezónních indexů
- **Smart Insights** – AI-ready interpretace dat

Podrobnosti: [Technická dokumentace](docs/TECHNICAL_DESCRIPTION.md)

---

## Licence & Autor
Projekt Metricord je proprietární software vytvořený jako součást bakalářské práce v roce 2026.
Všechna práva vyhrazena.
