# Privacy Builder

Nástroj pro generování zásad ochrany osobních údajů pro Discord server, který používá Metricord. Výsledný text vložte do kanálu `#pravidla` nebo `#privacy`.

## Rozsah sběru dat

Metricord sbírá pouze metadata nutná pro výpočet analytických metrik. Obsah zpráv se neukládá.

### Sbíraná data

| Typ dat | Konkrétní položky | Účel | TTL |
| :--- | :--- | :--- | :--- |
| Metadata zpráv | Čas odeslání, délka textu (počet znaků), příznak Reply | XP systém, Heatmapa, DAU | 30 dní |
| Voice aktivita | Čas začátku a konce session, délka v sekundách | Voice leaderboard, analytika | 30 dní |
| Moderátorské akce | Typ akce (ban, kick, timeout, smazání zprávy, změna role), čas | MII index, moderátorský report | 30 dní |
| Uživatelský profil | Discord jméno, avatar URL, ID rolí | Dashboard, identifikace | 7 dní |
| Discord User ID | Číselný identifikátor uživatele | Propojení všech dat | Po dobu uchovávání dat |

### Nesbíraná data

- Obsah zpráv (text, přílohy, média).
- Soukromé konverzace (DM).
- Hlasové nahrávky a přepisy řeči.
- IP adresy uživatelů.
- Data z jiných serverů (kromě propojených přes Discourse).

## Účel zpracování

Data se zpracovávají výhradně pro:

1. **XP systém a automatické role** - výpočet skóre aktivity a přidělování rolí na základě úrovně.
2. **Analytický dashboard** - vizualizace trendů, Heatmapa aktivity, distribuce zpráv.
3. **Prediktivní modely** - Markovovy řetězce (predikce churnu), Kaplan-Meier (survival analýza).
4. **Smart Insights** - automatická detekce anomálií a rizikových uživatelů.
5. **Moderátorský report** - přehled aktivity moderátorského týmu.

## Uchovávání dat (Data Retention)

| Typ dat | Výchozí TTL | Konfigurovatelné |
| :--- | :--- | :--- |
| Surové eventy (zprávy, voice, akce) | 30 dní | Ne (pevně nastaveno) |
| HyperLogLog statistiky (DAU) | 90 dní | Ne |
| Uživatelský profil cache | 7 dní | Ne (automatická expirace Redis) |
| Runtime status (heartbeat) | 60 sekund | Ne |
| GDPR deletion log | 30 dní | Ne |

Po uplynutí TTL Redis automaticky smaže příslušné klíče. Administrátor nemusí spouštět žádné čistící skripty.

## Práva uživatele (GDPR)

Každý uživatel má právo na:

| Právo | Příkaz | Popis |
| :--- | :--- | :--- |
| Přístup k datům | `/gdpr export` | Export všech dat v JSON formátu. Odpověď je ephemeral. |
| Výmaz dat | `/gdpr delete` | Nevratné smazání všech dat z databáze. Vyžaduje potvrzení. |
| Informace o zpracování | `/privacy` | Přehled sbíraných dat a zásad ochrany. |

### Postup výmazu

Příkaz `/gdpr delete` smaže:
1. Uživatelský profil (`user:info:{id}`).
2. Události zpráv na všech serverech (`events:msg:*:{id}`).
3. Voice sessions (`events:voice:*:{id}`).
4. Moderátorské akce (`events:action:*:{id}`).
5. Stavové proměnné (`activity:state:*:{id}:*`).
6. Denní statistiky (`stats:day:*:*:{id}`).

Po smazání bot vytvoří dočasný záznam o provedení výmazu (`gdpr:deletion_log:{id}`) s dobou platnosti 30 dní pro účely auditního logu.

## Šablona pro kanál #privacy

Doporučený text pro vložení na Discord server:

```
ZÁSADY OCHRANY OSOBNÍCH ÚDAJŮ

Tento server používá analytického bota Metricord.

CO SBÍRÁME:
- Metadata zpráv (čas, délka textu, kanál) - NE obsah zpráv
- Dobu strávenou ve voice kanálech
- Moderátorské akce (bany, kicky, timeouty)
- Veřejné profilové informace (jméno, avatar)

PROČ:
- XP systém a automatické role
- Statistiky aktivity pro správce serveru
- Predikce zdraví komunity

VAŠE PRÁVA:
- /gdpr export - stáhněte si kopii všech svých dat
- /gdpr delete - smažte všechna svá data (nevratné)
- /privacy - zobrazíte podrobné informace

Data jsou uchovávána maximálně 90 dní a automaticky
se mažou. Obsah zpráv, DM ani hlasové nahrávky
NIKDY neukládáme.
```

::: info Právní upozornění
Tato šablona je doporučeným výchozím textem. Majitel serveru nese odpovědnost za soulad se zákony v příslušné jurisdikci. Pro servery s uživateli v EU doporučujeme konzultaci s právníkem ohledně GDPR compliance.
:::

## Zabezpečení dat

- Data jsou uložena v Redis databázi s přístupem chráněným heslem (`requirepass`).
- Komunikace mezi botem a Redis probíhá přes interní Docker síť (bez expozice na veřejný port).
- Dashboard vyžaduje přihlášení přes Discord OAuth2 a ověření oprávnění `Manage Server`.
- Žádná data nejsou sdílena s třetími stranami.
- API endpointy jsou chráněny Bearer token autentizací a rate limitingem (60 req/min).
