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
                        id="radios-metrics",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-secondary",  # Changed to secondary
                        labelCheckedClassName="btn btn-secondary",    # Changed to secondary
                        options=[
                            {"label": "SH1-Mapo", "value": 'sh1'},
                            {"label": "SH2-DSL", "value": 'sh2'},
                            {"label": "Anritsu-DSL", "value": 'anritsu'},
                        ],
                    ),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start'}),

                # "Metrics" title in the middle
                html.Div([
                    html.H5("Daily Metrics", className="card-title"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                # Forward/back buttons and date picker on the right
                html.Div([
                    dbc.Button('Backward', id='metrics-backward-button', n_clicks=0, color="secondary", className="me-2"),
                    dcc.DatePickerSingle(
                        id='metrics-date-picker-single',
                        date=pd.to_datetime('today').strftime('%Y-%m-%d')
                    ),
                    dbc.Button('Forward', id='metrics-forward-button', n_clicks=0, color="secondary", className="ms-2"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'gap': '10px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='metrics-graph-plot',
                style={'height': '800px', 'width': '100%'}
            )
        ),
        style={'margin': '20px'}
    )
])

@callback(
    Output('metrics-date-picker-single', 'date'),
    Input('metrics-backward-button', 'n_clicks'),
    Input('metrics-forward-button', 'n_clicks'),
    State('metrics-date-picker-single', 'date'),
)
def update_date(backward_clicks, forward_clicks, current_date):
    if not ctx.triggered:
        return current_date
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_date = pd.to_datetime(current_date)

    if button_id == 'metrics-backward-button':
        new_date = current_date - timedelta(days=1)
    elif button_id == 'metrics-forward-button':
        new_date = current_date + timedelta(days=1)
    else:
        new_date = current_date

    return new_date.strftime('%Y-%m-%d')

@callback(
    Output('metrics-graph-plot', 'figure'),
    Input('radios-metrics', 'value'),
    Input('metrics-date-picker-single', 'date'),
)
def update_metrics_plot(device, selected_date):
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
        power_dict = data['data']

        if not power_dict:
            raise ValueError("No data available")

        # Convert the power data into a DataFrame
        power_values = pd.DataFrame(power_dict).T
        power_values.columns = frequencies

        # Compute the metrics
        mean_power = power_values.mean()
        median_power = power_values.median()
        min_power = power_values.min()
        max_power = power_values.max()

        # Create the frequency by power graph for the metrics
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=frequencies, y=mean_power, mode='lines', name='Mean Power'))
        fig.add_trace(go.Scatter(x=frequencies, y=median_power, mode='lines', name='Median Power'))
        fig.add_trace(go.Scatter(x=frequencies, y=min_power, mode='lines', name='Min Power'))
        fig.add_trace(go.Scatter(x=frequencies, y=max_power, mode='lines', name='Max Power'))

        # Update layout for dark theme with custom tick settings
        fig.update_layout(
            title=f'{device_name} {selected_date}',
            xaxis_title='Frequency (GHz)',
            yaxis_title='Power (dBm)',
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
