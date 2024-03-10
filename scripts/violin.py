import csv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

def load_data(filepath, target_frequency):
    """Load signal data for a specific frequency from a CSV file."""
    data = []
    try:
        with open(filepath, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row[0] == target_frequency:
                    data = [float(value) for value in row[1:] if value]
                    break
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return data

def convert_to_dbm(mw_values):
    """Convert power values from mW to dBm."""
    return 10 * np.log10(mw_values)

def compute_statistics(data_dbm):
    """Compute statistics for data in dBm."""
    stats_values = {
        'Min': np.min(data_dbm),
        'Max': np.max(data_dbm),
        'Mean': np.mean(data_dbm),
        'Median': np.median(data_dbm),
        'Skewness': stats.skew(data_dbm),
        'Kurtosis': stats.kurtosis(data_dbm),
    }
    return stats_values

def create_plots(data, target_frequency, date):
    """Create a layout with a violin plot for the data."""
    data_dbm = convert_to_dbm(data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.violinplot(data=data_dbm, ax=ax, inner=None)
    sns.swarmplot(data=data_dbm, color='k', alpha=0.5)  # Add swarmplot for individual points
    
    ax.set_title(f'Violin Plot for Frequency {target_frequency} MHz on {date}', fontsize=16)
    ax.set_xlabel('Power (dBm)')
    
    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"
    data_file = "20210112.csv"
    target_frequency = '8099.5'  # Assuming frequency is in MHz
    full_path = os.path.join(directory_path, data_file)
    
    date = data_file.split('.')[0]
    date_formatted = f"{date[:4]}-{date[4:6]}-{date[6:]}"

    data = load_data(full_path, target_frequency)
    if data:
        create_plots(data, target_frequency, date_formatted)
    else:
        print("No data found for the specified frequency.")

if __name__ == "__main__":
    main()







