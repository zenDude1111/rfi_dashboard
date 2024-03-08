import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_file(file_path):
    try:
        df = pd.read_csv(file_path)
        # Check if the third column is already removed
        if df.shape[1] < 3:
            print(f"Skipping {file_path}, already processed.")
            return

        # Remove the 3rd column
        df.drop(df.columns[2], axis=1, inplace=True)

        # Rename the 2nd column to "power_mW"
        df.rename(columns={df.columns[1]: 'power_mW'}, inplace=True)

        # Save the modified DataFrame back to the file
        df.to_csv(file_path, index=False)
        print(f"Processed {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def process_files(directory, max_workers=50):
    # Create a ThreadPoolExecutor to manage concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a dictionary to map future to file_path for error handling
        future_to_file = {executor.submit(process_file, os.path.join(root, file)): os.path.join(root, file)
                          for root, dirs, files in os.walk(directory) for file in files if file.endswith('.csv')}
        
        # Iterate over the as_completed() iterator to process files as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()  # Retrieve the result to trigger any exceptions caught during processing
            except Exception as exc:
                print(f"{file_path} generated an exception: {exc}")

# Example usage:
process_files(r'd:\SouthPole_Signal_Data\2023_24')

