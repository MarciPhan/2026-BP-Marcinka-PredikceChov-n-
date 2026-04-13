# Advanced API: Action Triggers

Vzdálené ovládání vašeho bota přes REST API. Metricord není jen o datech, je o akci.

## 1. Odesílání zpráv (Webhooks 2.0)

`POST /api/v1/guild/{id}/message`

### Request Body Schema:
```json
{
  "channel_id": "string",
  "content": "string",
  "embed": {
    "title": "string",
    "description": "string",
    "color": "integer (hex)",
    "fields": [
      { "name": "label", "value": "text", "inline": true }
    ]
  }
}
```

### Příklad odpovědi (201 Created):
```json
{
  "status": "success",
  "message_id": "123456789012345678",
  "channel_id": "999888777"
}
```

## 2. Moderační zásahy přes API

`POST /api/v1/guild/{id}/member/{uid}/timeout`

Parametry: `duration` (v minutách), `reason` (nepovinné). Můžete automatizovat tresty na základě externích signálů.

- **Timeout:** `POST /api/v1/guild/{id}/member/{uid}/timeout`
- **Kick:** `POST /api/v1/guild/{id}/member/{uid}/kick`

## 3. Správa rolí

Synchronizujte role s vaším webem nebo e-shopem.

```http
PUT /api/v1/guild/{id}/member/{uid}/roles
Content-Type: application/json

{
  "add": ["12345"],
  "remove": ["67890"]
}
```

::: danger Bezpečnost
Tyto endpointy vyžadují API klíč s oprávněním `WRITE_ACTIONS`. Nikdy tyto akce nepovolujte pro veřejné tokeny.
:::
