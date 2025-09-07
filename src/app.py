import mesa
from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from agents import cell_agent, resident_agent, developer_agent
from model import GentrificationModel


def agent_portrayal(agent):
    if isinstance(agent, cell_agent):
        return {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": True,
            "Layer": 0,
            "Color": "lightblue" if not agent.is_upgraded else "lightgreen",
            "text": f"{int(agent.property_value)}",
            "text_color": "black",
        }
    elif isinstance(agent, resident_agent):
        return {
            "Shape": "circle",
            "r": 0.3,
            "Filled": True,
            "Layer": 1,
            "Color": "yellow" if agent.status != "displaced" else "red",
        }
    elif isinstance(agent, developer_agent):
        return {
            "Shape": "triangle",
            "r": 0.4,
            "Filled": True,
            "Layer": 2,
            "Color": "purple",
        }


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


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


lineplot_component = make_plot_component(
    {
        "AveragePropertyValue": "tab:orange",
        "DisplacedResidents": "tab:cyan",
    },
    post_process=post_process_lines,
)

model = GentrificationModel()

renderer = make_space_component(
    agent_portrayal=agent_portrayal,
    backend="matplotlib",
)
renderer.post_process = post_process_space

page = SolaraViz(
    model,
    components=[
        renderer,
        lineplot_component,
        CommandConsole,
    ],
    name="Urban Growth and Gentrification Model",
    model_params=model_params,
)
page
