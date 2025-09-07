from mesa import Agent
import random
import logging

RENT_FACTOR = 0.05
MINIMUM_RESIDENCE_PERIOD = 3
HAPPINESS_FACTOR_THRESHOLD = 1
HAPPINESS_DECAY_RATE = 0.95  # check: 0.98
SEARCHING_RADIUS_INCREASE_RATE = 1.1


class cell_agent(Agent):
    def __init__(self, model, property_value, location_factor):
        super().__init__(model)
        self.model = model
        self.position = None
        self.property_value = (
            property_value  # ! TODO: compute property_value based on apartments value
        )
        # self.rent = property_value * RENT_FACTOR
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
        #     self.rent *= upgrade_factor # ! TODO: increase apartments value
        self.is_upgraded = True
        self.history.append(self.property_value)
        logging.info(
            f"🏠 Cell at {self.position} was upgraded. Property value increased from {old_value:.0f} to {self.property_value:.0f}."
        )

    def step_cell(self):
        # TODO: increase rent once per X months
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
        self.is_settled = False

    def __repr__(self):
        return f"Resident(unique_id={self.unique_id}, income={self.income}, happiness_factor={self.happiness_factor}, time_since_last_move={self.time_since_last_move}, searching_radius={self.searching_radius}, is_settled={self.is_settled}), apartment={self.apartment}"

    def assign_apartment(self, apartment):
        """Move resident into an apartment."""
        self.apartment = apartment
        self.model.grid.move_agent(self, apartment.position)
        apartment.occupied = True
        self.time_since_last_move = 0
        self.is_settled = True

    def update_happiness(self):
        """Happiness = (income / local rent) * (decay_rate ^ time_since_last_move)."""
        if self.apartment is not None:
            x, y = self.apartment.position
            local_rent = self.model.rent_layer.data[x, y]
            base_happiness = self.income / (local_rent + 1e-6)
            time_decay = HAPPINESS_DECAY_RATE**self.time_since_last_move
            self.happiness_factor = base_happiness * time_decay
        else:
            self.happiness_factor = 0

    def move_to_new_apartment(self):
        """Search neighborhood for a better apartment. Expand search radius if not moved recently."""

        # Increase search radius based on how long the resident hasn't moved
        self.searching_radius = max(
            1,
            int(
                self.searching_radius
                * (SEARCHING_RADIUS_INCREASE_RATE**self.time_since_last_move)
            ),
        )

        if self.is_settled and self.apartment:
            x, y = self.apartment.position
        else:
            (x, y) = int(self.model.grid.width / 2), int(
                self.model.grid.height / 2
            )  # TODO: currently resident w/o apt starts search in grid center

        neighborhood = self.model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=False,
            radius=self.searching_radius,
        )

        best_apartment = None
        best_happiness = self.happiness_factor
        logging.debug(
            f"Resident {self.unique_id} at {(x, y)} is searching for a new home (current happiness: {self.happiness_factor:.2f})."
        )

        for nx, ny in neighborhood:
            empty_ids = self.model.empty_apartments_layer.data[nx, ny]
            if not empty_ids:
                continue

            # TODO: check alternative selection option (one random empty apartment per cell)
            # idx = random.choice(
            #     list(empty_ids)
            # )  # Check one random empty apartment in this cell
            for idx in list(empty_ids):  # Check all empty apartments in this cell
                candidate_apartment = self.model.apartments_layer.data[nx, ny][idx]
                candidate_happiness = self.income / (candidate_apartment.rent + 1e-6)
                if (
                    candidate_happiness > best_happiness
                    and candidate_apartment.rent
                    < self.income  # Only consider apartments with rent below the resident's income
                ):
                    best_apartment = candidate_apartment
                    best_happiness = candidate_happiness

        if best_apartment:
            # Leave old apartment
            if self.apartment is not None:
                self.apartment.occupied = False
            # Move into new apartment
            self.assign_apartment(best_apartment)
            logging.info(
                f"✅ Resident {self.unique_id} FOUND better home. Moving from {x, y} to {best_apartment.position} (happiness {self.happiness_factor:.2f} -> {best_happiness:.2f})."
            )
        else:
            logging.info(
                f"❌ Resident {self.unique_id} at {x, y} STAYING. No better options found."
            )

    def step(self):
        """Resident decides whether to stay or move."""
        self.time_since_last_move += 1

        # Move when happiness is below HAPPINESS_FACTOR_THRESHOLD
        if not self.is_settled or (
            self.happiness_factor < HAPPINESS_FACTOR_THRESHOLD
            and self.time_since_last_move > MINIMUM_RESIDENCE_PERIOD
        ):
            self.move_to_new_apartment()

        # Apply happiness decay after each step
        self.update_happiness()
        logging.info(self)


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
