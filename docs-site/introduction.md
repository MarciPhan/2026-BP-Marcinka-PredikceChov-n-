# Úvod do Metricord

Vítejte v oficiální dokumentaci **Metricord** — analytické platformy nové generace pro Discord komunity. Náš nástroj zpracovává miliony událostí v reálném čase a poskytuje vám prediktivní analýzy, které vám pomohou aktivně řídit zdraví a růst vaší komunity.

Od sledování aktivity jednotlivých členů, přes analýzu voice kanálů, predikci budoucího růstu až po identifikaci toxických vzorců — vše máte pod kontrolou v jednom přehledném dashboardu.

## Klíčové vlastnosti

| Vlastnost | Popis | Kategorie |
| --- | --- | --- |
| **Real-time analytika** | Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování. | Analytika |
| **Predikce chování** | Markovovy řetězce pro předpověď retence a churn rate na 7 dní dopředu. | AI / ML |
| **Survival analýza** | Kaplan-Meier křivky ukazující střední délku života uživatelů na serveru. | AI / ML |
| **Engagement Score** | Kompozitní index zdraví komunity (0-100). | Metriky |
| **XP & Leveling** | Anti-spam XP systém s cooldownem a voice trackingem. | Gamifikace |
| **Export dat** | JSON export pro další zpracování v Excelu nebo Pythonu. | Data |

::: info Tip pro komunity
Pro dosažení nejlepších výsledků doporučujeme nechat bota běžet alespoň 7 dní, aby mohl nasbírat dostatek dat pro přesné predikce a trendy. Pokud chcete data ihned, použijte **Backfill systém** pro synchronizaci historie.
:::

## Pro koho je tato dokumentace?

- **Moderátoři a správci serverů:** Naučte se interpretovat metriky a optimalizovat růst komunity.
- **Vývojáři:** API reference, Redis schéma a architektura systému.
- **Akademická sféra:** Matematické základy prediktivních modelů a whitepaper.

## Technický stack

Metricord je postaven na moderních technologiích:
- **Python 3.9+** (discord.py, FastAPI, NumPy)
- **Redis / Valkey** (In-memory databáze)
- **Docker** (Kontejnerizace)
- **VitePress** (Moderní dokumentace)
