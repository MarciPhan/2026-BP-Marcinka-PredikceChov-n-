---
layout: home

hero:
  name: Metricord
  text: Analytická platforma nové generace
  tagline: Zpracovávejte miliony událostí v reálném čase a předpovídejte budoucnost vaší komunity.
  actions:
    - theme: brand
      text: Rychlý start
      link: /quickstart
    - theme: alt
      text: Architektura
      link: /architecture

features:
  - title: Real-time analytika
    details: Sledování aktivity v momentě, kdy se děje. Sub-sekundové zpracování každé zprávy.
    icon: ⚡
  - title: Predikce chování
    details: Markovovy řetězce pro předpověď retence a churn rate na 7 dní dopředu.
    icon: 🧠
  - title: Survival analýza
    details: Kaplan-Meier křivky ukazující střední délku života uživatelů na serveru.
    icon: 📈
  - title: Skóre bezpečnosti
    details: Unikátní algoritmus pro hodnocení zabezpečení serveru (MFA, verifikace).
    icon: 🛡️
  - title: Heatmapa aktivity
    details: Vizualizace aktivity po dnech a hodinách pro identifikaci špičkových časů.
    icon: 🔥
  - title: XP & Leveling
    details: Anti-spam XP systém s cooldownem, délkovým bonusem a voice trackingem.
    icon: 🎮
---

## Kam začít?

::: info Tip pro nové komunity
Pro dosažení nejlepších výsledků doporučujeme nechat bota běžet alespoň 7 dní, aby mohl nasbírat dostatek dat pro přesné predikce. Chcete-li data ihned, použijte [Backfill systém](/backfill).
:::

### 🚀 [Rychlý start](/quickstart)
Nastavte bota během 5 minut a začněte sbírat data. Krok za krokem.

### 👤 [Uživatelská příručka](/user-guide)
XP systém, příkazy pro členy, leveling křivka a vše o vašem soukromí.

### 🛡️ [Moderátorský průvodce](/moderators)
Jak interpretovat pokročilé metriky, predikce, krizové stavy a optimalizovat komunitu.

### 🧩 [Architektura systému](/architecture)
Technická dokumentace: Redis schéma, datový tok, Mermaid diagramy.

---

## Technický přehled

Metricord je postavený na moderním technologickém stacku optimalizovaném pro vysoký výkon:

- **Python 3.9+:** discord.py 2.6, FastAPI, NumPy.
- **Redis / Valkey:** In-memory DB, sub-ms latence.
- **Chart.js:** Interaktivní grafy a vizualizace.
- **Docker:** Kontejnerizované nasazení.

## Pro koho je tato dokumentace?

- **Moderátoři a správci serverů:** Naučte se interpretovat metriky a rozpoznávat krizové signály.
- **Vývojáři:** API reference, Redis schéma, architektura systému a příklady integrace.
- **Členové komunity:** Pochopte XP systém, příkazy a své možnosti.
- **Akademická sféra:** Matematické základy prediktivních modelů a [Whitepaper](/whitepaper).
