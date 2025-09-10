import random
from typing import Tuple

class Apartment:
    def __init__(
        self, position: Tuple[int, int], index: int, bills: float, rent: float, occupied: bool = False
    ):
        self.position = position
        self.index = index
        self.freshness = random.uniform(0.5, 1.0)
        
        self.bills = bills
        self.rent = rent
        self.occupied = occupied

    def update_freshness(self, decay_rate = 0.99):
        self.freshness = self.freshness * decay_rate

    def reset_freshness(self):
        self.freshness = random.uniform(0.85, 1.0)

    def __repr__(self):
        return f"Apartment(pos={self.position}, index={self.index}, rent={self.rent}, occupied={self.occupied})"

    def __eq__(self, other):
        return self.rent == other.rent

    def __lt__(self, other):
        return self.rent < other.rent