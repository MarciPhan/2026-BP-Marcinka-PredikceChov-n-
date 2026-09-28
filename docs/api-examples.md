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

Pokud chcete provádět vlastní hloubkovou analýzu, můžete využít endpoint pro export denní aktivity (zprávy, voice minuty, joins/leaves, DAU) za zvolené období ve formátu JSON. Kromě `activity` existují i další typy exportu (`leaderboard`, `voice_top`, `channels`, `users`, ...), viz [Export dat](/export).

```python
import requests
import json

def export_guild_data(api_key, session_cookie, start_date, end_date):
    url = (
        "http://localhost:8093/api/export/activity"
        f"?format=json&start_date={start_date}&end_date={end_date}"
    )
    headers = {"X-API-Key": api_key}
    cookies = {"session": session_cookie}
    
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        data = response.json()
        with open("communitymetrics_export.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Export úspěšně dokončen.")

# Použití (bez start_date/end_date se exportuje jen posledních 7 dní)
export_guild_data("VAŠ_API_KEY", "VAŠ_SESSION_COOKIE", "2026-01-01", "2026-01-31")
```

::: tip Omezení
Maximální rozsah jednoho exportu je 365 dní a rozhraní je omezeno na 120 požadavků za minutu na uživatele a komunitu. Jde vždy o agregovaná denní data, ne o export syrových jednotlivých zpráv.
:::
