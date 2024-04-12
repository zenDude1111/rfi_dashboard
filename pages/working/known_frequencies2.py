from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from io import StringIO

# Define the frequency ranges for each channel
CHANNEL_FREQUENCIES = {
    'tab-1': np.arange(8.0987, 8.1015, 0.0002),  # Skynet
    'tab-2': np.arange(8.2985, 8.3063, 0.0002),  # DSCS
    'tab-3': np.arange(0.4499, 0.4517, 0.0002),  # LMR
}

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
                    id='kf-rfi-date-picker',
                    min_date_allowed=date(1995, 8, 5),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    date=date.today(),
                    className='w-100',
                ),
                html.Button('Submit', id='submit-val', n_clicks=0, className='btn btn-primary mt-2'),  # Submit button
            ], width=12, lg=3),
            dbc.Col([
                dcc.Tabs(
                    id="kf-channel-tabs", 
                    value='tab-1', 
                    children=[
                        dcc.Tab(label='Skynet', value='tab-1', className='text-white bg-secondary fw-bold'),
                        dcc.Tab(label='DSCS', value='tab-2', className='text-white bg-secondary fw-bold'),
                        dcc.Tab(label='LMR', value='tab-3', className='text-white bg-secondary fw-bold'),
                    ],
                    className='w-100 fs-5',
                ),
            ], width=12, lg=9),
        ]),
        dbc.Row(dbc.Col(html.Div(id='kf-tabs-content'), width=12)),
    ], className='mt-3')



@callback(
    Output('kf-tabs-content', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('kf-channel-tabs', 'value'),
     State('kf-rfi-date-picker', 'date')]
)
def update_channel_tab_content(n_clicks, tab, selected_date):
    if n_clicks == 0 or not selected_date:
        # If button hasn't been clicked or no date is selected, do nothing
        return "Please select a date and click submit."

    selected_date_formatted = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%Y%m%d')
    channel_frequencies = CHANNEL_FREQUENCIES[tab]
    plots = []

    # Separate DataFrames for SH1 and SH2
    aggregated_data_sh1 = pd.DataFrame()
    aggregated_data_sh2 = pd.DataFrame()

    # Fetch and aggregate data for SH1
    for frequency in channel_frequencies:
        df_sh1 = fetch_data_from_server("1", selected_date_formatted, frequency)
        if not df_sh1.empty:
            df_sh1['Frequency'] = frequency
            aggregated_data_sh1 = pd.concat([aggregated_data_sh1, df_sh1], ignore_index=True)
    
    # Fetch and aggregate data for SH2
    for frequency in channel_frequencies:
        df_sh2 = fetch_data_from_server("2", selected_date_formatted, frequency)
        if not df_sh2.empty:
            df_sh2['Frequency'] = frequency
            aggregated_data_sh2 = pd.concat([aggregated_data_sh2, df_sh2], ignore_index=True)

    # Generate plots if data is available
    if not aggregated_data_sh1.empty:
        fig_sh1 = generate_plot(aggregated_data_sh1, 'Signal Hound 1')
        plots.append(dcc.Graph(figure=fig_sh1))
    
    if not aggregated_data_sh2.empty:
        fig_sh2 = generate_plot(aggregated_data_sh2, 'Signal Hound 2')
        plots.append(dcc.Graph(figure=fig_sh2))

    if not plots:
        return "No data available for the selected parameters."
    
    return html.Div(plots)

def generate_plot(aggregated_data, title):
    """Generates a contour plot for the given data."""
    fig = go.Figure(data=go.Contour(
        z=aggregated_data['Power (dBm)'],
        x=aggregated_data['Timestamp'],
        y=aggregated_data['Frequency'],
        colorscale='Viridis',
        contours=dict(coloring='heatmap', showlabels=True,)
    ))
    fig.update_layout(
        title=f"Power Heat Contour Map for {title}",
        xaxis_title="Time",
        yaxis_title="Frequency (GHz)"
    )
    return fig

