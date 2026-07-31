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

CommunityMetrics is a high-performance analytics engine designed to manage, measure, and analyze large-scale Discord communities. It processes real-time events to model user retention, map server growth, and audit community health using applied data science models (Markov Chains, Kaplan-Meier).

Built with Python, FastAPI, and Redis, it features a modular Service-Oriented Architecture (SOA) optimized for high throughput and horizontal scalability.

### Core Features

#### 1. Data-Driven Analytics
- **Behavioral Modeling:** Built-in calculation of user churn probability, daily active users (DAU) estimation, and long-term growth trends without storing private messages.
- **Community Health Audit:** Automatically assesses server configuration, moderation metrics, and active member ratios to calculate a comprehensive security and engagement score.
- **Smart Insights:** Generates actionable feedback for community managers based on statistically significant shifts in user behavior.

#### 2. High-Performance Infrastructure
- **Asynchronous Execution:** Handles thousands of events per second (EPS) using native Python `asyncio` coupled with `httpx` for Discord API interactions.
- **In-Memory Operations:** Leverages Redis advanced data structures. Uses HyperLogLog (`PFADD`, `PFCOUNT`) for efficient unique user counting and Sorted Sets (`ZADD`) for time-series event mapping, keeping memory footprint minimal.

#### 3. Privacy-by-Design
- **Zero Message Storage:** The platform strictly adheres to data protection standards. Message content is processed and immediately discarded.
- **Anonymized Aggregation:** User events are aggregated into statistical metadata, and all temporary event keys are subjected to strict Time-to-Live (TTL) expiration mechanisms.

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

The web dashboard and backend API will be available at `http://localhost:8092`.

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
3. Generate an OAuth2 invite link with the `Administrator` permission scope and add the bot to your server.

### System Architecture

The codebase adheres strictly to SOLID design principles and the MVC pattern to ensure maintainability:

- **`web/backend/routers/`**: FastAPI controllers handling HTTP requests and session authentication.
- **`web/backend/services/`**: Business logic layer. Contains classes like `AnalyticsService` responsible for math modeling and statistical data interpretation.
- **`web/backend/repositories/`**: Data access interfaces. Provides a clean boundary between the application logic and the database layer.
- **`tests/`**: Contains dependency-injected unit and architecture tests utilizing a `MockRepository` to validate mathematical models without requiring an active database connection.

To execute the isolated test suite:
```bash
python3 tests/test_architecture.py
```

### Contributing
Contributions are highly encouraged. When submitting a Pull Request, ensure your code complies with the project style guidelines (`flake8`, `black`). 

---

## Čeština

CommunityMetrics je výkonný analytický systém navržený pro správu, měření a analýzu rozsáhlých komunit na platformě Discord. Zpracovává události v reálném čase a aplikuje modely datové vědy (Markovovy řetězce, Kaplan-Meier) pro výpočet retence uživatelů, mapování růstu serveru a komplexní audit zdraví komunity.

Platforma je postavena na Pythonu, FastAPI a Redisu. Vyznačuje se plně modulární servisně orientovanou architekturou (SOA), která je optimalizována pro vysokou zátěž a horizontální škálovatelnost.

### Hlavní funkce

#### 1. Analytika založená na datech
- **Modelování chování:** Integrované výpočty pravděpodobnosti odchodu uživatelů (churn), odhady denně aktivních uživatelů (DAU) a analýza dlouhodobých trendů růstu komunity.
- **Audit komunity:** Systém automaticky vyhodnocuje konfiguraci serveru, efektivitu moderace a poměr aktivních členů, na základě čehož generuje bezpečnostní skóre a skóre zapojení.
- **Chytré přehledy (Smart Insights):** Generuje konkrétní doporučení pro administrátory na základě statisticky významných odchylek v aktivitě uživatelů.

#### 2. Vysoce výkonná infrastruktura
- **Asynchronní běh:** Zvládá zpracovat tisíce událostí za vteřinu (EPS) pomocí nativní knihovny `asyncio` a `httpx` pro komunikaci s Discord API.
- **In-Memory operace:** Využívá pokročilé datové struktury Redis. Pro efektivní počítání unikátních uživatelů s minimální spotřebou paměti implementuje HyperLogLog (`PFADD`, `PFCOUNT`) a pro časové řady událostí využívá seřazené množiny (`ZADD`).

#### 3. Ochrana soukromí
- **Žádné ukládání zpráv:** Platforma splňuje nejpřísnější standardy ochrany dat. Obsah zpráv je strojově zpracován za běhu a okamžitě zahozen.
- **Anonymizace a agregace:** Veškeré aktivity uživatelů se agregují výhradně do metadat. Všechny dočasné klíče v databázi navíc podléhají automatické expiraci (TTL).

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

Webové rozhraní a API backend budou dostupné na adrese `http://localhost:8092`.

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
3. Vygenerujte OAuth2 odkaz s právy `Administrator` a přidejte bota na svůj server.

### Architektura systému

Kód repozitáře přísně dodržuje principy SOLID a návrhový vzor MVC:

- **`web/backend/routers/`**: FastAPI kontrolery obsluhující webové rozhraní, autentizaci a API požadavky.
- **`web/backend/services/`**: Logická vrstva obsahující třídy (např. `AnalyticsService`), které zajišťují veškeré matematické výpočty a statistickou interpretaci dat.
- **`web/backend/repositories/`**: Databázové adaptéry s čistým rozhraním oddělujícím byznys logiku od fyzického úložiště.
- **`tests/`**: Sada jednotkových a architektonických testů, které využívají `MockRepository` k validaci matematických modelů zcela bez nutnosti připojení k databázi.

Spuštění testovací sady:
```bash
python3 tests/test_architecture.py
```

### Jak přispět
Příspěvky formou Pull Requestů jsou vítány. Před odesláním PR prosím zkontrolujte, že váš kód splňuje formátovací konvence projektu (pomocí `flake8` a `black`).
