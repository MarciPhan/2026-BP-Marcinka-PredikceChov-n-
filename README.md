<div align="center">

# CommunityMetrics

**Discord Community Analytics Engine**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](#english) | [Čeština](#čeština)

[Documentation](https://marciphan.github.io/2026-BP-Marcinka-PredikceChov-n-/) • [Architecture](#architecture) • [Installation](#installation)

</div>

---

## English

CommunityMetrics is an analytics engine designed to manage, measure, and analyze Discord servers and Discourse forums. It processes real-time events and API data to calculate user retention, map community growth, evaluate moderator workload, and provide prototype predictive indicators.

Built with Python, FastAPI, and Redis, it features a modular Service-Oriented Architecture (SOA) optimized for high throughput and clean data ingestion.

### Core Features

#### 1. Multi-Platform Data Analytics
- **Discord & Discourse Support:** Event-based real-time ingestion from Discord bots alongside periodic polling via Discourse HTTP API connectors.
- **Behavioral & Retention Modeling:** Automated calculation of user activity trends, DAU/WAU/MAU estimation via HyperLogLog, and prototype retention modeling (Markov chains & Kaplan-Meier survival curves).
- **Moderation Workload Tracking:** Moderator Intervention Index (MII) to monitor community safety and mod team burden.
- **Smart Insights:** Generates actionable feedback for community managers based on shifts in user behavior.

#### 2. High-Performance Infrastructure
- **Asynchronous Execution:** Handles thousands of events per second (EPS) using native Python `asyncio` coupled with `httpx` for Discord API interactions.
- **In-Memory Operations:** Leverages Redis advanced data structures. Uses HyperLogLog (`PFADD`, `PFCOUNT`) for efficient unique user counting and Sorted Sets (`ZADD`) for time-series event mapping, keeping memory footprint minimal.

#### 3. Privacy-by-Design
- **Zero Message Storage:** The platform strictly adheres to data protection standards. Message content is processed and immediately discarded.
- **Anonymized Aggregation:** User events are aggregated into statistical metadata. While temporary cache keys utilize strict Time-to-Live (TTL) expirations, historical analytics events are stored indefinitely until manually deleted.

#### 4. Enterprise Architecture
- **Dependency Injection:** Fully decoupled Repository and Service layers. The underlying data store (Redis) is accessed through a generic `BaseRepository` interface, allowing for seamless technology substitution (e.g., swapping to PostgreSQL) without altering the business logic.
- **Extensible API:** FastAPI provides auto-generated OpenAPI documentation, robust Pydantic validation, and clean endpoint routing for seamless integration.

### Installation

#### Prerequisites
- Python 3.9 or newer
- Redis server (or Valkey) running on the host or inside Docker

#### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Configure environment variables
cp .env.example .env
nano .env  # Supply your BOT_TOKEN and database details

# 3. Start the application (Linux/macOS)
./start.sh
```

The web dashboard and backend API will be available at `http://localhost:8093`.

#### Docker (Production)
For containerized deployments, use the provided Docker Compose configuration to orchestrate the backend, bot, and Redis instances simultaneously.

```bash
cp .env.example .env
docker-compose up -d --build
```

### Discord Bot Configuration
To collect accurate data and process analytics, the Discord Bot requires specific gateway intents. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications):

1. Go to the **Bot** tab.
2. Enable the **Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent` (required exclusively for command processing and metadata logging)
3. Generate an OAuth2 invite link with the `View Channels, Send Messages, Read Message History` permissions and add the bot to your server.

### System Architecture

The codebase adheres strictly to SOLID design principles and the MVC pattern to ensure maintainability:

- **`web/backend/routers/`**: FastAPI controllers handling HTTP requests and session authentication.
- **`web/backend/services/`**: Business logic layer. Contains classes like `AnalyticsService` responsible for math modeling and statistical data interpretation.
- **`web/backend/repositories/`**: Data access interfaces. Provides a clean boundary between the application logic and the database layer.
- **`tests/`**: Contains dependency-injected unit and architecture tests utilizing a `MockRepository` to validate mathematical models without requiring an active database connection.

To execute the isolated test suite:
```bash
pytest tests/
```

### Contributing
Contributions are highly encouraged. When submitting a Pull Request, ensure your code complies with the project style guidelines (`flake8`, `black`). 

---

## Čeština

CommunityMetrics je analytický systém navržený pro správu, měření a analýzu komunit na platformách Discord a Discourse. Zpracovává události v reálném čase i data z Discourse API a aplikuje statistické metody pro odhad aktivity uživatelů, zátěž moderátorů a výpočet indikátorů udržení členů.

Platforma je postavena na Pythonu, FastAPI a Redisu. Vyznačuje se modulární servisně orientovanou architekturou (SOA), která je optimalizována pro vysokou zátěž a čisté oddělení sběru dat od výpočtů.

### Hlavní funkce

#### 1. Víceplatformní analytika
- **Podpora Discordu a Discourse:** Průběžný událostní sběr událostí z Discordu a HTTP API konektor s možností automatické synchronizace pro Discourse fóra.
- **Modelování chování a retence:** Výpočty trendů aktivity, odhady denně aktivních uživatelů (DAU/WAU/MAU) přes HyperLogLog a prototypy matematických modelů retence (Markovovy řetězce, Kaplan-Meier).
- **Sledování moderační zátěže:** Ukazatel Moderator Intervention Index (MII) pro dohled nad bezpečností a vytížením moderačního týmu.
- **Chytré přehledy (Smart Insights):** Generuje doporučení pro administrátory na základě statistických odchylek v aktivitě uživatelů.

#### 2. Vysoce výkonná infrastruktura
- **Asynchronní běh:** Zvládá zpracovat tisíce událostí za vteřinu (EPS) pomocí nativní knihovny `asyncio` a `httpx` pro komunikaci s Discord API.
- **In-Memory operace:** Využívá pokročilé datové struktury Redis. Pro efektivní počítání unikátních uživatelů s minimální spotřebou paměti implementuje HyperLogLog (`PFADD`, `PFCOUNT`) a pro časové řady událostí využívá seřazené množiny (`ZADD`).

#### 3. Ochrana soukromí
- **Žádné ukládání zpráv:** Platforma splňuje nejpřísnější standardy ochrany dat. Obsah zpráv je strojově zpracován za běhu a okamžitě zahozen.
- **Anonymizace a agregace:** Veškeré aktivity uživatelů se agregují výhradně do metadat. Zatímco dočasné cache klíče podléhají automatické expiraci (TTL), historické analytické události jsou uloženy neomezeně až do jejich smazání administrátorem.

#### 4. Enterprise Architektura
- **Dependency Injection:** Kompletní oddělení datové (Repository) a logické (Service) vrstvy. Přístup do Redisu probíhá přes generické rozhraní `BaseRepository`. To umožňuje okamžitou výměnu databázové technologie (např. za PostgreSQL) bez jediného zásahu do analytického kódu.
- **Rozšiřitelné API:** Backend na FastAPI poskytuje automaticky generovanou OpenAPI dokumentaci, typovou validaci pomocí Pydantic a přehledné routování endpointů.

### Instalace

#### Požadavky
- Python 3.9 nebo novější
- Běžící Redis server (nebo Valkey)

#### Lokální spuštění

```bash
# 1. Klonování repozitáře
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Nastavení prostředí
cp .env.example .env
nano .env  # Vyplňte svůj BOT_TOKEN a konfiguraci databáze

# 3. Spuštění (Linux/macOS)
./start.sh
```

Webové rozhraní a API backend budou dostupné na adrese `http://localhost:8093`.

#### Docker (Produkce)
Pro nasazení v kontejnerech použijte přiloženou konfiguraci Docker Compose. Ta automaticky vytvoří propojenou infrastrukturu skládající se z backendu, bota a Redisu.

```bash
cp .env.example .env
docker-compose up -d --build
```

### Konfigurace Discord Bota
Aby mohl bot správně sbírat statistická metadata, musí mít na [Discord Developer Portal](https://discord.com/developers/applications) povolena správná oprávnění:

1. Přejděte na záložku **Bot**.
2. Zapněte následující **Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent` (zcela nezbytné pro detekci aktivity a zpracování příkazů)
3. Vygenerujte OAuth2 odkaz s právy pro čtení a posílání zpráv (View Channels, Send Messages, Read Message History) a přidejte bota na svůj server.

### Architektura systému

Kód repozitáře přísně dodržuje principy SOLID a návrhový vzor MVC:

- **`web/backend/routers/`**: FastAPI kontrolery obsluhující webové rozhraní, autentizaci a API požadavky.
- **`web/backend/services/`**: Logická vrstva obsahující třídy (např. `AnalyticsService`), které zajišťují veškeré matematické výpočty a statistickou interpretaci dat.
- **`web/backend/repositories/`**: Databázové adaptéry s čistým rozhraním oddělujícím byznys logiku od fyzického úložiště.
- **`tests/`**: Sada jednotkových a architektonických testů, které využívají `MockRepository` k validaci matematických modelů zcela bez nutnosti připojení k databázi.

Spuštění testovací sady:
```bash
pytest tests/
```

### Jak přispět
Příspěvky formou Pull Requestů jsou vítány. Před odesláním PR prosím zkontrolujte, že váš kód splňuje formátovací konvence projektu (pomocí `flake8` a `black`).

## Modul Zdraví komunity

Nová stránka `/community-health` rozšiřuje původní objemovou analytiku o kontextové funkce vycházející z dotazníkového šetření mezi správci komunit:

- opakované moderační události mezi stejným členem a moderátorem;
- nevyřešené žádosti o pomoc v explicitně zvolených kanálech;
- časový kontext před odchodem člena bez tvrzení příčinné souvislosti;
- popis rozložení moderační zátěže bez automatického hodnocení kvality moderátora;
- porovnání zájmu o Discord Scheduled Event se skutečnou účastí v připojeném hlasovém kanálu;
- měřitelné podklady pro lidské rozhodování o rolích doplněné ručním stanoviskem týmu.

Obsah zpráv se neukládá. Ukládají se pouze identifikátory, čas, kanál, vazba odpovědi, počet reakcí a další nezbytná metadata s expirací.

### Nastavení

1. Otevřete `/community-health` jako administrátor.
2. Vyberte typ komunity a zapněte pouze relevantní moduly.
3. Pro analýzu pomoci vložte ID podpůrných kanálů.
4. Historická data lze doplnit příkazem `/health backfill` (maximálně 180 dní).

### Interní API

Dokumentace aktuálně nasazených FastAPI endpointů je dostupná na `/docs`. Backend API slouží přednostně pro interakci s webovým dashboardem (využívá Session/CSRF ověřování).

Příklady nasazených endpointů (viz `docs/api.md`):
- `GET /api/analytics-tools`
- `GET /api/predictions-data`
- `POST /api/discourse/add`

### Testy

```bash
pytest -q
```

Aktuální sada obsahuje také testy kontextové analytiky a principu lidského rozhodování.
