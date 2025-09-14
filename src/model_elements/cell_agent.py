import logging
from typing import Tuple
import numpy as np
from mesa import Agent

from model_elements.apartment import Apartment
from model_elements.constants import HOUSE_BUILD_COST, START_RENT_PRICE
from model_elements.developer_agent import DeveloperAgent
from model_elements.gov_developer import GovDeveloper
from model_elements.landlord_agent import LandlordAgent

class CellAgent(Agent):
    def __init__(self, model, position: Tuple[int, int], bills: float):
        super().__init__(model)
        self.model = model
        self.position = position
        self.bills = bills

        self.apartments: list[Apartment] = []
        self.apartments_to_rent: list[Apartment] = []
        self.apartments_to_sell: list[Apartment] = []

    def remove_apartment(self, apartment: Apartment):
        apartment.position = None
        apartment.owner = None
        apartment.tenant = None

        if apartment in self.apartments:
            self.apartments.remove(apartment)
        if apartment in self.apartments_to_rent:
            self.apartments_to_rent.remove(apartment)
        if apartment in self.apartments_to_sell:
            self.apartments_to_sell.remove(apartment)

    def get_avg_cost(self):
        if not self.apartments_to_sell:
            return HOUSE_BUILD_COST
        return np.mean([apt.price for apt in self.apartments_to_sell])
    
    def get_avg_rent(self):
        if not self.apartments_to_rent:
            return START_RENT_PRICE
        return np.mean([apt.rent for apt in self.apartments_to_rent] + [apt.rent for apt in self.apartments if apt.tenant])

    def step(self, step: int):
        if step % 12 == 0:
            pass
            # bills_change = np.random.normal(loc=0.03, scale=0.02)
            # self.bills *= (1 + bills_change)
        
        for apt in self.apartments:
            # apt.bills = self.bills
            apt.update_freshness()
            
            if apt.owner is None:
                logging.info(f"‼️Warning: Apartment at {apt.position} has no owner.")
                logging.info(f"Apartment.deleted = {apt.deleted}, Apartment.occupied = {apt.occupied}, Apartment.owner = {apt.owner}, Apartment.tenant = {apt.tenant}, Apartment.time_at_market = {apt.time_at_market}, Apartment.time_rented = {apt.time_rented}")

        for apt in self.apartments_to_rent:
            if apt not in self.apartments:
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for rent but not in cell apartments.")
            if not isinstance(apt.owner, LandlordAgent):
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for rent but owner is not a landlord or developer.")

        for apt in self.apartments_to_sell:
            if apt not in self.apartments:
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for sale but not in cell apartments.")
            if not isinstance(apt.owner, DeveloperAgent ) and not isinstance(apt.owner, GovDeveloper):
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for sale but owner is not a landlord or developer.")
                logging.info(f"Apartment owner type: {type(apt.owner)}")
            if apt.deleted:
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for sale but marked as deleted.")
            if apt.owner is None:
                logging.info(f"‼️Warning: Apartment at {apt.position} listed for sale but has no owner.")
        #print values of all atributes of the cell:
        # logging.info (f"Cell {self.position} - Bills: {self.bills:.2f}, Apartments: {(self.apartments)}, For Rent: {(self.apartments_to_rent)}, For Sale: {(self.apartments_to_sell)}")
