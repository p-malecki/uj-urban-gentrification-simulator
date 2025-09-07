import logging
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
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
        self.rent = rent
        self.occupied = occupied

    def __repr__(self):
        return f"Apartment(pos={self.position}, index={self.index}, rent={self.rent}, occupied={self.occupied})"


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
        logging.info(
            f"Initializing GentrificationModel with {num_residents} residents and {num_developers} developers."
        )

        self.grid_size = grid_size
        self.num_residents = num_residents
        self.num_developers = num_developers
        self.residents_income = (
            residents_income if residents_income is not None else [10000, 20000, 30000]
        )

        self.grid = MultiGrid(grid_size, grid_size, torus=False)

        # --- Property layers ---
        self.apartments_layer = PropertyLayer(
            "apartments", grid_size, grid_size, default_value=None, dtype=object
        )
        self.empty_apartments_layer = PropertyLayer(
            "empty_apartments", grid_size, grid_size, default_value=None, dtype=object
        )
        self.rent_layer = PropertyLayer(
            "rent", grid_size, grid_size, default_value=1000.0, dtype=np.float64
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
                property_value = random.uniform(50, 150) * location_factor
                logging.info(
                    f"distance_to_center {distance_to_center} location_factor {location_factor} property_value {property_value} "
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
                        rent=np.random.randint(800, 2000),
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
                    resident.assign_apartment(apartment)
                    self.grid.move_agent(resident, (x, y))
                    assigned = True
            if not assigned:
                logging.warning(
                    f"Could not assign an initial apartment for resident {resident.unique_id}"
                )
                resident.status = "displaced"
        logging.info("Initial assignment complete.")

    def avg_property_value(self):
        cells = self.agents_by_type[cell_agent]
        if not cells:
            return 0
        return sum([c.property_value for c in cells]) / len(cells)

    def displaced_residents(self):
        residents = self.agents_by_type[resident_agent]
        return sum([1 for r in residents if r.status == "displaced"])

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
