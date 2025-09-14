import logging
import random
from mesa import Agent
import numpy as np

from model_elements.apartment import Apartment
from model_elements.constants import *
from model_elements.resident_agent import ResidentAgent

class DeveloperAgent(Agent):
    def __init__(self, model, profit_margin: float):
        super().__init__(model)
        self.profit_margin = profit_margin  # Starting desired profit margin for investments
        self.build_month = random.randint(0, 9)  # Random month to consider building new properties

        self.owned_properties: list[Apartment] = []
        self.capital = START_DEVELOPERS_CAPITAL * np.random.normal(loc=1.0, scale=0.05)

    def build_house(self, cell):
        self.capital -= HOUSE_BUILD_COST

        sell_prices = self.model.recent_sell_prices
        avg_price = np.mean(sell_prices) if sell_prices else HOUSE_BUILD_COST 
        if sell_prices:
            tendention = np.mean(sell_prices[-10:]) - np.mean(sell_prices[:10])
            if tendention > 0:
                avg_price *= 1 + tendention / avg_price

        apartment = Apartment(position=cell.position, price = avg_price * (1 + self.profit_margin), bills=cell.bills, owner=self)
        
        cell.apartments.append(apartment)
        cell.apartments_to_sell.append(apartment)
        self.owned_properties.append(apartment)

    def manage_house_for_sale(self, apartment: Apartment):
        apartment.freshness = max(apartment.freshness, 0.90)  # Ensure minimum freshness for unused apartments
        
        apartment.time_at_market += 1
        if apartment.time_at_market % 3 == 0:
            apartment.price = max(HOUSE_BUILD_COST, apartment.price * 0.98)  # Reduce price by 2% if not sold in 3 months

    def sell_house(self, apartment: Apartment):
        self.capital += apartment.price
        self.model.recent_sell_prices.append(apartment.price)

        if apartment in self.owned_properties:
            self.owned_properties.remove(apartment)
        else:
            logging.warning(f"Warning: Developer {self.unique_id} tried to sell apartment {apartment.position} not in owned properties.")

        cell = self.model.cell_agents_layer.data[apartment.position]
        if apartment in cell.apartments_to_sell:
            cell.apartments_to_sell.remove(apartment)
        else:
            logging.warning(f"Warning: Apartment {apartment.position} not found in cell's apartments_to_sell list during sale.")
        
        apartment.owner = None
        apartment.occupied = False
        apartment.time_at_market = 0

    def step(self, step: int):
        for house in self.owned_properties:
            self.manage_house_for_sale(house)

        if step % 10 == self.build_month:
            homeless_residents = len([agent for agent in self.model.agents_by_type.get(ResidentAgent, []) if not agent.owned_apartment])

            if homeless_residents > self.model.num_residents * 0.1 and self.capital > HOUSE_BUILD_COST and len(self.owned_properties) < 25:
                cell = random.choice(self.model.cell_agents_layer.data.flatten())
                for _ in range(min(50, int(self.capital // HOUSE_BUILD_COST))):
                    self.build_house(cell)