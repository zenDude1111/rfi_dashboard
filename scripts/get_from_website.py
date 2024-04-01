import os
import requests
import tarfile
import concurrent.futures
from datetime import datetime
from bs4 import BeautifulSoup

# URL of the website
URL = "http://bicep.rc.fas.harvard.edu/southpole_info/EMI_WG/keckdaq/signalhound2/"

def download_file(url, path):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte

    with open(path, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)

    print(f"Download completed for {path}")

def unpack_and_delete_tar(tar_path, save_directory):
    print(f"Unpacking {tar_path}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=save_directory)
    print(f"Unpacked {tar_path}")

    os.remove(tar_path)
    print(f"Deleted {tar_path}")

def download_and_process(url, link, save_directory):
    tar_path = os.path.join(save_directory, link)
    download_file(url + link, tar_path)
    unpack_and_delete_tar(tar_path, save_directory)

def download_and_unpack_tar(url, save_directory, start_date_str, end_date_str):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tar_links = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.tar.gz')]
    
    # Convert the start_date_str and end_date_str to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y%m%d')
    end_date = datetime.strptime(end_date_str, '%Y%m%d')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for link in tar_links:
            try:
                # Extract the date part from the filename
                file_date = datetime.strptime(link[:8], '%Y%m%d')
                # Check if the file_date is after the start_date and before or equal to the end_date
                if start_date < file_date <= end_date:
                    futures.append(executor.submit(download_and_process, url, link, save_directory))
            except ValueError:
                # Handle the error or log it as necessary
                continue

        for future in concurrent.futures.as_completed(futures):
            future.result()

# Example usage
save_dir = '/mnt/4tbssd/southpole_sh_data/sh2_2021'
start_date_str = '20211118'  # Example start date in YYYYMMDD format
end_date_str = '20211231'  # Example end date in YYYYMMDD format
download_and_unpack_tar(URL, save_dir, start_date_str, end_date_str)


