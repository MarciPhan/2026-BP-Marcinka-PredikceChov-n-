# Smart Insights Engine

Váš analytický asistent, který nikdy nespí. Insights Engine vyhodnocuje více než 20 metrik každou hodinu a automaticky detekuje anomálie, trendy a příležitosti pro moderátorský tým.

## Typy detekcí

### Bezpečnostní varování (Severity: Kritická)

| Insight | Podmínka | Doporučená akce moderátora |
| :--- | :--- | :--- |
| **Raid Detection** | Nárůst nových členů > 10 za 5 min + nárůst zpráv > 500%. | Aktivujte verification mode, zapněte slowmode. |
| **Mass Mention Spam** | Velký počet @everyone / @here zmínek od ne-adminů. | Ban útočníků, zkontrolujte oprávnění rolí. |
| **Alt Account Alert** | Dva účty se shodnými vzorci chování (časy, délky). | Prohlédněte profily v Security dashboardu. |

### Trendy a Retence (Závažnost: Střední)

| Insight | Podmínka | Doporučená akce |
| :--- | :--- | :--- |
| **Dead Server Warning** | DAU pokles > 30% oproti 30dennímu průměru. | Analyzujte příčinu. Uspořádejte event. |
| **Churn Spike** | Náhlý nárůst odchodů ze serveru. | Zkontrolujte poslední změny pravidel, drama. |
| **Onboarding Failure** | Survival křivka ukazuje > 60% odchod do 48h. | Vylepšete welcome kanál, přidejte role-select. |
| **Engagement Plateau** | Engagement Score stagnuje 7+ dní. | Komunita potřebuje nový impulz — nový kanál. |

### Management komunity (Závažnost: Informativní)

| Insight | Podmínka | Doporučená akce |
| :--- | :--- | :--- |
| **Moderation Gap** | Vysoká aktivita + nulové mod akce > 4 hodiny. | Zkontrolujte, zda jsou moderátoři online. |
| **Voice Overload** | Voice kanály často na 100% kapacity. | Vytvořte nové voice roomky. |
| **Understaffed Warning** | Doporučeno více moderátorů, než máte. | Identifikujte potenciální nové moderátory. |
| **Peak Time Shift** | Hodina max aktivity se posunula o 2+ hodiny. | Aktualizujte plán eventů a směny. |

## Notifikace

Insights se zobrazují na několika místech:
- **Dashboard:** Karta „Smart Insights" na hlavní stránce serveru.
- **Discord:** Kritické insighty lze posílat do moderátorského kanálu.
- **Bot Console:** Všechny insighty se logují pro audit.

::: info Confidence Score
Každý insight má skóre spolehlivosti (0–1.0). Insights s confidence < 0.5 se zobrazují jako „experimentální". Čím více dat (7+ dní), tím přesnější insighty.
:::
