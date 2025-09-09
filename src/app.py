import mesa
import solara
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mesa.visualization import (
    SolaraViz,
    Slider,
    make_space_component,
    make_plot_component,
)

from agents import cell_agent, resident_agent, developer_agent
from model import GentrificationModel


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
        color = to_rgba("yellow") if agent.is_settled else to_rgba("red")
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


avg_property_value_plot = make_plot_component(
    {
        "AveragePropertyValue": "tab:orange",
    },
    post_process=post_process_lines,
)

displaced_residents_plot = make_plot_component(
    {
        "DisplacedResidents": "tab:cyan",
    },
    post_process=post_process_lines,
)

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
        avg_property_value_plot,
        displaced_residents_plot,
    ],
    name="Urban Growth and Gentrification Model",
)
page  # This is required for Solara to render the page
