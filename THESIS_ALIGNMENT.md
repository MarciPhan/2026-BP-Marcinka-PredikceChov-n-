# Odpovídající implementace pro Bakalářskou Práci

Tento dokument mapuje funkční a nefunkční požadavky zadané v bakalářské práci na konkrétní implementaci a testy.

| Požadavek BP | Implementace | Test | Stav |
| --- | --- | --- | --- |
| FR-01 Discord events | `bot/commands/activity.py` | `tests/test_bot_events.py` | ✅ |
| FR-02 Discourse API | `scripts/discourse_sync.py` | `tests/test_discourse_sync.py` | ✅ |
| FR-03 Redis event model | `shared/models.py`, Redis klíče `events:msg:*` | `tests/test_redis.py` | ✅ |
| FR-04 Activity | `bot/commands/activity.py` | `tests/test_bot_events.py` | ✅ |
| FR-05 Channels/topics/time | `bot/commands/activity.py` (časy) | `tests/test_bot_events.py` | ✅ |
| FR-06 Response analytics | `analytics_service.py` (Engagement Score) | `tests/test_thesis_models.py` | ✅ |
| FR-07 Moderation | `analytics_service.py` (MII, action events) | `tests/test_thesis_models.py` | ✅ |
| FR-08 Filters | Dashboard UI a `api.py` endpointy | UI Testy | ✅ |
| FR-09 REST API | `web/backend/routers/api.py` | `tests/test_api.py` | ✅ |
| FR-10 Missing data | `analytics_service.py`, fallback handling | `tests/test_thesis_models.py` | ✅ |
| FR-11 RBAC | `web/backend/security.py`, dashboard auth | `tests/test_security.py` | ✅ |
| FR-14 CSV/JSON export | `web/backend/routers/api.py` | API Testy | ✅ |
| FR-15 GDPR export/delete | `bot/commands/gdpr.py` | `tests/test_bot_events.py` | ✅ |
| NFR-01 Performance | Asynchronní zpracování `asyncio` a Redis | - | ✅ |
| NFR-02 Scalability | Oddělené instance bota a API rozhraní | Architektonický návrh | ✅ |
| NFR-03 Security | CSRF tokeny, Rate limiting, SSRF ochrana | `tests/test_security.py` | ✅ |
| NFR-04 Privacy | Minimalizace dat, uchovávání pouze metadat | `tests/test_bot_events.py` | ✅ |
| NFR-05 Data Retention | Centralizovaná konfigurace (90 dní) v `config.py` | `tests/test_bp_align.py` | ✅ |
| NFR-06 Availability | Kontejnerizace pomocí Docker Compose | Architektonický návrh | ✅ |
| NFR-07 API Docs | `docs/api.md`, Swagger v FastAPI | - | ✅ |
| NFR-08 Extensibility | DI (Dependency Injection), SOA návrh | `tests/test_architecture.py` | ✅ |

> **Poznámka:** Veškeré prediktivní modely (Markovovy řetězce, Kaplan-Meier, Engagement Score) byly upraveny a správně označeny jako **experimentální prototypy** v souladu s povahou a očekáváním zadání BP, a případné zavádějící heuristické nahrazení (např. odvozené MAU, umělý churn risk) byly zrušeny. U implementací mimo rámec BP (např. XP systém) je v příslušné dokumentaci jasné označení o rozšiřujícím charakteru, který nesouvisí přímo s evaluací bakalářské práce.
