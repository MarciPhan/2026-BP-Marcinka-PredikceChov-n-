# Často kladené dotazy (FAQ)

Zde najdete odpovědi na nejčastější dotazy týkající se instalace, fungování a bezpečnosti systému CommunityMetrics.

## Instalace a nastavení

::: details Jak rychle zprovozním CommunityMetrics na svém serveru?
1. Naklonujte repozitář a vytvořte `.env` z šablony (viz [Rychlý start](/quickstart)).
2. Vyplňte `BOT_TOKEN` z Discord Developer Portalu.
3. Spusťte `./start.sh` pro lokální vývoj nebo `docker-compose up -d` pro produkci.
4. Na Discordu zadejte `*sync` pro registraci příkazů.
:::

::: details Proč se bot po pozvání nenachází v online stavu?
Zkontrolujte, zda jste správně nastavili proměnnou `BOT_TOKEN` v souboru `.env` a spustili proces pomocí `docker-compose up -d`. Pokud se bot přesto nepřipojí, ověřte logy příkazem `docker logs discord-bot-primary`.
:::

::: details Musím zapínat všechna Privileged Intents?
Ano. CommunityMetrics ke správnému fungování analytiky potřebuje **Message Content Intent** (pro výpočet délky zpráv) a **Server Members Intent** (pro sledování příchodů a odchodů). Bez nich bude většina metrik vykazovat nulové hodnoty.
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
**Ne.** CommunityMetrics byl navržen pro maximální soukromí. Zpracováváme pouze metadata: čas odeslání, délku zprávy v počtu znaků a ID kanálu. Samotný obsah zpráv se nikam neukládá ani nepřenáší.
:::

::: details Proč se mi v dashboardu nezobrazuje Engagement Score?
Výpočet Engagement Score vyžaduje minimálně **7 dní historie dat** (případně spuštění Backfillu). Pokud je váš server nový, počkejte, až systém nasbírá dostatečný objem údajů pro validní analýzu.
:::

::: details Co je DQS a proč jsou predikce deaktivovány?
DQS (Data Quality Score) indikuje úplnost dat pro prediktivní modely. Pokud je DQS < 0,5, systém nemá dostatek dat pro analytiku a automaticky ji deaktivuje. Spusťte [backfill](/backfill) nebo počkejte alespoň 7 dní.
:::

## Soukromí a GDPR

::: details Kam se ukládají data po smazání profilu?
Nikam. Příkaz `/gdpr delete` provede okamžitou operaci `DEL` nad hlavními klíči v Redisu spojenými s vaším uživatelským ID (zprávy, voice aktivita, moderační akce, community health data včetně ruční poznámky/hodnocení administrátora, statistiky a žebříčky). Tato operace je nevratná a data nelze obnovit ani ze zálohy, pokud byla mezitím přepsána. Odvozené agregované statistiky se po výmazu zpětně nepřepočítávají.
:::

::: details Můžu data exportovat do jiného systému?
Příkaz `/gdpr export` vám zobrazí ephemerní (jen vy ji vidíte) zprávu se souhrnnými počty vašich dat – nejde o soubor ke stažení. Pro skutečný export dat komunity ve formátu CSV nebo JSON slouží samostatné REST API endpointy `/api/export/{typ}` (viz [Export dat](/export)); v aktuální verzi na ně z dashboardu zatím nevede žádné tlačítko, takže je nutné sestavit URL ručně nebo je volat přes vlastní API klienta.
:::

::: details Jak dlouho se data uchovávají?
Surové eventy (zprávy, voice) se uchovávají dle konfigurovatelné retence (výchozí **90 dní**, parametr `EVENT_RETENTION_DAYS`). HyperLogLog statistiky **90 dní** a uživatelské profily **7 dní**. Po uplynutí TTL Redis klíče automaticky smaže. Ruční poznámka administrátora v Community Health má také TTL nastavené na `EVENT_RETENTION_DAYS`; některé pomocné community health indexy (např. propojení opakovaných konfliktů mezi členem a moderátorem nebo záznamy odchodu) v aktuální verzi žádné TTL nemají a je nutné je odstranit ručně přes `/gdpr delete`. Podrobnosti viz [Privacy Builder](/privacy-builder).
:::

## Technické otázky

::: details Proč používáte Redis a ne SQL?
Pro real-time analytiku v řádech milionů eventů je Redis (in-memory) mnohem rychlejší. SQL by způsobovalo znatelnou latenci při výpočtech on-the-fly. Redis navíc nabízí specializované datové struktury (HyperLogLog, Sorted Sets), které jsou pro analytiku ideální.
:::

::: details Mohu exportovat data do Excelu?
Ano, formát CSV (přímý import do Excelu) i JSON jsou podporované na backendu přes `/api/export/{typ}`. V aktuální verzi ale dashboard nemá samostatnou sekci „Centrum exportu" s tlačítkem – URL je nutné zavolat přímo (v prohlížeči s aktivní session, nebo přes API klienta). Viz [Export dat](/export).
:::

::: details Jak funguje Dual-bot režim (Lite Mode)?
CommunityMetrics podporuje provoz dvou instancí bota současně. Primary instance má plnou funkčnost (příkazy, tracking, backfill). Secondary instance (`BOT_LITE_MODE=1`) pouze sbírá data bez registrace slash příkazů. Obě instance zapisují do stejné Redis databáze. Viz [Správa instance](/admin-guide#dual-bot-rezim-lite-mode).
:::

---

> [!TIP]
> Nenašli jste odpověď na svůj dotaz? Podívejte se do [Troubleshootingu](/troubleshooting) nebo nás kontaktujte na [Support Serveru](https://discord.gg/35yeT32Knf).
