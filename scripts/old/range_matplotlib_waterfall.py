import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from scipy.ndimage import gaussian_filter

def datetime_to_numerical(dt, reference_time):
    # Convert to hours since midnight
    return (dt - reference_time).total_seconds() / 3600

def process_file(filename, directory, file_pattern, reference_time):
    match = re.match(file_pattern, filename)
    if match:
        datetime_obj = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%Y%m%d %H%M%S")
        numerical_time = datetime_to_numerical(datetime_obj, reference_time)

        df = pd.read_csv(os.path.join(directory, filename))
        # Convert MHz to GHz
        frequencies_ghz = df['Frequency (MHz)'] / 1000
        return frequencies_ghz, np.full(len(df), numerical_time), df['Power (mW)']

    return np.array([]), np.array([]), np.array([])

def create_smooth_contour_plot(directory, output_directory, sigma=1, vmin=-100, vmax=-20):
    file_pattern = r"(\d{8})_(\d{6})_trace\.csv"
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for date in sorted(set(re.match(file_pattern, filename).group(1) for filename in os.listdir(directory) if re.match(file_pattern, filename))):
        reference_time = datetime.strptime(date, "%Y%m%d")

        with ThreadPoolExecutor() as executor:
            files = [filename for filename in os.listdir(directory) if filename.startswith(date)]
            futures = [executor.submit(process_file, filename, directory, file_pattern, reference_time) for filename in files]
            results = [future.result() for future in tqdm(futures, total=len(files), desc=f"Processing {date}")]

        if not results:
            continue  # Skip if no results

        frequencies, times, powers = zip(*results)
        frequencies = np.concatenate(frequencies)
        times = np.concatenate(times)
        powers = np.concatenate(powers)
        powers_log = 10 * np.log10(powers + 1e-12)  # Convert power to dBm

        unique_times = np.unique(times)
        unique_freqs = np.unique(frequencies)

        power_grid = np.zeros((len(unique_times), len(unique_freqs)))
        for i, (time, freq, power) in enumerate(zip(times, frequencies, powers_log)):
            t_idx = np.searchsorted(unique_times, time)
            f_idx = np.searchsorted(unique_freqs, freq)
            power_grid[t_idx, f_idx] = power

        power_grid_smoothed = gaussian_filter(power_grid, sigma=sigma)

        plt.figure(figsize=(12, 6))
        # Ensure the contour plot reflects the intended color scale range correctly
        contour = plt.contourf(unique_freqs, unique_times, power_grid_smoothed, levels=np.linspace(vmin, vmax, 50), cmap='viridis', vmin=vmin, vmax=vmax)
        cbar = plt.colorbar(label='Power (dBm)', ticks=np.linspace(vmin, vmax, 9))  # Define ticks on the color bar for clarity

        plt.xlabel('Frequency (GHz)')
        plt.ylabel('Time (hours since midnight)')
        plt.title(f'SH1 {reference_time.strftime("%Y-%m-%d")}')
        plt.tight_layout(pad=1.08)  # Reduce white border

        output_path = os.path.join(output_directory, f'sh1_{reference_time.strftime("%Y%m%d")}.png')
        plt.savefig(output_path)
        plt.close()  # Close the figure to free memory

# Example usage
directory_path = '/mnt/4tbssd/southpole_sh_data/sh1_2024/202403/20240302'
output_directory_path = '/mnt/4tbssd/plots'
create_smooth_contour_plot(directory_path, output_directory_path)
