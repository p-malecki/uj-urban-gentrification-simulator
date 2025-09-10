import logging
from random import random
from typing import Tuple
import numpy as np
from mesa import Agent

class cell_agent(Agent):
    def __init__(self, model, property_value, location_factor, bills: float, position: Tuple[int, int]):
        super().__init__(model)
        self.model = model
        self.position = position
        self.bills = bills
        self.apartments = []
        self.apartments_to_rent = set()
        self.apartments_to_sell = set()

        # subject to deletion
        self.property_value = (
            property_value  # ! TODO: compute property_value based on apartments value
        )
        # self.rent = property_value * RENT_FACTOR
        self.location_factor = location_factor

    def step(self):
        bills_change = np.random.normal(loc=0.005, scale=0.02)
        self.bills *= (1 + bills_change)

        for apt in self.apartments:
            apt.bills = self.bills
            apt.update_freshness()

            if random() < 0.1:
                apt.reset_freshness() #TODO: should be done by developer