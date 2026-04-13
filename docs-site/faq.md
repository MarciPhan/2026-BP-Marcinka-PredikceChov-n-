# Časté dotazy (FAQ)

Zde najdete odpovědi na nejčastější dotazy rozdělené do kategorií.

## Instalace a Přihlášení

::: details Proč nevidím svůj server v seznamu po přihlášení?
Musíte splnit dvě podmínky:
1. Na serveru musíte mít oprávnění **"Manage Server"** nebo **"Administrator"**.
2. Bot musí být na serveru již přítomen. Pokud není, použijte tlačítko "Přidat bota".
:::

::: details Nepřišel mi kód pro E-mailové přihlášení (OTP).
Zkontrolujte složku **Spam** nebo **Promoakce**. Ujistěte se, že administrátor správně nastavil SMTP v souboru `.env`. Doporučujeme přihlášení přes Discord (OAuth2), které je stabilnější.
:::

## Data a Analytika

::: details Jak často se aktualizují grafy?
Základní metriky (DAU, Zprávy) se aktualizují v **reálném čase** (5-10s). Komplexní predikce (Markov, Survival) se přepočítávají **jednou za hodinu**.
:::

::: details Proč je Stickiness 0%, když jsou lidi online?
Stickiness se počítá na základě **aktivity** (psaní), nikoliv pouhé přítomnosti online. Uživatel musí něco napsat, aby byl započítán do DAU.
:::

## Moderace a Soukromí

::: details Vidí bot moje soukromé zprávy (DMs)?
**Ne.** Metricord analyzuje pouze data ze serverů, kam byl pozván. Vaše soukromé konverzace jsou zcela nedostupné.
:::

::: details Jak smažu všechna data svého serveru?
Pokud bota vyhodíte, data zůstanou v databázi dle TTL (90 dní). Pro okamžité smazání musí majitel serveru použít příkaz `/activity wipe_guild_confirm`.
:::

## Technické otázky

::: details Proč používáte Redis a ne SQL?
Pro real-time analytiku v řádech milionů eventů je Redis (in-memory) mnohem rychlejší. SQL by způsobovalo znatelnou latenci při výpočtech on-the-fly.
:::

::: details Mohu exportovat data do Excelu?
Ano, v sekci "Centrum exportu" si můžete stáhnout data ve formátu JSON, který lze snadno převést na CSV nebo otevřít v Excelu.
:::

::: info Nenašli jste odpověď?
Navštivte náš [Support Server](https://discord.gg/metricord) nebo nám napište na `podpora@metricord.app`.
:::
