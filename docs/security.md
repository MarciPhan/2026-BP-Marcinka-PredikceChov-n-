# Skóre bezpečnosti serveru (Doplňková funkce)

Skóre bezpečnosti ($S$) vyjadřuje doplňkový indikátor odolnosti Discord serveru proti spamu a útokům a míru zapojení moderátorů. Tato metrika je experimentální, stojí mimo hlavní analytické cíle (Engagement, MII) a vypočítává se z nastavení serveru, poměru moderátorů, aktivity moderátorského týmu a zapojení uživatelů.

## Výpočet skóre

Skóre je vážený průměr **4 komponent** v rozsahu 0–100. Pokud některá komponenta není dostupná (chybí data), její váha se vyřadí ze jmenovatele:

$$S = \frac{\sum_{k \in \text{available}} w_k \cdot C_k}{\sum_{k \in \text{available}} w_k}$$

| Komponenta | Váha (výchozí) | Zdroj dat | Výpočet |
| :--- | :--- | :--- | :--- |
| **Poměr moderátorů** (`mod_ratio`) | 25 % | `presence:total`, `stats:mod_count` | Skóre dle poměru uživatelů na moderátora (ideální rozsah 50–100). |
| **Zabezpečení serveru** (`security`) | 25 % | `guild:verification_level`, `guild:mfa_level`, `guild:explicit_filter` | Kompozit: verifikace (max 60b), explicitní filtr (max 20b), MFA (20b). |
| **Zapojení uživatelů** (`engagement`) | 25 % | HLL DAU, Help Requests, Voice events | Kompozit: participation rate (40b), reply ratio (30b), voice hours (30b). |
| **Zdraví moderace** (`moderation`) | 25 % | `events:action:{gid}:*` | Skóre dle intenzity moderačních zásahů na 100 uživatelů (ideální rozsah 1–5). |

## Klasifikace

| Rozsah | Kategorie | Popis |
| :--- | :--- | :--- |
| 90–100 | Fortress | Všechny filtry aktivní, aktivní moderace. |
| 60–89 | Stable | Základní ochrana, doporučeno zapnout MFA. |
| 30–59 | Exposed | Chybí filtry obsahu nebo nízká verifikace. |
| 0–29 | Vulnerable | Server je náchylný k raidům a spamu. |

## Zlepšení skóre

Doporučení pro zvýšení skóre na úroveň Fortress:

1. V nastavení Discord serveru nastavte **Verification Level** na „Medium" nebo „High".
2. Aktivujte **Explicit Content Filter** pro všechny členy.
3. Zapněte **2FA Requirement** pro moderátory (Server Settings → Safety Setup).
4. Zajistěte přítomnost moderátorů v časech špičky (dle Heatmapy aktivity).

## Dashboard

Skóre se zobrazuje na hlavní stránce dashboardu v kartě **Security Score**. Karta obsahuje:
- Aktuální skóre a kategorii.
- Rozpad na jednotlivé komponenty s doporučeními (Smart Insights).

::: info Ochrana soukromí
Výpočet skóre využívá pouze metadata nastavení serveru a audit log. Obsah zpráv uživatelů se neanalyzuje.
:::
