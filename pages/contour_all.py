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
                # Device buttons on the left
                html.Div([
                    dbc.RadioItems(
                        id="radios-contour",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-secondary",  
                        labelCheckedClassName="btn btn-secondary",    
                        options=[
                            {"label": "SH1-Mapo", "value": 'sh1'},
                            {"label": "SH2-DSL", "value": 'sh2'},
                            {"label": "Anritsu-DSL", "value": 'anritsu'},
                        ],
                    ),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start'}),

                # "Contour Plot" title in the middle
                html.Div([
                    html.H5("Contour Plots", className="card-title"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                # Forward/back buttons and date picker on the right
                html.Div([
                    dbc.Button('Backward', id='contour-backward-button', n_clicks=0, color="secondary", className="me-2"),
                    dcc.DatePickerSingle(
                        id='contour-date-picker-single',
                        date=pd.to_datetime('today').strftime('%Y-%m-%d')
                    ),
                    dbc.Button('Forward', id='contour-forward-button', n_clicks=0, color="secondary", className="ms-2"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'gap': '10px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='contour-graph-plot',
                style={'height': '800px', 'width': '100%'}
            )
        ),
        style={'margin': '20px'}
    )
])

@callback(
    Output('contour-date-picker-single', 'date'),
    Input('contour-backward-button', 'n_clicks'),
    Input('contour-forward-button', 'n_clicks'),
    State('contour-date-picker-single', 'date'),
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
    Output('contour-graph-plot', 'figure'),
    Input('radios-contour', 'value'),
    Input('contour-date-picker-single', 'date'),
)
def update_contour_map(device, selected_date):
    # Directly use the device value from the radio buttons
    device_name = device
    
    # Fetch the data from the Flask endpoint
    response = requests.get(f'http://universe.phys.unm.edu/data/time_series_matrix_data/{device_name}/{selected_date.replace("-", "")}')
    
    try:
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()

        # Extract frequencies, timestamps, and data
        frequencies = data['frequencies']
        timestamps = data['timestamps']
        power_values = pd.DataFrame(data['data']).values.T

        # Check if data is available
        if power_values.size == 0:
            raise ValueError("No data available")

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

        # Update layout for dark theme with custom tick settings
        fig.update_layout(
            title=f'{device_name} {selected_date}',
            xaxis_title='Frequency (GHz)',
            yaxis_title='Timestamp',
            template='plotly_dark',
            xaxis=dict(
                tickmode='auto',
                nticks=20  # Increase the number of ticks on the x-axis
            ),
            yaxis=dict(
                tickmode='auto',
                nticks=10  # Reduce the number of ticks on the y-axis
            )
        )

        return fig
    
    except (requests.exceptions.RequestException, KeyError, json.decoder.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}")
        fig = go.Figure()
        fig.add_annotation(text="No data available",
                           xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=20, color="red"))
        fig.update_layout(template='plotly_dark',
                          xaxis=dict(visible=False),
                          yaxis=dict(visible=False))
        return fig
