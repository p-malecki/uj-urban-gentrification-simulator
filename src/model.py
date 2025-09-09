import logging
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from mesa.visualization import Slider
import random
import numpy as np
from typing import Tuple

from agents import cell_agent, resident_agent, developer_agent

# --- SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Apartment:
    def __init__(
        self, position: Tuple[int, int], index: int, rent: float, occupied: bool = False
    ):
        self.position = position
        self.index = index
        # self.value = value # ! compute rent based on value
        self.rent = rent
        self.occupied = occupied

    def __repr__(self):
        return f"Apartment(pos={self.position}, index={self.index}, rent={self.rent}, occupied={self.occupied})"

    def __eq__(self, other):
        return self.rent == other.rent

    def __lt__(self, other):
        return self.rent < other.rent


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
        self.apartments_layer = PropertyLayer(
            "apartments",
            self.grid_size,
            self.grid_size,
            default_value=None,
            dtype=object,
        )
        self.empty_apartments_layer = PropertyLayer(
            "empty_apartments",
            self.grid_size,
            self.grid_size,
            default_value=None,
            dtype=object,
        )
        self.rent_layer = PropertyLayer(
            "rent",
            self.grid_size,
            self.grid_size,
            default_value=1000.0,
            dtype=np.float64,
        )

        self._initialize_apartments()

        self._create_cell_agents()
        self._create_resident_agents()
        # self._create_developer_agents() # TODO: add developer agents

        self._assign_initial_apartments_to_residents()

        # --- Data Collector ---
        self.datacollector = DataCollector(
            model_reporters={
                "AveragePropertyValue": self.avg_property_value,
                "DisplacedResidents": self.displaced_residents,
            },
        )

    def _create_cell_agents(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                distance_to_center = (
                    (x - self.grid_size / 2) ** 2 + (y - self.grid_size / 2) ** 2
                ) ** 0.5
                location_factor = 1 / (distance_to_center + 1)
                # Property value is computed based on summarized value of its apartments
                # property_value = (
                #     random.uniform(50, 150) * location_factor
                # ) # prev

                apartments_count = len(self.apartments_layer.data[x, y])
                property_value = sum(a.rent for a in self.apartments_layer.data[x, y])
                # ! TODO: take under account location_factor

                logging.info(
                    "📊 Cell Report (x=%d, y=%d)\n"
                    "  • Distance to center : %.2f\n"
                    "  • Location factor    : %.2f\n"
                    "  • Property value     : %.2f\n"
                    "  • Apartments count   : %d\n"
                    "  • Avg rent           : %.2f\n"
                    "  • Max rent           : %.2f\n"
                    "  • Min rent           : %.2f",
                    x,
                    y,
                    distance_to_center,
                    location_factor,
                    property_value,
                    apartments_count,
                    property_value / apartments_count if apartments_count > 0 else 0,
                    max(apt.rent for apt in self.apartments_layer.data[x, y]),
                    min(apt.rent for apt in self.apartments_layer.data[x, y]),
                )

                cell = cell_agent(self, property_value, location_factor)
                self.grid.place_agent(cell, (x, y))

    def _create_resident_agents(self):
        for _ in range(self.num_residents):
            income = random.choice(self.residents_income)
            resident = resident_agent(self, income)
            x, y = self.random.randrange(self.grid_size), self.random.randrange(
                self.grid_size
            )
            self.grid.place_agent(resident, (x, y))

    def _create_developer_agents(self):
        for _ in range(self.num_developers):
            developer = developer_agent(self)
            x, y = self.random.randrange(self.grid_size), self.random.randrange(
                self.grid_size
            )
            self.grid.place_agent(developer, (x, y))

    def _initialize_apartments(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                num_apts = np.random.randint(
                    1, 5
                )  # TODO select different max apartments number based on the cell type
                apartments = [
                    Apartment(
                        position=(x, y),
                        index=i,
                        rent=np.random.randint(
                            2000, 10000
                        ),  # TODO: adjust rents ranges based on the cell type, use different distribution than uniform
                        occupied=False,
                    )
                    for i in range(num_apts)
                ]
                self.apartments_layer.set_cell((x, y), apartments)
                self.empty_apartments_layer.set_cell(
                    (x, y), set(range(len(apartments)))
                )
                if apartments:
                    self.rent_layer.set_cell(
                        (x, y), np.mean([apt.rent for apt in apartments])
                    )
                else:
                    # The cell type is not residential
                    self.rent_layer.set_cell((x, y), 0)

    def _assign_initial_apartments_to_residents(self):
        logging.info("Assigning initial apartments...")
        residents = self.agents_by_type[resident_agent]
        for resident in residents:
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

    def get_property_value_range(self):
        cells = self.agents_by_type.get(cell_agent, [])
        min_val = min(a.property_value for a in cells)
        max_val = max(a.property_value for a in cells)
        return min_val, max_val

    def avg_property_value(self):
        cells = self.agents_by_type.get(cell_agent, [])
        if not cells:
            return 0
        return sum([c.property_value for c in cells]) / len(cells)

    def displaced_residents(self):
        residents = self.agents_by_type.get(resident_agent, [])
        return sum([1 for r in residents if not r.is_settled])

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
        self.agents.shuffle().do("step")

        self.datacollector.collect(self)
