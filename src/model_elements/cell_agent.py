import logging
from random import random
from typing import Tuple
import numpy as np
from mesa import Agent
import model_elements.constants as constants

class CellAgent(Agent):
    def __init__(self, model, property_value, location_factor, bills: float, position: Tuple[int, int]):
        super().__init__(model)
        self.model = model
        self.position = position
        self.bills = bills
        self.apartments = []
        self.apartments_to_rent = set()
        self.apartments_to_sell = set()
        self.avg_house_price = 0
        self.avg_rent_price = constants.START_RENT_PRICE

        # subject to deletion
        self.property_value = (
            property_value  # ! TODO: compute property_value based on apartments value
        )
        # self.rent = property_value * RENT_FACTOR
        self.location_factor = location_factor

    def step(self):
        bills_change = np.random.normal(loc=0.00075, scale=0.002)
        self.bills *= (1 + bills_change)
        constants.HOUSE_BUILD_COST *= (1 + bills_change)

        self.avg_house_price = np.mean([apt.price for apt in self.apartments]) if self.apartments else 0
        # self.avg_rent_price = np.mean([apt.rent for apt in self.apartments if isinstance(apt.owner, LandlordAgent)]) if any(apt.rent for apt in self.apartments if isinstance(apt.owner, LandlordAgent)) else self.avg_rent_price

        for apt in self.apartments:
            apt.bills = self.bills
            apt.update_freshness()
