"""
# module: test_csv_processing
Direct CSV Processing Test

This script directly tests the CSV processing pipeline to verify that our fixes
are working correctly. It bypasses the bot and directly calls the core components.
"""
import asyncio
import csv
import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('csv_test.log')
    ]
)
logger = logging.getLogger("csv_test")

# Import our components
from utils.sftp import SFTPManager, get_sftp_client
from utils.file_discovery import FileDiscovery
from utils.csv_processor_coordinator import CSVProcessorCoordinator
from utils.csv_parser import CSVParser

class CSVTester:
    """Test harness for CSV processing"""
    
    def __init__(self):
        """Initialize the test harness"""
        self.discovery = FileDiscovery()
        self.coordinator = CSVProcessorCoordinator()
        self.parser = CSVParser()
        self.sftp_connections = {}
        
    async def test_discovery(self, server_id: str, config: Dict[str, Any]):
        """Test file discovery
        
        Args:
            server_id: Server ID to use
            config: Server configuration with SFTP details
            
        Returns:
            Tuple[List[str], Dict[str, Any]]: Discovered files and stats
        """
        logger.info(f"Testing file discovery for server {server_id}")
        
        # Create SFTP manager
        sftp = await self._get_sftp_client(server_id, config)
        if not sftp:
            logger.error("Failed to create SFTP client")
            return [], {}
            
        # Set discovery parameters 
        days_back = 30  # Look back 30 days for historical data
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Run discovery
        files, stats = await self.discovery.discover_csv_files(
            sftp=sftp,
            server_id=server_id,
            start_date=start_date,
            days_back=days_back,
            historical_mode=True  # Use historical mode for more thorough search
        )
        
        # Log results
        logger.info(f"Discovery found {len(files)} CSV files")
        logger.info(f"Discovery stats: {stats}")
        
        if files:
            logger.info("First 5 files found:")
            for file in files[:5]:
                logger.info(f"  - {file}")
                
        # Get map files
        map_files = self.discovery.map_directory_files.get(server_id, set())
        logger.info(f"Map directory files found: {len(map_files)}")
        
        if map_files:
            logger.info("First 5 map files found:")
            for file in list(map_files)[:5]:
                logger.info(f"  - {file}")
                
        return files, stats
        
    async def test_download(self, server_id: str, config: Dict[str, Any], files: List[str]):
        """Test downloading CSV files
        
        Args:
            server_id: Server ID to use
            config: Server configuration with SFTP details
            files: List of files to download
            
        Returns:
            int: Number of files successfully downloaded
        """
        logger.info(f"Testing file download for server {server_id}")
        
        # Create SFTP manager
        sftp = await self._get_sftp_client(server_id, config)
        if not sftp:
            logger.error("Failed to create SFTP client")
            return 0
            
        # Create temp directory for downloads
        temp_dir = tempfile.mkdtemp(prefix="csv_test_")
        logger.info(f"Using temp directory: {temp_dir}")
        
        # Download files
        downloaded = 0
        for file_path in files[:5]:  # Only download first 5 files for testing
            try:
                # Get filename from path
                filename = os.path.basename(file_path)
                local_path = os.path.join(temp_dir, filename)
                
                # Download the file
                logger.info(f"Downloading {file_path} to {local_path}")
                success = await sftp.download_file(file_path, local_path)
                
                if success:
                    downloaded += 1
                    # Check file content
                    with open(local_path, 'r') as f:
                        content = f.read()
                        logger.info(f"File {filename} content preview: {content[:200]}...")
                else:
                    logger.error(f"Failed to download {file_path}")
            except Exception as e:
                logger.error(f"Error downloading {file_path}: {e}")
                
        logger.info(f"Successfully downloaded {downloaded} files")
        return downloaded
        
    async def test_parsing(self, server_id: str, config: Dict[str, Any]):
        """Test parsing CSV files
        
        Args:
            server_id: Server ID to use
            config: Server configuration with SFTP details
            
        Returns:
            Tuple[int, int]: Number of files and events processed
        """
        logger.info(f"Testing CSV parsing for server {server_id}")
        
        # Create SFTP manager
        sftp = await self._get_sftp_client(server_id, config)
        if not sftp:
            logger.error("Failed to create SFTP client")
            return 0, 0
            
        # Get temp directory for parsing
        temp_dir = tempfile.mkdtemp(prefix="csv_parse_")
        
        # Run the coordinator's historical processing directly
        try:
            # Set the coordinator's database callbacks to test functions
            self.coordinator.db_get_player = self._mock_get_player
            self.coordinator.db_update_player = self._mock_update_player
            self.coordinator.db_record_kill = self._mock_record_kill
            
            # Process files
            result = await self.coordinator.process_historical_files(
                server_id=server_id,
                sftp=sftp,
                days_back=30,
                work_dir=temp_dir
            )
            
            logger.info(f"Processing result: {result}")
            
            # Get files and events processed
            files_processed = result.get("files_processed", 0)
            events_processed = result.get("events_processed", 0)
            
            logger.info(f"Files processed: {files_processed}")
            logger.info(f"Events processed: {events_processed}")
            
            return files_processed, events_processed
        except Exception as e:
            logger.error(f"Error in CSV parsing test: {e}")
            return 0, 0
            
    async def _get_sftp_client(self, server_id: str, config: Dict[str, Any]) -> Optional[SFTPManager]:
        """Get an SFTP client for testing
        
        Args:
            server_id: Server ID
            config: Server configuration with SFTP details
            
        Returns:
            Optional[SFTPManager]: SFTP client or None if creation fails
        """
        try:
            # If we already have a connection, return it
            if server_id in self.sftp_connections:
                sftp = self.sftp_connections[server_id]
                
                # Check if it's still connected
                if sftp.is_connected:
                    return sftp
                    
                # If not, close it
                await sftp.close()
                del self.sftp_connections[server_id]
                
            # Create a new client
            sftp = await get_sftp_client(
                hostname=config["hostname"],
                port=config["port"],
                username=config["username"],
                password=config["password"],
                server_id=server_id,
                original_server_id=config.get("original_server_id"),
                force_new=True  # Force a new connection
            )
            
            if not sftp:
                logger.error(f"Failed to create SFTP client for {server_id}")
                return None
                
            # Store the connection
            self.sftp_connections[server_id] = sftp
            
            return sftp
        except Exception as e:
            logger.error(f"Error creating SFTP client: {e}")
            return None
            
    async def _mock_get_player(self, server_id: str, player_id: str) -> Dict[str, Any]:
        """Mock function for database player lookup
        
        Args:
            server_id: Server ID
            player_id: Player ID
            
        Returns:
            Dict[str, Any]: Player data
        """
        # Return a mock player record
        return {
            "server_id": server_id,
            "player_id": player_id,
            "name": f"Player_{player_id}",
            "kills": 0,
            "deaths": 0,
            "last_seen": datetime.now().isoformat()
        }
        
    async def _mock_update_player(self, server_id: str, player_id: str, data: Dict[str, Any]) -> bool:
        """Mock function for database player update
        
        Args:
            server_id: Server ID
            player_id: Player ID
            data: Player data to update
            
        Returns:
            bool: Success status
        """
        # Just log the update
        logger.debug(f"Would update player {player_id} on server {server_id} with data: {data}")
        return True
        
    async def _mock_record_kill(self, kill_data: Dict[str, Any]) -> bool:
        """Mock function for recording a kill
        
        Args:
            kill_data: Kill data to record
            
        Returns:
            bool: Success status
        """
        # Just log the kill
        logger.debug(f"Would record kill: {kill_data}")
        return True
        
    async def cleanup(self):
        """Clean up resources"""
        # Close SFTP connections
        for server_id, sftp in self.sftp_connections.items():
            try:
                await sftp.close()
                logger.info(f"Closed SFTP connection for {server_id}")
            except Exception as e:
                logger.warning(f"Error closing SFTP connection for {server_id}: {e}")
                
