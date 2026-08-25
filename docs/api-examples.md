# Pokročilé API příklady

Jak integrovat CommunityMetrics data do vašich vlastních projektů, botů nebo vlastních nástrojů.

::: warning Autentizace
Aktuální implementace používá hlavičku `X-API-Key` (SHA-256 hash) pro autentizaci API požadavků. Hlavní přístup k dashboardu je přes Discord OAuth2 session.
:::

## Příklady implementace

::: code-group

```bash [cURL]
curl -X GET "http://localhost:8093/api/stats" \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Cookie: session=YOUR_SESSION_COOKIE"
```

```python [Python]
import requests

url = "http://localhost:8093/api/stats"
headers = {"X-API-Key": "YOUR_API_KEY"}
cookies = {"session": "YOUR_SESSION_COOKIE"}

response = requests.get(url, headers=headers, cookies=cookies)
data = response.json()
print(f"Dashboard stats: {data}")
```

```javascript [JavaScript]
const fetchStats = async () => {
  const res = await fetch('http://localhost:8093/api/stats', {
    headers: { 'X-API-Key': 'YOUR_API_KEY' },
    credentials: 'include'
  });
  const data = await res.json();
  console.log('Stats:', data);
};
```

:::

## Automatizace s Webhooky

CommunityMetrics umožňuje odesílat kritická varování (Alerts) přímo na váš webhook v JSON formátu. To využijete pro okamžitou reakci na náhlý pokles aktivity:

```json
{
  "type": "INACTIVITY_ALERT",
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

def export_guild_data(api_key, session_cookie):
    url = "http://localhost:8093/api/export/activity?format=json"
    headers = {"X-API-Key": api_key}
    cookies = {"session": session_cookie}
    
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        data = response.json()
        with open("communitymetrics_export.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Export úspěšně dokončen.")

# Použití
export_guild_data("VAŠ_API_KEY", "VAŠ_SESSION_COOKIE")
```

::: tip Doporučení
Pro velké servery (> 10 000 členů) doporučujeme používat streamované stahování, abyste předešli přetížení operační paměti vašeho skriptu.
:::
