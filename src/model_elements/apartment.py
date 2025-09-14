import logging
import random
from typing import Tuple

class Apartment:
    def __init__(
        self, position: Tuple[int, int], price: float, bills: float, owner = None, rent: float = 0, occupied: bool = False
    ):
        self.position = position
        self.freshness = random.uniform(0.95, 1.0)
        
        self.price = price # price for which apartment can be bought
        self.bills = bills # monthly bills (utilities, maintenance, property tax, etc.) - paid to town
        self.rent = rent # monthly rent - paid to landlord

        self.occupied = occupied
        self.time_at_market = 0
        self.time_rented = 0
        
        self.tenant = None  # can be ResidentAgent
        self.owner = owner  # can be ResidentAgent, LandlordAgent or DeveloperAgent

        #DEBUG: TODO: remove
        self.deleted = False  # Flag to indicate if the apartment has been deleted

    # @property
    # def owner(self):
    #     return self._owner

    # @owner.setter
    # def owner(self, value):
    #     # logging.info(f"Transferring ownership of apartment {self.position} from {self._owner} to {value}")
    #     self._owner = value

    def update_freshness(self, decay_rate = 0.99):
        self.freshness = self.freshness * decay_rate

    def reset_freshness(self):
        self.freshness = random.uniform(0.85, 1.0)

    def full_cost(self):
        return self.rent + self.bills

    # def __repr__(self):
    #     return f"Apartment(pos={self.position}, index={self.index}, rent={self.rent}, occupied={self.occupied})"