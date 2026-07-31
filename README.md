<div align="center">

# 📊 CommunityMetrics

**Prediktivní analytika a komplexní správa pro Discord komunity.**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Webová Dokumentace](https://marciphan.github.io/2026-BP-Marcinka-PredikceChov-n-/) • [Funkce](#-klíčové-vlastnosti) • [Instalace](#-rychlý-start) • [Architektura](#-modulární-architektura)

</div>

---

**CommunityMetrics** je open-source platforma nové generace pro analýzu, predikci a správu velkých Discord komunit. 
Nesoustředí se pouze na sčítání zpráv; využívá matematické modely (Markovovy řetězce, Kaplan-Meier, HyperLogLog) k tomu, aby komunitním manažerům nabídla hluboký vhled do retence uživatelů, zdraví serveru a predikce budoucího růstu.

Vše je zabaleno v extrémně rychlé asynchronní architektuře postavené na **FastAPI** a **Redis**, doplněné o dechberoucí skleněný (Glassmorphism) webový dashboard.

---

## ✨ Klíčové vlastnosti

- 📈 **Real-time Predikce:** Automatické modelování růstu, pravděpodobnosti odchodu (churn) a odhad denně aktivních uživatelů (DAU) pomocí zabudovaných matematických modelů.
- ⚡ **Extrémní výkon:** Zpracování desítek tisíc událostí za vteřinu (10k+ EPS) s využitím asynchronní smyčky (`asyncio`) a Redis HyperLogLog agregací v reálném čase.
- 🧩 **100% Modulární architektura:** Implementace *Dependency Injection* a *Repository Patternu* zajišťuje čisté oddělení prezentační, byznysové a datové vrstvy. Databázi lze vyměnit jediným řádkem.
- 🔒 **Privacy-First (GDPR):** Systém neshromažďuje texty zpráv. Veškerá data jsou v Redisu anonymizována a zahozena po uplynutí retenční doby (TTL).
- 🎨 **Moderní Dashboard:** Responzivní, interaktivní a plně přizpůsobitelné webové rozhraní (Liquid Glass UI) pro prohlížení analytiky napříč zařízeními.

---

## 🏗 Modulární Architektura

CommunityMetrics dodržuje **SOLID** principy. Jádro běží na **Service-Oriented Architecture (SOA)**:

1. **Controllers (Routers):** Modulární FastAPI endpointy zpracovávají požadavky z webu (`web/backend/routers/`).
2. **Service Layer (`services/`):** Zde sídlí byznysová logika a náročné výpočty (např. generování *Engagement Score*). Injektuje se přes `BaseAnalyticsService` rozhraní.
3. **Repository Layer (`repositories/`):** Abstrakce databázové vrstvy. Aplikace nevyužívá přímo Redis klienty, ale abstraktní vrstvu `BaseRepository`. Tím se stává technologie pro ukládání dat zcela zastupitelnou a plně testovatelnou.
4. **Data Store:** Výchozí implementací je asynchronní **Redis**, který poskytuje in-memory caching a event brokering pro bota a web.

> 👉 Více o architektuře najdete v naší [oficiální dokumentaci](https://marciphan.github.io/2026-BP-Marcinka-PredikceChov-n-/).

---

## 🚀 Rychlý start

Zprovoznění platformy zabere méně než 2 minuty. Podporujeme spuštění lokálně přes skripty i v Dockeru.

### Požadavky
- **Python 3.9+**
- **Redis** nebo Valkey (pro lokální spuštění bez Dockeru)

### Varianta 1: Automatický instalační skript
Naše repozitáře obsahují chytré spouštěcí skripty pro Linux i Windows, které vyřeší virtuální prostředí a závislosti automaticky.

```bash
# 1. Klonování repozitáře
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Vytvoření konfigurace
cp .env.example .env
nano .env  # Vyplňte minimálně BOT_TOKEN

# 3. Spuštění
./start.sh   # Pro Linux/macOS
# start.bat  # Pro Windows
```

Webový dashboard bude ihned dostupný na **http://localhost:8092**.

### Varianta 2: Docker Compose (Doporučeno pro produkci)
Nejrychlejší způsob, jak nastartovat celou infrastrukturu (Redis + Bot + Backend) najednou.

```bash
cp .env.example .env
docker-compose up -d --build
```

---

## 🔑 Konfigurace Discord Bota

Pro správné fungování datové analytiky je nutné botovi udělit správná oprávnění na Discord Developer portálu:

1. Běžte na [Discord Developer Portal](https://discord.com/developers/applications).
2. Vytvořte aplikaci a v záložce **Bot** vygenerujte **Token** (vložte ho do `.env` jako `BOT_TOKEN`).
3. ⚠️ **Zcela klíčové:** V sekci Bot zapněte **Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent`
4. Vygenerujte zvací odkaz s právem `Administrator` a pozvěte bota na svůj server.

---

## 💻 Vývoj a Testování

Díky nasazení *Dependency Injection* obsahuje projekt vestavěné testy architektury. Ty simulují chod celé služby pouze s využitím `MockRepository` v paměti.

**Spuštění testů architektury:**
```bash
python3 tests/test_architecture.py
```

Výstup prokáže výpočty nezávislé na jakékoli běžící databázi.

---

## 🤝 Jak přispět?

Příspěvky (Pull Requests) od komunity jsou vřele vítány! Můžete pomoci s:
- Vylepšením Machine Learning modelů v `analytics_service.py`
- Tvorbou nových UI komponent do dashboardu
- Překladem dokumentace

Před otevřením PR se prosím ujistěte, že váš kód prochází přes linter (`flake8`) a formátovač (`black`).

---

## 📜 Licence

Tento software byl uvolněn pro komunitu pod [MIT licencí](LICENSE). Můžete jej volně používat, upravovat i nasazovat komerčně. Pro detaily si přečtěte soubor `LICENSE`.
