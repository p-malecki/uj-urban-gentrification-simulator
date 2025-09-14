import logging
import random
from mesa import Agent

from model_elements.apartment import Apartment
from model_elements.constants import *
from model_elements.resident_agent import ResidentAgent

class GovDeveloper(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.profit_margin = 0.05  # Starting desired profit margin for investments
        self.build_month = random.randint(0, 11)  # Random month to consider building new properties

        self.owned_properties: list[Apartment] = []
        self.capital = 1  # Government developer has infinite capital

    def build_house(self, cell):
        apartment = Apartment(position=cell.position, price=HOUSE_BUILD_COST * (1 + self.profit_margin), bills=cell.bills, owner=self)
        cell.apartments.append(apartment)
        cell.apartments_to_sell.append(apartment)
        self.owned_properties.append(apartment)

    def manage_house_for_sale(self, apartment: Apartment):
        apartment.freshness = max(apartment.freshness, 0.85)  # Ensure minimum freshness for unsold apartments
        # apartment.time_at_market += 1
        # if apartment.time_at_market > 3:
        #     apartment.price = max(HOUSE_BUILD_COST, apartment.price * 0.99)  # Reduce price by 2% if not sold in 3 months

    def sell_house(self, apartment: Apartment):
        if apartment in self.owned_properties:
            self.owned_properties.remove(apartment)
        else:
            logging.warning(f"Warning: Developer {self.unique_id} tried to sell apartment {apartment.position} not in owned properties.")

        cell = self.model.cell_agents_layer.data[apartment.position]
        if apartment in cell.apartments_to_sell:
            cell.apartments_to_sell.remove(apartment)
        else:
            logging.warning(f"Warning: Apartment {apartment.position} not found in cell's apartments_to_sell list during sale.")
        
        self.model.recent_sell_prices.append(apartment.price)
        apartment.owner = None
        apartment.occupied = False
        apartment.time_at_market = 0

    def step(self, step: int):
        for house in self.owned_properties:
            self.manage_house_for_sale(house)

        if step % 12 == self.build_month:
            homeless_residents = len([agent for agent in self.model.agents_by_type.get(ResidentAgent, []) if not agent.owned_apartment])
            
            if homeless_residents > self.model.num_residents * 0.05 and len(self.owned_properties) < 100:
                cell = random.choice(self.model.cell_agents_layer.data.flatten())
                for _ in range (100):
                    self.build_house(cell)

        # logging.info(f"👷Developer {self.unique_id} has capital: {self.capital:.2f}, profit margin: {self.profit_margin:.2f}, and {len(self.owned_properties)} properties to sell.")