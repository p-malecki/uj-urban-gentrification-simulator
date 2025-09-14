import logging
import random
from mesa import Agent
import numpy as np

from model_elements.apartment import Apartment
from model_elements.constants import *

class DeveloperAgent(Agent):
    def __init__(self, model, profit_margin: float):
        super().__init__(model)
        self.profit_margin = profit_margin  # Starting desired profit margin for investments
        self.build_month = random.randint(0, 2)  # Random month to consider building new properties

        self.owned_properties: list[Apartment] = []
        self.starting_capital = START_DEVELOPERS_CAPITAL * np.random.normal(loc=1.0, scale=0.05)
        self.capital = self.starting_capital

    def build_house(self, cell):
        self.capital -= HOUSE_BUILD_COST
        avg_price = np.mean(self.model.recent_sell_prices) if self.model.recent_sell_prices else HOUSE_BUILD_COST 
        apartment = Apartment(position=cell.position, price=avg_price * (1 + self.profit_margin), bills=cell.bills, owner=self)
        # logging.info(f"👷Developer {self.unique_id} built a new house at {cell.position} with price {apartment.price:.2f} and bills {apartment.bills:.2f}. Remaining capital: {self.capital:.2f}")
        # logging.info(f"House owner: {apartment.owner}, occupied: {apartment.occupied}, tenant: {apartment.tenant}, time_at_market: {apartment.time_at_market}, time_rented: {apartment.time_rented}, deleted: {apartment.deleted}")
        cell.apartments.append(apartment)
        cell.apartments_to_sell.append(apartment)
        self.owned_properties.append(apartment)

    def manage_house_for_sale(self, apartment: Apartment):
        apartment.freshness = max(apartment.freshness, 0.90)  # Ensure minimum freshness for unsold apartments
        apartment.time_at_market += 1
        if apartment.time_at_market > 3:
            apartment.price = max(HOUSE_BUILD_COST, apartment.price * 0.98)  # Reduce price by 2% if not sold in 3 months

    def sell_house(self, apartment: Apartment):
        # Increase profit margin if sold quickly
        # if apartment.time_at_market <= 1:
        #     self.profit_margin *= 1.05
        # elif apartment.time_at_market <= 3:
        #     self.profit_margin *= 1.02  
        # elif apartment.time_at_market <= 5:
        #     self.profit_margin *= 0.98  # Decrease profit margin if it took too long to sell
        # else:
        #     self.profit_margin *= 0.95

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

        if step % 6 == self.build_month:
            # Every year, try builing new properties in random location
            # homeless_residents = len([agent for agent in self.model.agents_by_type.get(ResidentAgent, []) if not agent.rented_apartment and not agent.owned_apartment])
            houses_on_market = sum(len(cell.apartments_to_sell) for cell in self.model.cell_agents_layer.data.flatten())

            if houses_on_market < self.model.num_residents * 0.1 and self.capital > HOUSE_BUILD_COST and len(self.owned_properties) < 25:
                cell = random.choice(self.model.cell_agents_layer.data.flatten())
                for _ in range (min(20, int(self.capital // HOUSE_BUILD_COST))):
                    self.build_house(cell)

        # logging.info(f"👷Developer {self.unique_id} has capital: {self.capital:.2f}, profit margin: {self.profit_margin:.2f}, and {len(self.owned_properties)} properties to sell.")