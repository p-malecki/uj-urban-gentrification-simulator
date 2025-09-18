# Urban Gentrification Simulator

An agent-based model exploring how economic forces, housing markets, and government interventions shape neighbourhood transformation in a city.

## Motivation

Housing is a rising concern in many countries worldwide, with increasing prices and rents. This problem is present in Poland as well, especially in larger cities like Warsaw, Krakow, or Wroclaw. For example, in Kraków, the average price per square meter in 2015 was around 6,000 PLN, while in 2025 it reached its all-time high of 16,000 PLN. This is a rise of 166% in just 10 years, despite the fact that the average salary in Poland rose by only around 100% in the same time period. This means that housing is becoming less and less affordable for average citizens, especially young people who are just starting their careers.

Politicians and economists often debate about the best way to solve this problem. Some argue that the government should intervene in the market by, for example, building more social housing, while others believe that the market should be left alone to regulate itself. This model aims to provide some insights into this debate by simulating different scenarios and observing their outcomes.

## Goals

The primary objectives of the model are to understand how various factors contribute to gentrification and its social consequences. Specifically, it aims to:

- Analyze how market-driven development leads to rising property values and the displacement of lower-income residents.
- Examine the role of government policies, such as property taxes and social housing, in mitigating negative outcomes.

## Features

### Core Components

- **Urban Cells**: The city is divided into a grid of cells, each representing a neighbourhood block. Cells manage local housing inventory, tracking apartments available for rent or sale. They also handle property maintenance, such as updating apartment freshness and removing units that are no longer viable.
- **Apartments**: These are the fundamental housing units, each with attributes like market price, monthly rent, utility bills, and a "freshness" factor that represents upkeep and desirability.
- **Agents**:
  - **Residents**: Simulate households seeking affordable, desirable housing.
  - **Developers**: Profit-driven builders who construct new apartments in under-supplied areas.
  - **Landlords**: Investors who purchase existing apartments and manage them as rental properties.
  - **Government Developers**: A special agent introduced to counteract market failures by building affordable housing.
- **Policies**:
  - **Ad Valorem Property Tax**: A progressive tax on property values based on the number of apartments owned by an individual.
  - **Social Housing Provision**: The government developer builds and sells apartments at a low price to address rising homelessness.

## Results

The results of the simulations are visualized through various plots, showing key metrics such as:

- **Average Sell Price over Time**: Shows the impact of different policies on housing prices.
- **Average Rent over Time**: Shows the impact of different policies on rental prices.
- **Homelessness Rate over Time**: Shows the percentage of residents unable to find housing.
- **House Ownership Rate over Time**: Shows the percentage of residents who own their homes.

### Key Findings

- **Government Intervention**: Particularly social housing, helps stabilize prices and rents, making housing more affordable for residents.
- **Ad Valorem Property Tax**: While effective in limiting landlord accumulation, it does not sufficiently address the core issues of supply and demand in the housing market.
