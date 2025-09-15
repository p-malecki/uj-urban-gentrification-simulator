from copy import deepcopy
import pickle
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

from model import GentrificationModel, CellAgent, ResidentAgent, DeveloperAgent, LandlordAgent
import threading


def agent_portrayal(agent):
    """Defines how each agent is drawn, mapping data to visual properties."""
    # if isinstance(agent, DeveloperAgent):
    #     return {
    #         "marker": "x",
    #         "color": to_rgba("purple"),
    #         "markersize": 25,
    #         "linewidth": 2,
    #     }
    # el
    if isinstance(agent, ResidentAgent):
        color = to_rgba("green") if agent.owned_apartment else to_rgba("yellow") if agent.rented_apartment else to_rgba("red")
        return {
            "marker": "o",
            "color": color,
            "markersize": 20,
        }
    elif isinstance(agent, CellAgent):
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
    "num_residents": Slider("Number of Residents", value=2000, min=1000, max=4000, step=250),
    "num_developers": Slider("Number of Developers", value=5, min=2, max=20, step=2),
    "num_landlords": Slider("Number of Landlords", value=50, min=2, max=70, step=2),
    "gov_developer": Slider("Government Developer", value=0, min=0, max=1, step=1),
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

average_sell_price = make_plot_component(
    {"AverageSellPrice": "red"},
    post_process=post_process_lines,
)

economic_plot = make_plot_component(
    {"AverageRent": "red"},
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
    {"HomelessnessRate": "red", "HouseOwnershipRate": "green", "RentRate": "black"},
    post_process=post_process_lines,
)

homeownership_top10_plot = make_plot_component(
    {"HomelessnessTop10Percent": "red", "HouseOwnershipTop10Percent": "green", "RentRateTop10Percent": "black"},
    post_process=post_process_lines,
)

homeownership_bottom10_plot = make_plot_component(
    {"HomelessnessBottom10Percent": "red", "HouseOwnershipBottom10Percent": "green", "RentRateBottom10Percent": "black"},
    post_process=post_process_lines,
)

market_plot = make_plot_component(
    {"HousesToRent": "red", "HousesToSell": "green"},
    post_process=post_process_lines,
)

inequality_plot = make_plot_component(
    {"PropertyValueGini": "magenta"},
    post_process=post_process_lines,
)

developers_capital = make_plot_component(
    {"DeveloperCapital": "purple"},
    post_process=post_process_lines,
)

landlords_capital = make_plot_component(
    {"LandlordCapital": "green"},
    post_process=post_process_lines,
)

landlords_owned_properties = make_plot_component(
    {"LandlordOwnedProperties": "blue"},
    post_process=post_process_lines,   
)

residents_count = make_plot_component(
    {"ResidentsCount": "orange"},
    post_process=post_process_lines,
)


# developer_plot = make_plot_component(
#     {"DeveloperCapitalAM": "green", "DeveloperCapitalBM": "purple"},
#     post_process=post_process_lines,
# )




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

for i in range(6,10):
    model_instance = GentrificationModel(**model_params)

    for _ in range(2500):
        model_instance.step()

    model_instance_gov_intervention = deepcopy(model_instance)
    model_instance_gov_intervention.add_gov_developer()

    model_instance_ad_valorem = deepcopy(model_instance)
    model_instance_ad_valorem.ad_valorem_tax = True

    model_instance_both = deepcopy(model_instance)
    model_instance_both.add_gov_developer()
    model_instance_both.ad_valorem_tax = True

    def run_steps(model, steps):
        for _ in range(steps):
            model.step()

    threads = [
        threading.Thread(target=run_steps, args=(model_instance_gov_intervention, 10000)),
        threading.Thread(target=run_steps, args=(model_instance_ad_valorem, 10000)),
        threading.Thread(target=run_steps, args=(model_instance_both, 10000)),
        threading.Thread(target=run_steps, args=(model_instance, 10000)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    pickle.dump(model_instance_gov_intervention.datacollector.get_model_vars_dataframe(), open(f"results/{i}/results_gov.pkl", "wb"))
    pickle.dump(model_instance.datacollector.get_model_vars_dataframe(), open(f"results/{i}/results_no_gov.pkl", "wb"))
    pickle.dump(model_instance_ad_valorem.datacollector.get_model_vars_dataframe(), open(f"results/{i}/results_ad_valorem.pkl", "wb"))
    pickle.dump(model_instance_both.datacollector.get_model_vars_dataframe(), open(f"results/{i}/results_both.pkl", "wb"))



# page = SolaraViz(
#     model_instance,
#     model_params=model_params,
#     components=[
#         model_description,
#         # renderer,
#         average_sell_price,
#         # AnalysisTabs, // TODO: optionally use tabs
#         economic_plot,
#         # population_plot,
        
#         # stability_plot,
#         homeownership_plot,
#         homeownership_top10_plot,
#         homeownership_bottom10_plot,
#         # developer_plot,
#         market_plot,
#         # inequality_plot,
#         developers_capital,
#         landlords_capital,
#         landlords_owned_properties,
#         residents_count,
#     ],
#     render_interval=5,
#     name="Urban Growth and Gentrification Model",
# )
# page  # This is required for Solara to render the page
