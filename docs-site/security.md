# Skóre bezpečnosti serveru

Skóre bezpečnosti ($S$) vyjadřuje odolnost Discord serveru proti spamu a útokům. Metrika se vypočítává z nastavení serveru a aktivity moderátorského týmu.

## Výpočet skóre

Skóre je vážený průměr 4 faktorů v rozsahu 0–100:

$$S = 0{,}3 \cdot F_{\text{MFA}} + 0{,}2 \cdot F_{\text{verif}} + 0{,}2 \cdot F_{\text{filter}} + 0{,}3 \cdot F_{\text{mod}}$$

| Faktor | Váha | Zdroj dat | Výpočet |
| :--- | :--- | :--- | :--- |
| $F_{\text{MFA}}$ (MFA Requirement) | 30 % | `guild.mfa_level` | 100 pokud vyžaduje MFA, jinak 0 |
| $F_{\text{verif}}$ (Verification Level) | 20 % | `guild.verification_level` | 0 / 25 / 50 / 75 / 100 podle úrovně |
| $F_{\text{filter}}$ (Content Filter) | 20 % | `guild.explicit_content_filter` | 0 / 50 / 100 podle nastavení |
| $F_{\text{mod}}$ (Moderator Activity) | 30 % | Audit log + přítomnost online | Průměrná reakční doba moderátorů |

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
