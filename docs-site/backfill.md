# Backfill historických dat

Backfill doplní do databáze historii zpráv a moderátorských akcí z období před přidáním bota na server. Bez backfillu pracují analytické funkce pouze s daty nasbíranými od okamžiku instalace.

## Kdy backfill spustit

- Ihned po přidání bota na existující server.
- Po obnově databáze ze zálohy, pokud chybí část dat.
- Po změně vah aktivit, pokud požadujete přepočet statistik.

## Spuštění backfillu

Předpoklady:
- Přístup na server s oprávněním **Administrator**.
- Bot musí mít oprávnění `Read Message History` a `View Audit Log`.

Zadejte příkaz:

```
/activity backfill days:30
```

| Parametr | Výchozí | Popis |
| :--- | :--- | :--- |
| `days` | 30 | Počet dní zpětně. Maximální rozsah závisí na historii Discord API. |

## Průběh zpracování

1. Bot smaže staré agregované statistiky pro daný server.
2. Projde všechny textové kanály, ke kterým má přístup.
3. Stáhne zprávy po dávkách (100 zpráv na API požadavek).
4. Z každé zprávy uloží do Redisu pouze metadata:
   - **Timestamp** - čas odeslání,
   - **User ID** - identifikátor autora,
   - **Délka zprávy** - počet znaků (`len`),
   - **Reply flag** - zda jde o odpověď na jinou zprávu.
5. Zpracuje audit log - bany, kicky, timeouty, smazané zprávy, změny rolí.
6. Zpracuje verifikační záznamy z log kanálu (pokud existuje).

::: warning Ochrana soukromí
Bot neukládá text zpráv. Backfill systém extrahuje pouze metadata potřebná pro výpočet metrik.
:::

## Výstup po dokončení

Bot zobrazí shrnutí:

```
Hotovo!
Zpracováno: 12 450 zpráv, 89 audit akcí, 23 verifikací.
Data uložena do event systému.
Zkus: /activity stats after:01-01-2025.
```

## Rate limiting

Backfill dodržuje limity Discord API. Pokud API vrátí HTTP 429, bot automaticky pozastaví stahování a pokračuje po uplynutí doby `Retry-After`. Stahování nepřeruší funkčnost bota ani ostatních příkazů.

## Redis klíče vytvořené backfillem

| Klíč | Typ | Obsah |
| :--- | :--- | :--- |
| `events:msg:{guild_id}:{user_id}` | Sorted Set | Metadata zpráv (score = timestamp) |
| `events:action:{guild_id}:{user_id}` | Sorted Set | Moderátorské akce (score = timestamp) |
| `events:voice:{guild_id}:{user_id}` | Sorted Set | Voice session data (score = timestamp) |
| `user:info:{user_id}` | Hash | Jméno, avatar, role (TTL 7 dní) |
