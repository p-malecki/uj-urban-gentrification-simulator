import logging
import random
from mesa import Agent
import numpy as np

from model_elements.apartment import Apartment
from model_elements.constants import *
from model_elements.gov_developer import GovDeveloper

class LandlordAgent(Agent):
    def __init__(self, model, profit_margin: float):
        super().__init__(model)
        self.profit_margin = profit_margin  # Desired profit margin for investments

        self.owned_properties: list[Apartment] = []
        self.apts_to_rent_count = 0
        self.starting_capital = START_LANDLORDS_CAPITAL * np.random.normal(loc=1.0, scale=0.05)
        self.capital = self.starting_capital

    def calc_roi(self, apartment: Apartment):
        full_buy_cost = apartment.price + ((1 - apartment.freshness) if apartment.freshness < 0.7 else 0) * FULL_HOUSE_RENOVATION_COST * random.uniform(0.8, 1.2)
        avg_rent = np.mean(self.model.recent_rent_prices) if self.model.recent_rent_prices else START_RENT_PRICE
        monthly_rent = avg_rent * (1 + self.profit_margin)
        return full_buy_cost / monthly_rent   # ROI in months

    def buy_property(self):
        cells = random.sample(list(self.model.cell_agents_layer.data.flatten()), DEVELOPER_CELL_LOOKUP_COUNT)
        
        best_offer = None
        best_roi = np.inf

        for cell in cells:
            apts_for_sale = cell.apartments_to_sell

            for apartment in apts_for_sale:
                if apartment.price > self.capital:
                    continue

                roi = self.calc_roi(apartment)
                if roi < best_roi and not isinstance(apartment.owner, GovDeveloper):
                    best_roi = roi
                    best_offer = apartment

        # logging.info(f"Developer {self.unique_id} evaluated {len(cells)} cells and found best ROI: {best_roi:.2f} months.")

        if best_offer:
            apartment = best_offer
            cell = self.model.cell_agents_layer.data[apartment.position]
            cell.apartments_to_rent.append(apartment)


            if apartment.owner:
                apartment.owner.sell_house(apartment)

            full_buy_cost = apartment.price + ((1 - apartment.freshness) if apartment.freshness < 0.7 else 0) * FULL_HOUSE_RENOVATION_COST * random.uniform(0.8, 1.2)
            self.capital -= full_buy_cost

            self.owned_properties.append(apartment)
            apartment.owner = self
            apartment.ocupied = False
            apartment.tenant = None
           
            apartment.reset_freshness()
            avg_rent = np.mean(self.model.recent_rent_prices) if self.model.recent_rent_prices else START_RENT_PRICE
            apartment.rent = avg_rent * (1 + self.profit_margin)
            
            apartment.time_rented = 0   
            apartment.time_at_market = 0
            self.apts_to_rent_count += 1

            # logging.info(f"🏠 Developer {self.unique_id} bought apartment {apartment.index} at {apartment.position}. Remaining capital: {self.capital:.2f}")

    def manage_rental_house(self, apartment: Apartment):
        if apartment.occupied:
            apartment.time_rented += 1
            self.capital += apartment.rent
            #From time to time, increase rent if tenant stayed long enough
            if apartment.time_rented % 12 == 0 and random.random() < 0.5:
                apartment.rent *= np.random.normal(loc=1.05, scale=0.02)
                avg_rent = np.mean(self.model.recent_rent_prices) if self.model.recent_rent_prices else START_RENT_PRICE
                apartment.rent = max(apartment.rent, avg_rent)
        else:
            self.capital -= apartment.bills
            apartment.time_at_market += 1
            # Looking for a new tenant, adjust rent
            # if apartment.time_at_market == 1:
            #     cell = self.model.cell_agents_layer.data[apartment.position]
            #     apartment.rent = apartment.bills * self.profit_margin
            #     if apartment.freshness < 0.5:
            #         self.capital -= FULL_HOUSE_RENOVATION_COST * (1 - apartment.freshness) * random.uniform(0.8, 1.2)
            #         apartment.reset_freshness()
            if apartment.time_at_market > 2:
                # self.profit_margin *= 0.98  # Decrease profit margin if it tooks too long to rent
                apartment.rent = apartment.rent * 0.975  # Reduce rent by 2% if not rented in 3 months

                if apartment.freshness < 0.4:
                    self.capital -= FULL_HOUSE_RENOVATION_COST * (1 - apartment.freshness) * random.uniform(0.8, 1.2)
                    apartment.reset_freshness()

    def rent_house(self, apartment: Apartment):
        apartment.owner = self
        apartment.occupied = True
        cell = self.model.cell_agents_layer.data[apartment.position]
        if apartment in cell.apartments_to_rent:
            cell.apartments_to_rent.remove(apartment)
        else:
            logging.warning(f"⚠️ Apartment {apartment.index} at {apartment.position} was not listed for rent in cell data.")
        apartment.time_rented = 0
        apartment.time_at_market = 0
        self.capital += apartment.rent
        self.apts_to_rent_count -= 1
        self.model.recent_rent_prices.append(apartment.rent)

        # if apartment.time_at_market <= 1:
        #     self.profit_margin *= 1.05
        # elif apartment.time_at_market <= 3:
        #     self.profit_margin *= 1.03

    def tenant_moved_out(self, apartment: Apartment):
        apartment.owner = self
        apartment.occupied = False
        apartment.tenant = None
        apartment.time_at_market = 0
        apartment.time_rented = 0
        self.apts_to_rent_count += 1
        cell = self.model.cell_agents_layer.data[apartment.position]
        if apartment not in cell.apartments_to_rent:
            cell.apartments_to_rent.append(apartment)
        else:
            logging.warning(f"⚠️ Apartment {apartment.index} at {apartment.position} was already listed for rent in cell data.")
        avg_rent = np.mean(self.model.recent_rent_prices) if self.model.recent_rent_prices else START_RENT_PRICE
        apartment.rent = avg_rent * (1 + self.profit_margin)
        # logging.info(f"🏃 Tenant moved out of apartment {apartment.index} at {apartment.position}. Apartment is now available for rent.")

    def step(self):
        if self.capital <= 0 and False:
            logging.info(f"💸 Landlord {self.unique_id} is out of capital and must sell a property.")
            if any(not apt.occupied for apt in self.owned_properties):
                apt = random.choice([apt for apt in self.owned_properties if not apt.occupied])
                cell = self.model.cell_agents_layer.data[apt.position]
                cell.apartments_to_rent.discard(apt.index)
                apt.owner = self
                apt.occupied = False
                apt.time_at_market = 0
                apt.time_rented = 0
                self.owned_properties.remove(apt)
                self.apts_to_sell.append(apt)
                avg_price = np.mean([apt.price for apt in cell.apartments if apt.index in cell.apartments_to_sell]) if cell.apartments_to_sell else HOUSE_BUILD_COST
                cell.apartments_to_sell.add(apt.index)
                apt.price = avg_price * random.uniform(1.05, 1.15)
            elif any(self.owned_properties):
                apt = random.choice(self.owned_properties)
                apt.tenant.assign_apartment(None, False)
                cell = self.model.cell_agents_layer.data[apt.position]
                cell.apartments_to_rent.discard(apt.index)
                apt.owner = self
                apt.occupied = False
                apt.time_at_market = 0
                apt.time_rented = 0
                self.owned_properties.remove(apt)
                self.apts_to_sell.append(apt)
                avg_price = np.mean([apt.price for apt in cell.apartments if apt.index in cell.apartments_to_sell]) if cell.apartments_to_sell else HOUSE_BUILD_COST
                cell.apartments_to_sell.add(apt.index)
                apt.price = avg_price * random.uniform(1.05, 1.15)
            else:
                logging.info(f"💀 Landlord {self.unique_id} went bankrupt and is removed from the simulation.")
                self.remove()
                return

        for house in self.owned_properties:
            self.manage_rental_house(house)

        if self.capital > HOUSE_BUILD_COST and random.random() < 0.7 and self.apts_to_rent_count < 5:
            self.buy_property()

        # logging.info(f"🐛 Landlord {self.unique_id} has capital: {self.capital:.2f} and {len(self.owned_properties) + len(self.apts_to_sell)} properties")
