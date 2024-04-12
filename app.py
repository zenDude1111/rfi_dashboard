from datetime import date
import os
import pandas as pd
import requests
from io import StringIO
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# Modularized layout imports
from pages import frequency_explorer
from pages import known_frequencies

# Create Dash application instance with external stylesheets for theming
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

def create_navbar():
    """Creates and returns the navigation bar component."""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Main", href="/")),
            dbc.NavItem(dbc.NavLink("Frequency Explorer", href="/frequency_explorer")),
            dbc.NavItem(dbc.NavLink("Known Frequencies", href="/known_frequencies")),
        ],
        brand="South Pole RF Environment Dashboard",
        brand_href="/",
        color="secondary",
        dark=True,
    )

def create_data_table():
    """Initializes and returns an empty DataTable component."""
    initial_df = pd.DataFrame()
    return dash_table.DataTable(
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

def layout_main_page():
    """Defines the main page layout using Bootstrap utility classes."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.P('Select a date:', className='mb-2'),  # mb-2: margin-bottom 2
                dcc.DatePickerSingle(
                    id='main-rfi-date-picker', #namespace id
                    min_date_allowed=date(1995, 8, 5),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    date=date.today(),
                    className='w-100',  # w-100: width 100%
                ),
            ], width=12, lg=3),
            dbc.Col([
                dcc.Tabs(
                    id="main-image-tabs", 
                    value='tab-1', 
                    children=[
                        dcc.Tab(label='SH1-MAPO', value='tab-1', className='text-white bg-secondary fw-bold'),
                        dcc.Tab(label='SH1-DSL', value='tab-2', className='text-white bg-secondary fw-bold'),
                        dcc.Tab(label='Signal Hound 3', value='tab-3', className='text-white bg-secondary fw-bold'),
                    ],
                    className='w-100 fs-5',  # w-100: width 100%, fs-5: font-size 5
                ),
            ], width=12, lg=9),
        ]),
        dbc.Row(dbc.Col(html.Div(id='main-tabs-content'), width=12)),
        dbc.Row(dbc.Col([html.H3('RF Environment Report', className='mt-3'), create_data_table()], width=12)),
    ], className='mt-3')  # mt-3: margin-top 3


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    create_navbar(),
    html.Div(id='page-content'),
])

@app.callback(
    Output('tabs-content', 'children'),
    [Input('image-tabs', 'value'), Input('rfi-date-picker', 'date')]
)
def update_image_tab_content(tab, selected_date):
    if not selected_date:
        return html.Div("Select a date.")

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
    [Output('main-rfi-data-table', 'data'), Output('rfi-data-table', 'columns')],
    [Input('main-image-tabs', 'value'), Input('rfi-date-picker', 'date')]
)
def update_data_table(tab, selected_date):

    #current date formatted as yyyymmdd
    current_date = date.today().strftime('%Y%m%d')

    if not selected_date or not tab:
        return [1], [current_date]

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
    if pathname == '/frequency_explorer':
        return frequency_explorer.layout
    elif pathname == '/known_frequencies':
        return known_frequencies.layout
    return layout_main_page()

if __name__ == '__main__':
    app.run_server(debug=True)
