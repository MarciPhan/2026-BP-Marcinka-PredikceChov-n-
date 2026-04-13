# Srovnání ML algoritmů v Metricordu

Proč jsme pro základní predikce vybrali Markovovy řetězce a jaké jsou alternativy pro budoucnost.

| Metoda | Využití v Metricordu | Výhody | Nevýhody |
| :--- | :--- | :--- | :--- |
| **Markovovy řetězce** | Predikce Retence/Churnu | Extrémně rychlé, nízká RAM, vysoká interpretovatelnost. | Nedostatek kontextu pro velmi dlouhé řady. |
| **LSTM (RNN)** | Experimentální (Labs) | Zachycuje dlouhodobé závislosti v datech. | Náročné na trénink, vyžaduje GPU/výkon. |
| **Kaplan-Meier** | Survival Analysis | Standard v medicíně/pojistné matematice pro sledování odchodů. | Statický model, nereaguje na okamžité změny. |

## Prognóza: Hybridní modely

V příští verzi Metricordu (Roadmap Q3) plánujeme propojení interpretovatelnosti Markovových řetězců s hloubkou LSTM sítí pro náročné enterprise zákazníky.

::: info Technický verdikt
Pro 95 % Discord serverů jsou Markovovy řetězce ideálním kompromisem mezi přesností a nároky na hosting.
:::
