"""
Simplified test script for CSV historical parsing that prints available cogs
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test():
    """
    Run a simplified test to check available cogs and run historical parse
    """
    try:
        # Import necessary modules
        from bot import initialize_bot

        logger.info("Initializing bot for testing...")
        bot = await initialize_bot(force_sync=False)
        
        # Wait for bot to fully initialize
        logger.info("Waiting for bot to fully initialize...")
        await asyncio.sleep(2)
        
        # List all available cogs
        cog_names = list(bot.cogs.keys())
        logger.info(f"Available cogs: {cog_names}")
        
        # Try to get the CSV processor cog by exact name
        for cog_name in cog_names:
            if "csv" in cog_name.lower():
                logger.info(f"Found CSV processor cog: {cog_name}")
                csv_processor = bot.get_cog(cog_name)
                
                # Check available methods in the cog
                methods = [method for method in dir(csv_processor) if not method.startswith('_')]
                logger.info(f"Available methods in {cog_name}: {methods}")
                
                # Look for methods related to historical parsing
                historical_methods = [m for m in methods if "historical" in m.lower()]
                logger.info(f"Historical methods: {historical_methods}")
                
                # Try to run historical parse if possible
                if "run_historical_parse" in methods:
                    server_id = "5251382d-8bce-4abd-8bcb-cdef73698a46"
                    logger.info(f"Running historical parse for server {server_id}")
                    result = await csv_processor.run_historical_parse(server_id, days=30)
                    logger.info(f"Historical parse result: {result}")
                elif historical_methods:
                    logger.info(f"Found potential historical methods but not run_historical_parse")
                    logger.info(f"Try with first available: {historical_methods[0]}")
                    server_id = "5251382d-8bce-4abd-8bcb-cdef73698a46"
                    method = getattr(csv_processor, historical_methods[0])
                    result = await method(server_id)
                    logger.info(f"Historical parse result: {result}")
                else:
                    logger.error("No historical parse methods found")
        
        # Disconnect the bot
        logger.info("Test completed, disconnecting bot")
        await bot.close()
        
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

def main():
    """Main function to run the test"""
    logger.info("Starting test")
    asyncio.run(run_test())
    logger.info("Test completed")

if __name__ == "__main__":
    main()