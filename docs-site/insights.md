# Smart Insights

Insights Engine automaticky vyhodnocuje metriky serveru a generuje varování, doporučení a anomálie. Výsledky se zobrazují v dashboardu na kartě **Smart Insights** a volitelně jako zprávy v moderátorském Discord kanálu.

## Bezpečnostní varování (kritická závažnost)

| Insight | Podmínka | Doporučená akce |
| :--- | :--- | :--- |
| **Raid Detection** | > 10 nových členů za 5 min + nárůst zpráv > 500 % | Aktivujte verification mode a slowmode. |
| **Mass Mention Spam** | Opakované @everyone / @here od ne-adminů | Zkontrolujte oprávnění rolí, zablokujte útočníky. |
| **Alt Account Alert** | Dva účty se shodnými vzorci chování (časy, délky zpráv) | Prověřte profily v Security dashboardu. |

## Retence a trendy (střední závažnost)

| Insight | Podmínka | Doporučená akce |
| :--- | :--- | :--- |
| **Dead Server Warning** | DAU pokles > 30 % oproti 30dennímu průměru | Analyzujte příčinu. Uspořádejte event. |
| **Churn Spike** | Náhlý nárůst odchodů | Zkontrolujte poslední změny pravidel. |
| **Onboarding Failure** | Survival křivka ukazuje > 60 % odchod do 48 h | Vylepšete uvítací kanál, přidejte role-select. |
| **Engagement Plateau** | Engagement Score stagnuje 7+ dní | Komunita potřebuje nový impulz. |

## Management komunity (informativní závažnost)

| Insight | Podmínka | Doporučená akce |
| :--- | :--- | :--- |
| **Moderation Gap** | Vysoká aktivita + nulové moderátorské akce > 4 h | Ověřte, zda jsou moderátoři online. |
| **Voice Overload** | Voice kanály na 100 % kapacity | Vytvořte nové voice kanály. |
| **Understaffed** | Doporučeno více moderátorů, než máte | Identifikujte potenciální moderátory. |
| **Peak Time Shift** | Hodina max. aktivity se posunula o 2+ h | Aktualizujte plán eventů a směny. |

## Doručování notifikací

Insighty se zobrazují na třech místech:

1. **Dashboard** - Karta „Smart Insights" na hlavní stránce serveru.
2. **Discord** - Kritické insighty odesílá bot do nakonfigurovaného moderátorského kanálu.
3. **Konzole** - Všechny insighty se logují do `bot.log` pro audit.

## Confidence Score

Každý insight má skóre spolehlivosti (0–1,0):

| Rozsah | Klasifikace | Význam |
| :--- | :--- | :--- |
| > 0,8 | Vysoká | Doporučena akce moderátora. |
| 0,5–0,8 | Střední | Indikativní - sledujte uživatele. |
| < 0,5 | Experimentální | Málo dat, zobrazuje se s označením. |

Spolehlivost roste s objemem nasbíraných dat. Pro plnou funkčnost insightů je doporučeno minimálně 7 dní historie (ideálně po [backfillu](/backfill)).
