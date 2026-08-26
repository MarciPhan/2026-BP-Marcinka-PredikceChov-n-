> **Note:** These features (including XP, leveling, and achievements) are additional extensions and are not part of the core functionality evaluated in the bachelor thesis.

# Úvod do CommunityMetrics

Vítejte v oficiální dokumentaci **CommunityMetrics** — analytické platformy nové generace pro Discord komunity. CommunityMetrics zpracovává události v reálném čase a poskytuje prediktivní analýzy, které vám pomohou aktivně řídit zdraví a růst vaší komunity.

Od sledování aktivity jednotlivých členů, přes analýzu voice kanálů, predikci budoucího růstu až po identifikaci krizových vzorců — vše máte pod kontrolou v jednom přehledném dashboardu.

## Klíčové vlastnosti

| Vlastnost | Popis | Kategorie |
| --- | --- | --- |
| **Real-time analytika** | Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování. | Analytika |
| **Predikce aktivity** | Prototypový model využívající Markovovy řetězce k analýze změn aktivity. | Analytika |
| **Analýza aktivity** | Kaplanův-Meierův odhad ukazující medián doby setrvání v aktivitě. | Analytika |
| **Engagement Score** | Kompozitní index Engagement Score (0–100). | Metriky |
| **XP & Leveling** | Anti-spam XP systém s cooldownem a voice trackingem. | Gamifikace |
| **Smart Insights** | Automatická doporučení a varování pro moderátory. | Analytika |
| **Export dat** | JSON/CSV export pro další zpracování v Excelu nebo Pythonu. | Data |
| **Skóre bezpečnosti** | Hodnocení zabezpečení serveru (MFA, verifikace, filtry). | Bezpečnost |

::: info Tip pro komunity
Pro dosažení nejlepších výsledků doporučujeme nechat bota běžet alespoň 30 dní, aby mohl nasbírat dostatek dat pro experimentální predikce (Markov, Kaplan-Meier). Základní statistiky jsou dostupné okamžitě. Pokud chcete data ihned, použijte [Backfill systém](/backfill) pro synchronizaci historie.
:::

## Pro koho je tato dokumentace?

| Cílová skupina | Kde začít | Co se dozvíte |
| :--- | :--- | :--- |
| **Správci serverů** | [Rychlý start](/quickstart) | Instalace, konfigurace, první metriky. |
| **Moderátoři** | [Průvodce pro moderátory](/moderators) | Interpretace metrik, krizové scénáře, best practices. |
| **Vývojáři** | [Vývojářský průvodce](/dev-guide) | API, Redis schéma, architektura, lokální vývoj. |
| **Členové komunity** | [Uživatelská příručka](/user-guide) | XP systém, příkazy, ochrana osobních údajů. |

## Technický stack

CommunityMetrics je postaven na moderních technologiích optimalizovaných pro vysoký výkon:

| Technologie | Verze | Účel |
| :--- | :--- | :--- |
| **Python** | 3.11 | discord.py 2.6.4, FastAPI 0.121.1, NumPy 2.3.2 |
| **Redis** | alpine (Docker) | In-memory databáze |
| **Chart.js** | 4.x | Interaktivní grafy a vizualizace |
| **VitePress** | ^1.0.0 | Moderní dokumentace |
| **Docker** | python:3.11-slim | Kontejnerizované nasazení |

## Začněte za 5 minut

Nejrychlejší cesta ke spuštění:

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-
cp .env.example .env    # Vyplňte BOT_TOKEN
chmod +x start.sh && ./start.sh
```

Podrobný návod najdete v [Rychlém startu](/quickstart) nebo v [Instalaci a konfiguraci](/setup).
