# Úvod do Metricord

Vítejte v oficiální dokumentaci **Metricord** — analytické platformy nové generace pro Discord komunity. Metricord zpracovává události v reálném čase a poskytuje prediktivní analýzy, které vám pomohou aktivně řídit zdraví a růst vaší komunity.

Od sledování aktivity jednotlivých členů, přes analýzu voice kanálů, predikci budoucího růstu až po identifikaci krizových vzorců — vše máte pod kontrolou v jednom přehledném dashboardu.

## Klíčové vlastnosti

| Vlastnost | Popis | Kategorie |
| --- | --- | --- |
| **Real-time analytika** | Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování. | Analytika |
| **Predikce chování** | Markovovy řetězce pro předpověď retence a churn rate na 7 dní dopředu. | AI / ML |
| **Survival analýza** | Kaplan-Meier křivky ukazující střední délku setrvání uživatelů na serveru. | AI / ML |
| **Engagement Score** | Kompozitní index zdraví komunity (0–100). | Metriky |
| **XP & Leveling** | Anti-spam XP systém s cooldownem a voice trackingem. | Gamifikace |
| **Smart Insights** | Automatická doporučení a varování pro moderátory. | AI |
| **Export dat** | JSON/CSV export pro další zpracování v Excelu nebo Pythonu. | Data |
| **Skóre bezpečnosti** | Hodnocení zabezpečení serveru (MFA, verifikace, filtry). | Bezpečnost |

::: info Tip pro komunity
Pro dosažení nejlepších výsledků doporučujeme nechat bota běžet alespoň 7 dní, aby mohl nasbírat dostatek dat pro přesné predikce a trendy. Pokud chcete data ihned, použijte [Backfill systém](/backfill) pro synchronizaci historie.
:::

## Pro koho je tato dokumentace?

| Cílová skupina | Kde začít | Co se dozvíte |
| :--- | :--- | :--- |
| **Správci serverů** | [Rychlý start](/quickstart) | Instalace, konfigurace, první metriky. |
| **Moderátoři** | [Průvodce pro moderátory](/moderators) | Interpretace metrik, krizové scénáře, best practices. |
| **Vývojáři** | [Vývojářský průvodce](/dev-guide) | API, Redis schéma, architektura, lokální vývoj. |
| **Členové komunity** | [Uživatelská příručka](/user-guide) | XP systém, příkazy, ochrana osobních údajů. |
| **Akademická sféra** | [Matematické základy](/math-foundations) | Formální popis prediktivních modelů a algoritmů. |

## Technický stack

Metricord je postaven na moderních technologiích optimalizovaných pro vysoký výkon:

| Technologie | Verze | Účel |
| :--- | :--- | :--- |
| **Python** | 3.9+ | discord.py 2.6, FastAPI, NumPy |
| **Redis / Valkey** | 6.0+ | In-memory databáze, sub-ms latence |
| **Chart.js** | 4.x | Interaktivní grafy a vizualizace |
| **VitePress** | 1.x | Moderní dokumentace |
| **Docker** | 20.10+ | Kontejnerizované nasazení |

## Začněte za 5 minut

Nejrychlejší cesta ke spuštění:

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-
cp .env.example .env    # Vyplňte BOT_TOKEN
chmod +x start.sh && ./start.sh
```

Podrobný návod najdete v [Rychlém startu](/quickstart) nebo v [Instalaci a konfiguraci](/setup).
