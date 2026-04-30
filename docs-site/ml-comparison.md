# Srovnání ML algoritmů

Přehled prediktivních algoritmů použitých v Metricord a důvody volby konkrétních metod.

## Implementované metody

| Metoda | Použití | Implementace |
| :--- | :--- | :--- |
| **Markovovy řetězce (DTMC)** | Predikce přechodu mezi stavy (Active → At-Risk → Churn) | `shared/models.py` → `calculate_markov_matrix()` |
| **Kaplan-Meierův odhad** | Survival analýza - odhad retence v čase | `shared/models.py` → `calculate_survival_rate()` |
| **HyperLogLog** | Odhad DAU/MAU s fixní pamětí 12 KB | Redis nativní `PFADD` / `PFCOUNT` |

## Kritéria výběru

Výběr algoritmů vychází z provozních omezení Discord bota:

| Kritérium | Požadavek | Splněno |
| :--- | :--- | :--- |
| Nároky na paměť | < 256 MB pro server s 5 000 členy | Ano - Markov matice 5×5 = 200 B |
| Latence predikce | < 10 ms | Ano - NumPy maticové násobení |
| Interpretovatelnost | Moderátor musí rozumět výstupu | Ano - Pravděpodobnosti, ne skóre |
| Trénink bez GPU | Běh na VPS bez dedikovaného HW | Ano - Žádné neuronové sítě |
| Minimum dat | Funkční od 7 dnů historie | Ano - Statistické metody |

## Zvažované alternativy

### LSTM (Recurrent Neural Network)

Zachycuje dlouhodobé závislosti v časových řadách. Nevhodné pro Metricord z důvodu:
- Vysoké nároky na trénovací data (> 10 000 vzorků na server).
- Vyžaduje GPU pro rozumnou dobu trénování.
- Výstup je skóre, ne interpretovatelná pravděpodobnost.

### Random Forest

Klasifikátor vhodný pro binární predikci (odejde / neodejde). Nevybrán z důvodu:
- Vyžaduje feature engineering (ruční výběr příznaků).
- Statický model - nepracuje přirozeně s časovými řadami.
- Interpretovatelnost nižší než u Markovových řetězců.

### Prophet (Facebook)

Model pro sezónní dekompozici. Potenciální doplněk pro budoucí verze:
- Dobře identifikuje periodické vzorce (víkendová aktivita).
- Vysoké nároky na knihovnu (Stan backend).

## Srovnání výkonu

| Metrika | Markov + KM | LSTM | Random Forest |
| :--- | :--- | :--- | :--- |
| Paměť na server | < 1 KB | 50–200 MB | 5–50 MB |
| Čas trénování | < 100 ms | minuty–hodiny | sekundy |
| Min. dat pro funkčnost | 7 dní | 90+ dní | 30+ dní |
| Interpretovatelnost | Vysoká | Nízká | Střední |
| GPU potřeba | Ne | Ano | Ne |
