# %%
#Set up all file path here:
from pathlib import Path
import re

#use folder 'Downloads' as default
download_folder = str(Path.home() / "Downloads")

mvrv_file = download_folder + '\\mvrv.json'
savefile = download_folder + '\\downloadMVRV.csv'
BitcoinMVRV_file = 'C:\Amibroker Data\Raw Data\\BitcoinMVRV.csv' #load existing MVRV file to combine with downloadMVRF.csv
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

import asyncio
from playwright.async_api import async_playwright, expect
from pathlib import Path


async def download_MVRV():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        # Step 1: Open the web page
        await page.goto("https://www.blockchain.com/explorer/charts/mvrv")
        
        # Wait for elements to be visible
        await expect(page.get_by_text("Get a copy of this data")).to_be_visible()
        await expect(page.locator("canvas")).to_be_visible()
        await asyncio.sleep(3)  # Wait for 3 seconds to ensure page is fully loaded

        # Step 2: Download file
        async with page.expect_download() as download_info:
            await page.get_by_text("Get a copy of this data").click()
            print("Button clicked successfully.")

        download = await download_info.value
        await download.save_as(mvrv_file)
        filename = download.suggested_filename
        print("suggested filename: " + filename)
        print(f"File downloaded to: {mvrv_file}")
        
        # Wait for download to complete
        import time
        max_wait = 30
        start_time = time.time()
        while not Path(mvrv_file).exists():
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"Download file {mvrv_file} was not created within {max_wait} seconds")
            await asyncio.sleep(0.5)
        
        # Wait until file size is stable (download complete)
        file_size = 0
        stable_checks = 0
        while stable_checks < 3:
            if Path(mvrv_file).exists():
                current_size = Path(mvrv_file).stat().st_size
                if current_size == file_size and file_size > 0:
                    stable_checks += 1
                else:
                    stable_checks = 0
                file_size = current_size
            await asyncio.sleep(0.5)
        
        print(f"Download completed successfully. File size: {file_size} bytes")
        
        # Wait to observe result
        await page.wait_for_timeout(3000)
        
        await context.close()
        await browser.close()


# Run the async function
asyncio.run(download_MVRV())

# %%
#STEP3 read json and made CSV file, save to foldrev 'download_folder' =>'Downloads'

# %%
import json
import pandas as pd
from datetime import datetime


# Load JSON data
print(f"Loading JSON data from: {mvrv_file}")
with open(mvrv_file, 'r') as f:
    data = json.load(f)

# Extract MVRV data
mvrv_data = data['mvrv']

# Convert to DataFrame
df = pd.DataFrame(mvrv_data)

print(df.head(5))

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



