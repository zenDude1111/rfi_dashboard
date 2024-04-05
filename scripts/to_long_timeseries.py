import os
import pandas as pd
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

def process_file(file_path, target_frequency):
    try:
        freq_column = pd.read_csv(file_path, usecols=[0])
        target_row_index = freq_column.index[freq_column.iloc[:, 0] == target_frequency].tolist()
        
        if target_row_index:
            target_row = pd.read_csv(file_path, skiprows=lambda x: x not in target_row_index)
            target_row = target_row.drop(columns=target_row.columns[0]).T
            target_row.columns = ['Power (dBm)']
            
            file_name = os.path.basename(file_path)
            date_str = file_name.split('_')[0]
            target_row['Date'] = pd.to_datetime(date_str, format='%Y%m%d')
            
            return target_row
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    return pd.DataFrame()

def aggregate_data_for_frequency_multithreaded(base_dir, target_frequency):
    files = [os.path.join(root, file)
             for root, dirs, files in os.walk(base_dir)
             for file in files if file.endswith('_matrix.csv')]

    aggregated_data = pd.DataFrame()

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = executor.map(process_file, files, [target_frequency] * len(files))

        for result in results:
            if not result.empty:
                aggregated_data = pd.concat([aggregated_data, result], ignore_index=True)

    aggregated_data.sort_values(by='Date', inplace=True)
    
    return aggregated_data

def plot_aggregated_data(aggregated_data):
    plt.figure(figsize=(12, 6))
    plt.plot(aggregated_data['Date'], aggregated_data['Power (dBm)'], marker='o', linestyle='-', label='Power (dBm)')
    plt.title(f'Power Over Time for Frequency {target_frequency} GHz')
    plt.xlabel('Date')
    plt.ylabel('Power (dBm)')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    base_dir = '/mnt/4tbssd/time_series_matrix_data/sh1/2023'  # Update with your directory path
    target_frequency = 8.0995  # Specify the frequency of interest

    aggregated_data = aggregate_data_for_frequency_multithreaded(base_dir, target_frequency)
    if not aggregated_data.empty:
        plot_aggregated_data(aggregated_data)
    else:
        print("No data found for the specified frequency.")


