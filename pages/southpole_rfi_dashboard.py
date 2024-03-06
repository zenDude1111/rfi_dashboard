import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Output, Input, dash_table
from datetime import date
import pandas as pd

# Correct path to the CSV file in the assets folder
df = pd.read_csv('assets/20240207_rfi_report.csv')

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
    style_table={'overflowX': 'auto'}  # Handle wide tables on small screens
)

layout = dbc.Container([
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
            ]),
        ], width=12, lg=9),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id='tabs-content')
        ], width=12),
    ]),
    dbc.Row([  # Row for the RFI report DataTable
        dbc.Col([
            html.H3('RFI Report'),
            data_table  # DataTable component
        ], width=12),
    ]),
], fluid=True)

@callback(
    Output('tabs-content', 'children'),
    [Input('image-tabs', 'value')]
)
def render_content(tab):
    if tab == 'tab-1':
        img_src = "/assets/sh1_20210101_waterfall.png"
    elif tab == 'tab-2':
        img_src = "/assets/DSL_20240207_waterfall.png"
    
    return html.Div(
        html.Img(src=img_src, style={"width": "100%", "height": "auto"}),
        style={"maxWidth": "1200px", "margin": "0 auto"}
    )
