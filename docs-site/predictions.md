# Technologie Predikce

Metricord využívá kombinaci statistických metod a lineární regrese pro odhad budoucího vývoje vaší komunity. Zde je podrobný popis toho, jak naše modely fungují.

::: warning Důležité upozornění
Všechny predikce jsou odhady založené na historických datech. Nepředvídatelné události (např. raid na server nebo zmínka influencera) mohou realitu výrazně změnit.
:::

## 1. Predikce růstu členů

Tento model odhaduje počet členů v horizontu 30, 60 a 90 dní.
- **Metodika:** Výpočet čistého přírůstku (Joins - Leaves) za posledních 12 měsíců.
- **Klouzavý průměr:** Model bere v úvahu průměrný měsíční růst a projektuje ho lineárně do budoucna.
- **Využití:** Pomáhá plánovat nábor nových moderátorů nebo škálování infrastruktury.

## 2. Lineární regrese a trend aktivity

Pro odhad počtu zpráv používáme metodu nejmenších čtverců pro nalezení trendové přímky.

::: info Vzorec
`y = ax + b`  
*Kde **a** reprezentuje sklon trendu (rychlost růstu/poklesu) a **b** počáteční bod.*
:::

Trend analyzuje data za posledních 30 dní a vyhodnocuje, zda aktivita serveru v čase roste nebo klesá.

## 3. Sezónní indexy (Weekend Effect)

Tradiční lineární regrese často selhává u Discord komunit, protože aktivita se výrazně mění podle dne v týdnu (např. víkendy jsou silnější).

**Jak to funguje:**
1. Systém vypočítá **koeficient** pro každý den v týdnu na základě historie.
2. Pokud je sobota obvykle o 20 % aktivnější než průměr, dostane index **1.2**.
3. Lineární predikce pro budoucí sobotu je pak vynásobena tímto indexem pro vyšší přesnost.

## 4. Predikce stability (Churn Analysis)

Widget "Predikce stability" vyhodnocuje riziko "vymírání" serveru.
- **Skóre stability:** Vypočítává se jako poměr odchodů k celkové velikosti komunity.
- **Interpretace:** Pokud odchody tvoří více než 5 % celkového počtu členů za měsíc, systém vyhlásí varování.
- **Stickiness (DAU/MAU):** Sledujeme, kolik procent měsíčních uživatelů se vrací každý den. Vysoké číslo (>20 %) značí zdravé jádro komunity.

## 5. Predikce špičky

Model analyzuje hodinovou aktivitu a identifikuje časy, kdy je v následujících 24 hodinách nejpravděpodobnější nejvyšší aktivita.
- **Využití:** Plánování ohlášení (announcements) nebo spuštění eventů tak, aby zasáhly co nejvíce lidí.
