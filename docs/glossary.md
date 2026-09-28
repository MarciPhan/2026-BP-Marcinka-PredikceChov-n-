# Glosář pojmů

Kompletní přehled termínů a zkratek, se kterými se v dokumentaci CommunityMetrics setkáte.

### A
- **Aktivní uživatel (Active User):** Uživatel, který v daném období (24h nebo 30d) provedl alespoň jednu aktivní akci (zpráva, voice).
- **Anti-Spam XP:** Mechanismus omezující zisk bodů na jednou za 60 sekund (Cooldown).
- **AOF (Append-Only File):** Režim persistence Redisu, který loguje každou operaci zápisu. Minimalizuje ztrátu dat při výpadku.
- **At-Risk Users:** Uživatelé v pasivním nebo inaktivním stavu, u kterých hrozí dlouhodobá neaktivita.

### B
- **Backfill:** Zpětné načtení historie zpráv ze serveru do Redisu pro okamžité vyplnění analytických dat.

### C
- **Cenzorovaná data (Censored Data):** Informace o uživatelích, kteří jsou stále na serveru. Jsou klíčová pro přesný odhad retence (Kaplan-Meier).
- **Neaktivita:** Stav, kdy uživatel přestal vykazovat aktivitu déle než nakonfigurovaný práh (`ACTIVITY_INACTIVITY_THRESHOLD_DAYS`, výchozí 14 dní).
- **Cooldown:** Časový limit (typicky 60 s), během kterého uživatel po napsání zprávy nezískává další XP, aby se zabránilo spamu.

### D
- **DAU (Daily Active Users):** Počet unikátních uživatelů, kteří byli aktivní během jednoho kalendářního dne.
- **DQS (Data Quality Score):** Bodová metrika 0–100 (výchozí 100, odečítá se za jednotlivé nedostatky) indikující úplnost vstupních dat — kratší historii, málo zpráv, chybějící moderační nebo voice události. Samotná dostupnost Markovovy/Kaplan-Meierovy predikce se řídí samostatnými prahy (viz [Predikce](/predictions#omezení-modelů)), ne přímo touto hodnotou.

### E
- **Engagement Score:** Metrika vyjadřující míru zapojení komunity, vypočítaná z poměru aktivity a velikosti serveru.
- **Extraction:** Fáze ML pipeline, kdy se surová data vytahují z databáze Redis pro další zpracování.

### H
- **HyperLogLog (HLL):** Efektivní datová struktura v Redisu používaná pro odhad počtu unikátních prvků (DAU) s minimální paměťovou náročností (12 KB).

### K
- **Kaplan-Meierův estimátor:** Statistická metoda používaná v CommunityMetricsu pro výpočet pravděpodobnosti setrvání uživatelů na serveru v čase.

### M
- **Markovův řetězec (Markov Chain):** Matematický model, který CommunityMetrics používá k předpovědi budoucího stavu uživatele na základě jeho současné aktivity.
- **Matice přechodu (Transition Matrix):** Tabulka pravděpodobností popisující šance, že uživatel přejde z jednoho stavu (např. Active) do jiného (např. Passive).
- **MAU (Monthly Active Users):** Počet unikátních uživatelů aktivních za posledních 30 dní.
- **MII (Moderator Intervention Index):** Poměr moderátorských zásahů k celkovému objemu zpráv. Indikátor moderační zátěže na serveru.

### P
- **Pipeline:** Sekvence kroků (Extraction -> Preprocessing -> Classification -> Computation), kterými procházejí data při výpočtu predikcí.
- **Preprocessing (Vektorizace):** Převod surových timestampů na číselné matice připravené pro matematické modely NumPy.

### S
- **Sezónní korekce (Seasonality):** Úprava predikcí s ohledem na týdenní cykly (např. vyšší aktivita o víkendech).
- **Sharding:** Rozdělení zátěže bota mezi více procesů pro obsluhu velkého množství serverů.
- **Smart Insights:** Automaticky generovaná doporučení pro moderátory založená na detekovaných trendech v datech.
- **Sorted Set (ZSET):** Datová struktura v Redisu, kde jsou prvky řazeny podle skóre (v CommunityMetricsu UNIX timestamp).
- **Střední délka setrvání (Mean Survival Time):** Průměrná doba, po kterou uživatel zůstává aktivním členem komunity.

### T
- **TTL (Time To Live):** Doba platnosti záznamu v Redisu. Po jejím uplynutí je klíč automaticky smazán. Ne všechny klíče v CommunityMetrics TTL mají — např. `hll:dau:*` nebo `user:info:*` přetrvávají bez expirace (viz [Architektura](/architecture#retence-dat)).

### X
- **XP (Experience Points):** Zkušenostní body přidělované za aktivitu. Základ leveling systému.

