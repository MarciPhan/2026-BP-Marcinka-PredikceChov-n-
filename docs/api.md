# Referenční příručka API (RESTful)

Rozhraní API CommunityMetrics umožňuje programový přístup k nasbíraným datům a správu konfigurace z pohledu webového dashboardu. 

::: tip Základní URL (Base URL)
`https://dashboard.communitymetrics.app/` (nebo lokální adresa vaší instance)
:::

## Zabezpečení a autentizace

API podporuje dva režimy autentizace: session-based pro webový dashboard a API klíče pro externí klienty.

### Autentizace pomocí sezení (Session-based)
Po přihlášení přes Discord OAuth2 systém vytvoří podepsanou session cookie (`itsdangerous`, `SameSite=Lax`). Pro všechny stavové metody (`POST`, `DELETE`) je vyžadován platný **CSRF token**, který systém ověřuje proti timing útokům pomocí kryptograficky bezpečné funkce `secrets.compare_digest` v `web/backend/security.py`.

### Autentizace pomocí API klíče (X-API-Key)
Externí klienti mohou přistupovat k REST API pomocí hlavičky `X-API-Key`. Klíče mají prefix `mtr_` a jsou uloženy v Redis jako SHA-256 digest (`shared/community_health.py: api_key_digest`). Generování klíčů je k dispozici v dashboardu.

> [!TIP]
> Interaktivní OpenAPI dokumentace je dostupná na `/api/docs` (Swagger UI), OpenAPI JSON schéma na `/api/openapi.json`.

---

## Endpointy: Analytika a metriky

### Analytické nástroje (MII, Engagement Score)
Vrátí aktuální vypočítané metriky pro zvolené časové okno. Využívá se pro vykreslení analytické stránky v dashboardu.

**`GET` /api/analytics-tools**

| Parametr | Typ | Povinný | Popis |
| :--- | :--- | :--- | :--- |
| `start_date` | String | Ne | Počáteční datum (YYYY-MM-DD). |
| `end_date` | String | Ne | Koncové datum (YYYY-MM-DD). |

**Příklad odpovědi (`200 OK`):**
```json
{
  "status": "ok",
  "trends": { ... },
  "engagement": { 
      "score": 85,
      "components": { "users": 80, "messages": 90, "reactions": 85 } 
  },
  "insights": [ ... ],
  "dqs": { "score": 95, "is_sufficient": true }
}
```

### Prototyp predikčních dat
Vrátí data pro zobrazení historických trendů, odhadovaného růstu (Markov, lineární trend se sezónností) a analýzy setrvání v aktivitě.

**`GET` /api/predictions-data**

---

## Endpointy: Integrace a Administrace

### Přidání fóra Discourse
Tento endpoint umožňuje administrátorům napojit fórum Discourse. Obsahuje zabudovanou robustní validaci **proti SSRF (Server-Side Request Forgery)** a DNS Rebinding útokům, blokující privátní a lokální adresy.

**`POST` /api/discourse/add**

| Parametr (Form) | Typ | Povinný | Popis |
| :--- | :--- | :--- | :--- |
| `url` | String | Ano | URL adresa Discourse fóra. |
| `api_key` | String | Ano | API klíč s oprávněním ke čtení. |
| `api_user` | String | Ano | API Username na fóru. |
| `csrf_token`| String | Ano | Bezpečnostní token ze sezení. |

### Ruční smazání dat
Smaže veškerá analytická data (Redis klíče) pro aktuálně vybraný server. Vyžaduje administrátorská oprávnění a správný CSRF token.

**`POST` /api/delete-server-data**

> [!TIP]
> Kompletní schéma API je k dispozici na `/api/docs` (Swagger UI). FastAPI automaticky generuje OpenAPI dokumentaci ze všech registrovaných routerů (`auth`, `pages`, `api`, `settings`, `community_health`).
