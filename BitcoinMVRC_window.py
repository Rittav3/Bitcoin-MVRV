# %%
#Set up all file path here:
from pathlib import Path

#use folder 'Downloads' as default
download_folder = str(Path.home() / "Downloads")

mvrv_file = download_folder + '\\mvrv.json'
savefile = download_folder + '\\downloadMVRV.csv'
BitcoinMVRV_file = 'C:\Amibroker Data\Raw Data\BitcoinMVRV.csv' #load existing MVRV file to combine with downloadMVRF.csv
#save_final_BitcoinMVRV_combined_file = download_folder + '\\BitcoinMVRV_combine.csv'
save_final_BitcoinMVRV_combined_file = BitcoinMVRV_file #overwrite to existing file


# %%
#Step 1: Delete old mvrv.json files in Downloads folder



def delete_matching_files_in_downloads():
    """
    Finds the user's Downloads folder and deletes files that match a specific pattern.

    The script will delete files that:
    - Are in the main "Downloads" folder.
    - Start with the prefix 'mvrv'.
    - End with the extension '.json'.
    """
    try:
        # 1. Get the path to the user's Downloads folder
        downloads_path = Path.home() / "Downloads"

        # Check if the Downloads folder actually exists
        if not downloads_path.is_dir():
            print(f"Error: The Downloads folder was not found at '{downloads_path}'")
            return

        print(f"Searching for files in: {downloads_path}")

        # 2. Find all files matching the pattern 'mvrv*.json'
        # The glob pattern 'mvrv*.json' finds all items in the directory
        # that start with 'mvrv' and end with '.json'.
        files_found = list(downloads_path.glob('mvrv*.json'))

        if not files_found:
            print("No files found matching the pattern 'mvrv*.json'. Nothing to delete.")
            return

        print(f"Found {len(files_found)} file(s) to delete:")
        for file_path in files_found:
            print(f" - {file_path.name}")

        # Optional: Ask for confirmation before deleting
        # confirm = input("Do you want to proceed with deletion? (y/n): ")
        # if confirm.lower() != 'y':
        #     print("Deletion cancelled.")
        #     return

        # 3. Delete the files
        for file_path in files_found:
            try:
                file_path.unlink()  # Deletes the file
                print(f"Successfully deleted: {file_path.name}")
            except OSError as e:
                print(f"Error deleting file {file_path.name}: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    delete_matching_files_in_downloads()


# %%
#step 2 click download button on webpage topo download new mvrv.json file

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Optional: specify path to chromedriver if not in PATH
# service = Service("C:/path/to/chromedriver.exe")

# Set Chrome options
options = webdriver.ChromeOptions()
#options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")

# Launch browser
driver = webdriver.Chrome(options=options)

try:
    # Step 1: Open the web page
    driver.get("https://www.blockchain.com/explorer/charts/mvrv")
    time.sleep(5)
    # Step 2: Wait for the element and click it
    #xpath of button "Download JSON"
    
    xpath =  '/html/body/div/div[2]/div[2]/main/div/div/div/div[1]/section/div/div/div/div[1]'

    wait = WebDriverWait(driver, 20)
    button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    button.click()

    print("Button clicked successfully.")

    # Optional: wait to observe result
    time.sleep(3)

finally:
    driver.quit()

# %%
#STEP3 read json and made CSV file, save to foldrev 'download_folder' =>'Downloads'

# %%
import json
import pandas as pd
from datetime import datetime


# Load JSON data
with open(mvrv_file, 'r') as f:
    data = json.load(f)

# Extract MVRV data
mvrv_data = data['mvrv']

# Convert to DataFrame
df = pd.DataFrame(mvrv_data)

# Convert timestamp from milliseconds to datetime
df['timestamp'] = pd.to_datetime(df['x'], unit='ms')
df['mvrv'] = df['y']

# Reorder and clean up
df = df[['timestamp', 'mvrv']]




# %%
df['Date'] = df['timestamp'].dt.date
#df_daily =df.groupby('date').agg({'mvrv': 'mean'}).reset_index()
df_mvrv_daily =df.groupby('Date').mean().reset_index()

#madfe open hi low close ... use same value as MVRV value
# df_mvrv_daily['mvrv'] => this colume is MVRV value
df_mvrv_daily['Ticker'] = 'Bitcoin-MVRV'
df_mvrv_daily['Open'] = df_mvrv_daily['mvrv'] 
df_mvrv_daily['High'] = df_mvrv_daily['mvrv']
df_mvrv_daily['Low'] = df_mvrv_daily['mvrv']
df_mvrv_daily['Close'] = df_mvrv_daily['mvrv']      
df_mvrv_daily['Volume'] = 0
df_mvrv_daily['Adj Close'] = df_mvrv_daily['mvrv']
df_mvrv_daily.drop(['mvrv','timestamp'], axis=1, inplace=True)



# %%
df_mvrv_daily.to_csv(savefile,index=False)
print('save file to :' + savefile)
del df, df_mvrv_daily

# %%
#STEP 4 load existing MVRV.csv and merge with new downloadMVRV.csv

# %%

df_bitcoin_mvrv = pd.read_csv(BitcoinMVRV_file)
df_download_mvrv = pd.read_csv(savefile)

# %%
# 2. Concatenate the two DataFrames.
combined_df = pd.concat([df_bitcoin_mvrv, df_download_mvrv], ignore_index=True)
# 3. Remove duplicates from the 'date' column, keeping the first entry.
del df_bitcoin_mvrv , df_download_mvrv
df_BitcoinMVRV = combined_df.drop_duplicates(subset=['Date'], keep='first')
df_BitcoinMVRV.dropna()
#df_BitcoinMVRV.sort_values(by='date', inplace=True)

df_BitcoinMVRV.to_csv(save_final_BitcoinMVRV_combined_file,index=False)
print ('Save MVRV file to :' + save_final_BitcoinMVRV_combined_file)

# %%
#delete mvrv.json, downloadMVRV.csv


# %%
import os

# %%
try:
    os.remove(mvrv_file)
except Exception as e:
    print(f"Error: Deleted File not found at path: {download_folder}")
try:
    os.remove(savefile)
except Exception as e:
    print(f"Error: Deleted File not found at path: {download_folder}")

print('All done')

# %%



