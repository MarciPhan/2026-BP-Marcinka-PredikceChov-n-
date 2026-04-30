# Referenční příručka API (RESTful)

Rozhraní API Metricord umožňuje programový přístup k nasbíraným datům, integraci s externími systémy a automatizaci správy. Celé API je postaveno na standardu REST s výstupy ve formátu JSON.

::: tip Základní URL (Base URL)
`https://dashboard.metricord.app/api/v1`
:::

## Zabezpečení a autentizace

Metricord API využívá dva hlavní způsoby ověření identity.

### A. Autentizace pomocí sezení (Session-based)
Tuto metodu využívá webový dashboard. Po přihlášení přes Discord systém vytvoří **HTTP-only cookie** se zašifrovaným ID uživatele. Tento přístup vás chrání před útoky typu XSS a CSRF.

### B. Bearer Token (Statický klíč)
Pro automatizované skripty použijte statické API klíče:
-   Vložte klíč do hlavičky požadavku: `Authorization: Bearer <vas_token>`.
-   API klíč vygenerujte v nastavení svého profilu na dashboardu.

> [!WARNING]
> API klíč považujte za ekvivalent hesla. Nikdy jej nepoužívejte ve veřejných skriptech na straně klienta (JavaScript v prohlížeči).

## Omezení četnosti požadavků (Rate Limiting)

Pro zajištění stability systému aplikujeme na každý uzel algoritmus **Token Bucket**:
-   **Limit:** Maximálně 60 požadavků za minutu na jednu IP adresu.
---

## Endpointy: Analytika a metriky

### Získání klíčových metrik serveru
Vrátí aktuální hodnoty DAU, MAU a Engagement Score.

**`GET` /guild/{guild_id}/metrics**

| Parametr | Typ | Povinný | Popis |
| :--- | :--- | :--- | :--- |
| `range` | Integer | Ne | Počet dní historie (výchozí 7). |

**Příklad odpovědi (`200 OK`):**
```json
{
  "guild_id": "123456789012345678",
  "metrics": {
    "active_users_dau": 1540,
    "active_users_mau": 8500,
    "total_messages": 125000,
    "engagement_score": 88.5
  },
  "metadata": { "cached": true, "expiry": "2026-04-13T18:30:00Z" }
}
```

### Data pro Heatmapu aktivity
Vrátí matici 7 × 24 s intenzitou zpráv pro vizualizaci.

**`GET` /guild/{guild_id}/metrics/heatmap**

---

## Endpointy: Predikce a AI

### Předpověď odchodu (Churn Prediction)
Vypočítá pravděpodobnost odchodu uživatelů v následujících 7 dnech.

**`GET` /guild/{guild_id}/predict/churn**

**Příklad odpovědi (`200 OK`):**
```json
{
  "churn_probability_7d": 0.12,
  "at_risk_users_count": 42,
  "confidence_score": 0.94
}
```

---

## Endpointy: Administrace a konfigurace

### Aktualizace konfigurace XP systému
Změní parametry pro přidělování zkušenostních bodů.

**`POST` /admin/config/update**

**Tělo požadavku (JSON):**
```json
{
  "xp_per_msg": 15,
  "voice_multiplier": 1.5
}
```

> [!TIP]
> Kompletní interaktivní dokumentaci ve formátu **Swagger/OpenAPI** naleznete na adrese `/api/v1/docs` vaší instance.
