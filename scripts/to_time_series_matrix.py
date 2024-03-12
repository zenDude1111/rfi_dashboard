import pandas as pd
import numpy as np
import os
import glob
from tqdm import tqdm
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
        # Read CSV file
        df = pd.read_csv(file_path, names=['Frequency (MHz)', 'Power (mW)'], skiprows=1)
        # Convert frequency to GHz and power to dBm
        df['Frequency (GHz)'] = df['Frequency (MHz)'] / 1000
        df['Power (dBm)'] = convert_power_mw_to_dbm(df['Power (mW)'])
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

def process_directory(directory_path):
    """Process all CSV files within the specified directory."""
    all_data = []
    file_paths = glob.glob(os.path.join(directory_path, '**/*_trace.csv'), recursive=True)

    for file_path in tqdm(file_paths, desc="Processing Files"):
        df = process_file(file_path)
        if not df.empty:
            all_data.append(df)

    final_df = reshape_data(all_data)

    if not final_df.empty:
        # Output file path
        output_file = os.path.join(directory_path, '20240101_matrix.csv')
        # Write to a new CSV file
        final_df.to_csv(output_file, index=False)
        print(f"Data combined and written to {output_file}")
    else:
        print("No data processed.")

# Example usage
directory_path = r'd:\SouthPole_Signal_Data\2023_24\20240101'
process_directory(directory_path)
