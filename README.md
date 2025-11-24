# 📊 Real-time Analytický Dashboard

Komplexní analytický dashboard pro monitorování Discord a Discourse komunit v reálném čase s analýzou historických dat.

## ✨ Funkce

- **Real-time Monitoring**: Živé WebSocket aktualizace pro okamžité sledování zpráv
- **Podpora Dvou Platforem**: Sběr dat z Discordu i Discourse
- **Bohaté Analýzy**: 17+ interaktivních grafů a vizualizací
- **Ochrana Soukromí**: Všechny identity uživatelů jsou anonymizovány pomocí SHA-256 hashování
- **Historická Data**: Automatické načítání a ukládání kompletní historie zpráv
- **Pokročilé Metriky**: DAU, WAU, MAU, engagement ratio, activity heatmapy

## 📈 Metriky Dashboardu

### Základní Statistiky
- Celkový počet zpráv napříč platformami
- Zprávy za hodinu/den/týden/měsíc
- Aktivní uživatelé (DAU/WAU/MAU)
- Rozdělení podle platforem (Discord vs Discourse)

### Vizualizace
- Timeline živých zpráv
- Hodinové a denní vzory aktivity
- Heatmapy zapojení uživatelů
- Distribuce délek zpráv
- Sledování kumulativního růstu
- Trendy akvizice nových uživatelů
- Engagement ratios (DAU/WAU, DAU/MAU)

## 🏗️ Architektura

```
├── backend/
│   ├── models.py              # Datové modely
│   ├── redis_db.py            # Redis databázová vrstva
│   └── app.py                 # FastAPI server
├── collectors/
│   ├── discord_collector.py   # Discord sběrač dat
│   └── discourse_collector.py # Discourse API sběrač
├── frontend/
│   └── index.html             # Dashboard UI
├── config.yaml                # Konfigurační soubor
└── requirements.txt           # Python závislosti
```

## 🚀 Instalace

### Požadavky
- Python 3.8+
- Redis server
- Discord bot token
- Discourse API přístupové údaje

### Nastavení

1. **Klonování repozitáře**
```bash
git clone <repository-url>
cd analytics-dashboard
```

2. **Instalace závislostí**
```bash
pip install -r requirements.txt
```

3. **Konfigurace Redis**
```bash
# Instalace Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Spuštění Redis
redis-server
```

4. **Vytvoření konfiguračního souboru**
```bash
cp config.yaml.example config.yaml
```

Upravte `config.yaml` s vašimi přihlašovacími údaji:
```yaml
redis:
  host: "127.0.0.1"
  port: 6379
  db: 0
  password: null
  salt: "váš-náhodný-salt-řetězec"

discord:
  token: "VÁŠ_DISCORD_BOT_TOKEN"

discourse:
  url: "https://vaše-fórum.cz"
  api_key: "VÁŠ_API_KLÍČ"
  api_user: "VAŠE_UŽIVATELSKÉ_JMÉNO"
```

5. **Spuštění aplikace**
```bash
python backend/app.py
```

6. **Přístup k dashboardu**
Otevřete prohlížeč a přejděte na:
```
http://localhost:8000
```

## 🔧 Konfigurace

### Nastavení Discord Bota

1. Jděte na [Discord Developer Portal](https://discord.com/developers/applications)
2. Vytvořte novou aplikaci
3. Přejděte do sekce "Bot" a vytvořte bota
4. Povolte "Message Content Intent"
5. Zkopírujte bot token do `config.yaml`
6. Pozvěte bota na váš server s příslušnými oprávněními

### Nastavení Discourse API

1. Přejděte do administrátorského panelu vašeho Discourse
2. Navigujte do sekce API
3. Vytvořte nový API klíč
4. Nastavte API klíč a uživatelské jméno v `config.yaml`

### Konfigurace Redis

Aplikace používá Redis pro:
- Ukládání a získávání zpráv
- Sledování aktivity uživatelů
- Real-time pub/sub messaging
- Správu checkpointů pro sběrače dat

## 📡 API Endpointy

### REST API
- `GET /api/messages` - Získání nedávných zpráv
- `GET /api/statistics` - Získání agregovaných statistik
- `GET /api/health` - Health check endpoint

### WebSocket
- `WS /ws` - Real-time stream zpráv

## 🔐 Soukromí & Bezpečnost

- **Anonymizace Uživatelů**: Všechna uživatelská ID jsou hashována pomocí SHA-256 + salt
- **Žádná Osobní Data**: Ukládány jsou pouze anonymizované hashe a metadata zpráv
- **Bezpečná Konfigurace**: Citlivé přihlašovací údaje v `config.yaml` (gitignored)

## 🛠️ Vývoj

### Struktura Projektu

**Backend** (`backend/`)
- `app.py`: FastAPI server, WebSocket handling, API endpointy
- `models.py`: Datové modely pro zprávy a statistiky
- `redis_db.py`: Redis operace a persistence dat

**Sběrače** (`collectors/`)
- `discord_collector.py`: Discord bot pro sběr zpráv
- `discourse_collector.py`: Discourse API polling

**Frontend** (`frontend/`)
- `index.html`: Single-page dashboard s Chart.js

### Tok Dat

```
Discord/Discourse → Sběrače → Redis → WebSocket → Dashboard
                                  ↓
                            REST API → Dashboard (počáteční načtení)
```

## 📊 Typy Grafů

1. **Live Timeline**: Tok zpráv v reálném čase
2. **Rozdělení Zdrojů**: Porovnání platforem (koláčový graf)
3. **Hodinová Aktivita**: Rozložení aktivity za 24 hodin
4. **Vzory Podle Dnů**: Analýza podle dní v týdnu
5. **Délka Zpráv**: Průměrný počet znaků za hodinu
6. **Monitor Rychlosti**: Zpráv za minutu
7. **Akvizice Uživatelů**: Noví uživatelé denně/měsíčně
8. **Engagement Metriky**: Trendy DAU/WAU/MAU
9. **Engagement Ratios**: Indikátory udržení uživatelů
10. **Histogram**: Distribuce délek zpráv
11. **Kumulativní Růst**: Celkový počet zpráv v čase
12. **Heatmapa**: Matice aktivity Hodina × Den

## 🐛 Řešení Problémů

### Problémy s Redis Připojením
```bash
# Zkontrolujte, zda běží Redis
redis-cli ping
# Mělo by vrátit: PONG
```

### Discord Bot se Nepřipojuje
- Ověřte bot token v `config.yaml`
- Zkontrolujte, že je povolen "Message Content Intent"
- Ujistěte se, že bot má správná oprávnění na serveru

### Chyby Discourse API
- Ověřte API klíč a uživatelské jméno
- Zkontrolujte rate limiting (výchozí: 1 req/sekunda)
- Potvrďte, že API klíč má oprávnění pro čtení

### Odpojování WebSocketu
- Zkontrolujte nastavení firewallu
- Ověřte konfiguraci proxy
- Monitorujte konzoli prohlížeče pro chyby

## ⚠️ Důležité Poznámky

- **Nikdy necommitujte `config.yaml`** - Obsahuje citlivé přihlašovací údaje
- Použijte silný, náhodný salt pro anonymizaci uživatelů
- Pravidelně zálohujte vaši Redis databázi
- Monitorujte využití paměti Redis pro velké komunity
- Zvažte rate limiting při škálování na více serverů

## 📞 Podpora

Pro problémy a dotazy:
- Otevřete issue na GitHubu
- Zkontrolujte existující issues pro řešení
- Projděte si sekci řešení problémů

---

**Vytvořeno s:** Python, FastAPI, Redis, Discord.py, Chart.js
