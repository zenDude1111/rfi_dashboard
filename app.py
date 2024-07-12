from datetime import date, timedelta
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc

# Modularized layout imports
from pages import freq_explorer, daily_metrics, contour_all

# Create Dash application instance with external stylesheets for theming
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

def create_navbar():
    """Creates and returns the navigation bar component."""
    return dbc.NavbarSimple(
        children=[
            #dbc.NavItem(dbc.NavLink("Static Waterfall Plots", href="/")),
            #dbc.NavItem(dbc.NavLink("Frequency Explorer", href="/freq_explorer")),
            dbc.NavItem(dbc.NavLink("Countours", href="/contour_all")),
            dbc.NavItem(dbc.NavLink("Daily Metrics", href="/daily_metrics")),
        ],
        brand="South Pole RFI Dashboard",
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
                        dbc.Row([
                            dbc.Col([
                                dcc.DatePickerSingle(
                                    id='main-rfi-date-picker',
                                    min_date_allowed=date(1995, 8, 5),
                                    max_date_allowed=date.today(),
                                    initial_visible_month=date.today(),
                                    date=date.today(),
                                    className='w-100'
                                ),
                            ], width=8),
                            dbc.Col([
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button("Previous Day", id="prev-day-button", color="secondary", className="me-1"),
                                        dbc.Button("Next Day", id="next-day-button", color="secondary"),
                                    ],
                                    className="mt-1"
                                ),
                            ], width=4, style={"display": "flex", "alignItems": "center", "justifyContent": "flex-end"}),
                        ]),
                        dcc.Tabs(
                            id="main-image-tabs", 
                            value='tab-1', 
                            children=[
                                dcc.Tab(label='SH1-MAPO', value='tab-1', className='text-white bg-secondary fw-bold'),
                                dcc.Tab(label='SH2-DSL', value='tab-2', className='text-white bg-secondary fw-bold'),
                                dcc.Tab(label='Anritsu-DSL', value='tab-3', className='text-white bg-secondary fw-bold'),
                            ],
                            className='w-100 fs-5'
                        ),
                        html.Div(id='main-tabs-content', style={"minHeight": "400px", "display": "flex", "AlignItems": "center", "justifyContent": "center"})
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

    # Check what tab is selected and edit the image source accordingly
    if tab == 'tab-1':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/sh1_{formatted_date}.png"
    elif tab == 'tab-2':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/sh2_{formatted_date}.png"
    elif tab == 'tab-3':
        img_src = f"http://universe.phys.unm.edu/data/waterfall/anritsu_{formatted_date}.png"

    try:
        response = requests.get(img_src)
        if response.status_code == 200:
            return html.Img(src=img_src, style={"maxWidth": "100%", "maxHeight": "100%"})
        else:
            return html.Div("No data available for the selected date and tab.", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})
    except requests.RequestException as e:
        return html.Div(f"Error fetching image: {e}", style={"textAlign": "center", "color": "red", "fontWeight": "bold"})

@app.callback(
    Output('main-page-content', 'children'),
    [Input('main-url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/freq_explorer':
        return freq_explorer.layout
    elif pathname == '/daily_metrics':
        return daily_metrics.layout
    elif pathname == '/contour_all':
        return contour_all.layout
    return contour_all.layout
    #return layout_main_page()

@app.callback(
    Output('main-rfi-date-picker', 'date'),
    [Input('prev-day-button', 'n_clicks'), Input('next-day-button', 'n_clicks')],
    [Input('main-rfi-date-picker', 'date')]
)
def navigate_date(prev_clicks, next_clicks, current_date):
    current_date_obj = pd.to_datetime(current_date)
    ctx = callback_context

    if not ctx.triggered:
        return current_date

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'prev-day-button':
        new_date = current_date_obj - timedelta(days=1)
    elif button_id == 'next-day-button':
        new_date = current_date_obj + timedelta(days=1)
    else:
        return current_date

    return new_date.strftime('%Y-%m-%d')

if __name__ == '__main__':
    app.run_server(debug=True)

