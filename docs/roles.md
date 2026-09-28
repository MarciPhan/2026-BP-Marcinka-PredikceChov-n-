> **Note:** These features (including XP, leveling, and achievements) are additional extensions and are not part of the core functionality evaluated in the bachelor thesis.

# XP systém a úrovně

CommunityMetrics obsahuje infrastrukturu pro XP žebříček a úrovně -- konfigurovatelný vzorec úrovně, žebříčkovou stránku v dashboardu (`/leaderboard`, resp. `GET /api/leaderboard/xp`) a nastavení vzorce v `/settings` (formulář ukládá do `config:xp_formula:{guild_id}` přes `POST /settings/xp-formula`).

::: warning Aktuální stav
Samotné **přidělování XP za zprávy, odpovědi nebo hlasovou aktivitu není v botovi implementováno** -- v `bot/commands/` neexistuje žádný kód, který by hodnotu v `levels:xp:{guild_id}` zvyšoval. Žebříčková stránka a API tuto strukturu jen čtou. Bez externího zápisu do tohoto klíče (např. ručně, nebo skriptem mimo tento repozitář) zůstane žebříček prázdný. Níže popsaný způsob bodování (délka zprávy, bonus za odpověď, hlasová aktivita, anti-spam a noční korekce) je tedy návrhem/specifikací zamýšleného chování, ne popisem toho, co bot v aktuální verzi dělá.
:::

## Zamýšlený výpočet XP (neimplementováno)

Návrh počítal s hodnocením podle objemu (délky) zprávy, aby systém neodměňoval pouhou přítomnost, ale aktivní interakci:

| Typ akce | XP | Podmínky |
| :--- | :--- | :--- |
| Krátká zpráva (< 15 znaků) | 1 | Jednoslovné reakce, emoji. |
| Standardní zpráva (15–100 znaků) | 5 | Běžná konverzace. |
| Dlouhý příspěvek (> 100 znaků) | 15–50 | Lineární nárůst s délkou, maximum 50 XP. |
| Odpověď (Reply) | +10 | Bonus za použití funkce Reply. |
| Voice aktivita | 5 / min | Mikrofon musí být aktivní (ne mute). |

Zamýšlené anti-spam mechanismy: cooldown 1 XP-profitující zpráva za 60 s, 0 XP za opakované odeslání stejné zprávy, noční korekce (2:00–6:00 koeficient 0,5) a náhodná odchylka ±15 % ke ztížení automatizovaného farmení. Žádný z těchto mechanismů není v současné verzi bota implementován.

## Výpočet úrovně (implementováno)

Úroveň $L$ se z celkových XP $X$ počítá podle kvadratické funkce, jejíž koeficienty $a$, $b$, $c$ jsou konfigurovatelné (výchozí hodnoty níže):

$$X(L) = a \cdot L^2 + b \cdot L + c \quad \text{(výchozí } a=50,\ b=200,\ c=100\text{)}$$

Příklady požadovaného XP pro vybrané úrovně při výchozích koeficientech:

| Úroveň | Požadované XP |
| :--- | :--- |
| 2 | 700 |
| 10 | 7 100 |
| 25 | 36 350 |
| 50 | 135 100 |

## Konfigurace vzorce úrovně

V dashboardu, v sekci **Nastavení**, lze upravit koeficienty `a`, `b`, `c` a rozsahy `min`/`max` pro zprávy a `voice_min`/`voice_max` pro hlasovou aktivitu (ty odpovídají zamýšlenému, ale neimplementovanému rozsahu bodování výše):

```bash
curl -X POST http://localhost:8093/settings/xp-formula \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d "xp_a=50&xp_b=200&xp_c=100&xp_min=15&xp_max=25&xp_voice_min=5&xp_voice_max=10&csrf_token=YOUR_CSRF_TOKEN"
```

Endpoint vyžaduje aktivní session a oprávnění `manage_settings` (administrátor komunity nebo pověřený team member), ne API klíč.

## Automatické role podle úrovně

Přestože se název tohoto dokumentu na to odkazuje, **automatické přidělování Discord rolí podle dosažené úrovně není v kódu implementováno** -- nenašel jsem k tomu žádnou konfiguraci ani logiku v botovi ani v dashboardu. Propojení role ↔ úroveň si prozatím musí administrátor řešit mimo aplikaci (např. ručně, nebo vlastním externím skriptem nad Redis daty).
