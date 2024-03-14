import os
import requests
import tarfile
import concurrent.futures
from datetime import datetime
from bs4 import BeautifulSoup

# URL of the website
URL = "http://bicep.rc.fas.harvard.edu/southpole_info/EMI_WG/keckdaq/signalhound1/"

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

def download_and_unpack_tar(url, save_directory):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tar_links = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.tar.gz')]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for link in tar_links:
            # Directly extract the date part from the filename
            try:
                file_date = datetime.strptime(link[:8], '%Y%m%d')
                # Adjust the condition to check both year and month
                if file_date.year == 2024 and file_date.month == 3:  # Example for March 2024
                    futures.append(executor.submit(download_and_process, url, link, save_directory))
            except ValueError:
                # Log error or handle it as necessary
                continue

        for future in concurrent.futures.as_completed(futures):
            future.result()


# Example usage
save_dir = '/mnt/4tbssd/southpole_sh_data/sh1_2024/202403'
download_and_unpack_tar(URL, save_dir)
