from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import date
import pandas as pd

# Assuming 'southpole_rfi_dashboard.py' exists in the 'pages' directory with a layout defined
from pages import rfi_explorer

# Correct path to the CSV file in the assets folder
df = pd.read_csv('assets/20240207_rfi_report.csv')

# Initialize Dash app
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Expose the Flask server for Gunicorn

# Define your navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Main", href="/")),
        dbc.NavItem(dbc.NavLink("RFI Explorer", href="/rfi_explorer")),
    ],
    brand="RFI Explorer",
    brand_href="/",
    color="secondary",
    dark=True,
)

# Create the DataTable from the DataFrame
data_table = dash_table.DataTable(
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
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

# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])

# Define layout for landing page
home_layout = html.Div([
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

# Define the callback for dynamic page loading
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/rfi_explorer':
        return rfi_explorer.layout  
    else:
        return home_layout

@app.callback(
    Output('tabs-content', 'children'),
    [Input('image-tabs', 'value')]
)
def render_content(tab):
    if tab == 'tab-1':
        img_src = "/assets/sh1_20210101_waterfall.png"
    elif tab == 'tab-2':
        img_src = "/assets/sh2_20210101_waterfall.png"
    elif tab == 'tab-3':
        img_src = "/assets/DSL_20240207_waterfall.png"
    
    return html.Div(
        html.Img(src=img_src, style={"width": "100%", "height": "auto"}),
        style={"maxWidth": "1200px", "margin": "0 auto"}
    )

if __name__ == '__main__':
    app.run_server(debug=True)
