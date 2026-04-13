# Centrum exportu

Vaše data patří vám. Metricord umožňuje exportovat surová data pro další zpracování, například pro reporty vedení, marketingové analýzy nebo tvorbu vlastních grafů.

## Kde najít export?

Tlačítko pro export se nachází v pravém horním rohu sekce **Analytics** v hlavním dashboardu.

## Dostupné formáty

### CSV (Comma Separated Values)
Nejvhodnější pro import do tabulkových procesorů:
- Microsoft Excel
- Google Sheets
- LibreOffice Calc

Struktura CSV obsahuje sloupce jako `date`, `messages`, `voice_minutes`, `joins`, `leaves`.

### JSON (JavaScript Object Notation)
Strukturovaný formát vhodný pro vývojáře.

```json
{
  "date": "2023-10-25",
  "stats": {
    "messages": 1542,
    "voice_users": 45,
    "new_members": 12
  }
}
```
