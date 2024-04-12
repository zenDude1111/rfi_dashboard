import pandas as pd
from scipy.stats import skew, kurtosis, kstest
import numpy as np
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures

# Define base directory paths
base_directory_path = '/mnt/4tbssd/time_series_matrix_data/sh2/'
output_base_path = '/mnt/4tbssd/day_reports/sh2/'

# Ensure the output base path exists
os.makedirs(output_base_path, exist_ok=True)

# Define functions for statistical calculations
def calculate_percent_above_1_5_iqr(chunk_df):
    q1 = chunk_df.quantile(0.25, axis=1)
    q3 = chunk_df.quantile(0.75, axis=1)
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    is_outlier = chunk_df.gt(threshold, axis=0)
    percent_outliers = is_outlier.mean(axis=1) * 100
    return percent_outliers.round(4)

def calculate_ks_test(chunk_df):
    means = chunk_df.mean(axis=1)
    stds = chunk_df.std(axis=1, ddof=1)
    ks_results = chunk_df.apply(lambda row: kstest(row.dropna(), 'norm', args=(means[row.name], stds[row.name])), axis=1)
    p_values = ks_results.apply(lambda x: x[1]).round(4)
    d_statistics = ks_results.apply(lambda x: x[0]).round(4)
    return p_values, d_statistics

def process_chunk(chunk):
    frequencies = chunk['Frequency (GHz)']
    numeric_chunk = chunk.drop(columns=['Frequency (GHz)'])
    ks_p_values, ks_d_statistics = calculate_ks_test(numeric_chunk)
    stats = {
        'Mean (dBm)': numeric_chunk.mean(axis=1).round(4),
        'Median (dBm)': numeric_chunk.median(axis=1).round(4),
        'Min (dBm)': numeric_chunk.min(axis=1).round(4),
        'Max (dBm)': numeric_chunk.max(axis=1).round(4),
        'Skew': skew(numeric_chunk, axis=1).round(4),
        'Kurtosis': kurtosis(numeric_chunk, axis=1).round(4),
        '% Above 1.5*IQR': calculate_percent_above_1_5_iqr(numeric_chunk),
        'KS Test D Statistic': ks_d_statistics
    }
    result_df = pd.DataFrame(stats)
    result_df.insert(0, 'Frequency (GHz)', frequencies.values)
    return result_df

def parallel_process(df, chunk_size):
    chunks = [df.iloc[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size)]
    results = []
    with ProcessPoolExecutor() as executor:
        future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}
        for future in concurrent.futures.as_completed(future_to_chunk):
            results.append(future.result())
    final_df = pd.concat(results, ignore_index=True)
    return final_df

# Main processing loop
for input_file_path in glob.glob(f'{base_directory_path}/**/*_matrix.csv', recursive=True):
    df = pd.read_csv(input_file_path)
    summary_df = parallel_process(df, chunk_size=1000)
    summary_df.sort_values(by='Frequency (GHz)', inplace=True)

    # Extracting date from the input file path
    date_part = os.path.basename(input_file_path).split('_')[0]
    output_summary_path = os.path.join(output_base_path, f'{date_part}_summary.csv')

    summary_df.to_csv(output_summary_path, index=False)
    print(f'Summary statistics written to {output_summary_path}')
