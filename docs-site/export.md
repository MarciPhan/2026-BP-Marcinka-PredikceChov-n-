# Export dat

Metricord umožňuje exportovat nasbíraná data pro další zpracování v tabulkových procesorech nebo vlastních skriptech.

## Přístup k exportu

Export je dostupný z webového dashboardu v sekci **Analytics**. Tlačítko **Export** se nachází v pravém horním rohu.

Předpoklady:
- Přihlášení do dashboardu s oprávněním `Manage Server`.

## Dostupné formáty

### CSV

Vhodný pro import do tabulkových procesorů (Microsoft Excel, Google Sheets, LibreOffice Calc).

Struktura CSV souboru:

| Sloupec | Typ | Popis |
| :--- | :--- | :--- |
| `date` | string | Datum ve formátu `YYYY-MM-DD` |
| `messages` | integer | Počet zpráv za den |
| `voice_minutes` | float | Minuty ve voice kanálech |
| `joins` | integer | Počet příchodů na server |
| `leaves` | integer | Počet odchodů ze serveru |
| `dau` | integer | Denní aktivní uživatelé (HyperLogLog odhad) |

### JSON

Strukturovaný formát pro strojové zpracování a integrace:

```json
{
  "guild_id": "123456789012345678",
  "period": {
    "start": "2026-04-01",
    "end": "2026-04-14"
  },
  "daily": [
    {
      "date": "2026-04-01",
      "messages": 1542,
      "voice_minutes": 320.5,
      "dau": 245,
      "joins": 12,
      "leaves": 3
    }
  ]
}
```

## Export přes API

Stejná data lze získat programově přes REST API:

```bash
curl -X GET "http://localhost:8092/api/v1/guild/{guild_id}/export?format=csv&range=30" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -o export.csv
```

| Parametr | Výchozí | Popis |
| :--- | :--- | :--- |
| `format` | `json` | Formát výstupu: `csv` nebo `json`. |
| `range` | `7` | Počet dní zpětně. |

## Omezení

- Maximální rozsah jednoho exportu je 365 dní.
- Export je omezen na 60 požadavků za minutu (rate limit).
- Exportovaná data neobsahují obsah zpráv - pouze agregované metriky.
