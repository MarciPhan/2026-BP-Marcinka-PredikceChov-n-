# Glosář pojmů

Kompletní přehled termínů a zkratek, se kterými se v dokumentaci Metricord setkáte.

### A
- **Aktivní uživatel (Active User):** Uživatel, který v daném období (24h nebo 30d) provedl alespoň jednu aktivní akci (zpráva, voice).
- **Anti-Spam XP:** Mechanismus omezující zisk bodů na jednou za 60 sekund (Cooldown).
- **AOF (Append-Only File):** Režim persistence Redisu, který loguje každou operaci zápisu. Minimalizuje ztrátu dat při výpadku.
- **At-Risk Users:** Uživatelé v pasivním nebo inaktivním stavu, u kterých hrozí brzký odchod (Churn).

### B
- **Backfill:** Zpětné načtení historie zpráv ze serveru do Redisu pro okamžité vyplnění analytických dat.

### C
- **Cenzorovaná data (Censored Data):** Informace o uživatelích, kteří jsou stále na serveru. Jsou klíčová pro přesný odhad retence (Kaplan-Meier).
- **Churn (Odchod):** Stav, kdy uživatel opustil server nebo je inaktivní déle než 14–30 dní.
- **Confidence Score (Skóre spolehlivosti):** Číslo od 0 do 1 vyjadřující, jak moc lze věřit předpovědi modelu na základě objemu dat.
- **Cooldown:** Časový limit (typicky 60 s), během kterého uživatel po napsání zprávy nezískává další XP, aby se zabránilo spamu.

### D
- **DAU (Daily Active Users):** Počet unikátních uživatelů, kteří byli aktivní během jednoho kalendářního dne.
- **DQS (Data Quality Score):** Metrika kvality dat určující spolehlivost predikcí. Nízké DQS (< 0,5) značí nedostatek historie.

### E
- **Engagement Score:** Metrika vyjadřující míru zapojení komunity, vypočítaná z poměru aktivity a velikosti serveru.
- **Extraction:** Fáze ML pipeline, kdy se surová data vytahují z databáze Redis pro další zpracování.

### H
- **HyperLogLog (HLL):** Efektivní datová struktura v Redisu používaná pro odhad počtu unikátních prvků (DAU) s minimální paměťovou náročností (12 KB).

### K
- **Kaplan-Meierův estimátor:** Statistická metoda používaná v Metricordu pro výpočet pravděpodobnosti setrvání uživatelů na serveru v čase.

### M
- **Markovův řetězec (Markov Chain):** Matematický model, který Metricord používá k předpovědi budoucího stavu uživatele na základě jeho současné aktivity.
- **Matice přechodu (Transition Matrix):** Tabulka pravděpodobností popisující šance, že uživatel přejde z jednoho stavu (např. Active) do jiného (např. Passive).
- **MAU (Monthly Active Users):** Počet unikátních uživatelů aktivních za posledních 30 dní.
- **MII (Moderator Intervention Index):** Poměr moderátorských zásahů k celkovému objemu zpráv. Indikátor toxicity nebo konfliktů na serveru.

### P
- **Pipeline:** Sekvence kroků (Extraction -> Preprocessing -> Classification -> Computation), kterými procházejí data při výpočtu predikcí.
- **Preprocessing (Vektorizace):** Převod surových timestampů na číselné matice připravené pro matematické modely NumPy.

### S
- **Sezónní korekce (Seasonality):** Úprava predikcí s ohledem na týdenní cykly (např. vyšší aktivita o víkendech).
- **Sharding:** Rozdělení zátěže bota mezi více procesů pro obsluhu velkého množství serverů.
- **Smart Insights:** Automaticky generovaná doporučení pro moderátory založená na detekovaných trendech v datech.
- **Sorted Set (ZSET):** Datová struktura v Redisu, kde jsou prvky řazeny podle skóre (v Metricordu UNIX timestamp).
- **Střední délka setrvání (Mean Survival Time):** Průměrná doba, po kterou uživatel zůstává aktivním členem komunity.

### T
- **TTL (Time To Live):** Doba platnosti záznamu v Redisu. Po jejím uplynutí je klíč automaty smazán.

### X
- **XP (Experience Points):** Zkušenostní body přidělované za aktivitu. Základ leveling systému.

