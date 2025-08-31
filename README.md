# uj-urban-gentrification-simulator

Urban growth and gentrification modeling. Simulate urban growth and gentrification using agent-based model. The model should capture how residents, developers, and policies interact over time, influencing housing prices, migration, and neighborhood evolution. The city can be modeled as a grid based system, where each cell represents a neighborhood or housing unit and has an initial property value. The agents of the system are the residents, that have an income level, the developers and identify low-cost properties to purchase and upgrade and government policies, like tax incentives, zoning laws or rent control. Questions that can be answered:
* How does gentrification emerge in an agent-based city model?
* What factors accelerate or slow down gentrification?
* How do different government policies impact urban growth?

Usefull links:
* https://arxiv.org/html/2410.18004v1#S2
* https://github.com/projectmesa/mesa?tab=readme-ov-file
* https://github.com/RafalKucharskiPK/ComplexSocialSystemsCourse/blob/main/labs/lab5/abm-predator-prey-with-wolves-with-plot.py
* https://www.zillow.com/research/data/
* https://www.redfin.com/news/data-center/

# Wstępny plan:
### 1. iteracja
* step = 1 miesiąc
* Pole w gridzie - obiekt, który agreguje `n` mieszkań, ma przypisaną wysokość czynszu
* Mieszkanie - obiekt, który jest przypisany do mieszkańca
* Mieszkaniec - ma random income (nie dzielimy na 3 grupy), każdy mieszkaniec wynajmuje (nie może posiadać). Migruje na jeden z dwóch sposobów:
    * raz na `m` miesięcy (z pewnym prawd. - exp) bierze pod uwagę zmianę mieszkania w obrębie pewnego seek_radius, chcąc maksymalizować happiness_factor

### 2. iteracja
* Deweloper - nie ma przypisanej pozycji na siatce, podejmuje `d` decyzji (akcji) wg ROI:
    * nic
    * kupuje działkę i buduje
    * ulepsza posiadaną działkę
    * podwyższa czynsz (limitowane przez policy)

### 3. iteracja
* policies, wizualizacje, typy pól

### 4. iteracja (opcjonalna)
* możliwość posiadania mieszkań przez mieszkańców