from dash import html, dcc, callback, State, callback_context
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from datetime import datetime, timedelta
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
    dbc.Card(
        dbc.CardBody(
            html.Div([
                # Device buttons and frequency input on the left
                html.Div([
                    dbc.RadioItems(
                        id='fe-signal-hound-input',
                        options=[
                            {'label': 'SH1-MAPO', 'value': 'sh1'},
                            {'label': 'SH2-DSL', 'value': 'sh2'},
                            {'label': 'Anritsu-DSL', 'value': 'anritsu'}
                        ],
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-secondary",
                        labelCheckedClassName="btn btn-secondary"
                    ),
                    dcc.Input(
                        id="fe-frequency-input",
                        type="number",
                        placeholder="Frequency in GHz",
                        step=0.0001,
                        className="me-2"
                    ),
                ], style={'flex': '2', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start'}),

                # "Frequency Explorer" title in the middle
                html.Div([
                    html.H5("Frequency Explorer", className="card-title"),
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                # Date picker and navigation buttons on the right
                html.Div([
                    dbc.Button('Backward', id='fe-backward-button', n_clicks=0, color="secondary", className="me-2"),
                    dcc.DatePickerSingle(
                        id='fe-date-picker-single',
                        min_date_allowed=datetime(1995, 1, 1),
                        max_date_allowed=datetime.now(),
                        initial_visible_month=datetime.now(),
                        date=datetime.now().date(),
                        className="me-2"
                    ),
                    dbc.Button('Forward', id='fe-forward-button', n_clicks=0, color="secondary", className="ms-2"),
                ], style={'flex': '2', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'gap': '10px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'gap': '10px'})
        ),
        style={'margin': '20px'}
    ),
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

def no_data_figure():
    fig = go.Figure()
    fig.add_annotation(text="No data available",
                       xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=20, color="red"))
    fig.update_layout(template='plotly_dark',
                      xaxis=dict(visible=False),
                      yaxis=dict(visible=False))
    return fig

@callback(
    [Output('time-series-graph', 'figure'),
     Output('combined-plot', 'figure'),
     Output('statistics-output', 'children')],
    [Input('fe-signal-hound-input', 'value'),
     Input('fe-date-picker-single', 'date'),
     Input('fe-frequency-input', 'value')]
)
def update_graphs_and_stats(signal_hound_number, date_str, frequency):
    if not signal_hound_number or not frequency:
        return no_data_figure(), no_data_figure(), "Enter all fields and click submit."
    formatted_date_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    df = fetch_data_from_server(signal_hound_number, formatted_date_str, frequency)
    if df.empty:
        return no_data_figure(), no_data_figure(), "No data available for the selected parameters."

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

@callback(
    Output('fe-date-picker-single', 'date'),
    [Input('fe-backward-button', 'n_clicks'),
     Input('fe-forward-button', 'n_clicks')],
    [State('fe-date-picker-single', 'date')]
)
def update_date(backward_clicks, forward_clicks, current_date):
    if not callback_context.triggered:
        return current_date
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    current_date_obj = pd.to_datetime(current_date)

    if button_id == 'fe-backward-button':
        new_date = current_date_obj - timedelta(days=1)
    elif button_id == 'fe-forward-button':
        new_date = current_date_obj + timedelta(days=1)
    else:
        new_date = current_date_obj

    return new_date.strftime('%Y-%m-%d')
