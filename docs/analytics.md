# Technické metriky a KPI

CommunityMetrics vypočítává širokou škálu ukazatelů výkonnosti (KPI). Tento dokument podrobně vysvětluje jejich matematický základ, způsob uložení v databázi a správnou interpretaci.

## Měření unikátní aktivity (DAU a MAU)

Pro efektivní počítání unikátních uživatelů v reálném čase využíváme pravděpodobnostní algoritmus **HyperLogLog (HLL)**.

-   **DAU (Daily Active Users):** Počet unikátních členů, kteří provedli aktivní úkon (zpráva, voice, reakce) během posledních 24 hodin.
-   **MAU (Monthly Active Users):** Počet unikátních aktivních členů za posledních 30 dní.

### Technická implementace
Využíváme Redis datovou strukturu HLL, která umožňuje odhadnout kardinalitu množiny s miliony prvků se standardní chybou pouze **0,81 %**, přičemž spotřebuje fixních **12 KB** paměti na jeden den. Pro výpočet MAU používáme příkaz `PFMERGE`, který sloučí 30 denních struktur do jedné.

## Analýza zapojení (Stickiness)

Tato metrika určuje loajalitu vaší komunity. Vyjadřuje, kolik procent měsíčních uživatelů se vrací na server každý den.

$$ \text{Stickiness} = \frac{\text{DAU}}{\text{MAU}} \times 100 $$

| Rozsah | Interpretace |
| :--- | :--- |
| **< 5 %** | Uživatelé se nevracejí. Nízká loajalita. |
| **10–15 %** | Standardní úroveň pro hobby a zájmové servery. |
| **> 25 %** | Extrémně silné a věrné jádro komunity. |

## Index moderační zátěže (MII)

MII (Moderation Intervention Index) vyjadřuje míru moderační zátěže vzhledem k celkovému objemu diskuze. Zvýšená hodnota neindikuje nutně "toxicitu" komunity, nýbrž může odrážet změnu pravidel nebo aktivnější přístup moderátorů.

$$ MII = \frac{\sum_k w_k M_k}{\max(1, N_{\text{interactions}})} $$

Váhy jednotlivých akcí:
-   **Ban:** 50 bodů
-   **Kick:** 30 bodů
-   **Timeout:** 10 bodů
-   **Smazaná zpráva:** 1 bod

## Engagement Score (Skóre aktivity)

Engagement Score je normalizovaný index (0–100), který slouží k porovnání aktivity stejné komunity v čase. Není to univerzální hodnocení "kvality" serveru. Vypočítá se jako vážený průměr dostupných datových zdrojů:

$$ S_{eng} = 100 \cdot \frac{w_uU + w_mM + w_rR + w_vV}{w_u + w_m + w_r + w_v} $$

| Složka | Význam |
| :--- | :--- |
| **$U$ (Uživatelé)** | Normalizovaný podíl aktivních uživatelů (DAU/Total). |
| **$M$ (Zprávy)** | Normalizovaný objem odeslaných zpráv. |
| **$R$ (Reakce)** | Normalizovaný počet interakcí/reakcí. |
| **$V$ (Hlas)** | Normalizovaná hlasová aktivita (pokud je dostupná). |

Váhy ($w$) jsou konfigurovatelné. Pokud některý údaj není dostupný (např. chybí hlasový kanál), odpovídající váha se vyřadí ze jmenovatele, aby nedošlo k umělému snížení skóre. Nulová hodnota a nedostupný údaj jsou striktně odlišeny.

## Vizualizace aktivity (Heatmapa)

Analytický engine generuje matici 7 × 24 (den v týdnu × hodina), která vizualizuje hustotu zpráv.

-   **Uložení:** Redis Hash s klíčem `stats:heatmap:{guild_id}`.
-   **Formát pole:** `den:hodina` (např. `1:14` pro pondělí 14:00 UTC).
-   **Využití:** Plánujte své klíčové aktivity na časy s nejvyšší hustotou v heatmapě.

## Kvalita dat (DQS)

DQS (Data Quality Score) je pomocný indikátor úplnosti vstupních dat pro celkovou analýzu, nikoliv statistická pravděpodobnost správnosti modelů. 

Zohledňuje rozdíl mezi situací, kdy **událost nenastala** (hodnota je 0), a kdy **údaj není dostupný** (platforma data neposkytuje).

| Indikace DQS | Interpretace |
| :--- | :--- |
| **Vysoká (> 80 %)** | Dostatek historie (např. > 30 dní) a kompletní datové zdroje. |
| **Střední** | Částečná historie nebo chybějící některé sekundární zdroje. |
| **Nízká (< 50 %)** | Nedostatek dat pro validní výpočet trendů. Data z agregace mohou být zkreslená. |
