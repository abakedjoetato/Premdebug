"""
Test script for running historical parse with recursive subdirectory searching.
"""
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_historical")

async def run_test():
    """Run the historical parse test"""
    from bot import initialize_bot
    
    bot = await initialize_bot()
    if not bot:
        logger.error("Failed to initialize bot")
        return
    
    # Get the setup cog
    setup_cog = bot.get_cog("Setup")
    if not setup_cog:
        logger.error("Setup cog not found")
        return
    
    # Get the run_historical_parse method
    if not hasattr(setup_cog, "run_historical_parse"):
        logger.error("run_historical_parse method not found in Setup cog")
        return
    
    # Run historical parse for server ID 7020
    server_id = "7020"
    days = 30
    
    start_time = datetime.now()
    logger.info(f"Running historical parse for server {server_id} with {days} days lookback")
    
    # Simulate ctx for the command
    class MockContext:
        def __init__(self):
            self.guild_id = "1219706687980568769"
            self.guild = None
            self.author = None
            self.channel = None
            
        async def send(self, content=None, embed=None):
            logger.info(f"MOCK CTX: {content}")
            return None
            
        async def reply(self, content=None, embed=None):
            logger.info(f"MOCK CTX REPLY: {content}")
            return None
    
    # Create mock context
    mock_ctx = MockContext()
    
    # Call the method
    result = await setup_cog.run_historical_parse(mock_ctx, server_id=server_id, days=days)
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    logger.info(f"Historical parse completed in {elapsed:.2f} seconds with result: {result}")
    
    # Close bot
    await bot.close()

if __name__ == "__main__":
    asyncio.run(run_test())