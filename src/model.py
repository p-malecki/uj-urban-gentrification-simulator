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
from model_elements.apartment import Apartment
import model_elements.constants as constants
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
        residents_income: list[float] = None,
    ):
        super().__init__()
        self.step_count = 0
        self.grid_size = grid_size.value if isinstance(grid_size, Slider) else grid_size
        self.num_residents = (
            num_residents.value if isinstance(num_residents, Slider) else num_residents
        )
        self.num_developers = num_developers.value if isinstance(num_developers, Slider) else num_developers
        self.num_landlords = num_landlords.value if isinstance(num_landlords, Slider) else num_landlords
        # self.num_developers = (
        #     num_developers.value
        #     if isinstance(num_developers, Slider)
        #     else num_developers
        # )
        self.residents_income = (
            residents_income if residents_income is not None else [10000, 20000, 30000]
        )

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

        # --- Data Collector ---
        self.datacollector = DataCollector(
             model_reporters={
            #     # Economic
            #     "AveragePropertyValue": lambda m: np.mean(
            #         [a.property_value for a in m.agents_by_type.get(cell_agent, [])]
            #     ),
                 "AverageRent": lambda m: np.mean(
                        [a.rent for cell_agent in m.agents_by_type.get(CellAgent, []) for a in cell_agent.apartments if isinstance(a.owner, LandlordAgent) and a.occupied]
                ),
                "AverageSellPrice": lambda m: np.mean(
                        [a.price for cell_agent in m.agents_by_type.get(CellAgent, []) for a in cell_agent.apartments if not a.occupied and a.owner and (a in a.owner.apts_to_sell if isinstance(a.owner, LandlordAgent) else True)]
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

    def _create_cell_agents(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                distance_to_center = 0 #(
                #     (x - self.grid_size / 2) ** 2 + (y - self.grid_size / 2) ** 2
                # ) ** 0.5
                location_factor = 0 #1 / (distance_to_center + 1)

                apartments_count = 0 #TODO len(self.apartments_layer.data[x, y])
                property_value = 0 #TODO sum(a.rent for a in self.apartments_layer.data[x, y])
                # ! TODO: take under account location_factor

                # logging.info(
                #     "📊 Cell Report (x=%d, y=%d)\n"
                #     "  • Distance to center : %.2f\n"
                #     "  • Location factor    : %.2f\n"
                #     "  • Property value     : %.2f\n"
                #     "  • Apartments count   : %d\n"
                #     "  • Avg rent           : %.2f\n",
                #     x,
                #     y,
                #     distance_to_center,
                #     location_factor,
                #     property_value,
                #     apartments_count,
                #     property_value / apartments_count if apartments_count > 0 else 0,
                # )

                bills = np.random.normal(loc=1000.0, scale=100.0)
                cell = CellAgent(self, property_value, location_factor, bills, (x, y))
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

    def _initialize_apartments(self):
        for cell in self.cell_agents_layer.data.flatten():
            num_apts = 5 # TODO select different max apartments number based on the cell type

            apartments = [
                Apartment(
                    position=(cell.position[0], cell.position[1]),
                    index=i,
                    price = constants.START_BUY_PRICE * np.random.normal(loc=1.0, scale=0.1),
                    bills=cell.bills
                )
                for i in range(num_apts)
            ]

            avg_house_price = sum(apt.price for apt in apartments) / num_apts

            cell.apartments = apartments
            cell.apartments_to_sell = set(range(len(apartments)))
            cell.apartments_to_rent = set()
            cell.avg_house_price = avg_house_price
        
    def get_cell_occupancy(self, cell_agent):
        pos = cell_agent.pos
        total_capacity = len(self.apartments_layer.data[pos[0], pos[1]])
        num_empty = len(self.empty_apartments_layer.data[pos[0], pos[1]])
        num_occupied = total_capacity - num_empty
        return num_occupied, total_capacity

    def get_cell_contents(self, pos):
        return self.grid.get_cell_list_contents([pos])

    def get_property_value_range(self):
        cells = self.agents_by_type.get(CellAgent, [])
        min_val = min(a.property_value for a in cells)
        max_val = max(a.property_value for a in cells)
        return min_val, max_val

    def step(self):
        self.step_count += 1
        logging.info(f"--- Step {self.step_count} ---")

        # Execute cell agents' steps once, before other agents
        for cell in self.cell_agents_layer.data.flatten():
            cell.step()

        for developer in self.agents_by_type.get(DeveloperAgent, []):
            developer.step(self.step_count)

        landlords = list(self.agents_by_type.get(LandlordAgent, []))
        self.random.shuffle(landlords)
        for landlord in landlords:
            landlord.step()

        residents = list(self.agents_by_type.get(ResidentAgent, []))
        self.random.shuffle(residents)
        for resident in residents:
            resident.step()

        self.datacollector.collect(self)
