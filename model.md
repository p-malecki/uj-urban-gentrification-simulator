# `class GentrificationModel(mesa.Model):`
Initialized parameters:
* `grid_size: int` - defines the size of the grid for the simulation (grid_size x grid_size)
* `num_residents: int` - defines the number of agents in the simulation
* `residents_income: list[float]` - defines the income levels of the agents in the simulation. Each element in the list corresponds to income of ```1/len(residents_income)``` of residents. Eg. [10000, 20000, 30000] means 33.3% of agents earn $1000, 33.3% earn $2000, and 33.3% earn $3000.

    For Poland: `[4242, 4242, 4500, 5080, 5680, 6427, 7365, 8567, 10409, 14224]` (GUS, february 2024)
* `grid_density: list[list[int]]/np.ndarray` (choose preferred one) - defines densities of grid cells in the simulation. Each element in the list corresponds to the capacity of the grid cell (num of citizens who can live there)

    not required, defaults to `None`, treated as a `[[num_residents / (grid_size ** 2) * 1.05]*grid_size]*grid_size` (every cell has the same density equal to average density + 5%)
* `cells_rents: list[list[float]]/np.ndarray` (choose preferred one) - defines initial rents of grid cells in the simulation. Each element in the list corresponds to the rent of the grid cell.

    not required, defaults to `None`, treated as a `[[avg(residents_income)]*grid_size]*grid_size` (every cell has the same rent equal to average income of citizens)

### For properties, check `mesa.PropertyLayer` and `mesa.grid.add_property_layer()` in Mesa documentation
For every grid cell I would add properties containing:
* `apartments: list[Apartment]` - defines the list of apartments in the grid cell
* `empty_apartments: Set[int]` - defines the set of empty apartments in the grid cell - every element is an index of the apartment in the `apartments` list
* `rent: float` - defines the rent in the grid cell

# `class Apartment():`
* `location: tuple[int, int]` - defines the location of the apartment on the grid (not needed, but just for the sake of clarity)
* `index: int` - defines the index of the apartment in the grid cell

For the time being, this class doesn't have any reason to exist - every cell could just store a number of empty apartments. But as we would like to expand this idea later (potentially), model's grid can have a property layer storing 

# `class Resident(mesa.Agent):`
* `income: float` - defines the income of the resident
* `apt: Apartment` - apartment the resident lives in (alternatively, `apt` could be type `int`/`list[int]` representing apartment index(es) in the apartments list of the grid)
* <s>`happiness_factor: float` - defines how happy the resident is with their current apartment. Let it be calculated as `income / model.grid[self.pos].rent` for now</s>
* `time_since_last_move: int` - defines how long it has been since the resident last moved (in steps).
* `searching_radius: int` - defines how far the resident is willing to search for a new apartment (in grid cells).

    I wouldn't complicate it more than necessary - let's say that scanning area is a rectangle with width and height equal to `2  * searching_radius + 1`. For example, for `searching_radius = 1` they would search in a 3x3 area with current position in the center (Moore neighborhood, `moore = True` in `grid.get_neighborhood()`). For clarification, check the first photo (chessboard) here: [Wikipedia - Chybyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance).

    Also, I'm not sure if we want to differentiate that parameters between residents. It can default to 1 and later we can adjust that or completely change the approach by moving this parameter to the `GentrificationModel` class - the same for all agents.

# Model logic
* At model initialization assign each resident to a random apartment in the grid and set `time_since_last_move` to `12` - that way most residents will move in the first step and optimize their living conditions.
* At every step of the simulation (before any agent actions), adjust the rent of every cell grid randomly by a percent taken from normal distribution with mean `0` and standard deviation `0.05` ([numpy.random.normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.normal.html)). For example, if normal dist. returns `-0.02`, the new rent would be `rent * (1 - 0.02)`.
* At every step of the simulation, for every resident, increase `time_since_last_move` by 1. Then, calculate probability of moving out given by a formula 
    ```
    probability_of_moving_out = min(0.0075 * (1.5 ** self.time_since_last_move), 0.9)
    ``` 
    This formula gives such (aproximated) probabilities:
   `time_since_last_move` | 1   | 2   | 4   | 6   | 8 | 10 | 11 | 12+
   ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | -------------
    probability | 1% | 2% | 4% | 8% | 20% | 43% | 65% | 90%

    If `random.random() < probability_of_moving_out` then resident looks for a new apartment:
    * Scan grid cells within `searching_radius` to find available apartments (`grid.get_neighborhood()`method might be useful: [docs](https://mesa.readthedocs.io/latest/apis/space.html#mesa.space.SingleGrid.get_neighborhood))
    * For every cell that has available apartments (check length of set containing indexes of `empty_apartments`), calculate happiness factor as `self.income / rent`.
    * Move to the grid cell with the highest happiness factor, or stay if no better option is found. If moving, update resident's apartment index, available apartment indexes in `grid` and reset `time_since_last_move` to `0`. If not moving, dont reset `time_since_last_move`, as it indicates the resident will be even more probable to move in the next step.