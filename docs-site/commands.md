# Příkazy (Slash Commands)

Kompletní referenční příručka všech příkazů Metricord bota. Bot používá moderní lomítkové příkazy integrované přímo do Discord chatu.

## Analytické příkazy

| Příkaz | Popis | Parametry | Viditelnost |
| :--- | :--- | :--- | :--- |
| `/activity stats` | Zobrazí detailní kartu uživatele — aktivita v chatu, voice čas, rank a úroveň. | `user`, `after`, `before` | Vidí všichni |
| `/activity leaderboard` | Žebříček TOP 10 nejaktivnějších členů podle váženého času. | — | Vidí všichni |
| `/ping` | Test odezvy bota a latence k Redis databázi. | — | Vidí všichni |
| `/help` | Interaktivní nápověda se selektem modulů. | `modul` | Ephemeral |

## Administrátorské příkazy

Vyžadují oprávnění `Administrator` nebo `Manage Server`.

| Příkaz | Popis | Poznámky |
| :--- | :--- | :--- |
| `/activity report` | Generuje report aktivity moderátorského týmu. | Využívá *Weighted Moderation Points*. |
| `/activity sync_names` | Vynutí aktualizaci přezdívek a rolí v Redis databázi. | Spusťte po velkých změnách v rolích. |
| `/activity backfill` | Načte historii zpráv ze serveru do Redisu. | CPU náročné. Výchozí: 30 dní. |
| `*sync` | Synchronizuje slash příkazy s Discord API (prefix). | Použijte po aktualizaci bota. |

## GDPR a soukromí

| Příkaz | Popis | Poznámky |
| :--- | :--- | :--- |
| `/gdpr export` | Stáhne kompletní přehled všech uložených dat o vás v JSON. | Ephemeral odpověď. |
| `/gdpr delete` | Nevratně smaže všechna vaše data z databáze bota. | Přijdete o všechny XP a historii. |
| `/privacy` | Přehled zásad ochrany osobních údajů. | Ephemeral odpověď. |

## Diagnostické příkazy

| Příkaz | Popis | Oprávnění |
| :--- | :--- | :--- |
| `/health` | Diagnostika — verze bota, Redis status, uptime. | Všichni |
| `/ping` | Latence bota k Discord API a Redisu. | Všichni |

::: info Slash vs. Prefix příkazy
Většina příkazů je implementována jako **slash commands** (lomítkové). Jediný prefix příkaz je `*sync`, který slouží k synchronizaci slash příkazů s Discord API. Po spuštění `*sync` se nové příkazy zobrazí v nabídce při psaní `/`.
:::
