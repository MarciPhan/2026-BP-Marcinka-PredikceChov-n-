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

Metricord umožňuje odesílat kritická varování (Alerts) přímo na váš webhook v JSON formátu. To využijete pro okamžitou reakci na náhlý pokles aktivity:

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

## Komplexní integrace (Export dat)

Pokud chcete provádět vlastní hloubkovou analýzu, můžete využít endpoint pro export kompletní historie serveru ve formátu JSON:

```python
import requests
import json

def export_guild_data(guild_id, token):
    url = f"http://localhost:8092/api/v1/admin/export/{guild_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(f"metricord_export_{guild_id}.json", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Export úspěšně dokončen.")

# Použití
export_guild_data("123456789", "VAŠ_API_TOKEN")
```

::: tip Doporučení
Pro velké servery (> 10 000 členů) doporučujeme používat streamované stahování, abyste předešli přetížení operační paměti vašeho skriptu.
:::
