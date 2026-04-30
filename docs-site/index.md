---
layout: home

hero:
  name: Metricord
  text: Analytická platforma pro Discord komunity
  tagline: Zpracování událostí v reálném čase. Predikce chování uživatelů. Správa založená na datech.
  actions:
    - theme: brand
      text: Rychlý start →
      link: /quickstart
    - theme: alt
      text: Architektura
      link: /architecture
    - theme: alt
      text: GitHub
      link: https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-

features:
  - title: Real-time analytika
    details: Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování každé zprávy.
    link: /analytics
  - title: Predikce chování
    details: Markovovy řetězce pro předpověď retence a churn rate na 7 dní dopředu.
    link: /predictions
  - title: Survival analýza
    details: Kaplan-Meier křivky ukazující střední délku setrvání uživatelů na serveru.
    link: /math-foundations
  - title: Skóre bezpečnosti
    details: Algoritmus pro hodnocení zabezpečení serveru (MFA, verifikace, filtry obsahu).
    link: /security
  - title: Heatmapa aktivity
    details: Vizualizace aktivity po dnech a hodinách pro identifikaci špičkových časů.
    link: /analytics#heatmap
  - title: XP a Leveling
    details: Anti-spam XP systém s cooldownem, délkovým bonusem a voice trackingem.
    link: /commands#xp
---

## Kde začít

::: info Tip pro nové servery
Pro přesné predikce doporučujeme nechat bota sbírat data alespoň 7 dní. Pro okamžité výsledky použijte [backfill historických dat](/backfill).
:::

<div class="premium-grid">
  <a href="/quickstart" class="premium-card">
    <h3>🚀 Rychlý start</h3>
    <p>Nastavení bota během 5 minut. Průvodce krok za krokem od instalace po první predikce.</p>
  </a>

  <a href="/user-guide" class="premium-card">
    <h3>📖 Uživatelská příručka</h3>
    <p>Příkazy, XP systém, leveling a ochrana osobních údajů.</p>
  </a>

  <a href="/moderators" class="premium-card">
    <h3>🛡️ Příručka pro moderátory</h3>
    <p>Interpretace metrik, predikce, krizové stavy a správa komunity.</p>
  </a>

  <a href="/architecture" class="premium-card">
    <h3>⚙️ Architektura</h3>
    <p>Redis schéma, datový tok, Mermaid diagramy a technické detaily.</p>
  </a>

  <a href="/dev-guide" class="premium-card">
    <h3>💻 Vývojářský průvodce</h3>
    <p>Lokální vývoj, přidávání příkazů, API a Redis best practices.</p>
  </a>

  <a href="/faq" class="premium-card">
    <h3>❓ FAQ & Troubleshooting</h3>
    <p>Odpovědi na časté dotazy a řešení běžných problémů.</p>
  </a>
</div>

---

## Technický přehled

Metricord je postavený na technologickém stacku optimalizovaném pro vysoký výkon:

- **Python 3.9+** — discord.py 2.6, FastAPI, NumPy.
- **Redis / Valkey** — In-memory databáze, sub-ms latence.
- **Chart.js** — Interaktivní grafy a vizualizace.
- **VitePress** — Moderní dokumentační platforma.
- **Docker** — Kontejnerizované nasazení.

## Pro koho je tato dokumentace

- **Moderátoři a správci serverů** — interpretace metrik a rozpoznávání krizových signálů.
- **Vývojáři** — API reference, Redis schéma, architektura a příklady integrace.
- **Členové komunity** — XP systém, příkazy a ochrana osobních údajů.
- **Akademická sféra** — [Matematické základy](/math-foundations) prediktivních modelů a [srovnání ML algoritmů](/ml-comparison).

## Rychlý start za 4 řádky

```bash
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-
cp .env.example .env    # Vyplňte BOT_TOKEN
./start.sh              # Spustí bot + dashboard + docs
```

Podrobný návod: [Rychlý start](/quickstart) | [Instalace a konfigurace](/setup) | [Docker nasazení](/deployment)
