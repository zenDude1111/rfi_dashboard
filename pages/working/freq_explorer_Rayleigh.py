from dash import html, dcc, Dash, callback, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew, rayleigh, norm
from datetime import datetime
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import os
from dash import callback_context

DATA_FOLDER = '/mnt/4tbssd/southpole_sh_data/sh2_2024/202403/20240301'  # Update this path to where your data is stored

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
    dcc.Graph(id="pdf-plot-gaussian"),  # Corrected: Added this line for Gaussian PDF
    dcc.Graph(id="qq-plot"),
])

@callback(
    [Output('time-series-graph', 'figure'),
     Output('box-plot', 'figure'),
     Output('pdf-plot', 'figure'),  # This will now show Rayleigh PDF
     Output('pdf-plot-gaussian', 'figure'),  # Corrected: This output is for Gaussian PDF
     Output('qq-plot', 'figure'),  # Updated to compare with both distributions
     Output('statistics-output', 'children')],
    [Input('submit-button', 'n_clicks')],
    [Input('date-picker-single', 'date'),
     Input('frequency-input', 'value')]
)
# Complete the callback function
def update_graphs_and_stats(n_clicks, date_str, frequency):
    # Check if the callback was triggered by the submit button
    ctx = callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'].split('.')[0] != 'submit-button':
        return [go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(), []]

    # Load and process the data
    df = load_and_process_data(date_str, frequency)
    if df.empty:
        return [go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(), "No data available for the selected date and frequency."]
    
    # Generate the plots and statistics using the loaded data

    # Time Series Graph
    time_series_fig = go.Figure(data=[go.Scatter(x=df['Timestamp'], y=df['Power (dBm)'], mode='lines+markers', name='Power')])
    time_series_fig.update_layout(title="Time Series of Power", xaxis_title="Time", yaxis_title="Power (dBm)", xaxis=dict(tickformat="%H:%M:%S"))
    
    # Box Plot - Now Horizontal
    box_plot_fig = go.Figure(data=[go.Box(x=df['Power (dBm)'], name='Power', orientation='h')])
    box_plot_fig.update_layout(title="Power Distribution Box Plot", xaxis_title="Power (dBm)")

    power_data = df['Power (dBm)'].values

    # Rayleigh Distribution
    sigma_est = np.sqrt(np.mean(power_data**2) / 2)
    x_values_rayleigh = np.linspace(0, max(power_data) * 1.1, 1000)
    rayleigh_pdf = rayleigh.pdf(x_values_rayleigh, scale=sigma_est)

    # Plot the Rayleigh distribution
    pdf_plot_rayleigh = go.Figure(data=[go.Scatter(x=x_values_rayleigh, y=rayleigh_pdf, name='Rayleigh PDF', mode='lines')])
    pdf_plot_rayleigh.update_layout(title="Rayleigh Distribution PDF of Power", xaxis_title="Power (dBm)", yaxis_title="Probability Density")

    # Gaussian Distribution
    mu, std = norm.fit(power_data)
    # For the Gaussian distribution, adjust x_values to cover μ ± 3σ
    x_values_gaussian = np.linspace(mu - 3*std, mu + 3*std, 1000)
    gaussian_pdf = norm.pdf(x_values_gaussian, loc=mu, scale=std)

    # Plot the Gaussian distribution
    pdf_plot_gaussian = go.Figure(data=[go.Scatter(x=x_values_gaussian, y=gaussian_pdf, name='Gaussian PDF', mode='lines')])
    pdf_plot_gaussian.update_layout(title="Gaussian Distribution PDF of Power", xaxis_title="Power (dBm)", yaxis_title="Probability Density")
    
    # Q-Q Plot for both Rayleigh and Gaussian Distributions
    qq_plot_fig = make_subplots(rows=1, cols=2, subplot_titles=("Rayleigh Q-Q Plot", "Gaussian Q-Q Plot"))
    
    # Rayleigh Q-Q
    theoretical_quantiles_rayleigh = np.sort(rayleigh.rvs(scale=sigma_est, size=len(power_data)))
    qq_plot_fig.add_trace(go.Scatter(x=theoretical_quantiles_rayleigh, y=np.sort(power_data), mode='markers', name='Rayleigh Quantiles'), row=1, col=1)
    
    # Gaussian Q-Q
    theoretical_quantiles_gaussian = np.sort(norm.rvs(loc=mu, scale=std, size=len(power_data)))
    qq_plot_fig.add_trace(go.Scatter(x=theoretical_quantiles_gaussian, y=np.sort(power_data), mode='markers', name='Gaussian Quantiles'), row=1, col=2)
    qq_plot_fig.update_layout(title="Q-Q Plots for Rayleigh and Gaussian Distributions")
    
    # Statistics
    stats_describe = df['Power (dBm)'].describe()
    additional_stats = pd.Series({
        "Skewness": skew(df['Power (dBm)'].values),
        "Kurtosis": kurtosis(df['Power (dBm)'].values, fisher=True)
    })
    stats_all = pd.concat([stats_describe, additional_stats])
    stats_output = [generate_card_content(stat, value) for stat, value in stats_all.items()]
    
    return time_series_fig, box_plot_fig, pdf_plot_rayleigh, pdf_plot_gaussian, qq_plot_fig, stats_output

