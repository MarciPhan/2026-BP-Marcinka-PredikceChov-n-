# Privacy Policy Generator

Pomůžeme vám sestavit zásady ochrany osobních údajů pro váš server na základě toho, jak Metricord využíváte.

## Šablona zásad ochrany údajů

Níže je doporučený text, který můžete vložit do svého kanálu `#pravidla` nebo `#privacy`.

### 1. Rozsah sběru dat
Sledujeme pouze metadata vaší aktivity pro účely XP systému a analytiky:
- **Zprávy:** Délka, čas odeslání, kanál. (Obsah zpráv se neukládá!)
- **Voice (pokud aktivní):** Doba strávená v hlasových kanálech.
- **Presence:** Online/Offline status (pro výpočet DAU).

### 2. Účel zpracování
Data využíváme výhradně pro:
- Výpočet úrovní (XP) a přidělování rolí.
- Vizualizaci špiček aktivity v dashboardu.
- Predikci zdraví komunity a retence členů.

### 3. Retence (Uchovávání dat)
Standardně uchováváme anonymizovaná data po dobu **90 dní**. Surová data starší 1 roku jsou automaticky mazána z Redis databáze.

### 4. Vaše práva (GDPR)
Každý uživatel má právo na:
- **Export dat:** Pomocí příkazu `/gdpr export` získáte JSON se všemi svými daty.
- **Smazání:** Příkaz `/gdpr delete` okamžitě a nevratně smaže všechna vaše data.

::: info Právní disclaimer
Tento text je doporučená šablona. Majitel serveru nese plnou odpovědnost za soulad se zákony v dané jurisdikci.
:::
