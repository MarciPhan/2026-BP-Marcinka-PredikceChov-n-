<div align="center">

# CommunityMetrics

**Discord Community Analytics & Prediction Engine**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](#english) | [Čeština](#čeština)

[Documentation](https://marciphan.github.io/2026-BP-Marcinka-PredikceChov-n-/) • [Architecture](#architecture)

</div>

---

## English

CommunityMetrics is an analytics and prediction engine designed for Discord communities. It processes real-time events to model user retention, predict server growth, and audit community health using applied data science models (Markov Chains, Kaplan-Meier).

Built with Python, FastAPI, and Redis, it features a modular Service-Oriented Architecture (SOA) and a responsive Glassmorphism web dashboard.

### Features
- **Predictive Modeling:** Built-in calculation of user churn probability, daily active users (DAU) estimation, and growth trends.
- **High Throughput:** Designed to process high-volume events using asynchronous execution (`asyncio`) and Redis in-memory data structures.
- **Privacy-by-Design:** Message content is not stored. Events are anonymized, aggregated into metadata, and subject to strict TTL expiration.
- **Modular Architecture:** Fully decoupled repository and service layers utilizing Dependency Injection, enabling seamless database substitution.
- **Web Dashboard:** Integrated responsive frontend providing visualization of community metrics.

### Installation

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

cp .env.example .env
# Edit .env and supply your BOT_TOKEN

# Local Setup (Linux/macOS)
./start.sh

# Docker Setup
docker-compose up -d --build
```
The web dashboard will be available at `http://localhost:8092`.

### Configuration
In the [Discord Developer Portal](https://discord.com/developers/applications), ensure the following **Privileged Gateway Intents** are enabled for your bot:
- Presence Intent
- Server Members Intent
- Message Content Intent

### Architecture
The codebase adheres to SOLID principles and the MVC pattern:
- `web/backend/routers/` - FastAPI controllers handling HTTP requests.
- `web/backend/services/` - Business logic and predictive algorithms.
- `web/backend/repositories/` - Data access layer interfaces.
- `tests/` - Architecture tests utilizing `MockRepository` to validate logic without a running database.

Run tests using: `python3 tests/test_architecture.py`

---

## Čeština

CommunityMetrics je analytický a prediktivní nástroj navržený pro Discord komunity. Zpracovává události v reálném čase k modelování retence uživatelů, predikci růstu serveru a auditu komunity s využitím aplikovaných modelů datové vědy (Markovovy řetězce, Kaplan-Meier).

Projekt je postaven na Pythonu, FastAPI a Redisu. Vyznačuje se modulární servisně orientovanou architekturou (SOA) a responzivním webovým rozhraním ve stylu Glassmorphism.

### Vlastnosti
- **Prediktivní modelování:** Integrovaný výpočet pravděpodobnosti odchodu uživatelů (churn), odhad denně aktivních uživatelů (DAU) a trendů růstu.
- **Vysoká propustnost:** Navrženo pro zpracování velkého objemu událostí pomocí asynchronního běhu (`asyncio`) a datových struktur Redis.
- **Ochrana soukromí:** Obsah zpráv není ukládán. Události jsou anonymizovány, agregovány do metadat a podléhají striktní expiraci (TTL).
- **Modulární architektura:** Plně oddělená datová a servisní vrstva využívající návrhový vzor Dependency Injection, což umožňuje snadnou záměnu databáze.
- **Webový Dashboard:** Integrovaný responzivní frontend poskytující vizualizaci komunitních metrik.

### Instalace

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

cp .env.example .env
# Upravte soubor .env a doplňte váš BOT_TOKEN

# Lokální spuštění (Linux/macOS)
./start.sh

# Docker spuštění
docker-compose up -d --build
```
Webový dashboard bude dostupný na adrese `http://localhost:8092`.

### Konfigurace
Na [Discord Developer Portálu](https://discord.com/developers/applications) se ujistěte, že má váš bot povolena následující oprávnění (**Privileged Gateway Intents**):
- Presence Intent
- Server Members Intent
- Message Content Intent

### Architektura
Kód dodržuje principy SOLID a návrhový vzor MVC:
- `web/backend/routers/` - FastAPI kontrolery obsluhující HTTP požadavky.
- `web/backend/services/` - Byznysová logika a prediktivní algoritmy.
- `web/backend/repositories/` - Rozhraní vrstvy přístupu k datům.
- `tests/` - Architektonické testy využívající `MockRepository` k validaci logiky bez spuštěné databáze.

Spuštění testů: `python3 tests/test_architecture.py`
