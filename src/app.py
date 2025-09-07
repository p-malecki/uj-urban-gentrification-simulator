import mesa
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
            "marker": "^",
            "color": "purple",
            "markersize": 15,
        }
    elif isinstance(agent, resident_agent):
        return {
            "marker": "o",
            "color": "yellow" if agent.status != "displaced" else "red",
            "markersize": 8,
        }
    elif isinstance(agent, cell_agent):
        return {
            "marker": "s",
            "color": "lightblue" if not agent.is_upgraded else "lightgreen",
            "markersize": 30,
        }
    # A fallback for any unexpected agent types
    return {"marker": "x", "color": "magenta", "markersize": 5}


model_params = {
    "grid_size": 10,
    "num_residents": 50,
    "num_developers": 5,
    "residents_income": [4242, 4242, 4500, 5080, 5680, 6427, 7365, 8567, 10409, 14224],
}


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
    model_instance,
    components=[
        renderer,
        lineplot_component,
    ],
    name="Urban Growth and Gentrification Model",
)
# This is required for Solara to render the page
page
