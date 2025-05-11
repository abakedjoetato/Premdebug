"""
Test script to trigger the CSV processor and verify our fixes.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set up mock bot
class MockBot:
    def __init__(self):
        self._db = None
        self._background_tasks = {}
        self._sftp_connections = {}
        self._home_guild_id = None
        self.user = MockUser()
        
    async def wait_until_ready(self):
        """Mock method for wait_until_ready"""
        return True
        
    @property
    def db(self):
        return self._db
        
    @db.setter
    def db(self, value):
        self._db = value
        
    @property
    def background_tasks(self):
        return self._background_tasks
        
    @background_tasks.setter
    def background_tasks(self, value):
        self._background_tasks = value
        
    @property
    def sftp_connections(self):
        return self._sftp_connections
        
    @sftp_connections.setter
    def sftp_connections(self, value):
        self._sftp_connections = value
        
    @property
    def home_guild_id(self):
        return self._home_guild_id
        
    @home_guild_id.setter
    def home_guild_id(self, value):
        self._home_guild_id = value

class MockUser:
    """Mock user class for the bot"""
    def __init__(self):
        self.id = 1360004212955545623
        self.name = "Emeralds Killfeed"
        self.discriminator = "0000"

async def main():
    logger.info("Starting CSV Processor Test")
    
    try:
        # Import CSVProcessorCog from module
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from cogs.csv_processor import CSVProcessorCog
        
        # Create mock bot
        mock_bot = MockBot()
        
        # Initialize processor cog without starting tasks
        cog = CSVProcessorCog(mock_bot)
        
        # Disable the background task to prevent startup issues
        cog.process_csv_files_task.cancel()
        
        # Set up tracking variables
        cog.all_map_csv_files = []
        cog.map_csv_files_found = []
        
        # Trigger process_csv_files directly instead of using the task
        logger.info(f"Manually triggering CSV processor at {datetime.now()}")
        
        # Process CSV files for the specific server
        server_id = '5251382d-8bce-4abd-8bcb-cdef73698a46'
        
        # Create a mock server config
        config = {
            'hostname': '79.127.236.1',
            'port': 8822,
            'username': 'baked',
            'password': 'emerald',
            'sftp_path': '/logs',
            'csv_pattern': '\\d{4}\\.\\d{2}\\.\\d{2}-\\d{2}\\.\\d{2}\\.\\d{2}\\.csv',
            'original_server_id': '7020',
            'guild_id': '1219706687980568769'
        }
        
        processed, events = await cog._process_server_csv_files(server_id, config)
        
        logger.info(f"CSV processing completed. Files processed: {processed}, Events: {events}")
        
        return True
    except Exception as e:
        logger.error(f"Error in CSV processor test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    asyncio.run(main())