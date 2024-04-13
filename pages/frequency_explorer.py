from dash import html, dcc, Dash, callback, State
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from datetime import datetime
import plotly.figure_factory as ff
import requests
from io import StringIO

layout = html.Div([
    html.H1("Frequency Explorer", style={"textAlign": "center"}),
    html.Div([
        dcc.Input(
            id="signal-hound-input",
            type="number",
            placeholder="Signal Hound Number",
            style={"marginRight": "10px"}
        ),
        dcc.DatePickerSingle(
            id='date-picker-single',
            min_date_allowed=datetime(1995, 1, 1),
            max_date_allowed=datetime.now(),
            initial_visible_month=datetime.now(),
            date=datetime.now().date(),
            style={"marginRight": "10px"}
        ),
        dcc.Input(
            id="frequency-input",
            type="number",
            placeholder="Frequency in GHz",
            step=0.0001,
            style={"marginRight": "10px"}
        ),
        html.Button("Submit", id="submit-button", n_clicks=0, style={"marginLeft": "10px"}),
    ], style={"textAlign": "center", "marginTop": "20px"}),
    html.Div(id="statistics-output", style={"textAlign": "center", "marginBottom": "20px", "display": "flex", "flexWrap": "wrap", "justifyContent": "center"}),
    dcc.Graph(id="time-series-graph"),
    dcc.Graph(id="box-plot"),
    dcc.Graph(id="pdf-plot"),
    dcc.Graph(id="qq-plot"),
])

def generate_card_content(stat, value):
    """Generate HTML content for a statistic card."""
    return html.Div([
        html.Div(stat, style={"fontSize": 16, "color": "#4CAF50"}),  # Stat name
        html.Div(f"{value:.2f}", style={"fontSize": 20, "fontWeight": "bold"})  # Stat value
    ], style={
        "margin": "10px",
        "padding": "20px",
        "border": "1px solid #ddd",
        "borderRadius": "5px",
        "boxShadow": "2px 2px 10px rgba(0,0,0,0.1)",
        "display": "inline-block",
        "width": "140px",
        "textAlign": "center",
        "backgroundColor": "#F9F9F9"
    })

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
     Output('box-plot', 'figure'),
     Output('pdf-plot', 'figure'),
     Output('qq-plot', 'figure'),
     Output('statistics-output', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('signal-hound-input', 'value'),
     State('date-picker-single', 'date'),
     State('frequency-input', 'value')]
)
def update_graphs_and_stats(n_clicks, signal_hound_number, date_str, frequency): 
    if n_clicks < 1 or frequency is None or signal_hound_number is None: 
        return [{}, {}, {}, {}, "Enter all fields and click submit."] 

    formatted_date_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    df = fetch_data_from_server(signal_hound_number, formatted_date_str, frequency)
    if df.empty:
        return [{}, {}, {}, {}, "No data available for the selected parameters."]
    
    # Time Series Graph
    time_series_fig = go.Figure(
        data=[go.Scatter(x=df['Timestamp'], y=df['Power (dBm)'], mode='lines+markers', name='Power')]
    )
    time_series_fig.update_layout(
        title="Time Series of Power",
        xaxis_title="Time",
        yaxis_title="Power (dBm)",
        xaxis=dict(tickformat="%H:%M:%S")
    )
    
    # Box Plot - Now Horizontal
    box_plot_fig = go.Figure(
        data=[go.Box(x=df['Power (dBm)'], name='Power', orientation='h')]
    )
    box_plot_fig.update_layout(
        title="Power Distribution Box Plot",
        yaxis_title="Power",
        xaxis_title="Power (dBm)"
    )
    
    # PDF Plot
    pdf_plot_fig = ff.create_distplot(
        [df['Power (dBm)'].values], ['Power'], show_hist=False, show_rug=False
    )
    pdf_plot_fig.update_layout(
        title="Probability Density Function of Power"
    )
    
    # QQ Plot
    qq_data = np.sort(df['Power (dBm)'].values)
    theoretical_quantiles = np.sort(np.random.normal(np.mean(qq_data), np.std(qq_data), len(qq_data)))
    qq_plot_fig = go.Figure(
        data=[go.Scatter(x=theoretical_quantiles, y=qq_data, mode='markers', name='Quantiles')]
    )
    qq_plot_fig.update_layout(
        title="Q-Q Plot of Power Distribution",
        xaxis_title="Theoretical Quantiles",
        yaxis_title="Sample Quantiles"
    )
    
    # Statistics
    stats_describe = df['Power (dBm)'].describe()
    additional_stats = pd.Series({
        "Skewness": skew(df['Power (dBm)'].values),
        "Kurtosis": kurtosis(df['Power (dBm)'].values, fisher=True)
    })

    stats_all = pd.concat([stats_describe, additional_stats])
    
    stats_output = html.Div(
        [generate_card_content(stat, value) for stat, value in stats_all.items()],
        style={"textAlign": "center", "display": "flex", "flexWrap": "wrap", "justifyContent": "center"}
    )

    # Return the updated figures and stats content 
    return time_series_fig, box_plot_fig, pdf_plot_fig, qq_plot_fig, stats_output 
