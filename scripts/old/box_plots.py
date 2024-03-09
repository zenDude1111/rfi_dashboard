import csv
import numpy as np
import matplotlib.pyplot as plt
import os

def load_data_for_all_frequencies(filepath):
    """Load signal data from a CSV file and organize by frequency."""
    data_by_frequency = {}
    try:
        with open(filepath, mode='r', newline='') as infile:
            reader = csv.reader(infile)
            for row in reader:
                frequency = row[0]
                readings = [float(value) for value in row[1:] if value]
                if frequency in data_by_frequency:
                    data_by_frequency[frequency].extend(readings)
                else:
                    data_by_frequency[frequency] = readings
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return data_by_frequency

def plot_box(data_by_frequency, target_frequencies):
    """Generate horizontal box plots for the specified frequencies."""
    data_to_plot = [data_by_frequency[freq] for freq in target_frequencies if freq in data_by_frequency]
    labels = [freq for freq in target_frequencies if freq in data_by_frequency]
    
    plt.figure(figsize=(12, 6))
    plt.boxplot(data_to_plot, labels=labels, vert=False)  # Set vert=False for horizontal box plots
    plt.title("Horizontal Box Plot of Power Readings by Frequency")
    plt.xlabel("Power Readings")
    plt.ylabel("Frequency")
    plt.show()

def main():
    directory_path = "D:\\SouthPole_Signal_Data\\2021"  # Update as necessary
    data_file = "20210112.csv"  # Ensure this file exists
    full_path = os.path.join(directory_path, data_file)
    target_frequencies = ['8000.1']  # Update as necessary, can add more frequencies to compare

    data_by_frequency = load_data_for_all_frequencies(full_path)
    if data_by_frequency:
        plot_box(data_by_frequency, target_frequencies)
    else:
        print("No data found.")

if __name__ == "__main__":
    main()

