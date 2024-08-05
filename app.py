from datetime import date, timedelta
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc

# Modularized layout imports
from pages import plots_page, daily_metric_plots

# Create Dash application instance with external stylesheets for theming
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

'''def create_navbar():
    """Creates and returns the navigation bar component."""
    return dbc.NavbarSimple(
        children=[
            #dbc.NavItem(dbc.NavLink("Contours", href="/contour_all")),
            #dbc.NavItem(dbc.NavLink("Daily Metrics", href="/daily_metrics")),
        ],
        brand="South Pole RFI Dashboard",
        brand_href="/",
        color="secondary",
        dark=True,
    )'''

def layout_main_page():
    return html.Div([
    ], className='mt-3')

app.layout = html.Div([
    dcc.Location(id='main-url', refresh=False),
    #create_navbar(),
    html.Div(id='main-page-content'),
])

@app.callback(
    Output('main-page-content', 'children'),
    [Input('main-url', 'pathname')]
)
def display_page(pathname):
    #if pathname == '/daily_metrics':
        #return daily_metric_plots.layout
    #elif pathname == '/contour_all' or pathname == '/':
        #return plots_page.layout
    return plots_page.layout

if __name__ == '__main__':
    app.run_server(debug=True)
