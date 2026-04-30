# Přehled příkazů

Zde najdete seznam všech dostupných příkazů Metricord. Všechny funkce vyvoláte pomocí lomítkových příkazů (Slash Commands).

## Metriky a statistiky (`/activity`)

Tyto příkazy slouží k prohlížení nasbíraných dat a generování reportů.

### Zobrazení statistik uživatele (`/activity stats`)
Zobrazí detailní statistiku aktivity konkrétního uživatele.

| Parametr | Povinný | Formát | Co ovlivňuje |
| :--- | :--- | :--- | :--- |
| `user` | Ne | @zmínka | Vybere uživatele (výchozí: vy). |
| `after` | Ne | `DD-MM-YYYY` | Začátek časového filtru. |
| `before` | Ne | `DD-MM-YYYY` | Konec časového filtru. |

V přehledu uvidíte:
- **Chat Time:** Čas strávený aktivním psaním.
- **Voice Time:** Čas strávený v hlasových kanálech.
- **Moderation:** Počet a typ provedených moderátorských zásahů.
- **Total Time:** Celkový vážený čas aktivity.

### `/activity leaderboard`
Ukáže žebříček 10 nejaktivnějších členů celého serveru.

| Parametr | Povinný | Formát | Co ovlivňuje |
| :--- | :--- | :--- | :--- |
| `after` | Ne | `DD-MM-YYYY` | Začátek období. |
| `before` | Ne | `DD-MM-YYYY` | Konec období. |

### `/activity report`
Vytvoří souhrnný report aktivity moderátorského týmu. Tento příkaz vyžaduje oprávnění **Administrator**.

### `/activity sync_names`
Synchronizuje jména a role členů do databáze Metricord. Příkaz použijte po velkých změnách v rolích nebo přejmenování členů. Vyžaduje oprávnění **Administrator**.

### `/activity backfill`
Načte historická data ze serveru (zprávy a akce) do analytických modulů. Vyžaduje oprávnění **Administrator**.

| Parametr | Povinný | Výchozí | Rozsah |
| :--- | :--- | :--- | :--- |
| `days` | Ne | 30 | Počet dní historie ke stažení. |

> [!WARNING]
> Backfill je náročný na výkon. U velkých serverů může trvat i desítky minut. Během procesu se v kanálech může objevit mírná latence.

## Soukromí a GDPR (`/gdpr`)

Příkazy pro správu vašich osobních údajů.

### `/gdpr export`
Zašle vám soukromý odkaz ke stažení všech dat, která o vás Metricord uchovává.

### `/gdpr delete`
Smaže veškerou vaši historii a profil z databáze Metricord.

> [!CAUTION]
> Tato operace je nevratná. Smazáním přijdete o všechny své XP, úrovně a historické statistiky.

## Systémové příkazy

Doplňkové funkce pro kontrolu stavu bota.

- `/privacy` - Zobrazí podrobné zásady ochrany osobních údajů.
- `/health` - Ukáže verzi bota a stav připojení k databázi.
- `/ping` - Změří latenci k Discord API.
- `/help` - Otevře interaktivní nabídku nápovědy.

## Příkaz pro synchronizaci (`*sync`)

Jediný prefixový příkaz. Slouží k registraci nových funkcí v Discord API. Používejte jej pouze po aktualizaci bota.

```text
*sync
```
