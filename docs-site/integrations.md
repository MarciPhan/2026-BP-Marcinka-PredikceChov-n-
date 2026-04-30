# Integrace a webhooky

Metricord odesílá HTTP notifikace (webhooky) při výskytu definovaných událostí. Tato sekce popisuje formát zpráv a dostupné události.

## Odchozí webhooky

Bot odesílá `POST` požadavek na zadanou URL s tělem ve formátu JSON při každém výskytu nakonfigurované události.

### Konfigurace

V dashboardu přejděte do sekce **Settings → Webhooks**:

1. Zadejte cílovou URL (HTTPS).
2. Vyberte události, pro které se webhook aktivuje.
3. Uložte konfiguraci.

### Dostupné události

| Událost | Podmínka spuštění |
| :--- | :--- |
| `member_join_anomaly` | Přípojení > 10 členů za 5 minut |
| `churn_risk_high` | AI identifikuje u člena riziko odchodu > 0,8 |
| `dqs_drop` | DQS (Data Quality Score) klesne pod nastavenou hranici |
| `engagement_drop` | Engagement Score klesne o > 20 % za 7 dní |

### Formát payloadu

```json
{
  "guild_id": "123456789012345678",
  "event": "churn_risk_high",
  "timestamp": "2026-04-13T12:00:00Z",
  "details": {
    "user_id": "987654321",
    "risk": 0.85,
    "last_active": "2026-04-07"
  }
}
```

### Ověření doručení

Každý webhook požadavek obsahuje hlavičku `X-Metricord-Signature` s HMAC-SHA256 podpisem payloadu. Ověření na straně příjemce:

```python
import hmac, hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Integrace s Discourse

Metricord podporuje propojení Discord účtů s účty na fóru Discourse:

- **Synchronizace rolí:** Automatické přidělení Discord rolí podle aktivity na fóru.
- **XP Merge:** Sloučení bodů z obou platforem.

Konfigurace v dashboardu:

1. V sekci **Integrations → Discourse** zadejte URL vašeho Discourse fóra.
2. Zadejte API klíč Discourse (Settings → API Keys v administraci Discourse).
3. Aktivujte synchronizaci.

Redis klíče:
- `discourse:conf:{guild_id}` - konfigurace propojení (Hash)
- `user:discourse:{user_id}` - seznam propojených Guild ID (Set)

## Zapier a Make

REST API Metricord podporuje integraci s automatizačními platformami. V nástroji Zapier nebo Make použijte modul **HTTP Request** a směřujte jej na endpointy popsané v [API Reference](/api).
