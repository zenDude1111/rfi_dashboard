import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
import glob

# Function to process each CSV file
def process_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Find the row with the target frequency
    target_row = df[df['Frequency (GHz)'] == target_frequency]
    
    # Check if the target frequency exists in the DataFrame
    if not target_row.empty:
        # Extract the '% Above 1.5*IQR' value for the target frequency
        iqr_percent = target_row['% Above 1.5*IQR'].iloc[0]
    else:
        # Handle case where the frequency is not found
        iqr_percent = None  # Or set a default value or flag as needed
    
    # Extract the date from the file name (format 'yyyymmdd_summary.csv')
    date = os.path.basename(file_path).split('_')[0]
    
    return date, iqr_percent

# Define the target frequency
target_frequency = 8.2989  # Adjust this to the frequency of interest

# Path to the directory containing the CSV files
csv_directory = '/mnt/4tbssd/day_reports/sh2/'
save_directory = '/mnt/4tbssd/channels/sh2_dscs_8.2989'
file_paths = glob.glob(os.path.join(csv_directory, '????????_summary.csv'))

# Use ThreadPoolExecutor to process files in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_csv, file_paths))

# Filter out None values if any frequency was not found
filtered_results = [result for result in results if result[1] is not None]

# Convert the results to a DataFrame
results_df = pd.DataFrame(filtered_results, columns=['Date', 'IQR Percent for Frequency {}'.format(target_frequency)])

# Sort the DataFrame by 'Date'
results_df['Date'] = pd.to_datetime(results_df['Date'], format='%Y%m%d')
results_df = results_df.sort_values(by='Date')
results_df['Date'] = results_df['Date'].dt.strftime('%Y%m%d')  # Converting back to string if needed

# Check if save_directory exists, if not, create it
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Define the name of the output file and construct the full path
output_file_name = 'sh2_dscs_daily_iqr_percents_2021_2022_2023.csv'
output_file_path = os.path.join(save_directory, output_file_name)

# Save the results to the new CSV file in the specified directory
results_df.to_csv(output_file_path, index=False)

