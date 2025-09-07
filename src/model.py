from mesa import Agent, Model
from mesa.space import MultiGrid, PropertyLayer
from mesa.datacollection import DataCollector

import random
import numpy as np
from typing import List, Set, Tuple
import logging


from agents import cell_agent, resident_agent, developer_agent


class Apartment:
    _id_counter = 0

    def __init__(self, position: Tuple[int, int], rent: float, occupied: bool = False):
        self.position = position
        self.rent = rent
        self.occupied = occupied

        self.id = f"apt_{position[0]}_{position[1]}_{Apartment._id_counter}"
        Apartment._id_counter += 1

    def __repr__(self):
        return f"Apartment(id={self.id}, pos={self.position}, rent={self.rent}, occupied={self.occupied})"


class GentrificationModel(Model):

    def __init__(
        self,
        grid_size=10,
        num_residents=50,
        num_developers=5,
        residents_income=[10000, 20000, 30000],
        grid_density=None,
        cells_rents=None,
    ):
        super().__init__()
        self.step_count = 0
        self.grid_size = grid_size
        self.num_residents = num_residents
        self.num_developers = num_developers
        self.residents_income = residents_income
        self.grid_density = grid_density
        self.cells_rents = cells_rents

        logging.info(
            f"Initializing GentrificationModel with {num_residents} residents and {num_developers} developers."
        )

        self.grid = MultiGrid(grid_size, grid_size, torus=False)

        # --- Property layers ---

        # Each cell will hold a list of Apartment objects
        self.apartments_layer = PropertyLayer(
            "apartments", grid_size, grid_size, default_value=None, dtype=object
        )

        # Each cell will hold a set of indexes of empty apartments
        self.empty_apartments_layer = PropertyLayer(
            "empty_apartments", grid_size, grid_size, default_value=None, dtype=object
        )

        # Each cell will have a base rent value
        self.rent_layer = PropertyLayer(
            "rent", grid_size, grid_size, default_value=1000.0
        )

        self.grid.add_property_layer(self.apartments_layer)
        self.grid.add_property_layer(self.empty_apartments_layer)
        self.grid.add_property_layer(self.rent_layer)

        # --- Initialize with some random apartments ---
        self._initialize_apartments()

        # Create Cell Agents
        for x in range(grid_size):
            for y in range(grid_size):
                distance_to_center = (
                    (x - grid_size / 2) ** 2 + (y - grid_size / 2) ** 2
                ) ** 0.5
                location_factor = 1 / (distance_to_center + 1)
                property_value = random.uniform(50, 150) * location_factor
                cell = cell_agent(self, property_value, location_factor)
                self.grid.place_agent(cell, (x, y))

        # Create Resident Agents
        for i in range(num_residents):
            income_class = random.choices(["L", "M", "H"], weights=[0.5, 0.3, 0.2])[0]
            income = {"L": 50, "M": 100, "H": 200}[income_class]
            resident = resident_agent(self, income)
            x, y = random.randrange(grid_size), random.randrange(grid_size)
            self.grid.place_agent(resident, (x, y))

        # Create Developer Agents
        for i in range(num_developers):
            developer = developer_agent(self)
            x, y = random.randrange(grid_size), random.randrange(grid_size)
            self.grid.place_agent(developer, (x, y))

        # Data Collector
        self.datacollector = DataCollector(
            model_reporters={
                "AveragePropertyValue": self.avg_property_value,
                "DisplacedResidents": self.displaced_residents,
            },
        )

    def avg_property_value(self):
        cells = [a for a in self.agents if isinstance(a, cell_agent)]
        return sum([c.property_value for c in cells]) / len(cells)

    def displaced_residents(self):
        residents = [a for a in self.agents if isinstance(a, resident_agent)]
        return sum([1 for r in residents if r.status == "displaced"])

    def _initialize_apartments(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                num_apts = np.random.randint(
                    1, 50
                )  # TODO: depending on cell type select range
                apartments = [
                    Apartment(
                        position=(x, y),
                        rent=np.random.randint(800, 2000),
                        occupied=False,
                    )
                    for _ in range(num_apts)
                ]
                self.apartments_layer.set_cell((x, y), apartments)
                self.empty_apartments_layer.set_cell(
                    (x, y), set(range(len(apartments)))
                )
                self.rent_layer.set_cell(
                    (x, y), np.mean([apt.rent for apt in apartments])
                )

    def step(self):
        self.step_count += 1
        logging.info(f"--- Step {self.step_count} ---")

        # 1. Adjust rents
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                current_rent = self.rent_layer.data[x, y]
                adjustment_factor = 1 + self.random.normalvariate(0, 0.05)
                new_rent = max(1, current_rent * adjustment_factor)
                self.rent_layer.set_cell((x, y), new_rent)

        # 2. Activate agents by type in a random order
        self.agents.shuffle().do("step_cell")
        self.agents.shuffle().do("step_resident")
        self.agents.shuffle().do("step_developer")

        # 3. Collect data
        self.datacollector.collect(self)
