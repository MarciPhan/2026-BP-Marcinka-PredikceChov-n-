# Integrace a Webhooky

Propojte Metricord s vašimi oblíbenými nástroji a automatizujte správu komunity na základě reálných dat.

## 1. Odchozí Webhooky (Outgoing)

Metricord může automaticky odesílat `POST` požadavky na vámi definované adresy při výskytu specifických událostí.

### Dostupné eventy:
- `member_join_anomaly`: Pokud se během krátké doby připojí neobvyklé množství lidí.
- `churn_risk_high`: Pokud AI identifikuje u významného člena vysoké riziko odchodu.
- `dqs_drop`: Pokud skóre kvality dat (DQS) klesne pod nastavenou hranici.

### Příklad payloadu:
```json
{
  "guild_id": "123456789",
  "event": "churn_risk_high",
  "timestamp": "2026-03-31T12:00:00Z",
  "details": {
    "user_id": "987654321",
    "risk": 0.85,
    "last_active": "2026-03-25"
  }
}
```

## 2. Integrace s Discourse

Metricord nativně podporuje propojování Discord účtů s účty na fóru Discourse. To umožňuje sledovat "cross-platform" aktivitu.
- **Sync rolí:** Automatické přidělování rolí na Discordu podle aktivity na fóru.
- **XP Merge:** Slučování bodů z obou platform pro spravedlivější žebříčky.

## 3. Zapier a Make (Integromat)

Díky našemu REST API můžete Metricord snadno propojit s nástroji jako Zapier nebo Make bez psaní kódu. Stačí použít modul **"HTTP Request"** a směřovat jej na naše API endpointy popsané v *API Reference*.

::: tip
Využijte webhooky pro zasílání upozornění do Slacku nebo Telegramu, aby váš mod-tým mohl reagovat okamžitě i mimo Discord.
:::
