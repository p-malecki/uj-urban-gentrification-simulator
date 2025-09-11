import logging
import random
from mesa import Agent
import numpy as np
from enum import Enum

from model_elements.apartment import Apartment
from model_elements.cell_agent import CellAgent
from model_elements.constants import *

class DevelopersPreset(Enum):
    AR = (0.2, 20, 1, 'AR')  # Aggressive renting
    BR = (0.05, 30, 1, 'BR')  # Balanced renting
    AS = (0.2, 20, 0, 'AS')  # Aggressive selling
    BS = (0.05, 30, 0, 'BS')  # Balanced selling
    AM = (0.2, 25, 0.5, 'AM')  # Aggressive mixed
    BM = (0.05, 30, 0.5, 'BM') # Balanced mixed

class LandlordAgent(Agent):
    def __init__(self, model, profit_margin: float):
        super().__init__(model)
        self.profit_margin = profit_margin  # Desired profit margin for investments

        self.owned_properties: list[Apartment] = []
        self.apts_to_sell: list[Apartment] = []
        self.starting_capital = START_LANDLORDS_CAPITAL * np.random.normal(loc=1.0, scale=0.05)
        self.capital = self.starting_capital

    def calc_roi(self, cell: CellAgent, apartment: Apartment):
        full_buy_cost = apartment.price + ((1 - apartment.freshness) if apartment.freshness < 0.7 else 0) * FULL_HOUSE_RENOVATION_COST * random.uniform(0.8, 1.2)
        monthly_rent = apartment.bills * self.profit_margin
        return full_buy_cost / monthly_rent   # ROI in months

    def buy_property(self):
        cells = random.sample(list(self.model.cell_agents_layer.data.flatten()), DEVELOPER_CELL_LOOKUP_COUNT)
        
        best_offer = None
        best_roi = np.inf

        for cell in cells:
            apts_for_sale_ids = cell.apartments_to_sell
            #logging.info(f"Developer {self.unique_id} evaluating cell at {cell.position} with {len(apts_for_sale_ids)} apartments for sale.")
            
            for id in apts_for_sale_ids:
                apartment = cell.apartments[id]
                if apartment.price > self.capital:
                    continue

                roi = self.calc_roi(cell, apartment)
                if roi < best_roi:
                    best_roi = roi
                    best_offer = apartment

        logging.info(f"Developer {self.unique_id} evaluated {len(cells)} cells and found best ROI: {best_roi:.2f} months.")

        if best_offer:
            apartment = best_offer
            cell: CellAgent = self.model.cell_agents_layer.data[apartment.position]
            self.owned_properties.append(apartment)
            if apartment.owner:
                apartment.owner.sell_house(apartment)

            full_buy_cost = apartment.price + ((1 - apartment.freshness) if apartment.freshness < 0.7 else 0) * FULL_HOUSE_RENOVATION_COST * random.uniform(0.8, 1.2)
            apartment.owner = self
            apartment.ocupied = False
            self.capital -= full_buy_cost
            apartment.reset_freshness()
            apartment.rent = cell.avg_rent_price * self.profit_margin
            cell.apartments_to_rent.add(apartment.index)
            cell.apartments_to_sell.discard(apartment.index)
            apartment.time_rented = 0
            apartment.time_at_market = 0

            logging.info(f"🏠 Developer {self.unique_id} bought apartment {apartment.index} at {apartment.position}. Remaining capital: {self.capital:.2f}")

    def manage_rental_house(self, apartment: Apartment):
        logging.info(apartment)

        if apartment.occupied:
            apartment.time_rented += 1
            self.capital += apartment.rent
            #From time to time, increase rent if tenant stayed long enough
            if apartment.time_rented % 12 == 0 and random.random() < 0.5:
                apartment.rent *= np.random.normal(loc=1.04, scale=0.02)
        else:
            self.capital -= apartment.bills
            apartment.time_at_market += 1
            # Looking for a new tenant, adjust rent
            if apartment.time_at_market == 1:
                cell = self.model.cell_agents_layer.data[apartment.position]
                apartment.rent = apartment.bills * self.profit_margin
                if apartment.freshness < 0.5:
                    self.capital -= FULL_HOUSE_RENOVATION_COST * (1 - apartment.freshness) * random.uniform(0.8, 1.2)
                    apartment.reset_freshness()
            if apartment.time_at_market > 3:
                self.profit_margin *= 0.98  # Decrease profit margin if it took too long to rent
                apartment.rent = apartment.bills * self.profit_margin

    def rent_house(self, apartment: Apartment):
        apartment.occupied = True
        cell = self.model.cell_agents_layer.data[apartment.position]
        cell.apartments_to_rent.discard(apartment.index)
        apartment.time_rented = 0

        if apartment.time_at_market <= 1:
            self.profit_margin *= 1.05
        elif apartment.time_at_market <= 3:
            self.profit_margin *= 1.02

        apartment.time_at_market = 0

    def manage_house_sale(self, apartment: Apartment):
        self.capital -= apartment.bills
        apartment.time_at_market += 1
        if apartment.time_at_market >= 3:
            apartment.price *= 0.975  # Reduce price by 2.5% if not sold in 3 months

    def sell_house(self, apartment: Apartment):
        self.capital += apartment.price
        self.apts_to_sell.remove(apartment)
        cell = self.model.cell_agents_layer.data[apartment.position]
        cell.apartments_to_sell.discard(apartment.index)
        apartment.owner = None
        apartment.occupied = False
        apartment.time_at_market = 0
        apartment.time_rented = 0

    def step(self):
        #Potential problems: TODO
        if self.capital <= 0:
            if any(not apt.occupied for apt in self.owned_properties):
                apt = random.choice([apt for apt in self.owned_properties if not apt.occupied])
                cell = self.model.cell_agents_layer.data[apt.position]
                apt.owner = self
                apt.occupied = False
                apt.time_at_market = 0
                apt.time_rented = 0
                self.owned_properties.remove(apt)
                self.apts_to_sell.append(apt)
                avg_price = np.mean([apt.price for apt in cell.apartments if apt.index in cell.apartments_to_sell]) if cell.apartments_to_sell else HOUSE_BUILD_COST
                cell.apartments_to_sell.add(apt.index)
                self.owned_apartment.price = avg_price * random.uniform(1.05, 1.15)
            return

        for house in self.owned_properties:
            self.manage_rental_house(house)
        for house in self.apts_to_sell:
            self.manage_house_sale(house)

        if self.capital > random.choice(self.model.cell_agents_layer.data.flatten()).avg_house_price:
            self.buy_property()

        logging.info(f"🐛 Landlord {self.unique_id} has capital: {self.capital:.2f} and {len(self.owned_properties) + len(self.apts_to_sell)} properties")