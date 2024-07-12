from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from io import StringIO

# Define the frequency range for LMR
LMR_FREQUENCIES = np.arange(0.4499, 0.4517 + 0.0002, 0.0002)  # LMR

def fetch_data_from_server(signal_hound_number, date_str, target_frequency_ghz):
    """Fetch data from the server based on parameters."""
    url = f"http://universe.phys.unm.edu/data/time_series_matrix_data/sh{signal_hound_number}/{date_str}/{target_frequency_ghz}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            json_str_io = StringIO(response.text)
            data_df = pd.read_json(json_str_io, orient='records')
            return data_df
        else:
            print(f"Error fetching data: Status code {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Exception while fetching data: {e}")
        return pd.DataFrame()

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.P('Select a date:', className='mb-2'),
            dcc.DatePickerSingle(
                id='rfi-date-picker',
                min_date_allowed=date(1995, 8, 5),
                max_date_allowed=date.today(),
                initial_visible_month=date.today(),
                date=date.today(),
                className='w-100',
            ),
        ], width=12, lg=3),
    ]),
    dbc.Row(dbc.Col(html.Div(id='tabs-content'), width=12)),
], className='mt-3')

@callback(
    Output('tabs-content', 'children'),
    [Input('rfi-date-picker', 'date')]
)
def update_channel_tab_content(selected_date):
    selected_date_formatted = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%Y%m%d')
    aggregated_data = pd.DataFrame()

    for frequency in LMR_FREQUENCIES:
        df = fetch_data_from_server("1", selected_date_formatted, frequency)
        if not df.empty:
            df['Frequency'] = frequency  # Assign frequency to each row
            aggregated_data = pd.concat([aggregated_data, df], ignore_index=True)

    if aggregated_data.empty:
        return "No data available for the selected parameters."

    # Visualization
    fig = go.Figure(data=go.Contour(
        z=aggregated_data['Power (dBm)'],
        y=aggregated_data['Timestamp'],
        x=aggregated_data['Frequency'],
        colorscale='Viridis',
        contours=dict(
            coloring='heatmap',
            showlabels=True,
        )
    ))

    fig.update_layout(
        title="Power Contour Map for LMR Frequency and Selected Date",
        yaxis_title="Time",
        xaxis_title="Frequency (GHz)"
    )

    return dcc.Graph(figure=fig)
