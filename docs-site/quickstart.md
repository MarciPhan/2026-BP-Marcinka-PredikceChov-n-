# Rychlý start s Metricord

Tento průvodce vás provede prvním nastavením během 5 minut. Od nuly k prvním predikcím.

::: info Krok 1: Pozvání bota a konfigurace Intents
Prvním krokem je přidání bota na váš server. Metricord vyžaduje specifická **Privileged Intents** pro správnou funkci analytiky. Bez nich nebude bot schopen sledovat zprávy ani voice aktivitu.

- **Message Content Intent:** Nutné pro analýzu délky zpráv a aktivity v kanálech.
- **Guild Members Intent:** Nutné pro sledování příchodů, odchodů a synchronizaci profilů.
- **Server Members Intent:** Nutné pro real-time statistiky online uživatelů.

[Pozvat bota na server →](/login?invite=true)
:::

::: tip Krok 2: Autorizace dashboardu
Přihlaste se pomocí svého Discord účtu. Tím získáte přístup ke všem serverům, kde máte práva **Manage Server** nebo **Administrator**.

Po prvním přihlášení Metricord automaticky zinventarizuje všechny role na serveru, což umožní pozdější filtrování statistik podle hodností.

**Bezpečnost:** Používáme OAuth2 s PKCE. Vaše heslo nikdy nevidíme, dostáváme pouze dočasný přístupový token.
:::

::: info Krok 3: První synchronizace (Backfill)
Ve výchozím stavu bot sleduje aktivitu od momentu pozvání. Chcete-li vidět historické trendy ihned, použijte modul **Backfill**.

```bash
/activity backfill days:30
```

*Tento příkaz projde historii zpráv ve všech kanálech a zpětně dopočítá XP a statistiky.*
:::

::: tip Krok 4: Kalibrace XP algoritmů
Každá komunita má jinou dynamiku. V sekci **Nastavení XP** můžete definovat:

- **Base XP:** Kolik bodů získá uživatel za jednu zprávu.
- **Voice Multiplier:** Koeficient pro minutu strávenou ve voice kanálu.
- **Length Bonus:** Dodatečné body za dlouhé zprávy.
- **Cooldown:** Minimální rozestup mezi zprávami pro zisk XP.
:::

## Důležité milníky po instalaci

Analytika Metricord pracuje v několika časových horizontech:

| Čas | Dostupná data | Účel |
| :--- | :--- | :--- |
| **1 hodina** | Real-time Heatmapa | Okamžitý přehled o aktuální špičce. |
| **24 hodin** | Denní trendy (DAU) | Porovnání dnešní aktivity s včerejškem. |
| **7 dní** | Prediktivní modely | První odhady retence členů a Engagement Score. |
| **30 dní** | Survival analýza | Kompletní Kaplan-Meier křivky přežití komunity. |

---

::: info Další krok
Přečtěte si [Best Practices](/best-practices), jak tato data využít pro růst serveru.
:::
