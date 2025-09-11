import random
from typing import Tuple

class Apartment:
    def __init__(
        self, position: Tuple[int, int], index: int, price: float, bills: float, owner = None, rent: float = 0, occupied: bool = False
    ):
        self.position = position
        self.index = index
        self.freshness = random.uniform(0.95, 1.0)
        
        self.price = price # price for which apartment can be bought
        self.bills = bills # monthly bills (utilities, maintenance, property tax, etc.) - paid to town
        self.rent = rent # monthly rent - paid to landlord

        self.occupied = occupied
        self.time_at_market = 0
        self.time_rented = 0
        
        self.owner = owner  # can be ResidentAgent, LandlordAgent or DeveloperAgent

    def update_freshness(self, decay_rate = 0.99):
        self.freshness = self.freshness * decay_rate

    def reset_freshness(self):
        self.freshness = random.uniform(0.85, 1.0)

    def full_cost(self):
        return self.rent + self.bills

    # def __repr__(self):
    #     return f"Apartment(pos={self.position}, index={self.index}, rent={self.rent}, occupied={self.occupied})"

    def __eq__(self, other):
        return self.rent == other.rent

    def __lt__(self, other):
        return self.rent < other.rent