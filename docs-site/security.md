# Skóre bezpečnosti (Security Score)

Metricord není jen o analytice aktivity, ale také o zabezpečení vaší komunity. Skóre bezpečnosti ($S$) je unikátní metrika, která vyjadřuje odolnost vašeho serveru proti útokům a spamu.

## Výpočet skóre

Skóre bezpečnosti je vypočítáno na základě několika kritických faktorů:

| Faktor | Váha | Popis |
| :--- | :--- | :--- |
| **MFA Requirement** | 30% | Vyžaduje server od moderátorů dvoufázové ověření? |
| **Verification Level** | 20% | Nastavení úrovně ověření nového člena (E-mail, telefon). |
| **Explicit Content Filter** | 20% | Automatické skenování a mazání nevhodných médií. |
| **Moderator Activity** | 30% | Reakční doba moderátorů na incidenty a jejich přítomnost. |

## Úrovně zabezpečení

Na základě skóre (0-100) je serveru přiřazena jedna z kategorií:

- **🟢 90-100 (Fortress):** Maximální zabezpečení. Všechny filtry zapnuty, aktivní moderace.
- **🟡 60-89 (Stable):** Dobré zabezpečení, doporučujeme zapnout MFA pro moderátory.
- **🟠 30-59 (Exposed):** Rizikový stav. Chybí filtry obsahu nebo je ověření příliš nízké.
- **🔴 0-29 (Vulnerable):** Kritický stav. Server je náchylný k raidům a spamu.

## Doporučení pro zlepšení

V dashboardu najdete sekci **Security Insights**, která vám v reálném čase navrhuje kroky ke zvýšení skóre:
1. Zapněte "Medium" nebo "High" verifikaci v nastavení Discordu.
2. Aktivujte filtr explicitního obsahu pro všechny členy.
3. Nastavte pravidlo pro automatické vyhazování účtů mladších než 24 hodin (Bot Protection).

::: info Soukromí
Metricord skenuje pouze metadata nastavení serveru. Žádné soukromé zprávy uživatelů nejsou pro potřeby skóre bezpečnosti analyzovány.
:::
