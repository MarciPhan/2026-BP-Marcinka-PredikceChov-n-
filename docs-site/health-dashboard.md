# System Health Dashboard

Ukázka toho, jak vypadá monitorovací rozhraní pro administrátory instance Metricord.

::: info Redis Uptime
**99.98%**
*24 dní bez výpadku*
:::

::: warning Memory Usage
**742 MB / 1024 MB**
[████████████░░░░] 72%
:::

::: info Redis OPS/sec
**1,240 msg/s**
*Špička: 4,500 msg/s*
:::

## Aktivní procesy

| Proces | Status | Poznámka |
| :--- | :--- | :--- |
| `bot.activity_monitor` | 🟢 Normal | Běží |
| `web.analytics_engine` | 🟢 Normal | Běží |
| `ai.retraining_service` | 🔵 Scheduled | Naplánováno za 4h |
