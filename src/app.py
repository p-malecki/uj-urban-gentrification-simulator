import mesa
import solara
import solara.lab
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mesa.visualization import (
    SolaraViz,
    Slider,
    make_space_component,
    make_plot_component,
)

from model import GentrificationModel, cell_agent, resident_agent, developer_agent


def agent_portrayal(agent):
    """Defines how each agent is drawn, mapping data to visual properties."""
    if isinstance(agent, developer_agent):
        return {
            "marker": "x",
            "facecolor": to_rgba("none"),
            "edgecolor": to_rgba("purple"),
            "markersize": 20,
            "linewidth": 2,
        }
    elif isinstance(agent, resident_agent):
        color = to_rgba("green") if agent.apartment is not None else to_rgba("red")
        return {
            "marker": "o",
            "color": color,
            "markersize": 20,
        }
    elif isinstance(agent, cell_agent):
        model = agent.model
        occupied, capacity = model.get_cell_occupancy(agent)
        occupancy_ratio = occupied / capacity if capacity > 0 else 0
        markersize = 15 + (30 * occupancy_ratio)
        min_val, max_val = model.get_property_value_range()
        if max_val == min_val:
            normalized_value = 0.5
        else:
            normalized_value = (agent.property_value - min_val) / (max_val - min_val)

        colormap = plt.cm.plasma
        color = colormap(normalized_value)
        if agent.is_upgraded:
            color = to_rgba("lightgreen")
        return {"marker": "s", "color": color, "markersize": markersize}
    return {"marker": "x", "color": to_rgba("black"), "markersize": 5}


model_params = {
    "grid_size": Slider("Grid size", value=10, min=3, max=25, step=1),
    "num_residents": Slider("Number of Residents", value=50, min=10, max=200, step=10),
    "num_developers": Slider("Number of Developers", value=5, min=0, max=20, step=1),
    "residents_income": [4242, 4242, 4500, 5080, 5680, 6427, 7365, 8567, 10409, 14224],
}


def model_description(model=None):
    solara.Markdown(
        """
        # Urban Growth and Gentrification Model
        This model simulates the dynamics of urban gentrification.
        - **Cells (Squares):** Color indicates property value (blue low, yellow high). Size indicates occupancy. Green are upgraded.
        - **Residents (Yellow Circles):** Seek affordable housing.
        - **Developers (Purple Crosses):** Upgrade properties for profit.
        """
    )


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.5, model_params["grid_size"] - 0.5)
    ax.set_ylim(-0.5, model_params["grid_size"] - 0.5)


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))
    ax.set_xlabel("Step")
    ax.set_ylabel("Value")


economic_plot = make_plot_component(
    {"AveragePropertyValue": "orange", "AverageRent": "red"},
    post_process=post_process_lines,
)

population_plot = make_plot_component(
    {"SettledResidents": "green", "DisplacedResidents": "cyan"},
    post_process=post_process_lines,
)

stability_plot = make_plot_component(
    {
        #"AverageTenure": "blue", 
        "AverageHappiness": "lime"},
    post_process=post_process_lines,
)

homeownership_plot = make_plot_component(
    {"HomelessnessRate": "red", "HouseOwnershipRate": "brown"},
    post_process=post_process_lines,
)


market_plot = make_plot_component(
    {"VacancyRate": "gray", "UpgradedProperties": "purple"},
    post_process=post_process_lines,
)

inequality_plot = make_plot_component(
    {"PropertyValueGini": "magenta"},
    post_process=post_process_lines,
)


# @solara.component
# def AnalysisTabs(model=None):
#     with solara.lab.Tabs():
#         with solara.lab.Tab("Economic"):
#             economic_plot(model=model)
#         with solara.lab.Tab("Population"):
#             population_plot(model=model)
#         with solara.lab.Tab("Stability"):
#             stability_plot(model=model)
#         with solara.lab.Tab("Market"):
#             market_plot(model=model)
#         with solara.lab.Tab("Inequality"):
#             inequality_plot(model=model)


renderer = make_space_component(
    agent_portrayal=agent_portrayal,
    backend="matplotlib",
)
renderer.post_process = post_process_space

model_instance = GentrificationModel(**model_params)

page = SolaraViz(
    model_instance,
    model_params=model_params,
    components=[
        model_description,
        renderer,
        # AnalysisTabs, // TODO: optionally use tabs
        # economic_plot,
        # population_plot,
        stability_plot,
        homeownership_plot,
        # market_plot,
        # inequality_plot,
    ],
    name="Urban Growth and Gentrification Model",
)
page  # This is required for Solara to render the page
