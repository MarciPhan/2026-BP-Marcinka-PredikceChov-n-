# Analytické metriky a Grafy

Data jsou srdcem Metricord. V této sekci naleznete technické detaily o tom, jak počítáme klíčové ukazatele výkonu (KPI) pro vaši komunitu.

## 1. Základní terminologie (KPIs)

::: info Všechny časy jsou v UTC
Dashboard zobrazuje data v koordinovaném světovém čase (UTC). Pokud odesíláte zprávu ve 20:00 SEČ, bot ji zapíše jako 19:00 UTC.
:::

### DAU (Daily Active Users)
Počet unikátních uživatelů, kteří provedli "aktivní akci" v průběhu 24 hodin.
- **Aktivní akce:** Odeslání zprávy, připojení do voice kanálu, přidání reakce.
- **Výpočet přes HyperLogLog:** Pro efektivitu používáme algoritmus HLL se standardní chybou **0.81%**. To umožňuje sledovat miliony uživatelů při konstantní spotřebě paměti 12 KiB.

## 2. Engagement Metriky

### Participation Rate (PR)
**Vzorec:** $$(DAU / Total Members) * 100$$

Tato metrika měří, jaké procento vaší komunity je skutečně aktivní každý den. PR je "metrikou pravdy".
- **< 5%:** Kriticky nízké. Server je pravděpodobně "hřbitov".
- **5 - 15%:** Průměr pro velké veřejné servery.
- **15 - 30%:** Velmi zdravá komunita.
- **> 30%:** Výjimečná úroveň zapojení.

### Reply Ratio (RR)
**Vzorec:** $$(Počet odpovědí / Celkový počet zpráv)$$

Vysoké RR naznačuje, že lidé spolu skutečně mluví (vedou vlákna). Ideální RR se pohybuje mezi **0.2 a 0.4**.

## 3. Stickiness (Návykovost)

Stickiness vyjadřuje schopnost serveru udržet uživatele v čase.

::: tip Stickiness Index
**Vzorec:** $$(DAU / MAU) * 100$$
Pokud je Stickiness 50 %, znamená to, že průměrný uživatel se na server vrací 15 dní v měsíci.
:::

**Benchmarky a interpretace:**
- **< 5% (Kritické):** Uživatelé přijdou jednou a už se nevrátí.
- **10-15% (Standard):** Běžná úroveň pro hobby servery.
- **> 25% (Elitní):** Komunita je velmi semknutá, uživatelé se vrací téměř denně.

## 4. Vysvětlení grafů

### Activity Heatmap (Tepelná mapa)
Mřížka 7x24 polí, která ukazuje intenzitu zpráv pro každou hodinu v týdnu.
- Identifikujte časové zóny vašich uživatelů.
- Najděte "hluchá místa" bez moderátorů.
- Optimalizujte časy pro oznámení novinek.

### Message Length Distribution
Rozděluje zprávy do tří kategorií:
- **Krátké (<15 znaků):** Emojis, jednoslovné odpovědi. Často tvoří 40-50% šumu.
- **Střední (15-60 znaků):** Jádro konverzace.
- **Dlouhé (>60 znaků):** Argumenty, popisy. Tato kategorie dává nejvíce XP bodů.

### Community Growth
Kombinovaný graf ukazující celkový počet členů (čára) a denní změny (sloupce).

::: danger Pozor na "Velrybí hřbety"
Pokud vidíte velké sloupce Joins a hned po nich Leaves, pravděpodobně proběhl nájezd botů nebo neúspěšná promo akce.
:::

## 5. Datová kvalita (DQS)

Metricord hodnotí i sám sebe pomocí **Data Quality Score**:
- **DQS 1.0 (Dokonalé):** Server má historii > 30 dní.
- **DQS < 0.5 (Varování):** Predikce mohou být nepřesné.
- **DQS < 0.2 (Sbíráme):** Prediktivní modely jsou dočasně vypnuty.
