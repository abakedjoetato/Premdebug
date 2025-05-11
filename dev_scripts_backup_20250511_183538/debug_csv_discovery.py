"""
# module: debug_csv_discovery
CSV Discovery Diagnostic Tool

This script provides comprehensive diagnostics on the CSV file discovery process.
It traces through each step of the file discovery pipeline to identify where
files are being lost or filtered out incorrectly.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('csv_debug.log')
    ]
)
logger = logging.getLogger("csv_debug")

# Import our components
from utils.sftp import SFTPManager, get_sftp_client
from utils.file_discovery import FileDiscovery
from utils.csv_processor_coordinator import CSVProcessorCoordinator

class CSVDiagnostics:
    """Diagnostic tool for CSV file discovery and processing"""
    
    def __init__(self):
        """Initialize the diagnostic tool"""
        self.file_discovery = FileDiscovery()
        self.coordinator = CSVProcessorCoordinator()
        self.sftp_connections = {}
        
    async def run_diagnostics(self, server_id: str, config: Dict[str, Any], historical_mode: bool = True):
        """Run comprehensive diagnostics on the CSV processing system
        
        Args:
            server_id: Server ID to diagnose
            config: Server configuration
            historical_mode: Whether to run in historical mode (more thorough)
        """
        logger.info("=" * 80)
        logger.info(f"STARTING CSV DIAGNOSTICS FOR SERVER {server_id}")
        logger.info("=" * 80)
        
        # Step 1: Test SFTP connection
        logger.info("\n## STEP 1: TESTING SFTP CONNECTION")
        sftp = await self._get_sftp_manager(server_id, config)
        if not sftp:
            logger.error("SFTP connection failed - cannot continue diagnostics")
            return
            
        logger.info(f"✓ SFTP connection successful to {config['hostname']}")
        
        # Step 2: Test directory_exists method
        logger.info("\n## STEP 2: TESTING DIRECTORY_EXISTS METHOD")
        root_exists = await sftp.directory_exists("/")
        logger.info(f"Root directory exists: {root_exists}")
        
        # Common paths to check
        test_paths = [
            "/",
            "/logs",
            "/Logs",
            "/game",
            "/data"
        ]
        
        for path in test_paths:
            exists = await sftp.directory_exists(path)
            logger.info(f"Directory {path} exists: {exists}")
            
            if exists:
                # List files in this directory
                try:
                    files = await sftp.listdir(path)
                    logger.info(f"Found {len(files)} entries in {path}:")
                    for file in files[:10]:  # Show first 10 entries
                        logger.info(f"  - {file}")
                    if len(files) > 10:
                        logger.info(f"  ... and {len(files) - 10} more")
                except Exception as e:
                    logger.error(f"Error listing files in {path}: {e}")
        
        # Step 3: Test find_base_paths
        logger.info("\n## STEP 3: TESTING FIND_BASE_PATHS")
        base_paths = await self.file_discovery._find_base_paths(sftp, server_id, historical_mode)
        logger.info(f"Found {len(base_paths)} base paths:")
        for path in base_paths:
            logger.info(f"  Base path: {path}")
            
        # Step 4: Test find_map_directories
        logger.info("\n## STEP 4: TESTING FIND_MAP_DIRECTORIES")
        map_dirs = await self.file_discovery._find_map_directories(sftp, base_paths)
        logger.info(f"Found {len(map_dirs)} map directories:")
        for directory in map_dirs:
            logger.info(f"  Map directory: {directory}")
            
        # Step 5: Test explicit CSV file discovery
        logger.info("\n## STEP 5: TESTING CSV FILE DISCOVERY")
        csv_pattern = r'.*\.csv$'
        
        all_files = []
        for directory in base_paths + map_dirs:
            logger.info(f"Searching for CSV files in {directory}...")
            csv_files = await self.file_discovery._list_csv_files(sftp, directory, csv_pattern)
            logger.info(f"  Found {len(csv_files)} CSV files in {directory}")
            all_files.extend(csv_files)
            
            if csv_files:
                for file in csv_files[:5]:  # Show first 5 files
                    logger.info(f"  - {file}")
                if len(csv_files) > 5:
                    logger.info(f"  ... and {len(csv_files) - 5} more")
        
        logger.info(f"Total CSV files found: {len(all_files)}")
        
        # Step 6: Test full discovery process
        logger.info("\n## STEP 6: TESTING FULL DISCOVERY PROCESS")
        days_back = 30 if historical_mode else 1
        start_date = datetime.now() - timedelta(days=days_back)
        
        files, metadata = await self.file_discovery.discover_csv_files(
            sftp=sftp,
            server_id=server_id,
            start_date=start_date,
            days_back=days_back,
            historical_mode=historical_mode
        )
        
        logger.info(f"Full discovery found {len(files)} files with metadata: {metadata}")
        
        if files:
            logger.info("Sample files found:")
            for file in files[:5]:
                logger.info(f"  - {file}")
            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more")
        
        # Step 7: Test coordinator
        logger.info("\n## STEP 7: TESTING COORDINATOR INTERFACE")
        try:
            coordinator_result = await self.coordinator.process_historical_files(
                server_id=server_id,
                sftp=sftp,
                days_back=days_back
            )
            logger.info(f"Coordinator result: {coordinator_result}")
        except Exception as e:
            logger.error(f"Error in coordinator: {e}")
            
        logger.info("\n## DIAGNOSTICS COMPLETE")
        
    async def _get_sftp_manager(self, server_id: str, config: Dict[str, Any]) -> Optional[SFTPManager]:
        """Get an SFTP manager for diagnostics
        
        Args:
            server_id: Server ID
            config: Server configuration
            
        Returns:
            SFTPManager or None if connection fails
        """
        try:
            # Get a new SFTP client in case our existing one has issues
            sftp = await get_sftp_client(
                hostname=config["hostname"],
                port=config["port"],
                username=config["username"],
                password=config["password"],
                server_id=server_id,
                original_server_id=config.get("original_server_id"),
                force_new=True
            )
            
            if not sftp:
                logger.error(f"Failed to create SFTP client for {server_id}")
                return None
                
            # Store connection for cleanup
            self.sftp_connections[server_id] = sftp
            
            return sftp
        except Exception as e:
            logger.error(f"Error getting SFTP manager: {e}")
            return None
            
    async def cleanup(self):
        """Clean up SFTP connections"""
        for server_id, sftp in self.sftp_connections.items():
            try:
                await sftp.close()
                logger.info(f"Closed SFTP connection for {server_id}")
            except Exception as e:
                logger.warning(f"Error closing SFTP connection for {server_id}: {e}")
                
async def main():
    """Main function to run diagnostics"""
    # Server details - use test server details
    server_id = "2143443" # Change this to match your server ID
    config = {
        "hostname": "208.103.169.139", # Change this to match your server hostname
        "port": 22,  # Change this to match your server port
        "username": "totemptation", # Change this to match your server username
        "password": "YzhkZnPqe6", # Change this to match your server password
        "original_server_id": "1" # Change this to match your server original ID
    }
    
    diagnostics = CSVDiagnostics()
    
    try:
        await diagnostics.run_diagnostics(server_id, config, historical_mode=True)
    finally:
        await diagnostics.cleanup()
        
if __name__ == "__main__":
    asyncio.run(main())