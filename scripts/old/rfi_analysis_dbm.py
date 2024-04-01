import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from scipy.stats import skew, kurtosis

def process_file(filename, directory, file_pattern):
    match = re.match(file_pattern, filename)
    if match:
        datetime_obj = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%Y%m%d %H%M%S")
        df = pd.read_csv(os.path.join(directory, filename))
        # Convert 'Power(mW)' column to 'Power(dBm)' upon loading
        df['Power(dBm)'] = 10 * np.log10(df['Power(mW)'])
        df.drop('Power(mW)', axis=1, inplace=True)  # Remove the original mW column
        df['Datetime'] = datetime_obj
        return df
    else:
        return pd.DataFrame()

def perform_stat_analysis(df):
    result = []
    for frequency, group in df.groupby('Frequency (MHz)'):
        power_values_dbm = group['Power(dBm)']

        q1 = np.percentile(power_values_dbm, 25)
        q3 = np.percentile(power_values_dbm, 75)
        iqr = q3 - q1
        iqr_multiplier = 1.5
        upper_bound = q3 + (iqr_multiplier * iqr)

        outliers = power_values_dbm > upper_bound
        percentage_of_outliers = np.mean(outliers) * 100

        median_power = np.median(power_values_dbm)
        mean_power = np.mean(power_values_dbm)
        mode_power = power_values_dbm.mode()
        if not mode_power.empty:
            mode_power = mode_power.iloc[0]
        else:
            mode_power = np.nan

        min_power = np.min(power_values_dbm)
        max_power = np.max(power_values_dbm)
        skewness = skew(power_values_dbm)
        kurtosis_val = kurtosis(power_values_dbm)
        std_dev = np.std(power_values_dbm, ddof=1)
        five_std_above_median = median_power + (5 * std_dev)
        percentage_above_5_std = np.mean(power_values_dbm > five_std_above_median) * 100

        result.append((frequency, median_power, mean_power, mode_power, min_power, max_power, skewness, kurtosis_val, std_dev, percentage_above_5_std, percentage_of_outliers, upper_bound))
    
    columns = ['Frequency (MHz)', 'Median Power (dBm)', 'Mean Power (dBm)', 'Mode Power (dBm)', 'Min Power (dBm)', 'Max Power (dBm)', 'Skewness', 'Kurtosis', 'Standard Deviation', 'Percentage > 5 Std Dev Above Median', 'Percentage of Outliers (IQR)', 'Cutoff Power (dBm) for Outliers']
    
    return pd.DataFrame(result, columns=columns)

def create_summary_file(analyzed_df, date_str, save_path):
    # Calculations for day summary
    day_max_power = analyzed_df['Max Power (dBm)'].max()
    day_min_power = analyzed_df['Min Power (dBm)'].min()
    percent_skew_above_zero = (analyzed_df['Skewness'] > 0).mean() * 100
    percent_kurtosis_above_zero = (analyzed_df['Kurtosis'] > 0).mean() * 100
    
    # These percentages are already calculated for each frequency, so we just take an average for the day
    avg_percent_above_5_std = analyzed_df['Percentage > 5 Std Dev Above Median'].mean()
    avg_percent_of_outliers = analyzed_df['Percentage of Outliers (IQR)'].mean()
    
    # Create a DataFrame for the summary
    summary_data = {
        'Day Max Power (dBm)': [day_max_power],
        'Day Min Power (dBm)': [day_min_power],
        'Percent Skewness > 0': [percent_skew_above_zero],
        'Percent Kurtosis > 0': [percent_kurtosis_above_zero],
        'Average Percent > 5 Std Dev': [avg_percent_above_5_std],
        'Average Percent of Outliers': [avg_percent_of_outliers]
    }
    summary_df = pd.DataFrame(summary_data)
    
    # Saving the summary
    summary_filename = f"summary-{date_str}.csv"
    summary_file_path = os.path.join(save_path, summary_filename)
    summary_df.to_csv(summary_file_path, index=False)
    print(f"Summary saved to {summary_file_path}")


def aggregate_and_analyze(directory, file_pattern, save_path):
    all_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                futures.append(executor.submit(process_file, filename, root, file_pattern))
            
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing files"):
            df = future.result()
            if not df.empty:
                all_data.append(df)
                
    if all_data:
        combined_df = pd.concat(all_data)
        analyzed_df = perform_stat_analysis(combined_df)
        
        # Extract the date from the directory name or file name
        date_match = re.search(r'(\d{8})', directory)  # Adjusted to use directory
        if date_match:
            date_str = date_match.group(1)
        else:
            date_str = datetime.now().strftime("%Y%m%d")
        
        output_filename = f"sh1-{date_str}.csv"
        output_file_path = os.path.join(save_path, output_filename)
        
        analyzed_df.to_csv(output_file_path, index=False)
        print(f"Analysis saved to {output_file_path}")
        create_summary_file(analyzed_df, date_str, save_path)

# Main directory path that contains subdirectories for each day
directory_path = r'd:\SouthPole_Signal_Data\signalhound1\20210101'
save_path = r'assets\csv'
file_pattern = r"(\d{8})_(\d{6})_trace\.csv"

# Process the data and save each analyzed dataset with a unique name
aggregate_and_analyze(directory_path, file_pattern, save_path)

