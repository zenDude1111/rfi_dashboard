import pandas as pd
import numpy as np
import os
import glob
from tqdm import tqdm
from datetime import datetime
from scipy.stats import kurtosis, skew

def convert_power_mw_to_dbm(power_mw):
    """Convert power from mW to dBm."""
    return 10 * np.log10(power_mw)

def calculate_metrics(df):
    # Assume df does not contain 'Power (dBm)' as a column but as multiple timestamp columns
    metrics_list = []

    for index, row in df.iterrows():
        row_data = row[1:]  # Exclude 'Frequency (GHz)' column
        max_power = row_data.max()
        min_power = row_data.min()
        skewness = skew(row_data.dropna())
        kurt = kurtosis(row_data.dropna(), fisher=True)
        
        # Calculating standard deviation outliers
        mean = row_data.mean()
        std_dev = row_data.std()
        outliers_std = ((row_data > (mean + 5 * std_dev)) | (row_data < (mean - 5 * std_dev))).mean()
        
        # Calculating IQR outliers
        Q1 = row_data.quantile(0.25)
        Q3 = row_data.quantile(0.75)
        IQR = Q3 - Q1
        outliers_iqr = ((row_data < (Q1 - 1.5 * IQR)) | (row_data > (Q3 + 1.5 * IQR))).mean()

        metrics_list.append({
            'Frequency (GHz)': row['Frequency (GHz)'],
            'Max Power (dBm)': max_power,
            'Min Power (dBm)': min_power,
            'Skewness': skewness,
            'Kurtosis': kurt,
            'Outliers Std Dev (%)': outliers_std * 100,
            'Outliers IQR (%)': outliers_iqr * 100
        })

    return pd.DataFrame(metrics_list)


def process_file(file_path):
    """Process an individual file to read, convert, and structure its data."""
    try:
        # Extract timestamp from the file name
        file_name = os.path.basename(file_path)
        timestamp = datetime.strptime(file_name.split('_')[1], '%H%M%S').strftime('%H:%M:%S')
        # Read CSV file
        df = pd.read_csv(file_path, names=['Frequency (MHz)', 'Power (mW)'], skiprows=1)
        # Convert frequency to GHz and power to dBm
        df['Frequency (GHz)'] = (df['Frequency (MHz)'] / 1000).round(4)
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
    """Process all CSV files within the specified directory and generate summary."""
    all_data = []
    file_paths = glob.glob(os.path.join(directory_path, '**/*_trace.csv'), recursive=True)

    for file_path in tqdm(file_paths, desc="Processing Files"):
        df = process_file(file_path)
        if not df.empty:
            all_data.append(df)

    final_df = reshape_data(all_data)

    if not final_df.empty:
        # Generate summary
        summary_df = calculate_metrics(final_df)

        # Write the final data and summary to CSV files
        output_file = os.path.join(directory_path, '20240302_matrix.csv')
        summary_file = os.path.join(directory_path, '20240302_rfe_summary.csv')

        final_df.to_csv(output_file, index=False)
        summary_df.to_csv(summary_file, index=False)

        print(f"Data combined and written to {output_file}")
        print(f"Summary written to {summary_file}")
    else:
        print("No data processed.")

# Example usage
directory_path = '/mnt/4tbssd/southpole_sh_data/sh1_2024/202403/20240302'
process_directory(directory_path)