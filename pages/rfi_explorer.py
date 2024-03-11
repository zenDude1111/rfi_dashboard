from dash import html, dcc, callback, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from datetime import datetime
import os
import plotly.figure_factory as ff
import glob

# Assuming your project structure includes a data folder like so: project_root/data/yyyy-mm-dd/
DATA_FOLDER = 'data'

def load_and_process_data(date_str, target_frequency):
    """Loads and processes RFI data for the given date, filtering for the specified frequency."""
    date_formatted = date_str.replace('-', '')  # Adjust date format to match file naming convention
    folder_path = os.path.join(DATA_FOLDER, date_formatted)
    pattern = os.path.join(folder_path, f"{date_formatted}_*_trace.csv")  # Pattern to match all files for the given date

    compiled_data = []
    times = []

    for file_path in glob.glob(pattern):
        # Extract timestamp from the filename (format assumed as 'yyyymmdd_hhmmss_trace.csv')
        timestamp = file_path.split('_')[1]
        try:
            df = pd.read_csv(file_path, header=None, names=['Frequency', 'Power_mW'])
            df = df[df['Frequency'] == target_frequency]
            if not df.empty:
                df['Power_dBm'] = 10 * np.log10(df['Power_mW'])
                df['Timestamp'] = pd.to_datetime(date_str + ' ' + timestamp, format='%Y-%m-%d %H%M%S')
                compiled_data.append(df)
                times.extend([timestamp] * len(df))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if compiled_data:
        full_df = pd.concat(compiled_data, ignore_index=True)
        full_df['Time'] = [t.time() for t in full_df['Timestamp']]  # Extract time from Timestamp for plotting
        return full_df
    else:
        return pd.DataFrame(columns=['Frequency', 'Power_mW', 'Power_dBm', 'Timestamp', 'Time'])

layout = html.Div([
    html.H1("RFI Explorer", style={"textAlign": "center"}),
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
            placeholder="Frequency in MHz",
            style={"marginLeft": "10px"}
        ),
        html.Button("Submit", id="submit-button", n_clicks=0, style={"marginLeft": "10px"}),
    ], style={"textAlign": "center"}),
    dcc.Graph(id="time-series-graph"),
    dcc.Graph(id="box-plot"),
    dcc.Graph(id="pdf-plot"),
    dcc.Graph(id="qq-plot"),
    html.Div(id="statistics-output", style={"textAlign": "center"})
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
        return [{}, {}, {}, {}, "Please select a date and enter a frequency."]

    df = load_and_process_data(date_str, frequency)
    if df.empty:
        return [{}, {}, {}, {}, "No data available for the selected date and frequency."]

    # Time Series Graph
    time_series_fig = go.Figure(
        data=[go.Scatter(x=df['Timestamp'], y=df['Power_dBm'], mode='lines+markers', name='Power')]
    )
    time_series_fig.update_layout(
        title="Time Series of Power",
        xaxis_title="Time",
        yaxis_title="Power (dBm)",
        xaxis=dict(tickformat="%H:%M:%S")
    )

    # Box Plot
    box_plot_fig = go.Figure(
        data=[go.Box(y=df['Power_dBm'], name='Power')]
    )
    box_plot_fig.update_layout(
        title="Power Distribution Box Plot"
    )

    # PDF Plot
    pdf_plot_fig = ff.create_distplot(
        [df['Power_dBm']], ['Power'], show_hist=False, show_rug=False
    )
    pdf_plot_fig.update_layout(
        title="Probability Density Function of Power"
    )

    # QQ Plot
    qq_data = np.sort(df['Power_dBm'])
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
    stats_describe = df['Power_dBm'].describe()
    additional_stats = {
        "Skewness": skew(df['Power_dBm']),
        "Kurtosis": kurtosis(df['Power_dBm'], fisher=True)  # Fisher's definition (true kurtosis minus 3)
    }
    stats_describe = stats_describe.append(pd.Series(additional_stats, name='Additional Stats'))

    stats_output = html.Ul([html.Li(f"{stat}: {value:.2f}") for stat, value in stats_describe.items()])

    return time_series_fig, box_plot_fig, pdf_plot_fig, qq_plot_fig, stats_output
