# Uživatelská příručka

Vítejte v Metricord! Tato příručka vám pomůže pochopit, jak bot funguje, co o vás ví a jak se můžete zapojit do života komunity.

## 1. Základní příkazy

Bot reaguje na lomítkové příkazy (Slash Commands). Stačí napsat `/` a vybrat si ze seznamu.

| Příkaz | Popis | Viditelnost |
| :--- | :--- | :--- |
| `/help` | Zobrazí nápovědu ke všem modulům. | Jen pro vás |
| `/activity stats` | Ukáže vaši celkovou aktivitu. | Vidí všichni |
| `/activity leaderboard` | Žebříček TOP 10 nejaktivnějších členů. | Vidí všichni |
| `/privacy` | Vysvětlí, jaká data bot sbírá. | Jen pro vás |
| `/ping` | Test odezvy bota. | Vidí všichni |

## 2. Jak funguje Engagement Score?

Engagement Score je číslo od 0 do 100, které vyjadřuje "zdraví" vaší aktivity nebo aktivity serveru.

::: info Složky vašeho skóre
- **Konzistence (40%):** Pravidelná denní aktivita má vyšší váhu.
- **Interakce (30%):** Reakce ostatních na vaše zprávy.
- **Hloubka (30%):** Smysluplnější příspěvky jsou hodnoceny lépe.
:::

## 3. Vývoj úrovní (Leveling Curve)

Metricord používá kvadratickou funkci pro výpočet potřebných XP na další úroveň:

$$ \text{Required XP} = 50 \cdot (\text{Level})^2 + 150 \cdot (\text{Level}) + 100 $$

| Level | Celkové XP | Průměrná doba |
| :--- | :--- | :--- |
| 1 | 100 | 5 minut |
| 10 | 6,600 | 1 týden |
| 50 | 132,600 | 3 měsíce |
| 100 | 515,100 | 1 rok |

::: tip Tip
Voice aktivita generuje XP pasivně každou minutu. Pokud streamujete video, získáte **20% bonus**.
:::

## 4. Vaše soukromí (GDPR & Data Safety)

Metricord byl navržen s ohledem na *Privacy by Design*.

### Transparentní sběr dat
Ukládáme pouze to, co je nezbytné pro analytiku:
- **Metadata zpráv:** Datum, čas a délka. **Obsah (text) zprávy se NIKDY neukládá.**
- **Voice relace:** Čas připojení a odpojení.
- **Profilové údaje:** Cache jména a avataru.

### Nástroje pro kontrolu dat
Zadejte příkaz `/gdpr help` pro zobrazení možností:

::: info `/gdpr data_request`
Vytvoří kompletní JSON export všech vašich dat.
:::

::: danger `/gdpr forget_me`
Anonymizuje všechny vaše záznamy a smaže váš profil. Tento krok je **nevratný**.
:::
