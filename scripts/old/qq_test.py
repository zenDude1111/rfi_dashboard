import csv
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import os

def load_data(filepath, frequency):
    """Load signal data matching the specified frequency from a CSV file."""
    try:
        with open(filepath, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row[0] == frequency:
                    return [float(value) for value in row[1:] if value]
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def plot_qq(readings, dist_type="expon"):
    """Generate a Q-Q plot comparing readings to a specified distribution."""
    plt.figure(figsize=(8, 6))
    stats.probplot(readings, dist=dist_type, plot=plt)
    plt.title(f"Q-Q Plot of Power Readings vs. {dist_type.capitalize()} Distribution")
    plt.xlabel("Theoretical Quantiles")
    plt.ylabel("Ordered Values (Power)")
    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"  # Update as necessary
    data_file = "20210112.csv"  # Ensure this file exists
    target_frequency = '8099.5'  # Update as necessary
    full_path = os.path.join(directory_path, data_file)

    readings = load_data(full_path, target_frequency)
    if readings:
        plot_qq(readings, dist_type="expon")
    else:
        print("No data found for the specified frequency or an error occurred.")

if __name__ == "__main__":
    main()

