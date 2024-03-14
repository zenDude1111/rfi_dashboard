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
    data_dbm = convert_to_dbm(data)
    mean = np.mean(data_dbm)
    std = np.std(data_dbm)
    q1, median, q3 = np.percentile(data_dbm, [25, 50, 75])
    iqr = q3 - q1
    
    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, figsize=(12, 12))
    fig.suptitle(f'Analysis for Frequency {target_frequency} MHz on {date}', fontsize=16)
    
    medianprops = dict(linestyle='-', linewidth=2, color='yellow')
    sns.boxplot(x=data_dbm, color='lightcoral', saturation=1, medianprops=medianprops,
                flierprops={'markerfacecolor': 'mediumseagreen'}, whis=1.5, ax=ax1)

    ticks = [mean + std * i for i in range(-4, 5)]
    ticklabels = [f'${i}\\sigma$' for i in range(-4, 5)]
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(ticklabels)
    ax1.set_yticks([])
    ax1.tick_params(labelbottom=True)
    ax1.set_ylim(-1, 1.5)

    # Enhanced annotations
    ax1.errorbar([q1, q3], [1, 1], yerr=[0.2, 0.2], color='black', lw=1)
    ax1.text(q1, 0.6, 'Q1', ha='center', va='center', color='black')
    ax1.text(q3, 0.6, 'Q3', ha='center', va='center', color='black')
    ax1.text(median, -0.6, 'median', ha='center', va='center', color='black')
    ax1.text(median, 1.2, 'IQR', ha='center', va='center', color='black')
    ax1.text(q1 - 1.5*iqr, 0.4, 'Q1 - 1.5*IQR', ha='center', va='center', color='black')
    ax1.text(q3 + 1.5*iqr, 0.4, 'Q3 + 1.5*IQR', ha='center', va='center', color='black')

    sns.kdeplot(data_dbm, ax=ax2)
    kdeline = ax2.lines[0]
    xs = kdeline.get_xdata()
    ys = kdeline.get_ydata()

    ylims = ax2.get_ylim()
    ax2.fill_between(xs, 0, ys, color='mediumseagreen', alpha=0.5)
    ax2.fill_between(xs, 0, ys, where=(xs >= q1 - 1.5*iqr) & (xs <= q3 + 1.5*iqr), color='skyblue', alpha=0.5)
    ax2.fill_between(xs, 0, ys, where=(xs >= q1) & (xs <= q3), color='lightcoral', alpha=0.5)
    ax2.set_ylim(0, ylims[1])

    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"
    data_file = "20210112.csv"
    target_frequency = '8000.1'  # Assuming frequency is in MHz
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