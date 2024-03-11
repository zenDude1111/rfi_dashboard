import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

def file_start_time(file_name):
    date_str, time_str = file_name.split('_')[0], file_name.split('_')[1]
    return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")

def calculate_timestamps(start_datetime, n):
    interval = timedelta(minutes=2) / n
    return [start_datetime + i * interval for i in range(n)]

def convert_mw_to_dbm(mw):
    return 10 * np.log10(mw)

def process_file(file_path):
    data = pd.read_csv(file_path)
    base_name = os.path.basename(file_path).replace('_trace.csv', '')
    start_datetime = file_start_time(base_name)
    interval = timedelta(minutes=2) / len(data)
    data['Timestamp'] = calculate_timestamps(start_datetime, len(data))
    data['Timestamp'] = data['Timestamp'].dt.strftime('%H%M%S')  # Format timestamp as hhmmss
    data['Frequency (GHz)'] = data['Frequency (MHz)'] * 0.001
    data['Power_dBm'] = convert_mw_to_dbm(data['Power (mW)'])
    data.drop(['Frequency (MHz)', 'Power (mW)'], axis=1, inplace=True)
    return data

def consolidate_data(input_directory):
    file_pattern = os.path.join(input_directory, "*_trace.csv")
    files = glob.glob(file_pattern)
    consolidated_data = []
    
    with ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(process_file, files), total=len(files), desc="Reading files"))
    
    consolidated_df = pd.concat(results, ignore_index=True)
    return consolidated_df

def create_frequency_files(consolidated_df, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    frequencies = consolidated_df['Frequency (GHz)'].unique()
    for frequency in tqdm(frequencies, desc="Processing frequencies"):
        group = consolidated_df[consolidated_df['Frequency (GHz)'] == frequency]
        output_file_name = f"{frequency:.3f}_GHz.csv"  # Changed file naming to match requirement
        output_file_path = os.path.join(output_directory, output_file_name)
        group[['Timestamp', 'Power_dBm']].to_csv(output_file_path, index=False)  # Ensure correct column order

def main():
    # Example usage
    input_directory = '/mnt/4tbssd/southpole_sh_data/sh2_2024/202403/20240301'  # Update this to your input directory path
    output_directory = '/mnt/4tbssd/southpole_sh_data/sh2_2024/202403/20240301/time_series'  # Update this to your output directory path
    
    consolidated_df = consolidate_data(input_directory)
    create_frequency_files(consolidated_df, output_directory)

if __name__ == '__main__':
    main()





