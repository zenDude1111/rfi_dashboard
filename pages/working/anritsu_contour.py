from datetime import date, timedelta
import pandas as pd
import requests
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import json

layout = html.Div(children=[

    dbc.Card(
        dbc.CardBody(
            html.Div([
                dbc.Button('Backward', id='contour-backward-button', n_clicks=0, color="secondary", className="me-2"),
                dcc.DatePickerSingle(
                    id='contour-date-picker',
                    date=pd.to_datetime('today').strftime('%Y-%m-%d')
                ),
                dbc.Button('Forward', id='contour-forward-button', n_clicks=0, color="secondary", className="ms-2"),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='contour-graph',
                style={'height': '800px', 'width': '100%'}
            )
        ),
        style={'margin': '20px'}
    )
])

@callback(
    Output('contour-date-picker', 'date'),
    Input('contour-backward-button', 'n_clicks'),
    Input('contour-forward-button', 'n_clicks'),
    State('contour-date-picker', 'date'),
)
def update_date(backward_clicks, forward_clicks, current_date):
    if not ctx.triggered:
        return current_date
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_date = pd.to_datetime(current_date)

    if button_id == 'contour-backward-button':
        new_date = current_date - timedelta(days=1)
    elif button_id == 'contour-forward-button':
        new_date = current_date + timedelta(days=1)
    else:
        new_date = current_date

    return new_date.strftime('%Y-%m-%d')

@callback(
    Output('contour-graph', 'figure'),
    Input('contour-date-picker', 'date'),
)
def update_contour_map(selected_date):
    device = 'anritsu'
    # Fetch the data from the Flask endpoint
    response = requests.get(f'http://universe.phys.unm.edu/data/time_series_matrix_data/{device}/{selected_date.replace("-", "")}')
    
    try:
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()

        # Extract frequencies, timestamps, and data
        frequencies = data['frequencies']
        timestamps = data['timestamps']
        power_values = pd.DataFrame(data['data']).values.T

        # Create the contour plot with specified color scale range and line width
        fig = go.Figure(data=go.Contour(
            z=power_values,
            x=frequencies,
            y=timestamps,
            colorscale='Viridis',
            ncontours=25,  # Specify the number of contour levels
            zmin=-110,  # Minimum value for the color bar
            zmax=-20,   # Maximum value for the color bar
            line_width=0  # Set the contour line width
        ))

        # Update layout for dark theme
        fig.update_layout(
            title=f'Contour Map for {device} on {selected_date}',
            xaxis_title='Frequency (GHz)',
            yaxis_title='Timestamp',
            template='plotly_dark'
        )

        return fig
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return go.Figure()

    except KeyError as e:
        print(f"Key error: {e}")
        return go.Figure()

    except json.decoder.JSONDecodeError:
        print("Error decoding JSON")
        return go.Figure()
