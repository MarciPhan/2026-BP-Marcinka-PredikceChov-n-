# Pokročilé API příklady

Jak integrovat Metricord data do vašich vlastních projektů, botů nebo firemních dashboardů.

## Příklady implementace

::: code-group

```bash [cURL]
curl -X GET "http://localhost:8092/api/v1/stats/123456789/DAU" \
     -H "Authorization: Bearer YOUR_SERVER_TOKEN"
```

```python [Python]
import requests

url = "http://localhost:8092/api/v1/stats/123456789/MAU"
headers = {"Authorization": "Bearer YOUR_SERVER_TOKEN"}

response = requests.get(url, headers=headers)
data = response.json()
print(f"Unikátních uživatelů za měsíc: {data['count']}")
```

```javascript [JavaScript]
const fetchStats = async (guildId) => {
  const res = await fetch(`http://localhost:8092/api/v1/stats/${guildId}/DAU`, {
    headers: { 'Authorization': 'Bearer YOUR_SERVER_TOKEN' }
  });
  const data = await res.json();
  console.log('Daily Active Users:', data.count);
};
```

:::

## Automatizace s Webhooky

Metricord umožňuje odesílat kritická varování (Alerts) přímo na váš webhook v JSON formátu:

```json
{
  "type": "CHURN_ALERT",
  "guild_id": "123456789",
  "severity": "HIGH",
  "users": [
    { "id": "987654321", "risk": 0.89 }
  ]
}
```
