import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

def convert_power_mw_to_dbm(power_mw):
    """Convert power from mW to dBm."""
    return 10 * np.log10(power_mw)

def process_file(file_path):
    """Process an individual file to read, convert, and structure its data."""
    try:
        # Extract timestamp from the file name
        file_name = os.path.basename(file_path)
        timestamp = datetime.strptime(file_name.split('_')[1], '%H%M%S').strftime('%H:%M:%S')
        # Read CSV file, specifying usecols to only read the first two columns
        df = pd.read_csv(file_path, usecols=[0, 1], names=['Frequency (MHz)', 'Amplitude Min(mW)'], skiprows=1)
        # Convert frequency to GHz and power to dBm
        df['Frequency (GHz)'] = (df['Frequency (MHz)'] / 1000).round(4)
        df['Power (dBm)'] = convert_power_mw_to_dbm(df['Amplitude Min(mW)'])
        # Assign timestamp to each row
        df['Timestamp'] = timestamp
        # Keep only necessary columns for the pivot operation
        return df[['Frequency (GHz)', 'Timestamp', 'Power (dBm)']]
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return pd.DataFrame()

def reshape_data(all_data):
    """Concatenate and pivot the dataframes to the desired structure."""
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        pivot_df = combined_df.pivot_table(index='Frequency (GHz)', columns='Timestamp', values='Power (dBm)', aggfunc='mean').reset_index()
        pivot_df.columns.name = None  # Remove the aggregation function name from the column
        return pivot_df
    else:
        return pd.DataFrame()

def process_day_directory(day_directory_path, output_directory):
    """Process all CSV files within a day directory and save the matrix."""
    all_data = []
    file_paths = glob.glob(os.path.join(day_directory_path, '*_trace.csv'))

    for file_path in file_paths:
        df = process_file(file_path)
        if not df.empty:
            all_data.append(df)

    final_df = reshape_data(all_data)

    if not final_df.empty:
        # Extract the date from the directory path
        day_directory = os.path.normpath(day_directory_path)  # Ensure the path is normalized
        day = day_directory.split(os.sep)[-1]  # Get the last part of the path, which should be the date
        # Save the final data to a CSV file
        output_file = os.path.join(output_directory, f'{day}_matrix.csv')
        final_df.to_csv(output_file, index=False)
        print(f"Matrix for {day} saved to {output_file}")
    else:
        print(f"No data processed for {day}.")

def process_all_days(input_directory, output_directory):
    """Process each day directory within the specified base directory."""
    day_directories = glob.glob(os.path.join(input_directory, '*/'))  # Directories for each day

    for day_directory in day_directories:
        process_day_directory(day_directory, output_directory)


# Example usage
input_directory = "/mnt/4tbssd/southpole_sh_data/sh2_2021"
output_directory = "/mnt/4tbssd/time_series_matrix_data/sh2/2021"  # Specify your output directory here
process_all_days(input_directory, output_directory)
