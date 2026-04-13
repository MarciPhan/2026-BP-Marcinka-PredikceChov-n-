# Inteligentní Backfill Systém

Při prvním přidání bota na server nemusíte začínat s prázdným grafem. Náš Backfill Engine dokáže zrekonstruovat historii serveru.

## Jak funguje proces doplňování dat?

Proces je navržen tak, aby byl maximálně efektivní a bezpečný vůči limitům Discord API.

### 1. Fáze indexace
Bot projde seznam všech textových kanálů, ke kterým má přístup, a vytvoří prioritizovanou frontu úloh. Nejaktivnější kanály jsou zpracovány jako první.

### 2. Dávkové zpracování (Batch Processing)
Zprávy jsou stahovány po blocích (100 zpráv na jeden API request). Tím snižujeme zátěž sítě o 99%.

### 3. Agregace a Anonymizace

::: warning Ochrana soukromí
Neukládáme a nikdy nečteme text vašich zpráv. Backfill systém extrahuje pouze metadata.
:::

**Ukládáme pouze:**
- **Timestamp:** Kdy byla zpráva odeslána.
- **UserID:** Identifikátor autora.
- **ChannelID:** Kde byla zpráva odeslána.
- **MessageLength:** Počet znaků (pro analýzu kvality diskuze).

### 4. Rate-Limit Management
Náš systém obsahuje "Smart Throttling". Pokud Discord API začne hlásit zpomalení (HTTP 429), backfill se automaticky pozastaví, aby neohrozil funkčnost ostatních botů na serveru.
