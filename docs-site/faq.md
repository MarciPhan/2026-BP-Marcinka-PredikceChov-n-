# Často kladené dotazy (FAQ)

Zde najdete odpovědi na nejčastější dotazy týkající se instalace, fungování a bezpečnosti systému Metricord.

## Instalace a nastavení

::: details Jak rychle zprovozním Metricord na svém serveru?
1. Naklonujte repozitář a vytvořte `.env` z šablony (viz [Rychlý start](/quickstart)).
2. Vyplňte `BOT_TOKEN` z Discord Developer Portalu.
3. Spusťte `./start.sh` pro lokální vývoj nebo `docker-compose up -d` pro produkci.
4. Na Discordu zadejte `*sync` pro registraci příkazů.
:::

::: details Proč se bot po pozvání nenachází v online stavu?
Zkontrolujte, zda jste správně nastavili proměnnou `BOT_TOKEN` v souboru `.env` a spustili proces pomocí `docker-compose up -d`. Pokud se bot přesto nepřipojí, ověřte logy příkazem `docker logs discord-bot-primary`.
:::

::: details Musím zapínat všechna Privileged Intents?
Ano. Metricord ke správnému fungování analytiky potřebuje **Message Content Intent** (pro výpočet délky zpráv) a **Server Members Intent** (pro sledování příchodů a odchodů). Bez nich bude většina metrik vykazovat nulové hodnoty.
:::

::: details Jaký je rozdíl mezi lokálním spuštěním a Docker Compose?
- **Lokální spuštění (`start.sh`):** Ideální pro vývoj. Spouští bot, dashboard i docs v jednom terminálu. Vyžaduje nainstalovaný Python, Node.js a Redis.
- **Docker Compose:** Ideální pro produkci. Automaticky vytvoří a propojí kontejnery. Nevyžaduje instalaci závislostí na hostiteli.
:::

## Fungování a metriky

::: details Jak bot počítá čas strávený ve voice kanálu?
Bot zaznamenává moment připojení (`JoinEvent`) a odpojení (`LeaveEvent`). Celkový čas je rozdílem těchto dvou hodnot. Pokud uživatel zůstane ve voice kanálu i po vypnutí bota, relace je uzavřena při příštím startu bota s časovou značkou posledního známého heartbeatu.
:::

::: details Ukládá bot text mých zpráv?
**Ne.** Metricord byl navržen pro maximální soukromí. Zpracováváme pouze metadata: čas odeslání, délku zprávy v počtu znaků a ID kanálu. Samotný obsah zpráv se nikam neukládá ani nepřenáší.
:::

::: details Proč se mi v dashboardu nezobrazuje Engagement Score?
Výpočet Engagement Score vyžaduje minimálně **7 dní historie dat** (případně spuštění Backfillu). Pokud je váš server nový, počkejte, až systém nasbírá dostatečný objem údajů pro validní analýzu.
:::

::: details Co je DQS a proč jsou predikce deaktivovány?
DQS (Data Quality Score) měří kvalitu dat pro prediktivní modely. Pokud je DQS < 0,5, systém nemá dostatek dat pro spolehlivé predikce a automaticky je deaktivuje. Spusťte [backfill](/backfill) nebo počkejte alespoň 7 dní.
:::

## Soukromí a GDPR

::: details Kam se ukládají data po smazání profilu?
Nikam. Příkaz `/gdpr delete` provede okamžitou operaci `DEL` nad všemi klíči v Redisu, které jsou spojené s vaším uživatelským ID. Tato operace je nevratná a data nelze obnovit ani ze zálohy, pokud byla mezitím přepsána.
:::

::: details Můžu data exportovat do jiného systému?
Ano. Příkaz `/gdpr export` vám vygeneruje JSON soubor, který obsahuje kompletní strukturu vašich dat. Tento soubor je kompatibilní se standardními nástroji pro analýzu dat (např. v jazyce Python nebo R). Pro CSV export využijte [Centrum exportu](/export) v dashboardu.
:::

::: details Jak dlouho se data uchovávají?
Surové eventy (zprávy, voice) se uchovávají **30 dní**, HyperLogLog statistiky **90 dní** a uživatelské profily **7 dní**. Po uplynutí TTL Redis klíče automaticky smaže. Podrobnosti viz [Privacy Builder](/privacy-builder).
:::

## Technické otázky

::: details Proč používáte Redis a ne SQL?
Pro real-time analytiku v řádech milionů eventů je Redis (in-memory) mnohem rychlejší. SQL by způsobovalo znatelnou latenci při výpočtech on-the-fly. Redis navíc nabízí specializované datové struktury (HyperLogLog, Sorted Sets), které jsou pro analytiku ideální.
:::

::: details Mohu exportovat data do Excelu?
Ano, v sekci „Centrum exportu" na dashboardu si můžete stáhnout data ve formátu CSV (přímý import do Excelu) nebo JSON pro strojové zpracování. Viz [Export dat](/export).
:::

::: details Jak funguje Dual-bot režim (Lite Mode)?
Metricord podporuje provoz dvou instancí bota současně. Primary instance má plnou funkčnost (příkazy, tracking, backfill). Secondary instance (`BOT_LITE_MODE=1`) pouze sbírá data bez registrace slash příkazů. Obě instance zapisují do stejné Redis databáze. Viz [Správa instance](/admin-guide#dual-bot-rezim-lite-mode).
:::

---

> [!TIP]
> Nenašli jste odpověď na svůj dotaz? Podívejte se do [Troubleshootingu](/troubleshooting) nebo nás kontaktujte na [Support Serveru](https://discord.gg/35yeT32Knf).
