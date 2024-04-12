import pandas as pd
import matplotlib.pyplot as plt

# Load the data
csv_path = '/mnt/4tbssd/channels/sh2_skynet_8.0995/sh2_skynet_daily_iqr_percents_2021_2022_2023.csv'
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

for year in years:
    # Filter data for the year
    yearly_data = data[data['Year'] == year]
    
    # Create a new figure for each year
    plt.figure(figsize=(10, 6))
    plt.plot(yearly_data['Date'], yearly_data['IQR Percent for Frequency 2.2325'], marker='o', linestyle='-', label=f'IQR Outlier Percent for {year}')
    plt.title(f'IQR Outlier Percent for TDRS 2.2325 GHz - {year}')
    plt.xlabel('Date')
    plt.ylabel('IQR Outlier Percent')
    
    # Set the same y-axis limits for all plots
    plt.ylim(global_min, global_max)
    
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)  # Rotate date labels for better readability
    plt.tight_layout()  # Adjust layout to not cut off labels
    
    # Save each plot with a unique filename based on the year
    plot_path = f'/mnt/4tbssd/channels/sh2_tdrs_2.2325/iqr_outlier_percent_plot_{year}.png'
    plt.savefig(plot_path)
    plt.close()  # Close the figure to free memory

    print(f'Plot saved for {year}: {plot_path}')


