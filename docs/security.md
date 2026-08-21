# Skóre bezpečnosti serveru (Doplňková funkce)

Skóre bezpečnosti ($S$) vyjadřuje doplňkový indikátor odolnosti Discord serveru proti spamu a útokům a kvalitu podpory. Tato metrika je experimentální, stojí mimo hlavní analytické cíle (Engagement, MII) a vypočítává se z nastavení serveru, aktivity moderátorského týmu a míry odpovědí na dotazy.

## Výpočet skóre

Skóre je vážený průměr 5 faktorů v rozsahu 0–100:

$$S = w_1 \cdot F_{\text{MFA}} + w_2 \cdot F_{\text{verif}} + w_3 \cdot F_{\text{filter}} + w_4 \cdot F_{\text{mod}} + w_5 \cdot F_{\text{reply}}$$

| Faktor | Váha (výchozí) | Zdroj dat | Výpočet |
| :--- | :--- | :--- | :--- |
| $F_{\text{MFA}}$ (MFA Requirement) | 20 % | `guild.mfa_level` | 100 pokud vyžaduje MFA, jinak 0 |
| $F_{\text{verif}}$ (Verification Level) | 15 % | `guild.verification_level` | 0 / 25 / 50 / 75 / 100 podle úrovně |
| $F_{\text{filter}}$ (Content Filter) | 15 % | `guild.explicit_content_filter` | 0 / 50 / 100 podle nastavení |
| $F_{\text{mod}}$ (Moderator Activity) | 20 % | Audit log | Intenzita moderačních zásahů |
| $F_{\text{reply}}$ (Reply Ratio) | 30 % | Help Requests | Podíl zodpovězených dotazů v určených kanálech |

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

Skóre se zobrazuje na hlavní stránce dashboardu v karté **Security Score**. Karta obsahuje:
- Aktuální skóre a kategorii.
- Rozpad na jednotlivé faktory s doporučeními.
- Historický vývoj skóre za posledních 30 dní.

::: info Ochrana soukromí
Výpočet skóre využívá pouze metadata nastavení serveru a audit log. Obsah zpráv uživatelů se neanalyzuje.
:::
