import logging
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from mesa.visualization import Slider
import random
import numpy as np

from model_elements.cell_agent import CellAgent
from model_elements.resident_agent import ResidentAgent
from model_elements.developer_agent import DeveloperAgent
from model_elements.landlord_agent import LandlordAgent
from model_elements.gov_developer import GovDeveloper
from model_elements.constants import *
from helpers import gini_coefficient

# --- SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class GentrificationModel(Model):
    def __init__(
        self,
        grid_size: int = 10,
        num_residents: int = 50,
        num_developers: int = 5,
        num_landlords: int = 5,
        gov_developer: int = 0,
        residents_income: list[float] = None,
        ad_valorem_tax: bool = False,
    ):
        super().__init__()
        self.step_count = 0
        self.grid_size = grid_size.value if isinstance(grid_size, Slider) else grid_size
        self.num_residents = num_residents.value if isinstance(num_residents, Slider) else num_residents
        self.num_developers = num_developers.value if isinstance(num_developers, Slider) else num_developers
        self.num_landlords = num_landlords.value if isinstance(num_landlords, Slider) else num_landlords
        self.residents_income = residents_income if residents_income is not None else [10000, 20000, 30000]
        self.ad_valorem_tax = ad_valorem_tax

        self.recent_sell_prices: list[float] = []
        self.recent_rent_prices: list[float] = []
        self.max_recent_prices = 20

        self.grid = MultiGrid(self.grid_size, self.grid_size, torus=False)

        logging.info(
            f"Initializing GentrificationModel with {num_residents} residents and {self.num_developers} developers."
        )

        # --- Property layers ---
        self.cell_agents_layer = PropertyLayer(
            "cell_agents",
            self.grid_size,
            self.grid_size,
            default_value=None,
            dtype=CellAgent,
        )
        self._create_cell_agents()

        self._create_resident_agents()

        self._create_landlord_agents()
        
        self._create_developer_agents()

        if gov_developer:
            self.add_gov_developer()

        # --- Data Collector ---
        self.datacollector = DataCollector(
             model_reporters={
                "AverageRent": lambda m: np.mean(
                        [a.rent for cell_agent in m.cell_agents_layer.data.flatten() for a in cell_agent.apartments if isinstance(a.owner, LandlordAgent) and a.occupied] + [a.rent for cell_agent in m.cell_agents_layer.data.flatten() for a in cell_agent.apartments_to_rent]
                ),
                "AverageSellPrice": lambda m: np.mean(
                        [a.price for cell_agent in m.cell_agents_layer.data.flatten() for a in cell_agent.apartments_to_sell]
                ),  

                "AverageRentProfitMargin": lambda m: np.mean(
                        [landlord.profit_margin for landlord in m.agents_by_type.get(LandlordAgent, [])]
                ), 
                "AverageDeveloperProfitMargin": lambda m: np.mean(
                        [developer.profit_margin for developer in m.agents_by_type.get(DeveloperAgent, [])]
                ),


                
            #     "PropertyValueGini": lambda m: gini_coefficient(
            #         [a.property_value for a in m.agents_by_type.get(cell_agent, [])]
            #     ),
            #     "VacancyRate": lambda m: sum(
            #         len(s) for s in m.empty_apartments_layer.data.flatten()
            #     )
            #     / sum(len(a) for a in m.apartments_layer.data.flatten()),
            #     # Social
            #     "SettledResidents": lambda m: sum(
            #         1 for a in m.agents_by_type.get(resident_agent, []) if a.is_settled
            #     ),
            #     "DisplacedResidents": lambda m: sum(
            #         1
            #         for a in m.agents_by_type.get(resident_agent, [])
            #         if not a.is_settled
            #     ),
                "AverageHappiness": lambda m: np.mean(
                    [
                        a.happiness_factor
                        for a in m.agents_by_type.get(ResidentAgent, [])
                    ]
                ),
                "HomelessnessRate": lambda m: sum(1 for a in m.agents_by_type.get(ResidentAgent, []) if not a.rented_apartment and not a.owned_apartment)
                    / m.num_residents,
                "HouseOwnershipRate": lambda m: sum(1 for a in m.agents_by_type.get(ResidentAgent, []) if a.owned_apartment)
                    / m.num_residents,
                "RentRate": lambda m: np.sum(1 for a in m.agents_by_type.get(ResidentAgent, []) if a.rented_apartment)
                    / m.num_residents,

                "HomelessnessTop10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income, reverse=True)[:max(1, m.num_residents // 10)] if not a.rented_apartment and not a.owned_apartment)/ max(1, m.num_residents // 10),
                "HouseOwnershipTop10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income, reverse=True)[:max(1, m.num_residents // 10)] if a.owned_apartment)/ max(1, m.num_residents // 10),
                "RentRateTop10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income, reverse=True)[:max(1, m.num_residents // 10)] if a.rented_apartment)/ max(1, m.num_residents // 10),

                "HomelessnessBottom10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income)[:max(1, m.num_residents // 10)] if not a.rented_apartment and not a.owned_apartment)/ max(1, m.num_residents // 10),
                "HouseOwnershipBottom10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income)[:max(1, m.num_residents // 10)] if a.owned_apartment)/ max(1, m.num_residents // 10),
                "RentRateBottom10Percent": lambda m: sum(1 for a in sorted(m.agents_by_type.get(ResidentAgent, []), key=lambda x: x.income)[:max(1, m.num_residents // 10)] if a.rented_apartment)/ max(1, m.num_residents // 10),
                
                "HousesToRent": lambda m: sum(len(cell.apartments_to_rent) for cell in self.cell_agents_layer.data.flatten()),
                "HousesToSell": lambda m: sum(len(cell.apartments_to_sell) for cell in self.cell_agents_layer.data.flatten()),
                
                "DeveloperCapital": lambda m: np.mean(
                    [a.capital for a in m.agents_by_type.get(DeveloperAgent, [])]
                ),
                "LandlordCapital": lambda m: np.mean(
                    [a.capital for a in m.agents_by_type.get(LandlordAgent, [])]
                ),
                "LandlordOwnedProperties": lambda m: np.mean(
                    [len(a.owned_properties) for a in m.agents_by_type.get(LandlordAgent, [])]
                ),

                "ResidentsCount": lambda m: len(m.agents_by_type.get(ResidentAgent, [])),

                "AverageIncome": lambda m: np.mean(
                    [a.income for a in m.agents_by_type.get(ResidentAgent, [])]
                ),
                
                # "DeveloperCapitalAM": lambda m: np.mean(
                #     [
                #         a.capital
                #         for a in m.agents_by_type.get(DeveloperAgent, []) if a.flag == 'AM'
                #     ]
                # ),
                # "DeveloperCapitalBM": lambda m: np.mean(
                #     [
                #         a.capital
                #         for a in m.agents_by_type.get(DeveloperAgent, []) if a.flag == 'BM'
                #     ]
                # ),



            #     "AverageTenure": lambda m: np.mean(
            #         [
            #             a.time_since_last_move
            #             for a in m.agents_by_type.get(resident_agent, [])
            #             if a.is_settled
            #         ]
            #     ),
            #     # Development
            #     "UpgradedProperties": lambda m: sum(
            #         1 for a in m.agents_by_type.get(cell_agent, []) if a.is_upgraded
            #     ),
             }
        )

    def add_gov_developer(self):
        gov_dev = GovDeveloper(self)
        self.grid.place_agent(gov_dev, (0, 0))
        self.num_developers += 1
        logging.info(f"🏛️ Government Developer added.")

    def _create_cell_agents(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                bills = np.random.normal(loc=1000.0, scale=100.0)
                cell = CellAgent(self, (x,y), bills)
                self.cell_agents_layer.set_cell((x, y), cell)

    def _create_resident_agents(self):
        for _ in range(self.num_residents):
            income = random.choice(self.residents_income)
            x, y = random.randrange(self.grid_size), random.randrange(self.grid_size)
            resident = ResidentAgent(self, income)

            self.grid.place_agent(resident, (x, y))

    def _create_developer_agents(self):
        for _ in range(self.num_developers):
            developer = DeveloperAgent(self, random.uniform(0.1, 0.3))
            self.grid.place_agent(developer, (0, 0))
            developer.step(0)  # Initial step

    def _create_landlord_agents(self):
        for _ in range(self.num_landlords):
            landlord = LandlordAgent(self, random.uniform(0.1, 0.3))
            self.grid.place_agent(landlord, (0, 0))

    def step(self):
        self.step_count += 1

        # if self.step_count % 10 == 0:
        #     for _ in range(random.randint(1, 3)):#int(self.num_residents + 1 - self.num_residents):
        #         income = random.choice(self.residents_income)
        #         x, y = random.randrange(self.grid_size), random.randrange(self.grid_size)
        #         resident = ResidentAgent(self, income)
        #         self.num_residents += 1

        #         self.grid.place_agent(resident, (x, y))

        for cell in self.cell_agents_layer.data.flatten():
            cell.step(self.step_count)

        for developer in self.agents_by_type.get(DeveloperAgent, []):
            developer.step(self.step_count)

        for gov_dev in self.agents_by_type.get(GovDeveloper, []):
            gov_dev.step(self.step_count)

        landlords = list(self.agents_by_type.get(LandlordAgent, []))
        self.random.shuffle(landlords)
        for landlord in landlords:
            landlord.step()
            
        avg_rent = np.mean([cell.get_avg_rent() for cell in self.cell_agents_layer.data.flatten()])
        avg_price = np.mean([cell.get_avg_cost() for cell in self.cell_agents_layer.data.flatten()])
        residents = list(self.agents_by_type.get(ResidentAgent, []))
        self.random.shuffle(residents)
        for resident in residents:
            resident.step(self.step_count, avg_rent, avg_price)

        self.datacollector.collect(self)

        if len(self.recent_sell_prices) > self.max_recent_prices:
            self.recent_sell_prices = self.recent_sell_prices[-self.max_recent_prices:]
        if len(self.recent_rent_prices) > self.max_recent_prices:
            self.recent_rent_prices = self.recent_rent_prices[-self.max_recent_prices:]

