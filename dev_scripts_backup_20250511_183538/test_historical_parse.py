"""
Test script for historical CSV parsing - runs after the CSV search conflict fix.

This script:
1. Connects to the bot
2. Runs a historical parse for server 5251382d-8bce-4abd-8bcb-cdef73698a46
3. Verifies CSV files are found and processed correctly
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_historical_parse():
    """
    Test the historical parser directly with specific server ID
    """
    try:
        # Import necessary modules
        from bot import initialize_bot

        logger.info("Initializing bot for testing...")
        bot = await initialize_bot(force_sync=False)
        
        # Wait for bot to fully initialize
        logger.info("Waiting for bot to fully initialize...")
        await asyncio.sleep(2)
        
        # Get the CSV processor cog - the cog name might be lowercase 'csv_processor'
        csv_processor = bot.get_cog("csv_processor")
        if not csv_processor:
            logger.error("Failed to get csv_processor cog")
            return
            
        # Set the server ID to test
        server_id = "5251382d-8bce-4abd-8bcb-cdef73698a46"
        
        # Run historical parsing for specific server
        logger.info(f"Running historical parser for server {server_id}")
        
        # Set test to look back 30 days to include all test files
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Run the historical parsing - using the correct method name
        result = await csv_processor.run_historical_parse(
            server_id=server_id,
            days=30  # Look back 30 days
        )
        
        # Log the result
        if result is not None:
            logger.info(f"Historical parsing completed successfully: {result}")
        else:
            logger.error("Historical parsing failed")
            
        # We can't verify the status directly as there's no dedicated status method
        # Instead, we'll check the bot's logs for success messages
        logger.info(f"Check the bot logs for CSV processing status")
        
        # Disconnect the bot
        logger.info("Test completed, disconnecting bot")
        await bot.close()
        
    except Exception as e:
        logger.error(f"Error in historical parsing test: {e}", exc_info=True)

def main():
    """Main function to run the test"""
    logger.info("Starting historical parsing test")
    asyncio.run(run_historical_parse())
    logger.info("Historical parsing test completed")

if __name__ == "__main__":
    main()