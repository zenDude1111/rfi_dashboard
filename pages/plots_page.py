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
                        value='sh2'  # Set SH2-DSL as the default selected value
                    ),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start'}),

                # "Contour Plot" title in the middle
                html.Div([
                    html.H5("", className="card-title"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                # Forward/back buttons and date picker on the right
                html.Div([
                    dbc.Button('Backward', id='contour-backward-button', n_clicks=0, color="secondary", className="me-2"),
                    dcc.DatePickerSingle(
                    id='contour-date-picker-single',
                    date=(pd.to_datetime('today') - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                ),
                    dbc.Button('Forward', id='contour-forward-button', n_clicks=0, color="secondary", className="ms-2"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'gap': '10px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '5px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='stats-graph-plot',
                style={'height': '200px', 'width': '100%'}  # Adjusted height
            )
        ),
        style={'margin': '5px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='contour-graph-plot',
                style={'height': '600px', 'width': '100%'}  # Adjusted height
            )
        ),
        style={'margin': '5px'}
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

def get_data(device_name, selected_date):
    url = f'http://universe.phys.unm.edu/data/time_series_matrix_data/{device_name}/{selected_date.replace("-", "")}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    frequencies = data.get('frequencies', [])
    timestamps = data.get('timestamps', [])
    power_values_data = data.get('data', [])
    power_values = pd.DataFrame(power_values_data).values.T

    if not frequencies or not timestamps or power_values.size == 0:
        raise ValueError("No data available or missing required keys")

    return frequencies, timestamps, power_values

@callback(
    Output('contour-graph-plot', 'figure'),
    Output('stats-graph-plot', 'figure'),
    Input('radios-contour', 'value'),
    Input('contour-date-picker-single', 'date'),
)
def update_contour_and_stats(device, selected_date):
    try:
        frequencies, timestamps, power_values = get_data(device, selected_date)

        # Define the common x-axis range
        xaxis_range = [min(frequencies), max(frequencies)]

        # Create the contour plot with specified color scale range and line width
        contour_fig = go.Figure(data=go.Contour(
            z=power_values,
            x=frequencies,
            y=timestamps,
            colorscale='Viridis',
            ncontours=25,  # Specify the number of contour levels
            zmin=-110,  # Minimum value for the color bar
            zmax=-20,   # Maximum value for the color bar
            line_width=0  # Set the contour line width
        ))

        # Update layout for dark theme with custom tick settings and minimal margins
        contour_fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title='Frequency (GHz)',
            yaxis_title='Time UTC',
            template='plotly_dark',
            xaxis=dict(
                tickmode='auto',
                nticks=20,  # Increase the number of ticks on the x-axis
                range=xaxis_range
            ),
            yaxis=dict(
                tickmode='auto',
                nticks=10,  # Reduce the number of ticks on the y-axis
            )
        )

        # Calculate statistics for each frequency
        stats_df = pd.DataFrame({
            'Frequency': frequencies,
            'Min': power_values.min(axis=0),
            'Max': power_values.max(axis=0),
            'Median': np.median(power_values, axis=0),
            'Mean': power_values.mean(axis=0)
        })

        # Create the statistics plot
        stats_fig = go.Figure()
        stats_fig.add_trace(go.Scatter(x=stats_df['Frequency'], y=stats_df['Min'], mode='lines', name='Min'))
        stats_fig.add_trace(go.Scatter(x=stats_df['Frequency'], y=stats_df['Max'], mode='lines', name='Max'))
        stats_fig.add_trace(go.Scatter(x=stats_df['Frequency'], y=stats_df['Median'], mode='lines', name='Median'))
        stats_fig.add_trace(go.Scatter(x=stats_df['Frequency'], y=stats_df['Mean'], mode='lines', name='Mean'))

        # Update layout for dark theme with custom tick settings and minimal margins
        stats_fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title='Frequency (GHz)',
            yaxis_title='Power (dBm)',
            template='plotly_dark',
            xaxis=dict(
                range=xaxis_range  # Ensure the x-axis range matches the contour plot
            ),
            yaxis=dict(
                tickmode='auto',
                tickformat='.4f'  # Format y-axis ticks to one decimal place
            )
        )

        return contour_fig, stats_fig

    except (requests.exceptions.RequestException, KeyError, json.decoder.JSONDecodeError, ValueError) as e:
        error_fig = go.Figure()
        error_fig.add_annotation(text="No data available",
                                 xref="paper", yref="paper",
                                 x=0.5, y=0.5, showarrow=False,
                                 font=dict(size=20, color="red"))
        error_fig.update_layout(template='plotly_dark',
                                xaxis=dict(visible=False),
                                yaxis=dict(visible=False),
                                margin=dict(l=10, r=10, t=10, b=10))
        return error_fig, error_fig
