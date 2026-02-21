"""
Rittavee 2026
Bitcoin MVRV Data Download and Processing Tool

This module provides a class for downloading Bitcoin MVRV data from blockchain.com,
converting it to CSV format, and merging it with existing data.
"""

import asyncio
import json
import os
import time
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright, expect


class BitcoinMVRVProcessor:
    """
    A class to handle downloading and processing Bitcoin MVRV data.
    
    This class manages the complete workflow:
    1. Delete old MVRV JSON files
    2. Download MVRV data from blockchain.com
    3. Convert JSON to CSV format
    4. Merge with existing MVRV data
    5. Clean up temporary files
    """
    
    def __init__(self, bitcoin_mvrv_file=None, download_folder=None):
        """
        Initialize the Bitcoin MVRV Processor.
        
        Args:
            bitcoin_mvrv_file (str): Path to existing BitcoinMVRV.csv file.
                                    Defaults to 'C:\\Amibroker Data\\Raw Data\\BitcoinMVRV.csv'
            download_folder (str): Path to downloads folder.
                                  Defaults to user's Downloads folder.
        """
        # Set default paths
        self.download_folder = download_folder or str(Path.home() / "Downloads")
        
        self.mvrv_file = os.path.join(self.download_folder, "mvrv.json")
        self.savefile = os.path.join(self.download_folder, "downloadMVRV.csv")
        
        self.bitcoin_mvrv_file = (
            bitcoin_mvrv_file or 
            r"C:\Amibroker Data\Raw Data\BitcoinMVRV.csv"
        )
        self.final_output_file = self.bitcoin_mvrv_file
    
    def delete_matching_files(self):
        """
        Delete old mvrv.json files in the Downloads folder.
        
        Searches for files matching the pattern 'mvrv*.json' and removes them.
        """
        try:
            downloads_path = Path.home() / "Downloads"
            
            if not downloads_path.is_dir():
                print(f"Error: The Downloads folder was not found at '{downloads_path}'")
                return
            
            print(f"Searching for files in: {downloads_path}")
            files_found = list(downloads_path.glob('mvrv*.json'))
            
            if not files_found:
                print("No files found matching the pattern 'mvrv*.json'. Nothing to delete.")
                return
            
            print(f"Found {len(files_found)} file(s) to delete:")
            for file_path in files_found:
                print(f" - {file_path.name}")
            
            for file_path in files_found:
                try:
                    file_path.unlink()
                    print(f"Successfully deleted: {file_path.name}")
                except OSError as e:
                    print(f"Error deleting file {file_path.name}: {e}")
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    async def download_mvrv_data(self):
        """
        Download MVRV data from blockchain.com using Playwright.
        
        Opens the MVRV chart page and downloads the data in JSON format.
        """
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                # Open the web page
                await page.goto("https://www.blockchain.com/explorer/charts/mvrv")
                
                # Wait for elements to be visible
                await expect(page.get_by_text("Get a copy of this data")).to_be_visible()
                await expect(page.locator("canvas")).to_be_visible()
                await asyncio.sleep(3)  # Wait for page to fully load
                
                # Download file
                async with page.expect_download() as download_info:
                    await page.get_by_text("Get a copy of this data").click()
                    print("Button clicked successfully.")
                
                download = await download_info.value
                await download.save_as(self.mvrv_file)
                filename = download.suggested_filename
                print(f"Suggested filename: {filename}")
                print(f"File downloaded to: {self.mvrv_file}")
                
                # Wait for download to complete
                max_wait = 30
                start_time = time.time()
                while not Path(self.mvrv_file).exists():
                    if time.time() - start_time > max_wait:
                        raise TimeoutError(
                            f"Download file {self.mvrv_file} was not created "
                            f"within {max_wait} seconds"
                        )
                    await asyncio.sleep(0.5)
                
                # Wait until file size is stable (download complete)
                file_size = 0
                stable_checks = 0
                while stable_checks < 3:
                    if Path(self.mvrv_file).exists():
                        current_size = Path(self.mvrv_file).stat().st_size
                        if current_size == file_size and file_size > 0:
                            stable_checks += 1
                        else:
                            stable_checks = 0
                        file_size = current_size
                    await asyncio.sleep(0.5)
                
                print(f"Download completed successfully. File size: {file_size} bytes")
                
                # Wait to observe result
                await page.wait_for_timeout(3000)
            
            finally:
                await context.close()
                await browser.close()
    
    def json_to_csv(self):
        """
        Convert MVRV JSON data to CSV format.
        
        Reads the downloaded JSON file, processes the data, and converts it
        to a daily MVRV CSV file suitable for use in Amibroker.
        """
        print(f"Loading JSON data from: {self.mvrv_file}")
        with open(self.mvrv_file, 'r') as f:
            data = json.load(f)
        
        # Extract MVRV data
        mvrv_data = data['mvrv']
        
        # Convert to DataFrame
        df = pd.DataFrame(mvrv_data)
        print(df.tail(5))
        
        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['x'], unit='ms')
        df['mvrv'] = df['y']
        df = df[['timestamp', 'mvrv']]
        
        # Create daily data
        df['Date'] = df['timestamp'].dt.date
        df_mvrv_daily = df.groupby('Date').mean().reset_index()
        
        # Create OHLCV format with MVRV as all price values
        df_mvrv_daily['Ticker'] = 'Bitcoin-MVRV'
        df_mvrv_daily['Open'] = df_mvrv_daily['mvrv']
        df_mvrv_daily['High'] = df_mvrv_daily['mvrv']
        df_mvrv_daily['Low'] = df_mvrv_daily['mvrv']
        df_mvrv_daily['Close'] = df_mvrv_daily['mvrv']
        df_mvrv_daily['Volume'] = 0
        df_mvrv_daily['Adj Close'] = df_mvrv_daily['mvrv']
        df_mvrv_daily.drop(['mvrv', 'timestamp'], axis=1, inplace=True)
        
        # Save to CSV
        df_mvrv_daily.to_csv(self.savefile, index=False)
        print(f'Saved file to: {self.savefile}')
    
    def merge_with_existing_data(self):
        """
        Merge newly downloaded MVRV data with existing BitcoinMVRV.csv file.
        
        Concatenates the existing and new data, removes duplicates based on Date,
        and saves the result.
        """
        df_bitcoin_mvrv = pd.read_csv(self.bitcoin_mvrv_file)
        df_download_mvrv = pd.read_csv(self.savefile)
        
        # Concatenate the two DataFrames
        combined_df = pd.concat([df_bitcoin_mvrv, df_download_mvrv], ignore_index=True)
        
        # Remove duplicates from the 'Date' column, keeping the first entry
        df_bitcoin_mvrv_merged = combined_df.drop_duplicates(subset=['Date'], keep='first')
        df_bitcoin_mvrv_merged = df_bitcoin_mvrv_merged.dropna()
        
        # Save merged file
        df_bitcoin_mvrv_merged.to_csv(self.final_output_file, index=False)
        print(f'Saved merged MVRV file to: {self.final_output_file}')
    
    def cleanup_temporary_files(self):
        """Delete temporary files (mvrv.json and downloadMVRV.csv)."""
        try:
            os.remove(self.mvrv_file)
            print(f"Deleted: {self.mvrv_file}")
        except FileNotFoundError:
            print(f"File not found: {self.mvrv_file}")
        except Exception as e:
            print(f"Error deleting {self.mvrv_file}: {e}")
        
        try:
            os.remove(self.savefile)
            print(f"Deleted: {self.savefile}")
        except FileNotFoundError:
            print(f"File not found: {self.savefile}")
        except Exception as e:
            print(f"Error deleting {self.savefile}: {e}")
    
    async def run(self):
        """
        Execute the complete MVRV data download and processing workflow.
        
        Steps:
        1. Delete old MVRV files
        2. Download MVRV data from blockchain.com
        3. Convert JSON to CSV
        4. Merge with existing data
        5. Clean up temporary files
        """
        print("Starting Bitcoin MVRV data processing...")
        
        print("\n[Step 1] Deleting old MVRV files...")
        self.delete_matching_files()
        
        print("\n[Step 2] Downloading MVRV data...")
        await self.download_mvrv_data()
        
        print("\n[Step 3] Converting JSON to CSV...")
        self.json_to_csv()
        
        print("\n[Step 4] Merging with existing data...")
        self.merge_with_existing_data()
        
        print("\n[Step 5] Cleaning up temporary files...")
        self.cleanup_temporary_files()
        
        print("\n✓ All done!")


if __name__ == "__main__":
    # Create processor instance and run the complete workflow
    processor = BitcoinMVRVProcessor()
    asyncio.run(processor.run())



