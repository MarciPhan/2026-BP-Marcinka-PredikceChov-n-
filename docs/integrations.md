> **Note:** These features (including XP, leveling, and achievements) are additional extensions and are not part of the core functionality evaluated in the bachelor thesis.

# Integrace

Tato stránka popisuje reálně dostupné způsoby propojení CommunityMetrics s okolím: import dat z Discourse a čtení přes REST API. Odchozí webhooky (aplikace sama aktivně volající vaši URL při události) **nejsou v aktuální implementaci k dispozici** — dřívější verze této stránky popisovala plánovanou funkci (`Settings → Webhooks`, HMAC podpis, události typu `dqs_drop`) tak, jako by už existovala; v kódu žádná taková logika není. Pokud takovou funkci potřebujete, zatím ji lze nahradit periodickým čtením [REST API](/api) nebo [exportů dat](/export) z vlastního skriptu.

## Integrace s Discourse

CommunityMetrics umí periodicky importovat témata z nakonfigurované Discourse instance (konektor `scripts/discourse_sync.py`, běží každých 300 sekund a čte endpoint `/latest.json`).

Konfigurace v dashboardu:

1. Otevřete stránku **Přidat Discourse** (`/add-discourse`).
2. Zadejte URL vašeho Discourse fóra (HTTPS) a API klíč a uživatelské jméno vygenerované v administraci Discourse (Settings → API Keys).
3. Uložením se instance přidá a od té chvíle ji `discourse_sync.py` pravidelně synchronizuje.

Adresa se validuje proti SSRF (blokovány jsou loopback, link-local a privátní adresy) jak při přidávání instance, tak znovu při každém běhu periodické synchronizace (`shared/net_security.py`) — pokud se DNS záznam domény po přidání změní na privátní/interní adresu (DNS rebinding), další synchronizace ho odmítne.

Redis klíče:
- `discourse:conf:{guild_id}` — konfigurace propojení (Hash)
- `discourse:synced_topics:{guild_id}` — množina už zpracovaných témat (zajišťuje idempotenci)
- `user:discourse:{user_id}` — seznam propojených komunit (Set)

Synchronizují se jen metadata nových témat (identifikátor, název, zdroj, počet reakcí) — ne kompletní obsah příspěvků, kategorie ani uživatelské profily.

## REST API a automatizace

CommunityMetrics poskytuje dokumentované REST API (viz [API Reference](/api)) a exportní endpointy (viz [Export dat](/export)). V nástrojích jako Zapier nebo Make je lze použít modulem **HTTP Request**, který bude API pravidelně dotazovat (polling) — nejde o obousměrnou webhookovou integraci.
