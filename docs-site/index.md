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
  - title: Predikce chování
    details: Markovovy řetězce pro předpověď retence a churn rate na 7 dní dopředu.
    link: /predictions
  - title: Real-time analytika
    details: Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování každé zprávy.
    link: /analytics
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
  <a href="/user-guide" class="premium-card">
    <h3> Uživatelská příručka</h3>
    <p>Příkazy, XP systém, leveling a ochrana osobních údajů.</p>
  </a>

  <a href="/quickstart" class="premium-card">
    <h3> Rychlý start</h3>
    <p>Nastavení bota během 5 minut. Průvodce krok za krokem od instalace po první predikce.</p>
  </a>

  <a href="/moderators" class="premium-card">
    <h3> Příručka pro moderátory</h3>
    <p>Interpretace metrik, predikce, krizové stavy a správa komunity.</p>
  </a>

  <a href="/architecture" class="premium-card">
    <h3> Architektura</h3>
    <p>Redis schéma, datový tok, Mermaid diagramy a technické detaily.</p>
  </a>

  <a href="/dev-guide" class="premium-card">
    <h3> Vývojářský průvodce</h3>
    <p>Lokální vývoj, přidávání příkazů, API a Redis best practices.</p>
  </a>

  <a href="/faq" class="premium-card">
    <h3> FAQ & Troubleshooting</h3>
    <p>Odpovědi na časté dotazy a řešení běžných problémů.</p>
  </a>
</div>

---


## Cílové skupiny a využití dokumentace

Tato dokumentace je strukturována podle rolí a konkrétních úkolů, které v systému Metricord řešíte. Vyberte si cestu, která odpovídá vašim potřebám.

### Pro moderátory a správce komunit
Metricord vám pomůže pochopit dynamiku vašeho serveru a činit rozhodnutí podložená daty.
- **Řízení aktivity:** Naučte se interpretovat [analytické metriky](/analytics) a spravovat [XP systém](/roles).
- **Prevence odchodů:** Včas identifikujte krizové signály pomocí [Smart Insights](/insights) a [predikce retence](/predictions).
- **Bezpečnost a soukromí:** Nastavte správně [skóre bezpečnosti](/security) a seznamte se s [ochranou osobních údajů](/privacy).

### Pro vývojáře a technické administrátory
Zde najdete vše potřebné pro instalaci, úpravu kódu a integraci bota do vaší infrastruktury.
- **Nasazení a správa:** Postupujte podle [průvodce instalací](/setup) nebo [nasazením do cloudu](/cloud-deployment).
- **Vývoj bota:** Prostudujte si [vývojářskou příručku](/dev-guide) a [příklady API požadavků](/api-examples).
- **Integrace:** Propojte Metricord s dalšími nástroji pomocí [webhooků](/integrations) a [API Reference](/api).

### Pro analytiky a akademický výzkum
Pokud vás zajímá teoretické pozadí a matematické modely použité pro predikci chování uživatelů.
- **Matematické modely:** Detailní popis [Markovových řetězců](/math-foundations) a statistických metod.
- **Srovnání algoritmů:** Analýza [výběru ML algoritmů](/ml-comparison) a jejich přesnosti v čase.
- **Struktura dat:** Kompletní přehled [Redis datového schématu](/data-schema) pro vlastní analýzy.

### Pro členy komunity
Informace o tom, jak bot ovlivňuje vaši zkušenost na serveru.
- **Funkce pro uživatele:** Přehled [příkazů bota](/commands) a fungování leveling systému.
- **Transparentnost:** Jaká data Metricord sbírá a jak s nimi nakládá najdete v [Zásadách ochrany soukromí](/privacy).

