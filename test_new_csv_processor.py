"""
# module: test_new_csv_processor
Test script for the new CSV processor system

This script tests the rebuilt CSV processing system with sample data
to verify that it works correctly in both historical and killfeed modes.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('csv_test.log')
    ]
)
logger = logging.getLogger("csv_test")

# Mock classes for testing
class MockDB:
    """Mock database for testing"""
    
    def __init__(self):
        self.players = MockCollection('players')
        self.kills = MockCollection('kills')
        self.rivalries = MockCollection('rivalries')
        self.servers = MockCollection('servers')
        self.game_servers = MockCollection('game_servers')
        self.guilds = MockCollection('guilds')
        
    async def find_one(self, query):
        return None
        
    async def find(self, query):
        return []
        
class MockCollection:
    """Mock collection for testing"""
    
    def __init__(self, name):
        self.name = name
        self.data = []
        
    async def find_one(self, query):
        return None
        
    async def find(self, query):
        return []
        
    async def insert_one(self, document):
        self.data.append(document)
        return MockInsertResult()
        
    async def update_one(self, query, update):
        return None
        
    async def update_stats(self, player_id, stat_type):
        return None
        
    async def update_nemesis_and_prey(self, killer_id, victim_id, server_id):
        return None
        
class MockInsertResult:
    """Mock insert result for testing"""
    
    def __init__(self):
        self.inserted_id = "mock_id"
        
class MockBot:
    """Mock bot for testing"""
    
    def __init__(self):
        self._db = MockDB()
        self._user = None
        
    @property
    def db(self):
        return self._db
        
    @property
    def user(self):
        return self._user
        
    async def wait_until_ready(self):
        return
        
class MockSFTP:
    """Mock SFTP manager for testing"""
    
    def __init__(self, hostname, port, username, password, server_id, original_server_id=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.server_id = server_id
        self.original_server_id = original_server_id
        self.is_connected = True
        self.sample_files = []
        
        # Load sample files from attached_assets
        self._find_sample_files()
        
    def _find_sample_files(self):
        """Find sample CSV files in attached_assets directory"""
        assets_dir = "attached_assets"
        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                if filename.endswith(".csv"):
                    self.sample_files.append(os.path.join(assets_dir, filename))
                    
        logger.info(f"Found {len(self.sample_files)} sample CSV files")
        
    async def connect(self):
        self.is_connected = True
        return self
        
    async def close(self):
        self.is_connected = False
        
    async def directory_exists(self, directory):
        return True
        
    async def listdir(self, directory):
        # Simulate directory listing
        return ["world_0", "logs", "config"]
        
    async def list_files(self, directory, pattern):
        # Return sample file basenames
        return [os.path.basename(f) for f in self.sample_files]
        
    async def read_file(self, file_path):
        # Try to find a matching sample file
        filename = os.path.basename(file_path)
        for sample_file in self.sample_files:
            if os.path.basename(sample_file) == filename:
                # Read and return the actual sample file content
                try:
                    with open(sample_file, 'r') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading sample file {sample_file}: {e}")
                    return ""
                    
        # If no matching file, return empty string
        return ""

async def test_historical_parser():
    """Test the historical CSV parser"""
    logger.info("Testing historical parser")
    
    # Import our classes
    from utils.csv_processor_coordinator import CSVProcessorCoordinator
    from utils.stable_csv_parser import StableCSVParser
    from utils.file_discovery import FileDiscovery
    
    # Create coordinator
    coordinator = CSVProcessorCoordinator()
    
    # Override the _process_events method to just log events
    original_process_events = coordinator._process_events
    
    async def mock_process_events(events, server_id):
        logger.info(f"Processed {len(events)} events for server {server_id}")
        for event in events:
            logger.info(f"  Event: {event['killer_name']} killed {event['victim_name']} with {event['weapon']}")
            
    coordinator._process_events = mock_process_events
    
    # Create SFTP manager with sample data
    sftp = MockSFTP(
        hostname="localhost",
        port=22,
        username="test",
        password="test",
        server_id="test_server"
    )
    
    # Run historical processing
    try:
        files_processed, events_processed = await coordinator.process_historical(
            sftp=sftp,
            server_id="test_server",
            days=30
        )
        
        logger.info(f"Historical processing results:")
        logger.info(f"  Files processed: {files_processed}")
        logger.info(f"  Events processed: {events_processed}")
        
        # Check statistics
        stats = coordinator.get_processing_stats("test_server")
        logger.info(f"Processing statistics: {stats}")
        
        # Validate success
        if files_processed > 0 and events_processed > 0:
            logger.info("Historical parser test: SUCCESS")
        else:
            logger.error("Historical parser test: FAILED")
    except Exception as e:
        logger.error(f"Error testing historical parser: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    # Restore original method
    coordinator._process_events = original_process_events

async def test_killfeed_parser():
    """Test the killfeed CSV parser"""
    logger.info("Testing killfeed parser")
    
    # Import our classes
    from utils.csv_processor_coordinator import CSVProcessorCoordinator
    from utils.stable_csv_parser import StableCSVParser
    from utils.file_discovery import FileDiscovery
    
    # Create coordinator
    coordinator = CSVProcessorCoordinator()
    
    # Override the _process_events method to just log events
    original_process_events = coordinator._process_events
    
    async def mock_process_events(events, server_id):
        logger.info(f"Processed {len(events)} events for server {server_id}")
        for event in events:
            logger.info(f"  Event: {event['killer_name']} killed {event['victim_name']} with {event['weapon']}")
            
    coordinator._process_events = mock_process_events
    
    # Create SFTP manager with sample data
    sftp = MockSFTP(
        hostname="localhost",
        port=22,
        username="test",
        password="test",
        server_id="test_server"
    )
    
    # First run historical to initialize state
    await coordinator.process_historical(
        sftp=sftp,
        server_id="test_server",
        days=30
    )
    
    # Simulate new content added to files
    # Run killfeed processing
    try:
        files_processed, events_processed = await coordinator.process_killfeed(
            sftp=sftp,
            server_id="test_server"
        )
        
        logger.info(f"Killfeed processing results:")
        logger.info(f"  Files processed: {files_processed}")
        logger.info(f"  Events processed: {events_processed}")
        
        # Check statistics
        stats = coordinator.get_processing_stats("test_server")
        logger.info(f"Processing statistics: {stats}")
        
        logger.info("Killfeed parser test: COMPLETED")
    except Exception as e:
        logger.error(f"Error testing killfeed parser: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    # Restore original method
    coordinator._process_events = original_process_events

async def test_cog_integration():
    """Test the CSV processor cog integration"""
    logger.info("Testing CSV processor cog integration")
    
    # Import the cog
    from cogs.new_csv_processor import CSVProcessorCog
    
    # Create a mock bot
    bot = MockBot()
    
    # Create the cog
    try:
        # Monkeypatch the _get_sftp_manager method to return our mock SFTP
        original_get_sftp = CSVProcessorCog._get_sftp_manager
        
        async def mock_get_sftp(self, server_id, config):
            return MockSFTP(
                hostname=config["hostname"],
                port=config["port"],
                username=config["username"],
                password=config["password"],
                server_id=server_id,
                original_server_id=config.get("original_server_id")
            )
            
        CSVProcessorCog._get_sftp_manager = mock_get_sftp
        
        # Also monkeypatch the _get_server_configs method
        original_get_configs = CSVProcessorCog._get_server_configs
        
        async def mock_get_configs(self):
            return {
                "test_server": {
                    "hostname": "localhost",
                    "port": 22,
                    "username": "test",
                    "password": "test",
                    "server_id": "test_server",
                    "name": "Test Server"
                }
            }
            
        CSVProcessorCog._get_server_configs = mock_get_configs
        
        # Create the cog
        cog = CSVProcessorCog(bot)
        
        # Test direct CSV processing
        files_processed, events_processed = await cog.direct_csv_processing(
            server_id="test_server",
            days=30
        )
        
        logger.info(f"Cog direct processing results:")
        logger.info(f"  Files processed: {files_processed}")
        logger.info(f"  Events processed: {events_processed}")
        
        # Test server CSV processing
        files_processed, events_processed = await cog._process_server_csv_files(
            server_id="test_server",
            config={
                "hostname": "localhost",
                "port": 22,
                "username": "test",
                "password": "test",
                "server_id": "test_server",
                "name": "Test Server"
            }
        )
        
        logger.info(f"Cog server processing results:")
        logger.info(f"  Files processed: {files_processed}")
        logger.info(f"  Events processed: {events_processed}")
        
        # Stop the background task
        cog.cog_unload()
        
        logger.info("CSV processor cog integration test: COMPLETED")
        
        # Restore original methods
        CSVProcessorCog._get_sftp_manager = original_get_sftp
        CSVProcessorCog._get_server_configs = original_get_configs
    except Exception as e:
        logger.error(f"Error testing cog integration: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Main test function"""
    logger.info("Starting CSV processor tests")
    
    # Test the historical parser
    await test_historical_parser()
    
    # Test the killfeed parser
    await test_killfeed_parser()
    
    # Test the cog integration
    await test_cog_integration()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    asyncio.run(main())