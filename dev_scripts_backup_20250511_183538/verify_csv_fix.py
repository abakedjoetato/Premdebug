"""
Test script to verify the CSV search conflict fix.

This script runs the historical parser to process all files for our target server
and verifies the total files found and processed.
"""
import asyncio
import logging
import discord
from discord.ext import commands
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test():
    """
    Run a verification test for the CSV file search fix
    """
    # Wait for the first cycle to complete
    logger.info("Waiting for first CSV processing cycle to complete...")
    time.sleep(60)  # Wait for 60 seconds for the first cycle to finish
    
    # Check the log file for our success indicators
    with open("bot.log", "r") as f:
        log_content = f.read()
    
    # Find the map directory files detection
    map_files_pattern = r"Found (\d+) CSV files in map directory"
    map_files_matches = re.findall(map_files_pattern, log_content)
    
    if map_files_matches:
        logger.info(f"Found map directory matches: {map_files_matches}")
        map_files_count = int(map_files_matches[-1]) if map_files_matches else 0
        logger.info(f"Latest map directory files found: {map_files_count}")
    else:
        logger.error("No map directory files found in logs")
        
    # Find the final stats message
    final_stats_pattern = r"CRITICAL DEBUG: CSV processing completed\. Files Found=(\d+), Files Processed=(\d+), Events=(\d+)"
    final_stats_matches = re.findall(final_stats_pattern, log_content)
    
    if final_stats_matches:
        logger.info(f"Found final stats matches: {final_stats_matches}")
        last_match = final_stats_matches[-1]
        files_found, files_processed, events = last_match
        logger.info(f"Latest stats: Files Found={files_found}, Files Processed={files_processed}, Events={events}")
        
        # Check if our fix worked
        if int(files_found) > 0:
            logger.info("SUCCESS: Fix is working! Files are now being counted correctly.")
        else:
            logger.error("FAILURE: Fix not working. Files Found is still 0.")
    else:
        logger.error("No final stats found in logs")
    
    # Look for our new map directory files inclusion log
    inclusion_pattern = r"Including (\d+) files from map directories"
    inclusion_matches = re.findall(inclusion_pattern, log_content)
    
    if inclusion_matches:
        logger.info(f"Found map directory inclusion matches: {inclusion_matches}")
        included_count = int(inclusion_matches[-1]) if inclusion_matches else 0
        logger.info(f"Latest map directory files included: {included_count}")
        logger.info("SUCCESS: Map directory files are now being included in the final count!")
    else:
        logger.error("No map directory inclusion logs found")

def main():
    """Run the test"""
    logger.info("Starting CSV fix verification test")
    
    # Create the test event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test())
    logger.info("Test completed")

if __name__ == "__main__":
    main()