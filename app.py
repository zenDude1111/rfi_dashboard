from datetime import date, timedelta
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc

# Modularized layout imports
from pages import plots_page

# Create Dash application instance with external stylesheets for theming
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

def layout_main_page():
    return html.Div([
    ], className='mt-3')

app.layout = html.Div([
    dcc.Location(id='main-url', refresh=False),
    html.Div(id='main-page-content'),
])

@app.callback(
    Output('main-page-content', 'children'),
    [Input('main-url', 'pathname')]
)
def display_page(pathname):
    return plots_page.layout

if __name__ == '__main__':
    app.run_server(debug=True)
