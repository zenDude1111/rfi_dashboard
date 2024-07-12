from datetime import date, timedelta
import pandas as pd
import requests
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import numpy as np

# Define the layout of the app
layout = html.Div(children=[

    dbc.Card(
        dbc.CardBody(
            html.Div([
                dbc.Button('Backward', id='backward-button', n_clicks=0, color="secondary", className="me-2"),
                dcc.DatePickerSingle(
                    id='date-picker',
                    date=pd.to_datetime('today').strftime('%Y-%m-%d')
                ),
                dbc.Button('Forward', id='forward-button', n_clicks=0, color="secondary", className="ms-2"),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='frequency-graph',
                style={'height': '800px', 'width': '100%'}
            )
        ),
        style={'margin': '20px'}
    )
])

@callback(
    Output('date-picker', 'date'),
    Input('backward-button', 'n_clicks'),
    Input('forward-button', 'n_clicks'),
    State('date-picker', 'date'),
)
def update_date(backward_clicks, forward_clicks, current_date):
    if not ctx.triggered:
        return current_date
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_date = pd.to_datetime(current_date)

    if button_id == 'backward-button':
        new_date = current_date - timedelta(days=1)
    elif button_id == 'forward-button':
        new_date = current_date + timedelta(days=1)
    else:
        new_date = current_date

    return new_date.strftime('%Y-%m-%d')

@callback(
    Output('frequency-graph', 'figure'),
    Input('date-picker', 'date'),
)
def update_graph(selected_date):
    # Fetch the data from the Flask endpoint
    response = requests.get(f'http://universe.phys.unm.edu/data/frequency_stats?date={selected_date}&source=anritsu')
    response2 = requests.get(f'http://universe.phys.unm.edu/data/anritsu_background')

    try:
        response.raise_for_status()  # Raise an error for bad status codes
        response2.raise_for_status()
        data = response.json()
        data2 = response2.json()

        # Extract data from the response
        frequencies = [item['Frequency (GHz)'] for item in data]
        mean_values = [item['Mean (dBm)'] for item in data]
        median_values = [item['Median (dBm)'] for item in data]
        min_values = [item['Min (dBm)'] for item in data]
        max_values = [item['Max (dBm)'] for item in data]
        avg_median = [item['Avg_Median'] for item in data2]
        avg_5_sigma_away = [item['Avg_5_Sigma_Away'] for item in data2]

        # Combine existing data with the new data
        df_combined = pd.DataFrame({
            'Frequency (GHz)': frequencies,
            'Mean (dBm)': mean_values,
            'Median (dBm)': median_values,
            'Min (dBm)': min_values,
            'Max (dBm)': max_values,
            'Avg_Median': avg_median,
            'Avg_5_Sigma_Away': avg_5_sigma_away
        })

        # Create traces for the plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Mean (dBm)'], mode='lines+markers', name='Mean (dBm)'))
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Median (dBm)'], mode='lines+markers', name='Median (dBm)'))
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Min (dBm)'], mode='lines+markers', name='Min (dBm)'))
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Max (dBm)'], mode='lines+markers', name='Max (dBm)'))
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Avg_Median'], mode='lines+markers', name='Average Median (dBm)'))
        fig.add_trace(go.Scatter(x=df_combined['Frequency (GHz)'], y=df_combined['Avg_5_Sigma_Away'], mode='lines+markers', name='5 Sigma from Average Median (dBm)'))

        # Update layout
        fig.update_layout(
            title=f'Daily Metrics for {selected_date}',
            xaxis_title='Frequency (GHz)',
            yaxis_title='Value (dBm)',
            legend_title='Metrics',
            template='plotly_dark',
            xaxis=dict(
                tickvals=np.arange(min(df_combined['Frequency (GHz)']), max(df_combined['Frequency (GHz)']) + 0.5, 0.5),
                ticktext=[f'{i:.1f}' for i in np.arange(min(df_combined['Frequency (GHz)']), max(df_combined['Frequency (GHz)']) + 0.5, 0.5)]
            )
        )

        return fig
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return go.Figure()

    except json.decoder.JSONDecodeError:
        print("Error decoding JSON")
        return go.Figure()
