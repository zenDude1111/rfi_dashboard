import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

def process_file_and_calculate_outliers(file_path, target_frequency):
    try:
        # Load the CSV to check frequencies directly
        df_full = pd.read_csv(file_path)
        # Assuming the first column is 'Frequency (GHz)'
        matched_row = df_full[df_full.iloc[:, 0] == target_frequency]

        if not matched_row.empty:
            power_values = matched_row.drop(columns=matched_row.columns[0]).values.flatten()

            # Calculate IQR
            q1, q3 = np.percentile(power_values, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Determine outliers
            outliers = power_values[(power_values < lower_bound) | (power_values > upper_bound)]
            outlier_percentage = (len(outliers) / len(power_values)) * 100

            # Extract the date from the file name
            date_str = os.path.basename(file_path).split('_')[0]
            date = pd.to_datetime(date_str, format='%Y%m%d')

            return date, outlier_percentage
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    return None

def aggregate_outlier_percentages(base_dir, target_frequency):
    files = [os.path.join(root, file)
             for root, dirs, files in os.walk(base_dir)
             for file in files if file.endswith('_matrix.csv')]

    # Use a ThreadPoolExecutor to process files in parallel
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_file_and_calculate_outliers, file, target_frequency) for file in files]
        results = [future.result() for future in futures]

    # Filter out None results and convert to DataFrame
    valid_results = [result for result in results if result]
    if not valid_results:
        return pd.DataFrame()
    df_outliers = pd.DataFrame(valid_results, columns=['Date', 'Outlier Percentage']).sort_values(by='Date')
    return df_outliers

def plot_outlier_percentages(df):
    plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df['Outlier Percentage'], marker='o', linestyle='-', label='Outlier Percentage')
    plt.title(f'Outlier Percentage Over Time for Frequency {target_frequency} GHz')
    plt.xlabel('Date')
    plt.ylabel('Outlier Percentage (%)')
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    base_dir = '/mnt/4tbssd/time_series_matrix_data/sh1/2021'  # Update this with your actual directory path
    target_frequency = 1.6207  # The specific frequency you're interested in

    df_outliers = aggregate_outlier_percentages(base_dir, target_frequency)
    if not df_outliers.empty:
        plot_outlier_percentages(df_outliers)
        # Save the outlier percentage data to a CSV file
        output_csv_path = '/mnt/4tbssd/day_reports/16207_2021_outlier_percentages.csv'
        df_outliers.to_csv(output_csv_path, index=False)
        print(f"Outlier percentage data saved to {output_csv_path}")
    else:
        print("No data found for the specified frequency or no outliers detected.")
