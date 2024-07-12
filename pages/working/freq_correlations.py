from datetime import date, timedelta
import pandas as pd
import requests
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import json
import networkx as nx

layout = html.Div(children=[

    dbc.Card(
        dbc.CardBody(
            html.Div([
                # Device buttons on the left
                html.Div([
                    dbc.RadioItems(
                        id="radios-metrics-unique",
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

                # "Frequency Correlations" title in the middle
                html.Div([
                    html.H5("Frequency Correlations", className="card-title"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                # Forward/back buttons and date picker on the right
                html.Div([
                    dbc.Button('Backward', id='metrics-backward-button-unique', n_clicks=0, color="secondary", className="me-2"),
                    dcc.DatePickerSingle(
                        id='metrics-date-picker-single-unique',
                        date=pd.to_datetime('today').strftime('%Y-%m-%d')
                    ),
                    dbc.Button('Forward', id='metrics-forward-button-unique', n_clicks=0, color="secondary", className="ms-2"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'gap': '10px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),

    dbc.Card(
        dbc.CardBody(
            dcc.Graph(
                id='metrics-graph-plot-unique',
                style={'height': '800px', 'width': '100%'}
            )
        ),
        style={'margin': '20px'}
    )
])

@callback(
    Output('metrics-date-picker-single-unique', 'date'),
    Input('metrics-backward-button-unique', 'n_clicks'),
    Input('metrics-forward-button-unique', 'n_clicks'),
    State('metrics-date-picker-single-unique', 'date'),
)
def update_date(backward_clicks, forward_clicks, current_date):
    if not ctx.triggered:
        return current_date
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_date = pd.to_datetime(current_date)

    if button_id == 'metrics-backward-button-unique':
        new_date = current_date - timedelta(days=1)
    elif button_id == 'metrics-forward-button-unique':
        new_date = current_date + timedelta(days=1)
    else:
        new_date = current_date

    return new_date.strftime('%Y-%m-%d')

@callback(
    Output('metrics-graph-plot-unique', 'figure'),
    Input('radios-metrics-unique', 'value'),
    Input('metrics-date-picker-single-unique', 'date'),
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

        # Calculate the change in power over time (first difference)
        power_changes = power_values.diff().dropna()

        # Compute the correlation matrix of the power changes
        correlation_matrix = power_changes.corr()

        # Create a graph from the correlation matrix
        G = nx.Graph()

        for i, freq in enumerate(frequencies):
            G.add_node(freq)

        for i in range(len(frequencies)):
            for j in range(i+1, len(frequencies)):
                correlation = correlation_matrix.iloc[i, j]
                if abs(correlation) > 0.5:  # Only include strong correlations
                    G.add_edge(frequencies[i], frequencies[j], weight=correlation)

        # Spring layout for better visual separation
        pos = nx.spring_layout(G, seed=42)  # Seed for reproducible layout

        edge_x = []
        edge_y = []
        edge_weights = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)
            edge_weights.append(edge[2]['weight'])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.0, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f'{float(node):.2f}')

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            hoverinfo='text',
            marker=dict(
                color='blue',
                size=20,  # Increase the size of the nodes
            ))

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title='Frequency Correlations',
            showlegend=False,
            template='plotly_dark',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
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
