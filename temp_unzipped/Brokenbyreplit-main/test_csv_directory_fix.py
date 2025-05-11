"""
Test the fixed CSV processing system with directory checking.

This script triggers a CSV processing cycle and watches the logs to verify
that our fixes for the directory_exists method are working correctly.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta

# Configure logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_csv_directory_fix")

async def wait_for_bot_ready():
    """Wait for the bot to be ready before continuing."""
    logger.info("Waiting for bot to be fully operational...")
    # Simple wait to ensure bot is running
    await asyncio.sleep(5)
    logger.info("Continuing with test")

async def trigger_csv_processing():
    """Import the CSV processor cog and manually trigger processing."""
    try:
        # First, let's import the required modules
        from utils.database import DatabaseManager, get_db, initialize_db
        from utils.config import get_server_ids
        from cogs.csv_processor import CSVProcessorCog
        import discord
        from discord.ext import commands
        
        # Create a mock bot for the cog
        class MockBot(commands.Bot):
            def __init__(self):
                super().__init__(command_prefix="!", intents=discord.Intents.all())
                self._db = None
                
            @property
            def db(self):
                return self._db
                
            async def wait_until_ready(self):
                return True
        
        # Initialize database
        db_manager = await initialize_db()
        
        # Create mock bot with db access
        bot = MockBot()
        bot._db = db_manager.db
        
        # Get all active server IDs
        server_ids = await get_server_ids()
        logger.info(f"Found {len(server_ids)} servers to test")
        
        if not server_ids:
            logger.error("No server IDs found in database")
            return
            
        # Create CSV processor cog instance
        csv_processor = CSVProcessorCog(bot)
        
        # Process each server
        for server_id in server_ids:
            logger.info(f"Testing CSV processing for server {server_id}")
            
            # Set a time window to ensure we capture files
            start_time = datetime.now() - timedelta(days=7)  # Look back 7 days
            
            # Manually process files for this server
            result = await csv_processor.process_csv_files(server_id, historical=True, date_from=start_time)
            
            # Check the result
            if not result or not isinstance(result, dict):
                logger.warning(f"No results returned for server {server_id}")
                continue
                
            files_found = result.get('files_found', 0)
            files_processed = result.get('files_processed', 0)
            events_processed = result.get('events_processed', 0)
            
            logger.info(f"Server {server_id} results:")
            logger.info(f"  - Files found: {files_found}")
            logger.info(f"  - Files processed: {files_processed}")
            logger.info(f"  - Events processed: {events_processed}")
            
            # Compare against previous errors
            if files_found == 0:
                logger.warning("No files were found. Directory checking might still have issues.")
            else:
                logger.info(f"Successfully found {files_found} files! Directory checking fix is working.")
                
            # Allow some time between server processing
            await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"Error during CSV processing test: {e}")
        import traceback
        traceback.print_exc()

async def check_latest_logs():
    """Check the latest bot logs for CSV processing activity."""
    try:
        logger.info("Checking latest bot logs...")
        with open("bot.log", "r") as f:
            # Get the last 100 lines
            lines = f.readlines()[-100:]
            
        # Look for directory_exists usage and CSV processing results
        directory_exists_calls = 0
        csv_files_found = 0
        
        for line in lines:
            if "directory_exists" in line and not "Error" in line:
                directory_exists_calls += 1
            if "CSV files found" in line:
                # Try to extract the number
                try:
                    csv_files_found = int(line.split("CSV files found:")[-1].strip())
                except:
                    pass
        
        logger.info(f"Found {directory_exists_calls} successful directory_exists calls in logs")
        logger.info(f"Found {csv_files_found} CSV files according to logs")
        
        if directory_exists_calls > 0:
            logger.info("✅ directory_exists method is being used successfully!")
        else:
            logger.warning("⚠️ directory_exists method might not be getting called")
            
        if csv_files_found > 0:
            logger.info("✅ CSV files are being found successfully!")
        else:
            logger.warning("⚠️ No CSV files found in logs")
    
    except Exception as e:
        logger.error(f"Error checking logs: {e}")

async def main():
    """Main test function."""
    logger.info("Starting CSV directory fix test")
    
    # Wait for bot to be ready
    await wait_for_bot_ready()
    
    # Check the logs before our test
    await check_latest_logs()
    
    # Trigger CSV processing
    await trigger_csv_processing()
    
    # Allow time for processing to complete and logs to be written
    logger.info("Waiting 10 seconds for processing to complete...")
    await asyncio.sleep(10)
    
    # Check logs again after our test
    await check_latest_logs()
    
    logger.info("CSV directory fix test completed")

if __name__ == "__main__":
    asyncio.run(main())