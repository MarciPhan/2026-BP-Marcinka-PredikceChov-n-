# Technické metriky a KPI

Metricord vypočítává širokou škálu ukazatelů výkonnosti (KPI). Tento dokument podrobně vysvětluje jejich matematický základ, způsob uložení v databázi a správnou interpretaci.

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

## Index intenzity moderace (MII)

MII (Moderator Intervention Index) měří úroveň toxicity a potřebu moderátorských zásahů vzhledem k objemu diskuze.

$$ MII = \sum_{i \in \text{Akce}} \frac{\text{Váha}(i)}{\text{Celkový počet zpráv}} $$

Váhy jednotlivých akcí:
-   **Ban:** 50 bodů
-   **Kick:** 30 bodů
-   **Timeout:** 10 bodů
-   **Smazaná zpráva:** 1 bod

## Metrika zdraví serveru (Engagement Score)

Engagement Score (ES) je kompozitní index (0–100), který shrnuje celkový stav serveru na základě čtyř klíčových oblastí:

$$ ES = 0,25 \cdot M + 0,25 \cdot S + 0,25 \cdot E + 0,25 \cdot T $$

| Složka | Význam |
| :--- | :--- |
| **$M$ (Moderace)** | Hodnota odvozená od MII a rychlosti reakce týmu. |
| **$S$ (Bezpečnost)** | Skóre zabezpečení (MFA, verifikace, filtry). |
| **$E$ (Zapojení)** | Participation Rate a Reply Ratio. |
| **$T$ (Tým)** | Intenzita aktivity moderátorského týmu. |

## Vizualizace aktivity (Heatmapa)

Analytický engine generuje matici 7 × 24 (den v týdnu × hodina), která vizualizuje hustotu zpráv.

-   **Uložení:** Redis Hash s klíčem `stats:heatmap:{guild_id}`.
-   **Formát pole:** `den:hodina` (např. `1:14` pro pondělí 14:00 UTC).
-   **Využití:** Plánujte své klíčové aktivity na časy s nejvyšší hustotou v heatmapě.

## Kvalita dat pro predikce (DQS)

DQS (Data Quality Score) určuje spolehlivost prediktivních modelů. Pokud je historie dat příliš krátká, systém predikce automaticky deaktivuje.

| Hodnota DQS | Stav modelů | Poznámka |
| :--- | :--- | :--- |
| **1,0** | Aktivní (Plná důvěra) | Historie dat > 30 dní. |
| **0,5–0,9** | Aktivní (Omezená důvěra) | Historie 7–30 dní. Možné odchylky. |
| **< 0,5** | Deaktivováno | Nedostatek dat pro validní výpočet. |
