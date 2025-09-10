import logging
from mesa import Agent
import random
from math import log, sqrt

import numpy as np
from model_elements.constants import *

class resident_agent(Agent):
    def __init__(self, model, income, apartment=None, searching_radius=1):
        super().__init__(model)
        self.income = income * 0.8  # assume residents spend 80% of income on housing
        self.apartment = None
        self.apt_owned = False
        self.base_searching_radius = searching_radius
        self.searching_radius = searching_radius
        self.happiness_factor = 0

    def __repr__(self):
        #TODO: enhance representation
        return f"Resident(unique_id={self.unique_id}, income={self.income}, happiness_factor={self.happiness_factor}, is_homeless={self.apartment is None}"

    def assign_apartment(self, apartment, owned):
        # Move out from current apartment if any
        if self.apartment:
            self.apartment.occupied = False
            if not self.apt_owned:
                self.model.cell_agents_layer.data[self.apartment.position].apartments_to_rent.add(self.apartment.index)
            else:
                self.model.cell_agents_layer.data[self.apartment.position].apartments_to_sell.add(self.apartment.index)

        """Move resident into an apartment."""
        self.apartment = apartment
        self.apt_owned = owned
        self.model.grid.move_agent(self, apartment.position)
        apartment.occupied = True

    def update_happiness(self):
        """
        happiness = log((1-(income / local rent)) * apr.freshness)
        additionally if resident owns the apartment, happiness is boosted by sqrt(happiness)
        """
        if self.apartment is not None:
            x, y = self.pos
            if self.apt_owned:
                happiness = log((1 - (self.apartment.bills / self.income)) * self.apartment.freshness) + 1
                self.happiness_factor = sqrt(happiness) if happiness > 0 else 0
            else:
                happiness = log((1 - ((self.apartment.bills + self.apartment.rent) / self.income)) * self.apartment.freshness) + 1
                self.happiness_factor = happiness if happiness > 0 else 0
        else:
            self.happiness_factor = 0

    def find_apt_to_rent(self):
        x,y = self.pos

        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=True,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = 0
        logging.debug(
            f"Resident {self.unique_id} at {(x, y)} is searching for a rental home."
        )

        for nx, ny in neighborhood:
            cell_agent = self.model.cell_agents_layer.data[nx, ny]

            k = int(len(cell_agent.apartments_to_rent) * 0.8)
            apts_for_rental = random.sample(list(cell_agent.apartments_to_rent), k)

            for idx in apts_for_rental:  # Check all empty apartments in this cell
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - ((candidate_apartment.bills + candidate_apartment.rent) / self.income)) * candidate_apartment.freshness
                candidate_happiness = log(temp) + 1 if temp > 0 else 0
                if candidate_happiness > best_happiness and candidate_apartment.rent + candidate_apartment.bills < self.income:
                    best_apartment = candidate_apartment
                    best_happiness = candidate_happiness

        if best_apartment:
            self.assign_apartment(best_apartment, False)
            self.happiness_factor = best_happiness
            self.searching_radius = self.base_searching_radius
            logging.info(
                f"✅ Resident {self.unique_id} FOUND a rental home. Moving from {x, y} to {best_apartment.position} (happiness {self.happiness_factor:.2f})."
            )
        else:
            self.searching_radius += 1  # Expand search radius for next time
            logging.info(
                f"❌ Resident {self.unique_id} at {x, y} is still homeless. No suitable rental options found."
            )
    
    def find_apt_to_move(self):
        x,y = self.pos

        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=True,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = self.happiness_factor
        logging.debug(
            f"Resident {self.unique_id} at {(x, y)} is searching for a new home."
        )

        for nx, ny in neighborhood:
            cell_agent = self.model.cell_agents_layer.data[nx, ny]

            k = int(len(cell_agent.apartments_to_buy) * 0.8)
            apts_for_rental = random.sample(list(cell_agent.apartments_to_buy), k)

            for idx in apts_for_rental:  # Check all empty apartments in this cell
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - (candidate_apartment.bills / self.income)) * candidate_apartment.freshness
                candidate_happiness = sqrt(log(temp)) + 1 if temp > 0 else 0
                if candidate_happiness > best_happiness:
                    best_apartment = candidate_apartment
                    best_happiness = candidate_happiness

        if best_apartment:
            self.assign_apartment(best_apartment, True)
            self.happiness_factor = best_happiness
            self.searching_radius = self.base_searching_radius
            logging.info(
                f"✅ Resident {self.unique_id} FOUND a new home. Moving from {x, y} to {best_apartment.position} (happiness {self.happiness_factor:.2f})."
            )
        else:
            self.searching_radius += 1  # Expand search radius for next time
            logging.info(
                f"❌ Resident {self.unique_id} at {x, y} has not moved. No better options found."
            )
            self.update_happiness()

    def find_apt_to_rent_or_buy(self):
        x,y = self.pos

        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=True,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = self.happiness_factor
        logging.debug(
            f"Resident {self.unique_id} at {(x, y)} is searching for a new home - rent or buy."
        )

        for nx, ny in neighborhood:
            cell_agent = self.model.cell_agents_layer.data[nx, ny]

            k_rental = int(len(cell_agent.apartments_to_rent) * 0.8)
            apts_for_rental = random.sample(list(cell_agent.apartments_to_rent), k_rental)
            k_sale = int(len(cell_agent.apartments_to_sell) * 0.8)
            apts_for_sale = random.sample(list(cell_agent.apartments_to_sell), k_sale)

            for idx in apts_for_rental:
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - ((candidate_apartment.bills + candidate_apartment.rent) / self.income)) * candidate_apartment.freshness
                candidate_happiness = log(temp) + 1 if temp > 0 else 0
                if candidate_happiness > best_happiness and candidate_apartment.rent + candidate_apartment.bills < self.income:
                    best_apartment = (candidate_apartment, False)
                    best_happiness = candidate_happiness

            for idx in apts_for_sale:
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - (candidate_apartment.bills / self.income)) * candidate_apartment.freshness
                candidate_happiness = sqrt(log(temp)) + 1 if temp > 0 else 0

                if candidate_happiness > best_happiness and self.income >= candidate_apartment.price * MORTGAGE_MONTHLY_FACTOR:
                    best_apartment = (candidate_apartment, True)
                    best_happiness = candidate_happiness

        if best_apartment:
            self.assign_apartment(*best_apartment)
            self.happiness_factor = best_happiness
            self.searching_radius = self.base_searching_radius
            logging.info(
                f"✅ Resident {self.unique_id} FOUND a new home. Moving from {x, y} to {best_apartment[0].position} (happiness {self.happiness_factor:.2f})."
            )
        else:
            self.searching_radius += 1
            logging.info(
                f"❌ Resident {self.unique_id} at {x, y} has not moved. No better options found."
            )
            self.update_happiness()

    def step(self):
        income_change = np.random.normal(loc=0.005, scale=0.02)
        self.income *= (1 + income_change)

        if not self.apartment:
            self.find_apt_to_rent()
            # logging.info(self)
            return
        
        if self.apt_owned:
            if self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD and random.random() > self.happiness_factor:
                self.find_apt_to_move()
            else:
                self.update_happiness()
                logging.info(self)
            return
        
        if self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD and random.random() > self.happiness_factor:
            self.find_apt_to_rent_or_buy()
        else:        
            self.update_happiness()    