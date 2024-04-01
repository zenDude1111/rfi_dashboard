import pandas as pd
from scipy.stats import skew, kurtosis, kstest
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import numpy as np

# Define your file paths here
input_file_path = '/mnt/4tbssd/time_series_matrix_data/sh1/2021/20210101_matrix.csv'
output_summary_path = '/mnt/4tbssd/day_reports/2021/20210101_summary.csv'

def calculate_percent_above_1_5_iqr(chunk_df):
    q1 = chunk_df.quantile(0.25, axis=1)
    q3 = chunk_df.quantile(0.75, axis=1)
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    is_outlier = chunk_df.gt(threshold, axis=0)
    percent_outliers = is_outlier.mean(axis=1) * 100
    return percent_outliers.round(4)

def calculate_ks_test(chunk_df):
    # Pre-calculate mean and std since they're used in each row's KS test
    means = chunk_df.mean(axis=1)
    stds = chunk_df.std(axis=1, ddof=1)  # Using sample standard deviation (ddof=1)
    # Apply KS test for each row
    ks_results = chunk_df.apply(lambda row: kstest(row.dropna(), 'norm', args=(means[row.name], stds[row.name])), axis=1)
    # Extract and return the p-values and D statistics
    p_values = ks_results.apply(lambda x: x[1]).round(4)
    d_statistics = ks_results.apply(lambda x: x[0]).round(4)
    return p_values, d_statistics

def process_chunk(chunk):
    frequencies = chunk['Frequency (GHz)']
    numeric_chunk = chunk.drop(columns=['Frequency (GHz)'])
    # Optimized to call calculate_ks_test once per chunk
    ks_p_values, ks_d_statistics = calculate_ks_test(numeric_chunk)
    stats = {
        'Mean': numeric_chunk.mean(axis=1).round(4),
        'Median': numeric_chunk.median(axis=1).round(4),
        'Min': numeric_chunk.min(axis=1).round(4),
        'Max': numeric_chunk.max(axis=1).round(4),
        'Skew': skew(numeric_chunk, axis=1).round(4),
        'Kurtosis': kurtosis(numeric_chunk, axis=1).round(4),
        '% Above 1.5*IQR': calculate_percent_above_1_5_iqr(numeric_chunk),
        #'KS Test P-Value': ks_p_values,
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

# Load the dataset
df = pd.read_csv(input_file_path)

# Determine an appropriate chunk size
chunk_size = 1000  # Adjust based on your system's memory and number of cores

# Parallel process
summary_df = parallel_process(df, chunk_size)

# Write the summary to a CSV file
summary_df.to_csv(output_summary_path, index=False)
print(f'Summary statistics written to {output_summary_path}')



"""
The Kolmogorov-Smirnov (K-S) Test for Normality:

The K-S test is a non-parametric test that compares the cumulative distribution function (CDF) of the observed data 
with the CDF of a specified theoretical distribution (in this case, the normal distribution). The test calculates the 
D statistic, which is the maximum difference between the two CDFs across all possible values. 

The process involves:
1. Calculating the empirical CDF of the observed data.
2. Calculating the CDF of a normal distribution with the same mean and standard deviation as the observed data.
3. Finding the maximum absolute difference (D statistic) between these two CDFs.
4. Computing a p-value based on the D statistic, which indicates the probability of observing such a difference 
   if the observed data actually followed the specified normal distribution.

A low p-value (typically < 0.05) suggests that the observed data significantly deviate from the normal distribution, 
indicating that the distribution of the data is not normal. Conversely, a high p-value suggests that the data could 
plausibly have come from a normal distribution, although it does not confirm normality outright.

This test is applied to each frequency's power readings in the dataset to assess the normality of their distribution. 
It provides a systematic method to identify deviations from normality, which can be critical for analyses assuming 
normal distribution of the data.

Note: While the K-S test is useful for assessing normality, it's important to consider its limitations. 
The test is more sensitive to differences near the center of the distribution than at the tails. 
Additionally, the test's efficacy might be reduced for very small or very large samples.
"""

