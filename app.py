from dash import Dash, dcc, html, Input, Output, dash_table, callback_context
import dash_bootstrap_components as dbc
from datetime import date
import pandas as pd
import os 
import requests
from io import StringIO

# Import the layout from the pages module
from pages import rfi_explorer

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Main", href="/")),
        dbc.NavItem(dbc.NavLink("RFI Explorer", href="/rfi_explorer")),
    ],
    brand="RFI Dashboard",
    brand_href="/",
    color="secondary",
    dark=True,
)

# Initial setup for DataTable to ensure it exists before data is loaded
initial_df = pd.DataFrame()
data_table = dash_table.DataTable(
    id='rfi-data-table',
    columns=[{"name": i, "id": i} for i in initial_df.columns],
    data=initial_df.to_dict('records'),
    style_cell={'textAlign': 'left', 'padding': '5px'},
    style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        'fontWeight': 'bold'
    },
    style_data={
        'backgroundColor': 'rgb(50, 50, 50)',
        'color': 'white'
    },
    style_table={'overflowX': 'auto'}
)

# Define the main page layout
def main_page_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.P('Select a date for RFI data:'),
                dcc.DatePickerSingle(
                    id='rfi-date-picker',
                    min_date_allowed=date(1995, 8, 5),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    date=date.today()
                ),
            ], width=12, lg=3),
            dbc.Col([
                dcc.Tabs(id="image-tabs", value='tab-1', children=[
                    dcc.Tab(label='Signal Hound 1', value='tab-1'),
                    dcc.Tab(label='Signal Hound 2', value='tab-2'),
                    dcc.Tab(label='Signal Hound 3', value='tab-3'),
                ]),
            ], width=12, lg=9),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='tabs-content')
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.H3('RFI Report'),
                data_table
            ], width=12),
        ]),
    ])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content'),
])

@app.callback(
    Output('tabs-content', 'children'),
    [Input('image-tabs', 'value'),
     Input('rfi-date-picker', 'date')]
)
def update_image_tab_content(tab, selected_date):
    if not selected_date:
        return html.Div("Please select a date.")

    selected_date_obj = pd.to_datetime(selected_date)
    formatted_date = selected_date_obj.strftime('%Y%m%d')  # Format date as YYYYMMDD
    
    # 'tab' is structured in a way that appending its value directly maps to the correct png file
    # Dynamically update image source paths to point to your Flask application
    img_src = f"http://universe.phys.unm.edu/data/png/sh{tab[-1]}_{formatted_date}.png"
    
    return html.Div(
        html.Img(src=img_src, style={"width": "100%", "height": "auto"}),
        style={"maxWidth": "1200px", "margin": "0 auto"}
    )

@app.callback(
    [Output('rfi-data-table', 'data'), Output('rfi-data-table', 'columns')],
    [Input('image-tabs', 'value'),
     Input('rfi-date-picker', 'date')]
)
def update_data_table(tab, selected_date):
    if not selected_date or not tab:
        return [], []

    selected_date_obj = pd.to_datetime(selected_date)
    formatted_date = selected_date_obj.strftime('%Y%m%d')  # Format date as YYYYMMDD
    
    # 'tab' is structured in a way that appending its value directly maps to the correct CSV file
    csv_url = f'http://universe.phys.unm.edu/data/rfi_reports/sh{tab[-1]}_{formatted_date}_rfi_report.csv'

    try:
        response = requests.get(csv_url)
        if response.status_code == 200:
            # If the request was successful, parse the CSV data
            df = pd.read_csv(StringIO(response.text))
            columns = [{"name": i, "id": i} for i in df.columns]
            data = df.to_dict('records')
            return data, columns
        else:
            # Handle HTTP errors (e.g., file not found on the server)
            return [], []
    except requests.RequestException as e:
        # Handle other request issues, such as network errors
        print(f"Error fetching CSV: {e}")
        return [], []

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/rfi_explorer':
        return rfi_explorer.layout
    else:
        return main_page_layout()

if __name__ == '__main__':
    app.run_server(debug=True)
