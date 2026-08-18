#  CommunityMetrics: Komplexní příručka pro moderátory

Vítejte u podrobné dokumentace systému **CommunityMetrics**. Tento dokument slouží jako hlavní zdroj informací pro moderátory a správce komunit, kteří chtějí naplno využít potenciál analytických a prediktivních nástrojů pro rozvoj svého serveru.

---

##  Obsah
1. [Úvod a filozofie systému](#1-úvod-a-filozofie-systému)
2. [Interpretace metrik v dashboardu](#2-interpretace-metrik-v-dashboardu)
3. [Prediktivní modely a včasné varování](#3-prediktivní-modely-a-včasné-varování)
4. [Toxicity Index (MII) a správa týmu](#4-toxicity-index-mii-a-správa-týmu)
5. [Bot příkazy pro moderátory](#5-bot-příkazy-pro-moderátory)
6. [Gamifikace a XP systém](#6-gamifikace-a-xp-systém)
7. [GDPR a ochrana soukromí](#7-gdpr-a-ochrana-soukromí)
8. [Best Practices pro růst komunity](#8-best-practices-pro-růst-komunity)
9. [Glosář pojmů a Architektura](#9-glosář-pojmů-a-architektura)

---

## 1. Úvod a filozofie systému
CommunityMetrics není jen "další bot na statistiky". Je to analytický ekosystém, který se snaží pomocí agregace aktivity a jednoduchých heuristik pochopit **životní cyklus uživatele**.

**Cíl moderátora:** Udržet uživatele co nejdéle v aktivních stavech a minimalizovat "Churn" (odchod ze serveru).

---

## 2. Interpretace metrik v dashboardu

###  Engagement Score (0–100)
Kompozitní index zdraví serveru. Pokud klesne pod **40**, komunita stagnuje. Pokud je nad **80**, server organicky roste.
- **Složení:** 25% Moderace, 25% Bezpečnost, 25% Zapojení (Engagement), 25% Aktivita týmu.

###  Stickiness (Lepivost)
Vzorec: `(DAU / MAU) * 100`. 
- **Interpretace:** Kolik % vašich měsíčních uživatelů se vrací každý den. 
- **Cíl:** Nad 20% pro velmi aktivní komunity.

###  Churn Rate (Míra odchodu)
Klíčový indikátor problému. Pokud Churn Rate náhle vzroste, zkontrolujte:
1. Poslední konflikty v chatu.
2. Změny v pravidlech nebo struktuře serveru.
3. Aktivitu moderátorů (přílišná přísnost vs. anarchie).

---

## 3. Prediktivní modely a včasné varování

### 📊 Prediktivní analýza (Retence a růst)
Systém analyzuje historická data (vstupy a výstupy uživatelů) a extrapoluje trend vývoje členů a denní aktivity na nadcházejících 30 dní.
- **Predikce:** Dashboard ukazuje odhadovaný počet členů a zpráv s ohledem na týdenní sezónnost (např. víkendové výkyvy).
- **Akce:** Targetujte uživatele speciálními eventy, pokud predikce ukazuje pokles aktivity, abyste je "reaktivovali".

---

## 4. Toxicity Index (MII) a správa týmu

**MII (Moderator Intervention Index)** měří toxicitu jako poměr moderátorských zásahů k objemu zpráv.
- **Nízký MII + Nízký Engagement:** Komunita je mrtvá.
- **Vysoký MII + Vysoký Engagement:** Komunita je živá, ale konfliktní (typické pro politické nebo herní servery).

**Doporučení pro tým:**
CommunityMetrics automaticky vypočítává `N_mod` – ideální počet moderátorů pro aktuální zátěž. Pokud systém hlásí "Nedostatek moderátorů", hrozí vyhoření týmu nebo nárůst neřešené toxicity.

---

## 5. Bot příkazy pro moderátory

### `/activity stats [user] [after] [before]`
Zobrazí detailní rozbor aktivity konkrétního uživatele. 
- **Využití:** Kontrola kandidátů na moderátory nebo prověření problémových uživatelů.

### `/activity leaderboard`
Žebříček nejaktivnějších členů podle **váženého času**. 
- *Poznámka:* Vážený čas zohledňuje délku zpráv, hlasovou aktivitu a moderátorské zásahy.

### `/activity report` (Admin)
Generuje týdenní/měsíční přehled aktivity celého moderátorského týmu. 
- **Cíl:** Spravedlivé hodnocení práce moderátorů (kdo reálně tráví čas ve voice, kdo maže zprávy atd.).

### `/activity sync_names` (Admin)
Vynutí aktualizaci přezdívek a rolí v databázi dashboardu. Spusťte po velkých změnách v rolích.

---

## 6. Gamifikace a XP systém
CommunityMetrics používá **Anti-Spam XP systém**. Body se získávají maximálně jednou za minutu.
- **Logika:** Delší zprávy a zapojení do diskuzí (odpovědi) dávají bonusové body.
- **Leveling:** Křivka je kvadratická. Dosažení vyšších úrovní vyžaduje exponenciálně více úsilí, což podporuje dlouhodobou věrnost.

---

## 7. GDPR a ochrana soukromí
Jako moderátoři máte přístup k analytickým datům. Respektujte soukromí uživatelů:
- **Právo na smazání:** Pokud uživatel požádá o smazání dat, odkažte ho na příkaz `/gdpr delete`.
- **Transparentnost:** Příkaz `/gdpr export` stáhne uživateli vše, co o něm bot ví. Pro rychlý přehled slouží `/privacy`.

---

## 8. Best Practices pro růst komunity

1. **Sledujte Peak Times:** Podle Heatmapy v dashboardu plánujte eventy na hodiny s nejvyšší přirozenou aktivitou.
2. **Reagujte na Exodus:** Pokud predikce ukazuje nárůst odchodů, uspořádejte "Community Meeting".
3. **Odměňujte věrnost:** Používejte leaderboard pro identifikaci klíčových členů ("Evangelists") a dejte jim speciální role.
4. **Kalibrace toxicity:** Pokud je MII dlouhodobě vysoký, zvažte úpravu pravidel pro automatické filtry Discordu.

---

## 9. Glosář pojmů a Architektura
Pro hlubší pochopení technických termínů (HLL, SARIMA, DQS) nebo fungování systému na pozadí navštivte:
- [Glosář pojmů](/docs/glossary)
- [Technická architektura](/docs/architecture)
- [API Reference](/docs/api)
- [Nasazení a údržba](/docs/deployment)
- [Troubleshooting](/docs/troubleshooting)

---
*Dokumentace verze 2.3 (Stripe-style Edition, Březen 2026)*
