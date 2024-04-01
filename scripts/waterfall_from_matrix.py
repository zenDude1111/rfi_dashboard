import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define the paths
input_csv_path = '/mnt/4tbssd/time_series_matrix_data/sh1/2021/20210101_matrix.csv'  # Update this path
output_plot_path = '/mnt/4tbssd/plots/jet4_sh1_20210101.png'  # Update this path

# Read the CSV file
data = pd.read_csv(input_csv_path, index_col='Frequency (GHz)')

# Function to convert timestamps to hours since midnight
def hours_since_midnight(s):
    return (pd.to_datetime(s).hour + pd.to_datetime(s).minute / 60 + pd.to_datetime(s).second / 3600)

# Convert the column headers (timestamps) to hours since midnight
time_stamps = [hours_since_midnight(ts) for ts in data.columns]

# Create meshgrid for frequencies and times
F, T = np.meshgrid(data.index, time_stamps)

# Transpose the data to align with the meshgrid, skipping the frequency column
power_readings = data.values.T  # Transpose to align with F and T dimensions

# Create the plot
plt.figure(figsize=(10, 6))
c = plt.pcolormesh(F, T, power_readings, shading='auto', cmap='jet', vmin=-100, vmax=-60)

# Labeling
plt.xlabel('Frequency (GHz)')
plt.ylabel('Time since midnight (hours)')
plt.title('Waterfall Plot of Power Readings')
plt.colorbar(c, label='Power (dBm)')

# Save the plot to a file
plt.tight_layout()
plt.savefig(output_plot_path)

# Optionally display the plot as well
# plt.show()
