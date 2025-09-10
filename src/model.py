import logging
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from mesa.visualization import Slider
import random
import numpy as np

from model_elements.cell_agent import cell_agent
from model_elements.resident_agent import resident_agent
from model_elements.developer_agent import developer_agent
from model_elements.apartment import Apartment
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
        grid_size=10,
        num_residents=50,
        num_developers=5,
        residents_income=None,
        grid_density=None,
        cells_rents=None,
    ):
        super().__init__()
        self.step_count = 0
        self.grid_size = grid_size.value if isinstance(grid_size, Slider) else grid_size
        self.num_residents = (
            num_residents.value if isinstance(num_residents, Slider) else num_residents
        )
        self.num_developers = (
            num_developers.value
            if isinstance(num_developers, Slider)
            else num_developers
        )

        self.residents_income = (
            residents_income if residents_income is not None else [10000, 20000, 30000]
        )

        self.grid = MultiGrid(self.grid_size, self.grid_size, torus=False)

        logging.info(
            f"Initializing GentrificationModel with {num_residents} residents and {num_developers} developers."
        )

        # --- Property layers ---
        self.cell_agents_layer = PropertyLayer(
            "cell_agents",
            self.grid_size,
            self.grid_size,
            default_value=None,
            dtype=cell_agent,
        )
        self._create_cell_agents()

        self._initialize_apartments()

        self._create_resident_agents()
        # self._create_developer_agents() # TODO: add developer agents

        # --- Data Collector ---
        self.datacollector = DataCollector(
             model_reporters={
            #     # Economic
            #     "AveragePropertyValue": lambda m: np.mean(
            #         [a.property_value for a in m.agents_by_type.get(cell_agent, [])]
            #     ),
            #     "AverageRent": lambda m: np.mean(m.rent_layer.data),
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
                        for a in m.agents_by_type.get(resident_agent, [])
                    ]
                ),
                "HomelessnessRate": lambda m: sum(1 for a in m.agents_by_type.get(resident_agent, []) if a.apartment is None)
                    / m.num_residents,
                "HouseOwnershipRate": lambda m: sum(1 for a in m.agents_by_type.get(resident_agent, []) if a.apt_owned)
                    / m.num_residents,
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
                distance_to_center = (
                    (x - self.grid_size / 2) ** 2 + (y - self.grid_size / 2) ** 2
                ) ** 0.5
                location_factor = 1 / (distance_to_center + 1)

                apartments_count = 0 #TODO len(self.apartments_layer.data[x, y])
                property_value = 0 #TODO sum(a.rent for a in self.apartments_layer.data[x, y])
                # ! TODO: take under account location_factor

                logging.info(
                    "📊 Cell Report (x=%d, y=%d)\n"
                    "  • Distance to center : %.2f\n"
                    "  • Location factor    : %.2f\n"
                    "  • Property value     : %.2f\n"
                    "  • Apartments count   : %d\n"
                    "  • Avg rent           : %.2f\n",
                    x,
                    y,
                    distance_to_center,
                    location_factor,
                    property_value,
                    apartments_count,
                    property_value / apartments_count if apartments_count > 0 else 0,
                )

                bills = np.random.normal(loc=1000.0, scale=100.0)
                cell = cell_agent(self, property_value, location_factor, bills, (x, y))
                self.cell_agents_layer.set_cell((x, y), cell)

    def _create_resident_agents(self):
        av_apt_to_buy = set((x,y) for x in range(self.grid_size) for y in range(self.grid_size) if self.cell_agents_layer.data[x,y].apartments_to_buy)
        
        for _ in range(self.num_residents):
            income = random.choice(self.residents_income)
            
            # if random.random() < 0.3: # 30% chance to start with an owned apartment
            #     x, y = random.choice(list(av_apt_to_buy))
            #     apt_index = self.cell_agents_layer.data[x, y].apartments_to_buy.pop()
            #     apartment = self.cell_agents_layer.data[x, y].apartments[apt_index]
            #     resident = resident_agent(self, income, apartment)
            #     if not self.cell_agents_layer.data[x, y].apartments_to_buy:
            #         av_apt_to_buy.remove((x,y))
            # else:
            x, y = random.randrange(self.grid_size), random.randrange(self.grid_size)
            resident = resident_agent(self, income, None)

            self.grid.place_agent(resident, (x, y))

    def _create_developer_agents(self):
        for _ in range(self.num_developers):
            developer = developer_agent(self)
            x, y = self.random.randrange(self.grid_size), self.random.randrange(
                self.grid_size
            )
            self.grid.place_agent(developer, (x, y))

    def _initialize_apartments(self):
        for cell in self.cell_agents_layer.data.flatten():
            num_apts = 5 # TODO select different max apartments number based on the cell type

            apartments = [
                Apartment(
                    position=(cell.position[0], cell.position[1]),
                    index=i,
                    bills=cell.bills,
                    rent=random.randint(1000, 3000), #TODO change that
                    occupied=False,
                )
                for i in range(num_apts)
            ]

            cell.apartments = apartments
            cell.apartments_to_buy = set() #TODO
            cell.apartments_to_rent = set(range(len(apartments)))

    def _assign_initial_apartments_to_residents(self):
        logging.info("Assigning initial apartments...")

        residents = self.agents_by_type[resident_agent]
        unassigned_residents = []
        for resident in residents:
            if self.empty_apartments_layer.data[resident.pos[0], resident.pos[1]]:
                apt_index = self.empty_apartments_layer.data[resident.pos[0], resident.pos[1]].pop()
                apartment = self.apartments_layer.data[resident.pos[0], resident.pos[1]][apt_index]
                resident.assign_apartment(apartment)
            else:
                unassigned_residents.append(resident)
        
        for resident in unassigned_residents:
            assigned = False
            attempts = 0
            while not assigned and attempts < self.grid_size**2:
                x, y = self.random.randrange(self.grid_size), self.random.randrange(
                    self.grid_size
                )
                empty_ids = self.empty_apartments_layer.data[x, y]
                if empty_ids:
                    apt_index = empty_ids.pop()
                    apartment = self.apartments_layer.data[x, y][apt_index]
                    resident.assign_apartment(
                        apartment
                    )  # ! ASSING RESIDENTS BASED ON THEIR INCOME AND RENT (HAPPINESS_FACTOR)
                    self.grid.move_agent(resident, (x, y))
                    assigned = True
            if not assigned:
                logging.warning(
                    f"Could not assign an initial apartment for resident {resident.unique_id}"
                )
                resident.is_settled = False
        logging.info("Initial assignment complete.")

    def get_cell_occupancy(self, cell_agent):
        pos = cell_agent.pos
        total_capacity = len(self.apartments_layer.data[pos[0], pos[1]])
        num_empty = len(self.empty_apartments_layer.data[pos[0], pos[1]])
        num_occupied = total_capacity - num_empty
        return num_occupied, total_capacity

    def get_cell_contents(self, pos):
        return self.grid.get_cell_list_contents([pos])

    def get_property_value_range(self):
        cells = self.agents_by_type.get(cell_agent, [])
        min_val = min(a.property_value for a in cells)
        max_val = max(a.property_value for a in cells)
        return min_val, max_val

    def step(self):
        self.step_count += 1
        logging.info(f"--- Step {self.step_count} ---")

        # TODO: Adjust rents
        # for x in range(self.grid_size):
        #     for y in range(self.grid_size):
        #         current_rent = self.rent_layer.data[x, y]
        #         adjustment_factor = 1 + self.random.normalvariate(0, 0.05)
        #         new_rent = max(1, current_rent * adjustment_factor)
        #         self.rent_layer.set_cell((x, y), new_rent)

        # Activate agents
        # Execute cell agents' steps once, before other agents
        for cell in self.cell_agents_layer.data.flatten():
            cell.step()

        # Then activate all other agents (excluding cell agents)
        non_cell_agents = [agent for agent in self.agents if not isinstance(agent, cell_agent)]
        self.random.shuffle(non_cell_agents)
        for agent in non_cell_agents:
            agent.step()

        self.datacollector.collect(self)
