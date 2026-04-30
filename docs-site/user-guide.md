# Uživatelská příručka

Vítejte v Metricord! Tato příručka vám vysvětlí, jak bot funguje, jaká data o vás shromažďuje a jak se zapojíte do života své komunity.

## Jak používat příkazy

Metricord ovládáte pomocí lomítkových příkazů (Slash Commands). Do chatu napište `/` a vyberte si ze seznamu dostupných funkcí.

| Příkaz | Co udělá | Kdo výsledek uvidí |
| :--- | :--- | :--- |
| `/help` | Zobrazí nápovědu ke všem modulům. | Pouze vy |
| `/activity stats` | Zobrazí vaši celkovou aktivitu na serveru. | Celý server |
| `/activity leaderboard` | Ukáže žebříček 10 nejaktivnějších členů. | Celý server |
| `/privacy` | Vysvětlí zásady zpracování vašich dat. | Pouze vy |
| `/ping` | Ověří rychlost odezvy bota. | Celý server |

## Jak funguje Engagement Score

Engagement Score vyjadřuje úroveň vašeho zapojení do komunity na stupnici 0–100. Čím vyšší skóre máte, tím aktivnějším členem jste.

### Složky vašeho skóre
- **Konzistence (40 %):** Pravidelné psaní každý den zvyšuje vaše skóre nejvíce.
- **Interakce (30 %):** Body získáte, když ostatní reagují na vaše zprávy.
- **Hloubka (30 %):** Systém hodnotí délku a smysluplnost vašich příspěvků.

## Získávání úrovní (Leveling)

Vaše úroveň (Level) roste se získanými zkušenostmi (XP). Pro postup na vyšší úroveň potřebujete stále více XP podle tohoto vzorce:

$$ \text{Potřebné XP} = 50 \cdot (\text{Level})^2 + 150 \cdot (\text{Level}) + 100 $$

| Úroveň | Celkové XP | Odhadovaná doba k dosažení |
| :--- | :--- | :--- |
| 1 | 100 | 5 minut |
| 10 | 6 600 | 1 týden |
| 50 | 132 600 | 3 měsíce |
| 100 | 515 100 | 1 rok |

> [!TIP]
> Za pobyt ve voice kanálu získáváte XP pasivně každou minutu. Pokud u toho sdílíte video nebo obrazovku, získáte **20% bonus**.

## Ochrana vašich osobních údajů (GDPR)

Metricord respektuje vaše soukromí a sbírá pouze data nezbytná pro fungování analytiky.

### Jaká data sbíráme?
Ukládáme pouze metadata, nikoliv obsah vašich zpráv:
- **Metadata zpráv:** Čas odeslání a počet znaků. **Text vašich zpráv nikdy nečteme ani neukládáme.**
- **Hlasová aktivita:** Čas připojení a odpojení od voice kanálu.
- **Základní profil:** Vaše uživatelské jméno a avatar pro zobrazení v žebříčcích.

### Jak spravovat svá data?
Pomocí příkazu `/gdpr help` získáte přístup ke svým datům:

- `/gdpr data_request` - Stáhněte si kompletní JSON soubor se všemi svými daty.
- `/gdpr forget_me` - Nevratně smažte svůj profil a anonymizujte všechny své záznamy v databázi.
