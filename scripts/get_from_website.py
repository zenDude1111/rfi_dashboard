import os
import requests
from bs4 import BeautifulSoup
import tarfile
from datetime import datetime
from tqdm import tqdm
import shutil
import concurrent.futures
import pandas as pd

# URL of the website
URL = "http://bicep.rc.fas.harvard.edu/southpole_info/EMI_WG/keckdaq/signalhound1/"

def download_file(url, path):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(path, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

def cleanup_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def unpack_and_delete_tar(tar_path, save_directory):
    print(f"Unpacking {tar_path}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=save_directory)
    os.remove(tar_path)

def download_and_process(url, link, save_directory):
    tar_path = os.path.join(save_directory, link)
    print(f"Downloading {link}...")
    download_file(url + link, tar_path)
    unpack_and_delete_tar(tar_path, save_directory)

def download_and_unpack_tar(url, save_directory):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    else:
        cleanup_directory(save_directory)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tar_links = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.tar.gz')]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for link in tar_links:
            try:
                file_date = datetime.strptime(link.split('.')[0], "%Y%m%d")
                if file_date.year in [2024]:
                    futures.append(executor.submit(download_and_process, url, link, save_directory))
            except ValueError:
                continue

        for future in concurrent.futures.as_completed(futures):
            future.result()

# Example usage
save_dir = r'd:\SouthPole_Signal_Data\2023_24'
download_and_unpack_tar(URL, save_dir)

