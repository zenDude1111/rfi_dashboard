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
    """Create a layout with a horizontal boxplot, PDF plot underneath, then Q-Q plot and statistics underneath that."""
    data_dbm = convert_to_dbm(data)
    
    fig = plt.figure(figsize=(12, 12))  # Adjust figure size for better fit
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 2, 1])  # Define grid layout

    fig.suptitle(f'Analysis for Frequency {target_frequency} MHz on {date}', fontsize=16)

    # Boxplot
    ax0 = fig.add_subplot(gs[0, :])  # Boxplot across the top
    sns.boxplot(data=data_dbm, orient="h", ax=ax0)
    ax0.set_title('Horizontal Boxplot (dBm)')
    ax0.set_xlim([np.min(data_dbm)-5, np.max(data_dbm)+5])  # Extend the x-axis scale for box plot

    # PDF with Normal Distribution Overlay
    ax1 = fig.add_subplot(gs[1, :])  # PDF plot below the boxplot
    sns.kdeplot(data_dbm, ax=ax1, label="PDF (dBm)", bw_adjust=0.5)
    mean, std = np.mean(data_dbm), np.std(data_dbm)
    xmin, xmax = ax1.get_xlim()
    x = np.linspace(np.min(data_dbm)-5, np.max(data_dbm)+5, 100)  # Extend the x-axis scale for PDF plot
    p = stats.norm.pdf(x, mean, std)
    ax1.plot(x, p, 'k--', linewidth=2, label="Normal Distribution Overlay")
    ax1.set_title('PDF with Normal Distribution Overlay (dBm)')
    ax1.legend()
    ax1.set_xlim([np.min(data_dbm)-5, np.max(data_dbm)+5])  # Extend the x-axis scale for PDF plot

    # Add quartile lines to PDF plot
    quartiles = np.percentile(data_dbm, [25, 50, 75])
    for quartile in quartiles:
        ax1.axvline(quartile, color='r', linestyle='--', linewidth=1)

    # Q-Q Plot
    ax2 = fig.add_subplot(gs[2, 0])  # Q-Q plot in the bottom left
    stats.probplot(data_dbm, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot (dBm)')

    # Statistics
    ax3 = fig.add_subplot(gs[2, 1])  # Statistics display in the bottom right
    ax3.axis('off')  # Hide the axis
    statistics = compute_statistics(data_dbm)
    stats_text = '\n'.join([f'{key}: {value:.4f}' for key, value in statistics.items()])
    ax3.text(0.5, 0.5, stats_text, ha='center', va='center', fontsize=10, transform=ax3.transAxes,
             bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=1'))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"
    data_file = "20210112.csv"
    target_frequency = '449.5'  # Assuming frequency is in MHz
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







