"""
Script to verify our file count tracking fix is working properly.

This script:
1. Waits for the CSV processor to run
2. Checks the logs for the updated file count
"""
import os
import time
import re

def scan_logs_for_pattern():
    """Scan logs for patterns indicating our fix is working"""
    # Wait for the first CSV processing cycle to complete
    print("Waiting for CSV processor to run...")
    time.sleep(30)  # Wait 30 seconds for CSV processor to run
    
    # Check the bot.log file
    try:
        with open("bot.log", "r") as f:
            log_content = f.read()
            
        # Look for our log message about map directory files
        if "Including " in log_content and "files from map directories in final count" in log_content:
            print("SUCCESS: Found our map directory tracking log message!")
            # Extract the file count
            match = re.search(r"Including (\d+) files from map directories", log_content)
            if match:
                file_count = match.group(1)
                print(f"Found {file_count} files in map directories")
                
        # Look for the final stats with corrected file count
        match = re.search(r"CRITICAL DEBUG: CSV processing completed\. Files Found=(\d+)", log_content)
        if match:
            file_count = match.group(1)
            print(f"Final stats show Files Found={file_count}")
            if file_count != "0":
                print("SUCCESS: File count is correctly reported!")
            else:
                print("WARNING: File count is still reported as 0")
        else:
            print("Could not find final stats message")
            
        # Check for map directory CSV file detection
        match = re.search(r"Found (\d+) CSV files in map directory", log_content)
        if match:
            map_file_count = match.group(1)
            print(f"Found {map_file_count} CSV files in map directory")
            if map_file_count != "0":
                print("SUCCESS: CSV files are being found in map directory!")
            else:
                print("WARNING: No CSV files found in map directory")
        else:
            print("Could not find map directory file detection message")
            
        return True
    except Exception as e:
        print(f"Error scanning logs: {e}")
        return False

def main():
    """Main function to verify our fix"""
    print("Starting fix verification...")
    
    # Check if the fix is applied
    if scan_logs_for_pattern():
        print("Verification complete")
    else:
        print("Verification failed")

if __name__ == "__main__":
    main()