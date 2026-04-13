# Vážený XP Systém a Správa Rolí

Metricord nepoužívá statické body. Náš systém je dynamický a reaguje na kvalitu interakce. Cílem je vytvořit spravedlivé prostředí, kde "kvantita" neznamená automaticky "vliv".

## 1. Algoritmus výpočtu XP

Každá akce uživatele prochází filtrem kvality předtím, než jsou připsány body.

| Typ Akce | Získané XP | Podmínky a Bonusy |
| :--- | :--- | :--- |
| **Krátká zpráva** (< 15 znaků) | 1 bod | Zahrnuje emojis a jednoslovné příkazy. |
| **Standardní zpráva** (15 - 100 znaků) | 5 bodů | Základní stavební kámen konverzace. |
| **Dlouhý příspěvek** (> 100 znaků) | 15+ bodů | Body rostou lineárně s délkou (max 50 XP). |
| **Odpověď (Reply)** | +10 bodů | Bonus k základnímu XP za použití funkce 'Reply'. |
| **Voice Aktivita** | 5 body / min | Musí být aktivní mikrofon (ne mute). |

::: info Variable Ratio Reinforcement
Systém přidává náhodnou složku (±15%) ke každému XP zisku. Tato metoda zvyšuje psychologickou angažovanost uživatelů a ztěžuje předvídatelnost pro farmící boty.
:::

## 2. Anti-Spam a Fraud Detekce

- **Message Cooldown (60s):** Omezení na 1 XP-profitující zprávu za minutu.
- **Duplicate Check:** Odeslání stejné zprávy vícekrát za sebou dává 0 XP.
- **Noční korekce (2:00-6:00):** Body jsou násobeny koeficientem `0.5`, aby se předešlo nočnímu farmení.

## 3. Úrovně a Progrese

Výpočet úrovně $L$ z celkových XP $X$ se řídí kvadratickou funkcí:

$$X(L) = 50 \cdot L^2 + 200 \cdot L + 100$$

To znamená, že progrese je schválně náročná, aby role měly svou váhu a prestiž.
- **Level 2:** 700 XP
- **Level 10:** 7 100 XP
- **Level 50:** 135 100 XP

## 4. Automatizace rolí (Auto-Levels)

V dashboardu můžete propojit konkrétní úrovně s Discord rolemi. Bot provádí synchronizaci:
1. Při každém získání nové úrovně.
2. Pravidelně každých 24 hodin.
3. Manuálně pomocí příkazu `/activity sync_names`.

::: tip Doporučení pro adminy
Nenastavujte příliš mnoho rolí (např. každou úroveň). Ideální je odměnit úrovně 5, 10, 25, 50 a 100.
:::
