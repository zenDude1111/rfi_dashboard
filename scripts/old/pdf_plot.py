import csv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os

def load_data_for_all_frequencies(filepath, target_frequencies):
    """Load signal data from a CSV file and organize by frequency."""
    data_by_frequency = {freq: [] for freq in target_frequencies}
    try:
        with open(filepath, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row[0] in target_frequencies:
                    # Transform readings to log power immediately upon reading
                    data_by_frequency[row[0]].extend([np.log10(float(value)) for value in row[1:] if value and float(value) > 0])
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return data_by_frequency

def plot_pdf_with_normal_overlay(data_by_frequency):
    """Generate KDE plots with a normal distribution overlay for the specified frequencies."""
    plt.figure(figsize=(12, 6))
    for freq, data in data_by_frequency.items():
        if data:  # Check if there's data for the frequency
            # Plot KDE for log-transformed data
            sns.kdeplot(data, label=f'Freq: {freq} MHz', bw_adjust=0.5)
            # Overlay Normal Distribution for log-transformed data
            mean, std = np.mean(data), np.std(data)
            xmin, xmax = plt.xlim()
            x = np.linspace(xmin, xmax, 100)
            p = stats.norm.pdf(x, mean, std)
            plt.plot(x, p, 'k', linewidth=2, label=f'Normal Dist for Freq: {freq} MHz')
    plt.title("Probability Density Function of Log-transformed Power Readings by Frequency with Normal Distribution Overlay")
    plt.xlabel("Log-transformed Power Readings")
    plt.ylabel("Density")
    plt.legend()
    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"
    data_file = "20210112.csv"
    full_path = os.path.join(directory_path, data_file)
    target_frequencies = ['449.9']  # Update to the specific frequency or frequencies of interest

    data_by_frequency = load_data_for_all_frequencies(full_path, target_frequencies)
    if any(data_by_frequency.values()):  # Check if any data was loaded
        plot_pdf_with_normal_overlay(data_by_frequency)
    else:
        print("No data found for the specified frequencies.")

if __name__ == "__main__":
    main()

