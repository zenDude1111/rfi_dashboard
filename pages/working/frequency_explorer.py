from dash import html, dcc, callback, State
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from datetime import datetime
import plotly.figure_factory as ff
import requests
from io import StringIO

def generate_card_content(stat, value):
    """Generate HTML content for a statistic card with Bootstrap classes."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(stat, className="card-title"),
            html.P(f"{value:.2f}", className="card-text"),
        ]),
        className="m-2 text-center",
        style={"width": "140px", "backgroundColor": "#F9F9F9"}
    )

layout = html.Div([
    html.H4("Frequency Explorer", className="text-center mb-4"),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dcc.RadioItems(
                        id='fe-signal-hound-input',
                        options=[
                            {'label': 'SH1-MAPO', 'value': '1'},
                            {'label': 'SH2-DSL', 'value': '2'}
                        ],
                        inline=False,
                        className="me-2"
                    )
                ]),
                className="mb-2"
            ),
            width="auto"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dcc.DatePickerSingle(
                        id='fe-date-picker-single',
                        min_date_allowed=datetime(1995, 1, 1),
                        max_date_allowed=datetime.now(),
                        initial_visible_month=datetime.now(),
                        date=datetime.now().date(),
                        className="me-2"
                    )
                ]),
                className="mb-2"
            ),
            width="auto"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dcc.Input(
                        id="fe-frequency-input",
                        type="number",
                        placeholder="Frequency in GHz",
                        step=0.0001,
                        className="me-2"
                    )
                ]),
                className="mb-2"
            ),
            width="auto"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.Button("Submit", id="fe-submit-button", n_clicks=0, className="btn btn-secondary")
                ]),
                className="mb-4"
            ),
            width="auto"
        )
    ], className="justify-content-center"),
    html.Div(id="statistics-output", className="text-center mb-4 d-flex flex-wrap justify-content-center"),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="time-series-graph"))), width=12, className="mb-4"),
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="combined-plot", style={"height": "800px"}))), width=12, className="mb-4"),
    ], className="justify-content-center")
], className="container")

def fetch_data_from_server(signal_hound_number, date_str, target_frequency_ghz):
    url = f"http://universe.phys.unm.edu/data/time_series_matrix_data/sh{signal_hound_number}/{date_str}/{target_frequency_ghz}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Wrap the JSON string in a StringIO object
            json_str_io = StringIO(response.text)
            data_df = pd.read_json(json_str_io, orient='records')
            return data_df
        else:
            print(f"Error fetching data: Status code {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Exception while fetching data: {e}")
        return pd.DataFrame()

@callback(
    [Output('time-series-graph', 'figure'),
     Output('combined-plot', 'figure'),
     Output('statistics-output', 'children')],
    [Input('fe-submit-button', 'n_clicks')],
    [State('fe-signal-hound-input', 'value'),
     State('fe-date-picker-single', 'date'),
     State('fe-frequency-input', 'value'),]
)
def update_graphs_and_stats(n_clicks, signal_hound_number, date_str, frequency):
    if n_clicks < 1 or frequency is None or signal_hound_number is None:
        return [{}, {}, "Enter all fields and click submit."]
    formatted_date_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    df = fetch_data_from_server(signal_hound_number, formatted_date_str, frequency)
    if df.empty:
        return [{}, {}, "No data available for the selected parameters."]

    time_series_fig = go.Figure(
        data=[go.Scattergl(x=df['Timestamp'], y=df['Power (dBm)'], mode='lines+markers', name='Power')]
    )
    time_series_fig.update_layout(
        title="Time Series of Power",
        xaxis_title="Time",
        yaxis_title="Power (dBm)",
        xaxis=dict(tickformat="%H:%M:%S")
    )

    # Combined Box Plot and PDF Plot
    combined_fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.3, 0.5],
        vertical_spacing=0.02
    )

    # Adding Box plot
    combined_fig.add_trace(
        go.Box(x=df['Power (dBm)'], name='Power', marker_color='blue', boxmean=False),
        row=1, col=1
    )

    # Adding PDF plot
    hist_data = [df['Power (dBm)']]
    group_labels = ['Power']
    fig_dist = ff.create_distplot(hist_data, group_labels, show_hist=False, show_rug=False)

    for trace in fig_dist['data']:
        combined_fig.add_trace(trace, row=2, col=1)

    combined_fig.update_layout(
        title="Power Distribution and Density",
        xaxis2_title="Power (dBm)",
        yaxis=dict(title="Density"),
        showlegend=False
    )

    # Statistics
    stats_describe = df['Power (dBm)'].describe()
    additional_stats = pd.Series({
        "Skewness": skew(df['Power (dBm)'].values),
        "Kurtosis": kurtosis(df['Power (dBm)'].values, fisher=True)
    })

    stats_all = pd.concat([stats_describe[['count', 'min', 'max', 'mean']], additional_stats])

    stats_output = html.Div(
        [generate_card_content(stat, value) for stat, value in stats_all.items()],
        style={"textAlign": "center", "display": "flex", "flexWrap": "wrap", "justifyContent": "center"}
    )

    # Return the updated figures and stats content
    return time_series_fig, combined_fig, stats_output
