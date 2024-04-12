import pandas as pd
import matplotlib.pyplot as plt

# Load the data
csv_path = '/mnt/4tbssd/channels/sh2_tdrs_2.2325/sh2_tdrs_daily_iqr_percents_2021_2022_2023.csv'
data = pd.read_csv(csv_path)

# Ensure 'Date' is a datetime type
data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d')

# Extract the year from the 'Date' for grouping
data['Year'] = data['Date'].dt.year

# Determine global min and max for "IQR Outlier Percent" to standardize y-axis across plots
global_min = data['IQR Percent for Frequency 2.2325'].min()
global_max = data['IQR Percent for Frequency 2.2325'].max()

# Slightly adjust the global max and min for better visualization
global_min -= (global_max - global_min) * 0.1
global_max += (global_max - global_min) * 0.1

# Get unique years for plotting
years = data['Year'].unique()

# Plot settings
plt.style.use('default')
plt.figure(figsize=(15, 6))  # Adjust figure size here to make it wider

for year in years:
    # Filter data for the year
    yearly_data = data[data['Year'] == year]
    
    # Plot data for the year with specified color and no marker
    plt.plot(yearly_data['Date'], yearly_data['IQR Percent for Frequency 2.2325'], linestyle='-', color='blue')

# General plot adjustments
plt.title('IQR Outlier Percent for TDRS 2.2325 GHz - 2021 to 2023')
plt.xlabel('Date')
plt.ylabel('IQR Outlier Percent')

# Set the same y-axis limits for the combined plot
plt.ylim(global_min, global_max)

plt.legend()
plt.grid(True)
plt.xticks(rotation=45)  # Rotate date labels for better readability
plt.tight_layout()  # Adjust layout to not cut off labels

# Save the combined plot
plot_path = '/mnt/4tbssd/channels/sh2_tdrs_2.2325/iqr_outlier_percent_plot_2021_to_2023_wide.png'
plt.savefig(plot_path, dpi=200)
#plt.show()  # Optionally display the plot

print(f'Combined plot saved: {plot_path}')

