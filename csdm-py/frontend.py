'''
***********************************************

This'll be where the page layout and running of the app is laid out

UILM.Page will contain a property called state that's a JSON which gets passed to the frontend on every change

Updating that in the frontend will in turn render the new page

***********************************************

THIS IS JUST FOR EXAMPLE - every aspect is up in the air rn

*******************************

import UILM  # "UI elements"
from ./csdm-py import demand_model, ingress, viz

def load_data(files):
    df = ingress(files)
    page.remove_container(id='upload')


def run_model(dfs):
    results = demand_model(dfs)
    page.remove_element(id='run_button')
    return results

def make_graph(results):
    return viz.forecast_graph('png')

page = UILM.Page()

uploaders = {i: UILM.uploader('csv', callback=load_data) for i in range(5)}
uploaders_table = UILM.Table(5, 1, uploaders)
page.add_container(uploaders_table, id='upload')

run_button = UILM.Button(text='Run', id='run_button', callback=run_model)
page.add_element(run_button)

or whatever...
etc...
'''
