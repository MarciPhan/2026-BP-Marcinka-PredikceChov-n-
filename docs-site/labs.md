# Experimentální funkce (Labs)

Funkce v rané fázi vývoje. Aktivace vyžaduje nastavení proměnných prostředí. Experimentální funkce nejsou garantovány pro produkční provoz.

## Voice Sentiment Detection

Analýza tónu hlasu (ne obsahu řeči) pro detekci emočních stavů ve voice kanálech.

**Princip:** Systém extrahuje akustické příznaky (hlasitost, tempo řeči, frekvence pauz). Klasifikátor rozlišuje 3 stavy: Neutrální, Vzrušený, Tichý. Obsah řeči se neukládá ani netranskribuje.

**Aktivace:**
```bash
LABS_VOICE_SENTIMENT=1
```

**Status:** Alpha

::: warning Výkon
VoiceAI zvyšuje CPU zátěž o 15–20 %. Doporučeno pro dedikované instance.
:::

## Anomaly Detection (Z-Score)

Automatická detekce statistických anomálií v hodinových metrikách.

**Princip:** Pro každou hodinovou metriku systém vypočítá Z-skóre:

$$Z = \frac{x - \mu}{\sigma}$$

Pokud $|Z| > 3$, systém vyhodnotí anomálii a vygeneruje Smart Insight.

**Příklad:** Průměrný počet zpráv v 15:00 je 120 ($\mu = 120$, $\sigma = 25$). Pokud přijde 250 zpráv:

$$Z = \frac{250 - 120}{25} = 5{,}2 \quad \rightarrow \quad \text{anomálie}$$

**Status:** Beta

## Image Pattern Recognition

Detekce vizuálního spamu pomocí perceptuálního hashování (pHash).

**Princip:** Každý obrázek se převede na 64bitový hash. Systém porovná hash s databází známých vzorů. Při Hammingově vzdálenosti < 6 (shoda > 90 %) generuje alert.

**Status:** Výzkum
