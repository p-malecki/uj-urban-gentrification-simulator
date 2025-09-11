import logging
import random
from mesa import Agent
import numpy as np

from model_elements.apartment import Apartment
from model_elements.cell_agent import CellAgent
from model_elements.constants import *

class DeveloperAgent(Agent):
    def __init__(self, model, profit_margin: float):
        super().__init__(model)
        self.profit_margin = profit_margin  # Starting desired profit margin for investments

        self.owned_properties: list[Apartment] = []
        self.starting_capital = START_DEVELOPERS_CAPITAL * np.random.normal(loc=1.0, scale=0.05)
        self.capital = self.starting_capital

    def manage_house_for_sale(self, apartment: Apartment):
        apartment.freshness = max(apartment.freshness, 0.85)  # Ensure minimum freshness for unsold apartments
        apartment.time_at_market += 1
        if apartment.time_at_market > 3:
            apartment.price = max(HOUSE_BUILD_COST, apartment.price * 0.98)  # Reduce price by 2% if not sold in 3 months

    def sell_house(self, apartment: Apartment):
        # Increase profit margin if sold quickly
        if apartment.time_at_market <= 1:
            self.profit_margin *= 1.05
        elif apartment.time_at_market <= 3:
            self.profit_margin *= 1.02  
        elif apartment.time_at_market <= 5:
            self.profit_margin *= 0.98  # Decrease profit margin if it took too long to sell
        else:
            self.profit_margin *= 0.95
        self.capital += apartment.price
        self.owned_properties.remove(apartment)
        cell = self.model.cell_agents_layer.data[apartment.position]
        cell.apartments_to_sell.discard(apartment.index)
        apartment.owner = None
        apartment.occupied = False
        apartment.time_at_market = 0

    def step(self, step: int):
        for house in self.owned_properties:
            self.manage_house_for_sale(house)

        if step % 12 == 0:
            # Every year, try builing new properties in random location
            cell: CellAgent = self.model.cell_agents_layer.data[random.randint(0, self.model.grid.width - 1), random.randint(0, self.model.grid.height - 1)]
            
            for _ in range (int(self.capital // HOUSE_BUILD_COST)):
                self.capital -= HOUSE_BUILD_COST
                apartment = Apartment(position=cell.position, index=len(cell.apartments), price=HOUSE_BUILD_COST * (1 + self.profit_margin), bills=cell.bills, owner=self)
                cell.apartments.append(apartment)
                cell.apartments_to_sell.add(apartment.index)
                self.owned_properties.append(apartment)
                logging.info(f"🏗️ Developer {self.unique_id} built new apartment and set its price to {apartment.price}.")
        
        logging.info(f"Developer {self.unique_id} has capital: {self.capital:.2f} and profit margin: {self.profit_margin:.2f}")