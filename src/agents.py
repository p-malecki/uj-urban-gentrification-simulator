from mesa import Agent
import random
import logging

RENT_FACTOR = 0.05
MINIMUM_RESIDENCE_PERIOD = 2
HAPPINESS_FACTOR_THRESHOLD = 0.5


class cell_agent(Agent):
    def __init__(self, model, property_value, location_factor):
        super().__init__(model)
        self.model = model
        self.position = None
        self.property_value = property_value
        self.rent = property_value * RENT_FACTOR
        self.is_upgraded = False
        self.location_factor = location_factor
        self.history = [property_value]

    def upgrade(self, upgrade_factor=1.5, max_rent_increase=None):
        old_value = self.property_value
        self.property_value *= upgrade_factor
        # if max_rent_increase: # TODO: add max rent policy
        #     self.rent = min(
        #         self.rent * upgrade_factor, self.rent * (1 + max_rent_increase)
        #     )
        # else:
        #     self.rent *= upgrade_factor
        self.is_upgraded = True
        self.history.append(self.property_value)
        logging.info(
            f"🏠 Cell at {self.position} was upgraded. Property value increased from {old_value:.0f} to {self.property_value:.0f}."
        )

    def step_cell(self):
        # TODO: increase rent once per X months
        # self.property_value *= 1 + self.model.max_rent_increase
        pass


class resident_agent(Agent):
    def __init__(self, model, income, searching_radius=1):
        super().__init__(model)
        self.income = income
        self.apartment = None
        self.happiness_factor = 0
        self.time_since_last_move = 0
        self.searching_radius = searching_radius
        # self.affordability_threshold = affordability_threshold
        self.status = "resident"

    def assign_apartment(self, apartment):
        """Move resident into an apartment."""
        self.apartment = apartment
        apartment.occupied = True
        self.update_happiness()

    def update_happiness(self):
        """Happiness = income / local rent."""
        if self.apartment is not None:
            x, y = self.apartment.position
            local_rent = self.model.rent_layer.data[x, y]
            self.happiness_factor = self.income / (local_rent + 1e-6)
        else:
            self.happiness_factor = 0

    def step(self):
        """Resident decides whether to stay or move."""
        self.time_since_last_move += 1

        # Move when happiness is too low
        if (
            self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD
            and self.time_since_last_move > MINIMUM_RESIDENCE_PERIOD
        ):
            self.move_to_new_apartment()

    def move_to_new_apartment(self):
        """Search neighborhood for a better apartment."""
        x, y = self.position
        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=False,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = self.happiness_factor
        logging.debug(
            f"Resident {self.unique_id} at {self.position} is searching for a new home (current happiness: {self.happiness_factor:.2f})."
        )

        for nx, ny in neighborhood:
            empty_ids = self.model.empty_apartments_layer.data[nx, ny]
            if not empty_ids:
                continue

            # Check one random empty apartment in this cell
            idx = random.choice(list(empty_ids))
            candidate_apartment = self.model.apartments_layer.data[nx, ny][idx]

            candidate_happiness = self.income / (candidate_apartment.rent + 1e-6)
            if candidate_happiness > best_happiness:
                best_apartment = candidate_apartment
                best_happiness = candidate_happiness

        if best_apartment:
            # Leave old apartment
            if self.apartment is not None:
                self.apartment.occupied = False
            logging.info(
                f"✅ Resident {self.unique_id} FOUND better home. Moving from {x, y} to {best_apartment.position} (happiness {self.happiness_factor:.2f} -> {best_happiness:.2f})."
            )
        else:
            logging.info(
                f"❌ Resident {self.unique_id} at {x, y} STAYING. No better options found."
            )


class developer_agent(Agent):
    def __init__(
        self,
        model,
        roi_threshold=0.2,
        investment_aggressiveness=0.5,
        scan_radius=2,
    ):
        super().__init__(model)
        self.roi_threshold = roi_threshold
        self.investment_aggressiveness = investment_aggressiveness
        self.scan_radius = scan_radius

    def step(self):
        pass
        # Scan neighborhood for cheap properties
        # neighbors = self.model.grid.get_neighborhood(
        #     self.position, moore=True, radius=self.scan_radius
        # )
        # candidate_cells = [
        #     c for c in neighbors if isinstance(c, cell_agent) and not c.is_upgraded
        # ]
        # if not candidate_cells:
        #     return
        # cell = random.choice(candidate_cells)
        # potential_roi = (
        #     cell.property_value * 1.5 - cell.property_value
        # ) / cell.property_value
        # effective_roi_threshold = self.roi_threshold * (
        #     1  # - self.model.tax_incentive_factor
        # )
        # if (
        #     potential_roi >= effective_roi_threshold
        #     and random.random() < self.investment_aggressiveness
        # ):
        #     logging.info(
        #         f"📈 Developer {self.unique_id} is upgrading cell at {cell.position} (Potential ROI: {potential_roi:.2f})."
        #     )
        #     cell.upgrade()
        #     # cell.upgrade(max_rent_increase=self.model.max_rent_increase)