async def main():
    """Main function"""
    # Server details - use test server details
    server_id = "2143443" # Change this to match your server ID
    config = {
        "hostname": "208.103.169.139", # Change this to match your server hostname
        "port": 22,  # Change this to match your server port
        "username": "totemptation", # Change this to match your server username
        "password": "YzhkZnPqe6", # Change this to match your server password
        "original_server_id": "1" # Change this to match your server original ID
    }
    
    tester = CSVTester()
    
    try:
        # Step 1: Test file discovery
        logger.info("\n### TESTING FILE DISCOVERY ###")
        files, stats = await tester.test_discovery(server_id, config)
        
        if not files:
            logger.error("No files found, cannot continue testing")
            return
            
        # Step 2: Test file download
        logger.info("\n### TESTING FILE DOWNLOAD ###")
        downloaded = await tester.test_download(server_id, config, files)
        
        if downloaded == 0:
            logger.error("No files downloaded, cannot continue testing")
            return
            
        # Step 3: Test file parsing
        logger.info("\n### TESTING FILE PARSING ###")
        files_processed, events_processed = await tester.test_parsing(server_id, config)
        
        # Log overall results
        logger.info("\n### TEST SUMMARY ###")
        logger.info(f"Files found: {len(files)}")
        logger.info(f"Files downloaded: {downloaded}")
        logger.info(f"Files processed: {files_processed}")
        logger.info(f"Events processed: {events_processed}")
        
        if events_processed > 0:
            logger.info("✅ CSV PROCESSING TEST SUCCESSFUL!")
        else:
            logger.error("❌ CSV PROCESSING TEST FAILED: No events processed")
            
    finally:
        # Clean up
        await tester.cleanup()
        
if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())