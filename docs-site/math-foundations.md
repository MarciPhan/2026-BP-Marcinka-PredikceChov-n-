# Matematické základy Metricord

Tato sekce slouží jako teoretický podklad pro bakalářskou práci a zájemce o datovou vědu v oblasti komunitního managementu.

## 1. Markovovy řetězce prvního řádu

Pro predikci stavu uživatele využíváme diskrétní Markovovy řetězce (DTMC). Tento model předpokládá, že budoucí stav uživatele závisí pouze na jeho aktuálním stavu, nikoliv na celé historii.

### Stavový prostor S
Uživatele klasifikujeme do 5 diskrétních stavů na základě jejich aktivity v posledních 30 dnech:
- **$S_0$: New (Nový)** — Užitvatel se připojil v posledních 24 hodinách.
- **$S_1$: Active (Aktivní)** — Alespoň 3 zprávy nebo 10 min ve voice za posledních 48h.
- **$S_2$: Passive (Pasivní)** — Aktivita v posledním týdnu, ale ne v posledních 48h.
- **$S_3$: Inactive (Inaktivní)** — Bez aktivity více než 7 dní.
- **$S_4$: Churned (Odešel)** — Uživatel opustil server nebo je inaktivní > 30 dní.

### Matice přechodu a predikce
Matice přechodu $P$ je srdcem našeho prediktivního jádra. Každý prvek $p_{ij}$ představuje pravděpodobnost, že uživatel ve stavu $i$ přejde do stavu $j$ během jednoho dne.

Budoucí rozložení komunity po $n$ dnech vypočítáme jako $\mathbf{v}_{n} = \mathbf{v}_{0} \cdot P^n$, kde $\mathbf{v}_{0}$ je aktuální vektor rozložení členů.

## 2. Kaplan-Meierův odhad (Analýza přežití)

Survival Analysis nám umožňuje odpovědět na otázku: *"Jaká je pravděpodobnost, že nový člen zůstane na serveru i po 14 dnech?"*

Tento odhad je **ne-parametrický**, což znamená, že nevyžaduje předpoklad o konkrétním rozdělení pravděpodobnosti, což je ideální pro heterogenní Discord komunity.

## 3. Engagement Score (Index zapojení)

Engagement Score ($E$) je kompozitní metrika vypočítaná jako vážený průměr několika faktorů:
- DAU/MAU ratio
- Average Message Length
- Survival Rate

Váhy jsou dynamicky upravovány na základě velikosti serveru, aby skóre zůstalo relevantní jak pro malé servery, tak pro velké komunity.

## 4. Analýza časové složitosti (Big O)

Metricord je optimalizován pro real-time zpracování milionů událostí.

| Operace | Složitost | Datová struktura |
| :--- | :--- | :--- |
| Zápis zprávy | $O(1)$ | Redis HyperLogLog (PFADD) |
| Výpočet žebříčku | $O(\log N)$ | Redis Sorted Set (ZREVRANGE) |
| Predikce Churnu | $O(S^2)$ | Maticové násobení ($S$ = počet stavů) |

Díky $O(1)$ složitosti zápisu do HyperLogLogu můžeme sledovat neomezený počet unikátních uživatelů bez CPU overheadu.
