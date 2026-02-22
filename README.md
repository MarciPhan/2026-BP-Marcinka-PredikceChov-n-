# 📊 Metricord

Discord bot s pokročilou analytikou, prediktivními modely a interaktivním dashboardem pro správu a rozvoj komunit.

Projekt vznikl jako součást bakalářské práce zaměřené na **predikci chování uživatelů na Discord serverech**.

## 🚀 Hlavní Funkce

### 📈 Analytika & Monitoring
- **Real-time sledování aktivity**: Detailní monitoring DAU/MAU/WAU (denní/měsíční/týdenní aktivní uživatelé).
- **HyperLogLog**: Efektivní počítání unikátních uživatelů s minimální paměťovou náročností.
- **Heatmapy aktivity**: Vizualizace nejoblíbenějších hodin a dní v týdnu pro zasílání zpráv.
- **Sledování růstu**: Historie příchodů a odchodů členů s přepínatelnými grafy.

### 🏠 Skóre komunity (Community Health)
- **Komplexní hodnocení**: Algoritmus počítající celkové zdraví serveru na základě:
    - Poměru moderátorů k počtu uživatelů.
    - Úrovně zabezpečení serveru (verification levels, MFA, explicit filter).
    - Zapojení uživatelů (participation rate, reply ratio, voice activity).
    - Aktivity moderátorského týmu.
- **Chytré postřehy (Insights)**: Automaticky generované tipy a varování na základě naměřených metrik.

### 🔮 Predikce & Trendy
- **Predikce růstu**: Odhad počtu členů a zpráv na následující období.
- **Stickiness & Retention**: Analýza toho, jak se uživatelé na server vrací a jaká je jejich retence.
- **Predictive Analytics**: Identifikace trendů v zapojení a včasné varování před stagnací.

### 🛠️ Moderace & Správa
- **Event Logging**: Podrobné logování zpráv, hlasové aktivity a akcí moderátorů do Redis.
- **Verifikace**: Systematické potvrzování nových členů pro zvýšení bezpečnosti.
- **Bot příkazy**:
    - `/stats` - Okamžitý přehled statistik serveru.
    - `/verify` - Spuštění verifikačního procesu.
    - `/report` - Generování PDF/textových reportů (pouze admin).
    - `/purge` - Hromadné mazání zpráv.

## 💻 Webový Dashboard
Interaktivní rozhraní postavené na **FastAPI** a **Chart.js** s moderním "dark-glass" designem.
- **Přizpůsobitelné rozložení**: Možnost měnit pořadí i velikost widgetů přímo v prohlížeči.
- **Demo režim**: Plně funkční ukázkový režim pro testování bez nutnosti připojení k reálnému serveru.
- **OAuth2 integrace**: Bezpečné přihlášení přes Discord.
- **Live Logs**: Sledování aktivity na serveru v reálném čase přímo v dashboardu.

## 🏗️ Technologický Stack
- **Backend**: Python 3.10+, FastAPI
- **Bot**: discord.py / nextcord
- **Database**: Redis (Valkey) - primární úložiště pro real-time data a cache
- **Frontend**: HTML5, Vanilla CSS (modern glassmorphism UI), Jinja2 templates, Chart.js

## 🛠️ Instalace & Spuštění

### 1. Příprava prostředí
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfigurace
Vytvořte `.env` soubor:
```env
BOT_TOKEN=váš_bot_token
DASHBOARD_TOKEN=token_pro_dashboard
REDIS_URL=redis://localhost:6379/0
```

### 3. Rychlý start
Metricord obsahuje automatizační skript, který spustí Redis i oba procesy najednou:
```bash
chmod +x start.sh
./start.sh
```

## 📝 Licence & Autor
Projekt Metricord je proprietární software vytvořený jako součást bakalářské práce v roce 2026.
Všechna práva vyhrazena.
