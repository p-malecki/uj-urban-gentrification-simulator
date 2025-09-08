import mesa
import solara
from mesa.visualization import (
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from agents import cell_agent, resident_agent, developer_agent
from model import GentrificationModel


def agent_portrayal(agent):
    if isinstance(agent, developer_agent):
        return {
            "marker": "x",
            "color": "purple",
            "markersize": 15,
        }
    elif isinstance(agent, resident_agent):
        return {
            "marker": "o",
            "color": "yellow" if agent.is_settled else "red",
            "markersize": 8,
        }
    elif isinstance(agent, cell_agent):
        return {
            "marker": "s",
            "color": (
                "lightblue" if not agent.is_upgraded else "lightgreen"
            ),  # TODO: add different cell types that are distinct from residential
            "markersize": 30,
        }
    # A fallback for any unexpected agent types
    return {"marker": "x", "color": "magenta", "markersize": 5}


model_params = {
    "grid_size": 5,
    "num_residents": 10,
    "num_developers": 5,
    "residents_income": [4242, 4242, 4500, 5080, 5680, 6427, 7365, 8567, 10409, 14224],
}


def model_description(model=None):
    solara.Markdown(
        """
        # Urban Growth and Gentrification Model
        This model simulates the dynamics of urban gentrification.
        ## It includes three types of agents:
        - **Residents (Yellow/Red Circles)**: Seek affordable housing based on their income. They may be displaced if rent becomes too high.
        - **Developers (Purple Crosses):** Look for properties with high potential return on investment to upgrade.
        - **Cells (Blue/Green Squares):** Represent parcels of land. Upgraded cells turn green.
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


lineplot_component = make_plot_component(
    {
        "AveragePropertyValue": "tab:orange",
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
    model_instance,  # ! TODO: fix bug: model_params are not used when reset button is pressed
    components=[
        model_description,
        renderer,
        lineplot_component,
    ],
    name="Urban Growth and Gentrification Model",
)
# This is required for Solara to render the page
page
