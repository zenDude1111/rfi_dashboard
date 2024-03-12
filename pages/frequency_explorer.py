from dash import html, dcc, Dash, callback, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from datetime import datetime
import plotly.figure_factory as ff
import os

DATA_FOLDER = r'assets/csv/time_series'  # Update this path to where your data is stored

def load_and_process_data(date_str, target_frequency_ghz):
    date_formatted = date_str.replace('-', '')
    file_path = os.path.join(DATA_FOLDER, f"{date_formatted}_matrix.csv")
    
    try:
        df = pd.read_csv(file_path, index_col=0)
        df.index = df.index.astype(float)  # Ensure index is float for frequency comparison
        target_frequency_ghz = float(target_frequency_ghz)  # Ensure input frequency is float
        
        if target_frequency_ghz not in df.index:
            print(f"Frequency {target_frequency_ghz} GHz not found in the DataFrame.")
            return pd.DataFrame()

        power_values_row = df.loc[target_frequency_ghz]
        power_values_df = power_values_row.to_frame(name='Power (dBm)').reset_index()
        power_values_df.rename(columns={'index': 'Timestamp'}, inplace=True)
        power_values_df['Timestamp'] = pd.to_datetime(power_values_df['Timestamp'], format='%H:%M:%S').dt.time

        return power_values_df
    except Exception as e:
        print(f"Error loading or processing {file_path}: {e}")
        return pd.DataFrame()

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

layout = html.Div([
    html.H1("Frequency Explorer", style={"textAlign": "center"}),
    html.Div([
        dcc.DatePickerSingle(
            id='date-picker-single',
            min_date_allowed=datetime(1995, 1, 1),
            max_date_allowed=datetime.now(),
            initial_visible_month=datetime.now(),
            date=datetime.now().date()
        ),
        dcc.Input(
            id="frequency-input",
            type="number",
            placeholder="Frequency in GHz",
            step=0.0001,
            style={"marginLeft": "10px"}
        ),
        html.Button("Submit", id="submit-button", n_clicks=0, style={"marginLeft": "10px"}),
    ], style={"textAlign": "center"}),
    html.Div(id="statistics-output", style={"textAlign": "center", "marginBottom": "20px", "display": "flex", "flexWrap": "wrap", "justifyContent": "center"}),  # Prepared for cards
    dcc.Graph(id="time-series-graph"),
    dcc.Graph(id="box-plot"),
    dcc.Graph(id="pdf-plot"),
    dcc.Graph(id="qq-plot"),
])

@callback(
    [Output('time-series-graph', 'figure'),
     Output('box-plot', 'figure'),
     Output('pdf-plot', 'figure'),
     Output('qq-plot', 'figure'),
     Output('statistics-output', 'children')],
    [Input('submit-button', 'n_clicks')],
    [Input('date-picker-single', 'date'),
     Input('frequency-input', 'value')]
)
def update_graphs_and_stats(n_clicks, date_str, frequency):
    if n_clicks < 1 or frequency is None:
        return [{}, {}, {}, {}, []]  # Updated to return an empty list for stats
    
    df = load_and_process_data(date_str, frequency)
    if df.empty:
        return [{}, {}, {}, {}, "No data available for the selected date and frequency."]
    
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
    
    return time_series_fig, box_plot_fig, pdf_plot_fig, qq_plot_fig, stats_output

