import logging
from mesa import Agent

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