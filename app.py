from datetime import date
import os
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Modularized layout imports
from pages import frequency_explorer
# from pages import known_frequencies2

# Create Dash application instance with external stylesheets for theming
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

def create_navbar():
    """Creates and returns the navigation bar component."""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Main", href="/")),
            dbc.NavItem(dbc.NavLink("Frequency Explorer", href="/frequency_explorer")),
            # dbc.NavItem(dbc.NavLink("Known Frequencies", href="/known_frequencies")),
        ],
        brand="South Pole RF Environment Dashboard",
        brand_href="/",
        color="secondary",
        dark=True,
    )

def layout_main_page():
    """Defines the main page layout using Bootstrap utility classes."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.P('Select a date:', className='mb-2'),
                        dcc.DatePickerSingle(
                            id='main-rfi-date-picker',
                            min_date_allowed=date(1995, 8, 5),
                            max_date_allowed=date.today(),
                            initial_visible_month=date.today(),
                            date=date.today(),
                            className='w-100'
                        ),
                        dcc.Tabs(
                            id="main-image-tabs", 
                            value='tab-1', 
                            children=[
                                dcc.Tab(label='SH1-MAPO', value='tab-1', className='text-white bg-secondary fw-bold'),
                                dcc.Tab(label='SH2-DSL', value='tab-2', className='text-white bg-secondary fw-bold'),
                                dcc.Tab(label='Anritsu-DSL', value='tab-3', className='text-white bg-secondary fw-bold'),
                                dcc.Tab(label='Compare', value='tab-4', className='text-white bg-secondary fw-bold'),
                            ],
                            className='w-100 fs-5'
                        ),
                        html.Div(id='main-tabs-content', style={"minHeight": "400px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                    ])
                )
            ], width=12)
        ], className='mb-3')
    ], className='mt-3')

app.layout = html.Div([
    dcc.Location(id='main-url', refresh=False),
    create_navbar(),
    html.Div(id='main-page-content'),
])

@app.callback(
    Output('main-tabs-content', 'children'),
    [Input('main-image-tabs', 'value'), Input('main-rfi-date-picker', 'date')]
)
def update_image_tab_content(tab, selected_date):
    if not selected_date:
        return html.Div("Select a date.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

    selected_date_obj = pd.to_datetime(selected_date)
    formatted_date = selected_date_obj.strftime('%Y%m%d')  # Format date as YYYYMMDD

    if tab == 'tab-4':  # Compare tab
        return html.Div([
            dcc.Tabs(
                id="compare-tabs",
                value='compare-1',
                children=[
                    dcc.Tab(label='SH1-MAPO', value='compare-1', className='text-white bg-secondary fw-bold'),
                    dcc.Tab(label='SH2-DSL', value='compare-2', className='text-white bg-secondary fw-bold'),
                    dcc.Tab(label='Anritsu-DSL', value='compare-3', className='text-white bg-secondary fw-bold'),
                ],
                className='w-100 fs-5'
            ),
            html.Div(id='compare-tabs-content', style={"minHeight": "400px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], style={"width": "100%"})
    
    #check what tab is selected and edit the image source accordingly
    if tab == 'tab-1':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/sh1_{formatted_date}.png"
    elif tab == 'tab-2':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/sh2_{formatted_date}.png"
    elif tab == 'tab-3':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/anritsu_{formatted_date}.png"

    try:
        response = requests.get(img_src)
        if response.status_code == 200:
            return html.Img(src=img_src, style={"maxWidth": "85%", "maxHeight": "85%"})
        else:
            return html.Div("No data available for the selected date and tab.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})
    except requests.RequestException as e:
        return html.Div(f"Error fetching image: {e}", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

@app.callback(
    Output('compare-tabs-content', 'children'),
    [Input('compare-tabs', 'value'), Input('main-rfi-date-picker', 'date')]
)
def update_compare_tabs_content(compare_tab, selected_date):
    if compare_tab == 'compare-1':
        return update_compare_image('1', selected_date)
    elif compare_tab == 'compare-2':
        return update_compare_image('2', selected_date)
    elif compare_tab == 'compare-3':
        return update_compare_image('3', selected_date)
    return html.Div("Select a date.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

def update_compare_image(tab_suffix, selected_date):
    if not selected_date:
        return html.Div("Select a date.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

    selected_date_obj = pd.to_datetime(selected_date)
    formatted_date = selected_date_obj.strftime('%Y%m%d')  # Format date as YYYYMMDD

    #check what tab is selected and edit the image source accordingly
    if tab_suffix == '1':
        img_src = f"http://universe.phys.unm.edu/data/waterfall_compare/sh1_{formatted_date}.png"
    elif tab_suffix == '2':
        img_src = f"http://universe.phys.unm.edu/data/waterfall_compare/sh2_{formatted_date}.png"
    elif tab_suffix == '3':
        img_src = f"http://universe.phys.unm.edu/data/waterfall_compare/anritsu_{formatted_date}.png"

    try:
        response = requests.get(img_src)
        if response.status_code == 200:
            return html.Img(src=img_src, style={"maxWidth": "85%", "maxHeight": "85%"})
        else:
            return html.Div("No data available for the selected date and tab.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})
    except requests.RequestException as e:
        return html.Div(f"Error fetching image: {e}", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

@app.callback(
    Output('main-page-content', 'children'),
    [Input('main-url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/frequency_explorer':
        return frequency_explorer.layout
    # elif pathname == '/known_frequencies':
        # return known_frequencies2.layout
    return layout_main_page()

if __name__ == '__main__':
    app.run_server(debug=True)
