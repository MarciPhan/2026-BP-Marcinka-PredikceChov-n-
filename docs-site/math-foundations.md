# Matematické základy Metricord

Tato sekce slouží jako teoretický podklad pro bakalářskou práci a zájemce o datovou vědu v oblasti komunitního managementu.

## 1. Markovovy řetězce prvního řádu

Pro predikci stavu uživatele využíváme diskrétní Markovovy řetězce (DTMC). Tento model předpokládá, že budoucí stav uživatele závisí pouze na jeho aktuálním stavu, nikoliv na celé historii.

### Stavový prostor S
Každý uživatel $u \in \mathcal{U}$ je v čase $t$ klasifikován do jednoho z 5 diskrétních stavů na základě jeho pozorované aktivity v předchozím okně 30 dnů:
- **$S_0$: New (Nový)** - Uživatel se k serveru připojil v posledních 24 hodinách.
- **$S_1$: Active (Aktivní)** - Uživatel je silně zapojen (alespoň 3 zprávy nebo 10 min ve voice kanálu za posledních 48h).
- **$S_2$: Passive (Pasivní)** - Uživatel projevil aktivitu v posledním týdnu, ale nikoliv v posledních 48h.
- **$S_3$: Inactive (Inaktivní)** - Uživatel nevykázal žádnou aktivitu po dobu delší než 7 dnů.
- **$S_4$: Churned (Odešel)** - Absorpční stav. Uživatel buď server opustil, nebo je inaktivní déle než 30 dnů.

### Matice přechodu a predikce

Matice přechodu $P$ je čtvercová matice řádu 5, kde každý prvek $p_{ij} \in [0, 1]$ představuje pravděpodobnost přechodu ze stavu $i$ do stavu $j$ během jednoho časového kroku (24 hodin). Součet každého řádku matice musí být roven 1: $\sum_{j=1}^{n} p_{ij} = 1$.

$$
P = \begin{pmatrix}
p_{00} & p_{01} & p_{02} & p_{03} & p_{04} \\
p_{10} & p_{11} & p_{12} & p_{13} & p_{14} \\
p_{20} & p_{21} & p_{22} & p_{23} & p_{24} \\
p_{30} & p_{31} & p_{32} & p_{33} & p_{34} \\
p_{40} & p_{41} & p_{42} & p_{43} & p_{44}
\end{pmatrix}
$$

Budoucí rozložení komunity po $n$ dnech vypočítáme jako mocninu matice přechodu:
$$\mathbf{v}_{n} = \mathbf{v}_{0} \cdot P^n$$
Kde $\mathbf{v}_{0}$ je řádkový vektor aktuálního počtu členů v jednotlivých stavech.

## 2. Kaplan-Meierův odhad (Analýza přežití)

Survival Analysis nám umožňuje odhadnout pravděpodobnost setrvání uživatele na serveru v čase $t$. Kaplan-Meierův odhad funkce přežití $S(t)$ je neparametrický odhad definovaný jako:

$$
\hat{S}(t) = \prod_{i: t_i \le t} \left( 1 - \frac{d_i}{n_i} \right)
$$

Kde:
- $t_i$ - časový okamžik, kdy došlo k alespoň jedné události (odchod uživatele).
- $d_i$ - počet událostí (odchodů), ke kterým došlo v čase $t_i$.
- $n_i$ - počet uživatelů "v riziku" (at risk) těsně před časem $t_i$. Sem patří všichni uživatelé, kteří do času $t_i$ neodešli, ani u nich nedošlo k cenzorování dat.

### Cenzorování dat (Censoring)
Většina uživatelů v databázi stále na serveru je. Jejich data jsou tzv. **zprava cenzorovaná** (Right Censored) - víme, že "přežili" do dnešního dne, ale nevíme, kdy v budoucnu odejdou. Kaplan-Meierův model s těmito daty korektně pracuje započítáním těchto uživatelů do jmenovatele $n_i$ až do okamžiku cenzorování.

## 3. Pravděpodobnostní počítání (HyperLogLog)

Pro sledování DAU/MAU u extrémně velkých komunit využívá Metricord algoritmus **HyperLogLog (HLL)**. Ten umožňuje odhadnout kardinalitu (počet unikátních prvků) s chybou cca 0.81 % při použití pouze 12 KB paměti.

Základem je sledování počtu počátečních nul v hashované hodnotě identifikátoru uživatele. Odhad $E$ je dán harmonickým průměrem:

$$
E = \alpha_m m^2 \left( \sum_{j=1}^{m} 2^{-M_j} \right)^{-1}
$$

Kde $m$ je počet registrů a $M_j$ je maximální počet nul pozorovaný v registru $j$.

## 4. Engagement Score (Index zapojení)

Engagement Score ($ES$) je kompozitní metrika v rozsahu $0 \dots 100$, kterou vypočítáte jako vážený průměr čtyř dílčích indexů:

$$
ES = w_1 \cdot M + w_2 \cdot S + w_3 \cdot E + w_4 \cdot T
$$

Kde váhy $w_i$ jsou normalizovány tak, aby $\sum w_i = 1$. Výchozí nastavení Metricord využívá rovnoměrné rozložení (0.25 pro každou složku):

1.  **$M$ (Moderation Index):** Inverzní hodnota počtu banů a kicků vůči celkové aktivitě. Vyšší hodnota značí klidnější komunitu.
2.  **$S$ (Security Score):** Hodnocení nastavení serveru (MFA, verifikace, filtry obsahu).
3.  **$E$ (Engagement):** Poměr DAU/MAU a průměrná délka zpráv.
4.  **$T$ (Team Activity):** Aktivita moderátorského týmu vs. počet ohlášených incidentů.

Tento index slouží k rychlé identifikaci "zdraví" komunity bez nutnosti studovat jednotlivé grafy.

## 5. Analýza časové složitosti (Big O)

Metricord je optimalizován pro real-time zpracování milionů událostí.

| Operace | Složitost | Datová struktura |
| :--- | :--- | :--- |
| Zápis zprávy | $O(1)$ | Redis HyperLogLog (PFADD) |
| Výpočet žebříčku | $O(\log N)$ | Redis Sorted Set (ZREVRANGE) |
| Predikce Churnu | $O(S^2)$ | Maticové násobení ($S$ = počet stavů) |

Díky $O(1)$ složitosti zápisu do HyperLogLogu můžeme sledovat neomezený počet unikátních uživatelů bez CPU overheadu.
