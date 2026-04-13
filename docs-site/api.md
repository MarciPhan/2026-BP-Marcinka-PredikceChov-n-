# API Reference

Metricord poskytuje RESTful rozhraní pro integraci s dalšími systémy. Většina endpointů vyžaduje autentizaci pomocí sezení (session) nebo API klíče.

::: tip Base URL
`https://dashboard.metricord.app/api/v1`
:::

## 1. Autentizace a Bezpečnost

Metricord API podporuje dva způsoby autentizace:
- **Session Cookie:** Pro požadavky z prohlížeče (dashboard).
- **Bearer Token:** Pro externí integrace a boty. Token získáte v nastavení profilu.

---

### `POST` /auth/request-otp
Zašle 6-místný jednorázový kód na e-mail uživatele.

**Body:**
```json
{ "email": "string" }
```

**Responses:**
- `200`: `{ "success": true, "wait": 60 }`
- `429`: `{ "error": "Rate limit exceeded" }`

---

## 2. Metriky a Statistiky (Metrics API)

### `GET` /guild/{guild_id}/metrics/summary
Vrátí klíčové ukazatele (DAU, MAU, MsgCount) pro daný server.

**Params:** `guild_id` (Snowflake)

**Response `200`:**
```json
{
  "active_users": 1540,
  "engagement_score": 88.5,
  "trend": "up"
}
```

### `GET` /guild/{guild_id}/metrics/heatmap
Vrátí data pro zobrazení hodinové aktivity (heatmapy).

**Response `200`:**
```json
{
  "data": { "0:14": 450, "1:15": 380 },
  "timezone": "UTC"
}
```

---

## 3. Predikce a AI (Predictions API)

### `GET` /guild/{guild_id}/predict/churn
Vypočítá pravděpodobnost odchodu členů na základě Markovových řetězců.

**Response `200`:**
```json
{
  "churn_probability_7d": 0.12,
  "at_risk_users": 42,
  "confidence": 0.94
}
```

---

## 4. Administrace (Admin API)

### `POST` /admin/config/update
Hromadná aktualizace konfigurace bota.

**Body:**
```json
{ "xp_per_msg": 15, "voice_multiplier": 1.5 }
```

**Response `200`:**
```json
{ "status": "updated" }
```
