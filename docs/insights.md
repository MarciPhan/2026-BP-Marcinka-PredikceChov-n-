# Smart Insights

Karta **💡 Insights** na dashboardu zobrazuje krátký seznam textových postřehů, které se generují z právě spočítaných metrik komunity (`get_insights()` v analytické vrstvě). Jde o jednoduchá pravidla nad agregovanými čísly, ne o samostatný detekční nebo bezpečnostní systém — pro hodnocení zabezpečení serveru (MFA, verifikace, filtr obsahu) slouží samostatná karta popsaná na stránce [Skóre bezpečnosti](/security).

## Co karta skutečně ukazuje

Každý postřeh má typ `positive` / `negative` / `neutral`, který určuje barvu ikony, a krátký text:

| Postřeh | Podmínka | Ukázkový text |
| :--- | :--- | :--- |
| Týdenní růst aktivity | Aktivita tento týden roste oproti minulému | 🚀 Silný týdenní růst! Počet aktivních uživatelů stoupá. |
| Týdenní pokles aktivity | Aktivita tento týden klesá | 📉 Pozor, týdenní aktivita klesá. Zkuste uspořádat event. |
| Vysoký podíl aktivních členů | Vysoký poměr DAU k celkovému počtu členů | 💎 Vysoký podíl aktivních členů v aktuálním období. |
| Nízký podíl aktivních členů | Nízký poměr DAU k celkovému počtu členů | ⚠️ Nízký podíl aktivních členů v aktuálním období. |
| Aktivní voice kanály | Vysoký podíl voice aktivity | 🗣️ Komunita je velmi upovídaná v hlasových kanálech! |
| Málo voice aktivity | Nízký podíl voice aktivity vůči textu | 💬 Lidé píší, ale málo mluví. Zkuste vytvořit „Chill" voice room. |
| Nejpoužívanější příkaz | Existuje dominantní příkaz v statistikách použití | 🤖 Nejoblíbenější příkaz je „/{příkaz}" ({N}×). |
| Dobrý poměr příchodů/odchodů | Přichází výrazně víc lidí, než kolik odchází | 📈 Skvělý nábor! Přichází 2× více lidí než odchází. |
| Jednoduchá trendová extrapolace | Dostatek historie pro odhad | 🔮 Jednoduchá extrapolace současného trendu odpovídá přibližně {N} denním aktivním uživatelům. Nejde o validovaný prediktivní model. |
| Nedostatek dat | Žádné z výše uvedených pravidel se nespustilo | Zatím nemám dost dat pro generování specifických postřehů. |

Text posledního postřehu v tabulce je záměrně formulovaný jako upozornění — jde o extrapolaci současného trendu, ne o výstup ověřeného prediktivního modelu (viz [Predikce](/predictions), kde je stejná opatrnost popsána podrobněji).

## Doručování

Insighty se aktuálně zobrazují pouze v dashboardu (karta „💡 Insights" na hlavní stránce serveru). Nejsou automaticky odesílány do Discord kanálu ani samostatně logovány — pokud potřebujete historii upozornění, sledujte standardní logy backendu.

## Předpoklady pro smysluplné výstupy

Insighty vycházejí z týdenních a měsíčních agregací, takže pro smysluplné hodnocení je potřeba alespoň několik dní historie aktivity. Pokud bot běží krátce, zobrazí se hláška o nedostatku dat. Pro rychlejší nasbírání historie použijte [backfill historických dat](/backfill).
