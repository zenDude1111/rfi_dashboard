import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from scipy.stats import skew, kurtosis

def process_file(filename, directory, file_pattern):
    match = re.match(file_pattern, filename)
    if match:
        datetime_obj = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%Y%m%d %H%M%S")
        df = pd.read_csv(os.path.join(directory, filename))
        df['Datetime'] = datetime_obj
        return df
    else:
        return pd.DataFrame()

def perform_stat_analysis(df):
    result = []
    for frequency, group in df.groupby('Frequency (MHz)'):
        power_values = group['Power(mW)']
        q1 = np.percentile(power_values, 25)
        q3 = np.percentile(power_values, 75)
        iqr = q3 - q1
        iqr_multiplier = 1.5
        upper_bound = q3 + (iqr_multiplier * iqr)

        outliers = power_values > upper_bound
        percentage_of_outliers = np.mean(outliers) * 100

        median_power = np.median(power_values)
        mean_power = np.mean(power_values)
        mode_power = power_values.mode()
        if not mode_power.empty:
            mode_power = mode_power.iloc[0]
        else:
            mode_power = np.nan

        min_power = np.min(power_values)
        max_power = np.max(power_values)
        skewness = skew(power_values)
        kurtosis_val = kurtosis(power_values)
        std_dev = np.std(power_values, ddof=1)
        five_std_above_median = median_power + (5 * std_dev)
        percentage_above_5_std = np.mean(power_values > five_std_above_median) * 100

        result.append((frequency, median_power, mean_power, mode_power, min_power, max_power, skewness, kurtosis_val, std_dev, percentage_above_5_std, percentage_of_outliers, upper_bound))
    
    columns = ['Frequency (MHz)', 'Median Power (mW)', 'Mean Power (mW)', 'Mode Power (mW)', 'Min Power (mW)', 'Max Power (mW)', 'Skewness', 'Kurtosis', 'Standard Deviation', 'Percentage > 5 Std Dev Above Median', 'Percentage of Outliers (IQR)', 'Cutoff Power (mW) for Outliers']
    
    return pd.DataFrame(result, columns=columns)

def create_summary_file(analyzed_df, date_str, save_path):
    # Calculations for day summary
    day_max_power = analyzed_df['Max Power (mW)'].max()
    day_min_power = analyzed_df['Min Power (mW)'].min()
    percent_skew_above_zero = (analyzed_df['Skewness'] > 0).mean() * 100
    percent_kurtosis_above_zero = (analyzed_df['Kurtosis'] > 0).mean() * 100
    # These percentages are already calculated for each frequency, so we just take an average for the day
    avg_percent_above_5_std = analyzed_df['Percentage > 5 Std Dev Above Median'].mean()
    avg_percent_of_outliers = analyzed_df['Percentage of Outliers (IQR)'].mean()
    
    # Create a DataFrame for the summary
    summary_data = {
        'Day Max Power (mW)': [day_max_power],
        'Day Min Power (mW)': [day_min_power],
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
    for root, dirs, files in os.walk(directory):
        all_data = []
        for filename in tqdm(files, desc=f"Processing files in {root}"):
            df = process_file(filename, root, file_pattern)
            if not df.empty:
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data)
            analyzed_df = perform_stat_analysis(combined_df)
            
            # Extract the date from the directory name or file name
            date_match = re.search(r'(\d{8})', root)
            if date_match:
                date_str = date_match.group(1)
            else:
                # Default to current date if no date found
                date_str = datetime.now().strftime("%Y%m%d")
            
            output_filename = f"sh1-{date_str}.csv"
            output_file_path = os.path.join(save_path, output_filename)
            
            analyzed_df.to_csv(output_file_path, index=False)
            print(f"Analysis saved to {output_file_path}")
            create_summary_file(analyzed_df, date_str, save_path)

# Main directory path that contains subdirectories for each day
directory_path = r'd:\SouthPole_Signal_Data\signalhound1'
save_path = r'assets\csv'
file_pattern = r"(\d{8})_(\d{6})_trace\.csv"

# Process the data and save each analyzed dataset with a unique name
aggregate_and_analyze(directory_path, file_pattern, save_path)

