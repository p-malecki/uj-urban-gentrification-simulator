import logging
from mesa import Agent
import random
from math import log

import numpy as np
from model_elements.constants import *
from model_elements.developer_agent import DeveloperAgent

class ResidentAgent(Agent):
    def __init__(self, model, income, searching_radius=1):
        super().__init__(model)
        self.income = income * 0.8  # assume residents spend 80% of income on housing

        self.rented_apartment = None
        self.time_apt_rented = 0
        self.owned_apartment = None
        self.time_apt_owned = 0

        self.base_searching_radius = searching_radius
        self.searching_radius = searching_radius

        self.happiness_factor = 0

    def __repr__(self):
        #TODO: enhance representation
        return f"Resident(unique_id={self.unique_id}, income={self.income}, happiness_factor={self.happiness_factor}, has_home={self.rented_apartment or self.owned_apartment})"

    def assign_apartment(self, apartment, owned):
        #Selling the house
        if self.owned_apartment:
            self.owned_apartment.occupied = False
            self.owned_apartment.owner = None
            self.owned_apartment.time_at_market = 0
            self.owned_apartment.time_rented = 0
            self.owned_apartment.reset_freshness()
            cell = self.model.cell_agents_layer.data[self.owned_apartment.position]
            cell.apartments_to_sell.add(self.owned_apartment.index)
            avg_price = np.mean([apt.price for apt in cell.apartments if apt.index in cell.apartments_to_sell]) if cell.apartments_to_sell else HOUSE_BUILD_COST
            self.owned_apartment.price = avg_price * (1 + random.uniform(0.05, 0.15))

        #Moving out from rented apartment
        if self.rented_apartment:
            self.owned_apartment.occupied = False
            self.owned_apartment.time_at_market = 0
            self.owned_apartment.time_rented = 0
            self.owned_apartment.owner.tenant_moved_out(self.owned_apartment) # notify landlord

        self.rented_apartment = None
        self.time_apt_rented = 0
        self.owned_apartment = None
        self.time_apt_owned = 0
        self.happiness_factor = 0
            
        """Move resident into an apartment."""
        if apartment:
            if owned:
                if apartment.owner:
                    apartment.owner.sell_house(apartment)
                self.owned_apartment = apartment
                apartment.occupied = True
                apartment.owner = self
                apartment.time_at_market = 0
                apartment.time_rented = 0
            else:
                apartment.owner.rent_house(apartment)
                self.rented_apartment = apartment
                apartment.occupied = True

        self.update_happiness()

    def update_happiness(self):
        """
        happiness = log((1-(income / local rent)) * apr.freshness) + 1
        additionally if resident owns the apartment, happiness is boosted to log((1-(income / local rent)) * apr.freshness + 0.2) + 1
        """
        if self.rented_apartment:
            temp = (1 - ((self.rented_apartment.full_cost()) / self.income)) * self.rented_apartment.freshness
            self.happiness_factor = log(temp) + 1 if temp > 0 else 0
            return
        
        if self.owned_apartment:
            # temp = (1 - (self.owned_apartment.full_cost() / self.income)) * self.owned_apartment.freshness + 0.2
            # self.happiness_factor = log(temp) + 1 if temp > 0 else 0
            self.happiness_factor = 1
            return
        
        self.happiness_factor = 0

    def find_apt_to_rent(self):
        x,y = self.pos

        logging.info(self.searching_radius)

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

            k = int(round(len(cell_agent.apartments_to_rent) * 0.8))
            apts_for_rental = random.sample(list(cell_agent.apartments_to_rent), k)
            logging.info(f"cell.apartments_to_rent {cell_agent.apartments_to_rent}")
            logging.info(f"sample {apts_for_rental}")
            logging.info(cell_agent.apartments)
            for idx in apts_for_rental:  # Check all empty apartments in this cell
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - ((candidate_apartment.bills + candidate_apartment.rent) / self.income)) * candidate_apartment.freshness
                candidate_happiness = log(temp) + 1 if temp > 0 else 0
                if candidate_happiness > best_happiness and candidate_apartment.full_cost() < self.income:
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

            k = int(round(len(cell_agent.apartments_to_sell) * 0.8))
            apts_for_sell = random.sample(list(cell_agent.apartments_to_sell), k)

            for idx in apts_for_sell:  # Check all empty apartments in this cell
                candidate_apartment = cell_agent.apartments[idx]

                temp = (1 - (candidate_apartment.bills / self.income)) * candidate_apartment.freshness + 0.2
                candidate_happiness = log(temp) + 1 if temp > 0 else 0
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

            k_rental = int(round(len(cell_agent.apartments_to_rent) * 0.8))
            apts_for_rental = random.sample(list(cell_agent.apartments_to_rent), k_rental)
            k_sale = int(round(len(cell_agent.apartments_to_sell) * 0.8))
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

                temp = (1 - (candidate_apartment.bills / self.income)) * candidate_apartment.freshness + 0.2
                candidate_happiness = log(temp) + 1 if temp > 0 else 0

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
        income_change = np.random.normal(loc=0.00075, scale=0.002)
        self.income *= (1 + income_change)

        if not self.rented_apartment and not self.owned_apartment:
            self.find_apt_to_rent()

        elif self.rented_apartment:
            self.time_apt_rented += 1
            if (self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD and random.random() > self.happiness_factor) or self.time_apt_rented > 24:
                self.find_apt_to_rent_or_buy()

            elif self.rented_apartment.full_cost() > self.income * 1.2:
                self.assign_apartment(None, False)
                logging.info(f"🏚️ Resident {self.unique_id} at {self.pos} moved out because of high rent cost")
                self.find_apt_to_rent()
            else:
                self.update_happiness()
        
        elif self.owned_apartment:
            self.time_apt_owned += 1
            self.update_happiness()

            if self.time_apt_owned > 24:
                self.assign_apartment(None, False)
                logging.info(f"🏚️ Resident {self.unique_id} at {self.pos} moved out because of long ownership. New agent takes his place")
                self.income *= np.random.normal(loc=1.0, scale=0.05)
                self.find_apt_to_rent()
