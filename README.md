<div align="center">

# CommunityMetrics

**Discord Community Analytics & Prediction Engine**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Documentation](https://marciphan.github.io/2026-BP-Marcinka-PredikceChov-n-/) • [Installation](#installation) • [Architecture](#architecture)

</div>

---

CommunityMetrics is a high-performance analytics and prediction engine designed for large-scale Discord communities. It processes real-time events to model user retention, predict server growth, and audit community health using applied data science models (Markov Chains, Kaplan-Meier, HyperLogLog).

Built with Python, FastAPI, and Redis, it features a modular architecture that easily scales horizontally.

## Features

- **Predictive Modeling:** Built-in calculation of user churn probability, daily active users (DAU) estimation, and long-term growth trends.
- **High Throughput:** Designed to process thousands of events per second using `asyncio` and Redis in-memory data structures.
- **Privacy-by-Design:** No message content is stored. Events are anonymized, aggregated into metadata, and subject to strict TTL expiration (GDPR compliant).
- **Service-Oriented Architecture (SOA):** Fully decoupled repository and service layers utilizing Dependency Injection. The underlying data store can be swapped without altering business logic.
- **Web Dashboard:** Integrated responsive frontend providing immediate visualization of community metrics.

## Installation

### Prerequisites
- Python 3.9 or newer
- Redis server (or Valkey)

### Local Setup

Clone the repository and run the automated initialization script:

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-.git
cd 2026-BP-Marcinka-PredikceChov-n-

# Copy the example configuration
cp .env.example .env

# Edit .env and supply your BOT_TOKEN
nano .env

# Initialize environment and start services
./start.sh
```

The web dashboard will be available at `http://localhost:8092`.

### Docker (Production)

For containerized deployment, use the provided Docker Compose configuration:

```bash
cp .env.example .env
docker-compose up -d --build
```

## Configuration

To collect accurate data, the Discord Bot requires specific intents. In the [Discord Developer Portal](https://discord.com/developers/applications):

1. Navigate to the **Bot** tab.
2. Enable the following **Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent` (required for parsing command interactions and message counts)
3. Invite the bot to your server using the `Administrator` permission scope.

## Architecture

The codebase strictly adheres to SOLID principles and the MVC pattern:

- `web/backend/routers/` - FastAPI controllers handling HTTP requests.
- `web/backend/services/` - Business logic and predictive algorithms (e.g., `AnalyticsService`).
- `web/backend/repositories/` - Data access layer interfaces. Provides a clean boundary between the application and the Redis database.
- `tests/` - Includes architecture tests utilizing `MockRepository` to validate logic in isolation without a running Redis instance.

Run tests using:
```bash
python3 tests/test_architecture.py
```

## Contributing

Contributions are welcome. Please ensure that your pull requests adhere to the existing code style (checked via `flake8` and `black`). 

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewAnalyticModel`)
3. Commit your changes (`git commit -m 'Add new model'`)
4. Push to the branch (`git push origin feature/NewAnalyticModel`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
