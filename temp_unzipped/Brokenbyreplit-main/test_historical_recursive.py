"""
Test script for the historical recursive subdirectory searching functionality.
This script will directly execute the historical parse command via the bot's command system.
"""
import asyncio
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_historical")

async def run_test():
    """Run the historical parse test directly using the bot instance"""
    logger.info("Starting historical parse test with recursive subdirectory searching")
    
    # Import the bot initialization
    from bot import initialize_bot
    
    # Initialize the bot
    bot = await initialize_bot(force_sync=False)
    if not bot:
        logger.error("Failed to initialize bot")
        return
    
    logger.info("Bot initialized successfully")
    
    # Get the CSV processor cog
    csv_processor = bot.get_cog("CSVProcessor")
    if not csv_processor:
        logger.error("Failed to get CSV processor cog")
        return
    
    logger.info("Got CSV processor cog")
    
    # Test with the numeric server ID
    server_id = "7020"
    
    # Run the historical parse function
    logger.info(f"Running historical parse for server ID: {server_id}")
    start_time = datetime.now()
    
    # Use 30 days for testing
    files_processed, events_imported = await csv_processor.run_historical_parse_with_original_id(server_id, days=30)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"Historical parse completed:")
    logger.info(f"  - Files processed: {files_processed}")
    logger.info(f"  - Events imported: {events_imported}")
    logger.info(f"  - Time elapsed: {elapsed:.2f} seconds")
    
    # Close bot client and cleanup
    await bot.close()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(run_test())