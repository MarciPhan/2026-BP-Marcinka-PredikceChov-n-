> **Note:** These features (including XP, leveling, and achievements) are additional extensions and are not part of the core functionality evaluated in the bachelor thesis.

# Přehled příkazů

Zde najdete seznam všech dostupných příkazů CommunityMetrics. Všechny funkce vyvoláte pomocí lomítkových příkazů (Slash Commands).

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
Synchronizuje jména a role členů do databáze CommunityMetrics. Příkaz použijte po velkých změnách v rolích nebo přejmenování členů. Vyžaduje oprávnění **Administrator**.

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
Zobrazí vám ephemerní (jen vy ji vidíte) zprávu se souhrnnými počty dat, která o vás CommunityMetrics uchovává za jednotlivé servery (počet zpráv, voice relací a jejich délka, moderační akce, community health data). Nejde o soubor ke stažení ani o odkaz – jde o přehledový souhrn přímo v Discordu.

### `/gdpr delete`
Po potvrzení smaže vaši hlavní historii a profil z databáze CommunityMetrics (zprávy, voice aktivitu, moderační akce, community health data, statistiky a žebříčky).

> [!CAUTION]
> Tato operace je nevratná. Smazáním přijdete o všechny své XP, úrovně a historické statistiky, včetně případné ruční poznámky/hodnocení, které o vás mohl uložit administrátor v modulu Community Health.

## Community Health (`/chealth`)

Kontextová analytika modulu Engagement Score/Community Health (viz [Community Health](/COMMUNITY_HEALTH)). Obě podpříkazy vyžadují oprávnění **Administrator**.

### `/chealth status`
Zobrazí, které moduly Community Health jsou pro server zapnuté (žádosti o pomoc, kontext moderace, kontext odchodů, převod zájmu o akce na účast) a kolik podpůrných kanálů je nastaveno.

### `/chealth backfill`
Doplní historický kontext zpráv, moderačních zásahů a žádostí o pomoc zpětně.

| Parametr | Povinný | Výchozí | Rozsah |
| :--- | :--- | :--- | :--- |
| `days` | Ne | 30 | 1–180 dní historie. |

## Systémové příkazy

Doplňkové funkce pro kontrolu stavu bota.

- `/privacy` - Zobrazí podrobné zásady ochrany osobních údajů.
- `/health` - Zobrazí Engagement Score serveru (aktivitu, moderační zátěž MII, doporučený počet moderátorů). S parametrem `research: true` doplní i Markovovu predikci a analýzu přežití aktivity.
- `/ping` - Změří latenci k Discord API a přidá náhodný motivační citát.
- `/help` - Otevře interaktivní nabídku nápovědy.

## Příkaz pro synchronizaci (`*sync`)

Jediný prefixový příkaz. Slouží k registraci nových funkcí v Discord API. Používejte jej pouze po aktualizaci bota.

```text
*sync
```
