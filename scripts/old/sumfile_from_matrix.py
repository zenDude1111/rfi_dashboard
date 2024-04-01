import pandas as pd
from scipy.stats import skew, kurtosis
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures

# Define your file paths here
input_file_path = '/mnt/4tbssd/time_series_matrix_data/sh1/2021/20210101_matrix.csv'
output_summary_path = '/mnt/4tbssd/day_reports/2021/20210101_summary.csv'
output_high_iqr_path = '/mnt/4tbssd/day_reports/2021/20210101_high_iqr.csv'

def calculate_percent_above_1_5_iqr(chunk_df):
    q1 = chunk_df.quantile(0.25, axis=1)
    q3 = chunk_df.quantile(0.75, axis=1)
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    is_outlier = chunk_df.gt(threshold, axis=0)
    percent_outliers = is_outlier.mean(axis=1) * 100
    return percent_outliers.round(4)

def process_chunk(chunk):
    frequencies = chunk['Frequency (GHz)']
    numeric_chunk = chunk.drop(columns=['Frequency (GHz)'])
    stats = {
        'Mean': numeric_chunk.mean(axis=1).round(4),
        'Median': numeric_chunk.median(axis=1).round(4),
        'Min': numeric_chunk.min(axis=1).round(4),
        'Max': numeric_chunk.max(axis=1).round(4),
        'Skew': skew(numeric_chunk, axis=1).round(4),
        'Kurtosis': kurtosis(numeric_chunk, axis=1).round(4),
        '% Above 1.5*IQR': calculate_percent_above_1_5_iqr(numeric_chunk)
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

# Load the dataset
df = pd.read_csv(input_file_path)

# Determine an appropriate chunk size
chunk_size = 1000  # Adjust based on your system's memory and number of cores

# Parallel process
summary_df = parallel_process(df, chunk_size)

# Write the summary to a CSV file
summary_df.to_csv(output_summary_path, index=False)
print(f'Summary statistics written to {output_summary_path}')

# Filter frequencies with IQR % higher than 1 and save to another file
#high_iqr_df = summary_df[summary_df['% Above 1.5*IQR'] > 1]
#high_iqr_df.to_csv(output_high_iqr_path, index=False)
#print(f'Frequencies with IQR outlier percentage greater than 1% written to {output_high_iqr_path}')