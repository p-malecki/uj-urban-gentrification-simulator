import logging
from mesa import Agent
import random
from math import log

import numpy as np
from model_elements.constants import *

class ResidentAgent(Agent):
    def __init__(self, model, income, searching_radius=2):
        super().__init__(model)
        self.income = income * 0.6  # assume residents spend 50% of income on housing

        self.rented_apartment = None
        self.time_apt_rented = 0
        self.owned_apartment = None
        self.time_apt_owned = 0

        self.base_searching_radius = searching_radius
        self.searching_radius = searching_radius

        self.happiness_factor = 0

    def __repr__(self):
        return f"Resident(unique_id={self.unique_id}, income={self.income}, happiness_factor={self.happiness_factor}, status = {'rented' if self.rented_apartment else 'owned' if self.owned_apartment else 'homeless'})"

    def assign_apartment(self, apartment, owned):
        #Selling the house
        if self.owned_apartment:
                cell = self.model.cell_agents_layer.data[self.owned_apartment.position]
                # Usuń apartament ze wszystkich list w komórce
                cell.apartments.remove(self.owned_apartment)
                # if self.owned_apartment in cell.apartments_to_sell:
                #     cell.apartments_to_sell.remove(self.owned_apartment)
                # if self.owned_apartment in cell.apartments_to_rent:
                #     cell.apartments_to_rent.remove(self.owned_apartment)
                self.owned_apartment.owner = None
                self.owned_apartment.deleted = True
                self.owned_apartment.occupied = False
                self.owned_apartment.tenant = None

        #Moving out from rented apartment
        if self.rented_apartment:
            self.rented_apartment.tenant = None
            self.rented_apartment.occupied = False
            self.rented_apartment.time_at_market = 0
            self.rented_apartment.time_rented = 0
            try:
                self.rented_apartment.owner.tenant_moved_out(self.rented_apartment) # notify landlord
            except:
                logging.info(f"Error: Apartment {self.rented_apartment} at {self.rented_apartment.position} could not notify landlord about tenant move out.")
                logging.info(f"Apartment.deleted = {self.rented_apartment.deleted}, Apartment.occupied = {self.rented_apartment.occupied}, Apartment.owner = {self.rented_apartment.owner}, Apartment.tenant = {self.rented_apartment.tenant}, Apartment.time_at_market = {self.rented_apartment.time_at_market}, Apartment.time_rented = {self.rented_apartment.time_rented}")

        self.rented_apartment = None
        self.time_apt_rented = 0
        self.owned_apartment = None
        self.time_apt_owned = 0
        self.happiness_factor = -1
            
        """Move resident into an apartment."""
        if apartment:
            if owned:
                # if apartment.owner:
                #     try:
                apartment.owner.sell_house(apartment)
                    # except:
                    #     logging.info(f"Error: Apartment {apartment} at {apartment.position} could not be sold to Resident {self.unique_id}.")
                    #     logging.info(f"Apartment.deleted = {apartment.deleted}, Apartment.occupied = {apartment.occupied}, Apartment.owner = {apartment.owner}, Apartment.tenant = {apartment.tenant}, Apartment.time_at_market = {apartment.time_at_market}, Apartment.time_rented = {apartment.time_rented}")
                self.owned_apartment = apartment
                apartment.occupied = True
                apartment.time_at_market = 0
                apartment.time_rented = 0
                apartment.owner = self
            else:
                # if apartment.owner:
                #     try:
                apartment.owner.rent_house(apartment)
                    # except:
                    #     logging.info(f"Error: Apartment {apartment} at {apartment.position} could not be rented by Resident {self.unique_id}.")
                    #     logging.info(f"Apartment.deleted = {apartment.deleted}, Apartment.occupied = {apartment.occupied}, Apartment.owner = {apartment.owner}, Apartment.tenant = {apartment.tenant}, Apartment.time_at_market = {apartment.time_at_market}, Apartment.time_rented = {apartment.time_rented}")  
                self.rented_apartment = apartment
                apartment.occupied = True
                apartment.tenant = self

        self.update_happiness()

    def update_happiness(self):
        """
        happiness = log((1-(income / local rent)) * apr.freshness) + 1
        additionally if resident owns the apartment, happiness is boosted to log((1-(income / local rent)) * apr.freshness + 0.2) + 1
        """
        if self.rented_apartment:
            temp = (1 - ((self.rented_apartment.full_cost()) / self.income)) * self.rented_apartment.freshness
            self.happiness_factor = max(log(temp) + 1 if temp > 0 else 0, 0)
            return
        
        if self.owned_apartment:
            # temp = (1 - (self.owned_apartment.full_cost() / self.income)) * self.owned_apartment.freshness + 0.2
            # self.happiness_factor = log(temp) + 1 if temp > 0 else 0
            self.happiness_factor = 1
            return
        
        self.happiness_factor = -1

    def find_apt_to_rent(self):
        x,y = self.pos

        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=True,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = float('-inf')

        for nx, ny in neighborhood:
            cell_agent = self.model.cell_agents_layer.data[nx, ny]

            apts_for_rental = cell_agent.apartments_to_rent

            for candidate_apartment in apts_for_rental:
                if random.random() < 0.2:
                    continue

                partial_happiness = (1 - ((candidate_apartment.full_cost()) / self.income)) * candidate_apartment.freshness
                # candidate_happiness = log(temp) + 1 if temp > 0 else 0
                if partial_happiness > best_happiness and candidate_apartment.full_cost() < self.income: #and isinstance(candidate_apartment.owner, LandlordAgent):
                    best_apartment = (candidate_apartment, False)
                    best_happiness = partial_happiness

        if best_apartment and best_happiness > self.happiness_factor: #and best_happiness >= 0 and log(best_happiness) + 1 > self.happiness_factor:
            # logging.info(f"Resident {self.unique_id} found a new apartment at {best_apartment[0].position} with expected happiness {log(best_happiness) + 1:.2f} (current happiness {self.happiness_factor:.2f}).")
            self.assign_apartment(*best_apartment)
            self.searching_radius = self.base_searching_radius
            # logging.info(
            #     f"✅ Resident {self.unique_id} FOUND a new home. Moving from {x, y} to {best_apartment[0].position} (happiness {self.happiness_factor:.2f})."
            # )
        else:
            self.searching_radius += 1
            # logging.info(
            #     f"❌ Resident {self.unique_id} at {x, y} has not moved. No better options found."
            # )
            # logging.info(
            #     f"Current happiness: {self.happiness_factor:.2f}, Best found happiness: {best_happiness}, Searching radius: {self.searching_radius}, income: {self.income:.2f}"
            # )
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
        best_rental_apartment = None
        best_purchase_apartment = None
        best_rental_happiness = float('-inf')
        best_purchase_happiness = float('-inf')

        for nx, ny in neighborhood:
            if random.random() < 0.1:
                continue

            cell_agent = self.model.cell_agents_layer.data[nx, ny]

            apts_for_rental = cell_agent.apartments_to_rent
            apts_for_sale = cell_agent.apartments_to_sell

            for candidate_apartment in apts_for_rental:
                if random.random() < 0.2:
                    continue
                
                if candidate_apartment.full_cost() > self.income:
                    continue

                temp = (1 - ((candidate_apartment.full_cost()) / self.income)) * candidate_apartment.freshness
                # candidate_happiness = max(log(temp) + 1 if temp > 0 else 0, 0)
                if temp > best_rental_happiness:
                    best_rental_apartment = candidate_apartment
                    best_rental_happiness = temp

            for candidate_apartment in apts_for_sale:
                if random.random() < 0.2:
                    continue
                if self.income < candidate_apartment.price * MORTGAGE_MONTHLY_FACTOR:
                    continue

                temp = (1 - (candidate_apartment.bills / self.income)) * candidate_apartment.freshness
                # candidate_happiness = max(log(temp) + 1 if temp > 0 else 0, 0)

                if temp > best_purchase_happiness:
                    best_purchase_apartment = candidate_apartment
                    best_purchase_happiness = temp

        candidate_rental_happiness = max(log(best_rental_happiness) + 1 if best_rental_happiness > 0 else 0, 0)
        candidate_purchase_happiness = max(log(best_purchase_happiness) + 1 if best_purchase_happiness > 0 else 0, 0)

        if candidate_purchase_happiness >= candidate_rental_happiness and best_purchase_apartment:
            best_apartment = (best_purchase_apartment, True)
            best_happiness = best_purchase_happiness
        elif best_rental_apartment:
            best_apartment = (best_rental_apartment, False)
            best_happiness = best_rental_happiness

        if best_apartment and best_happiness > self.happiness_factor: #and best_happiness >= 0 and log(best_happiness) + 1 > self.happiness_factor:
            # logging.info(f"Resident {self.unique_id} found a new apartment at {best_apartment[0].position} with expected happiness {log(best_happiness) + 1:.2f} (current happiness {self.happiness_factor:.2f}).")
            self.assign_apartment(*best_apartment)
            self.searching_radius = self.base_searching_radius
            # logging.info(
            #     f"✅ Resident {self.unique_id} FOUND a new home. Moving from {x, y} to {best_apartment[0].position} (happiness {self.happiness_factor:.2f})."
            # )
        else:
            # self.searching_radius += 1
            # logging.info(
            #     f"❌ Resident {self.unique_id} at {x, y} has not moved. No better options found."
            # )
            # logging.info(
            #     f"Current happiness: {self.happiness_factor:.2f}, Best found happiness: {best_happiness}, Searching radius: {self.searching_radius}, income: {self.income:.2f}"
            # )
            self.update_happiness()

    def step(self, step, avg_rent, avg_price):
        if step % 12 == 0:
            pass
            # income_change = np.random.normal(loc=0.03, scale=0.02)
            # self.income *= (1 + income_change)

        if not self.rented_apartment and not self.owned_apartment and (self.income > avg_rent * 0.8 or self.income > avg_price * MORTGAGE_MONTHLY_FACTOR * 0.8 or random.random() < 0.1):
            self.find_apt_to_rent_or_buy()

        elif self.rented_apartment:
            self.time_apt_rented += 1
            if (self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD and random.random() > self.happiness_factor and self.time_apt_rented > 6) or self.time_apt_rented > 12:
                self.find_apt_to_rent_or_buy()

            elif self.rented_apartment.full_cost() > self.income * 1.2:
                self.assign_apartment(None, False)
                # logging.info(f"🏚️ Resident {self.unique_id} at {self.pos} moved out because of high rent cost")
                self.find_apt_to_rent_or_buy()
            else:
                self.update_happiness()
        
        elif self.owned_apartment:
            self.time_apt_owned += 1
            self.update_happiness()

            if self.time_apt_owned > 60:
                self.assign_apartment(None, False)
                # logging.info(f"🏚️ Resident {self.unique_id} at {self.pos} moved out because of long ownership. New agent takes his place")

