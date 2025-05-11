"""
Test SFTP Directory Existence Check

This script tests the new directory_exists method in the SFTPManager class
to ensure it properly checks if directories exist before listing files.
"""

import asyncio
import logging
import sys
from utils.sftp import SFTPManager
from utils.database import DatabaseManager, get_database
from utils.config import get_server_ids, get_server_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_sftp_directory_exists")

async def test_directory_existence():
    """Test directory_exists method implementation."""
    # Initialize database for config access
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Get all server IDs and test each one
    server_ids = await get_server_ids()
    logger.info(f"Testing directory_exists for {len(server_ids)} servers")
    
    for server_id in server_ids:
        # Get server configuration with SFTP details
        config = await get_server_config(server_id)
        if not config:
            logger.warning(f"Could not find config for server {server_id}")
            continue
            
        # Initialize SFTP manager
        sftp = SFTPManager(
            hostname=config.get("sftp_host"),
            port=config.get("sftp_port", 22),
            username=config.get("sftp_username"),
            password=config.get("sftp_password"),
            server_id=server_id
        )
        
        # Connect to the server
        connected = await sftp.connect()
        if not connected:
            logger.error(f"Failed to connect to SFTP for server {server_id}")
            continue
            
        logger.info(f"Connected to SFTP for server {server_id}")
        
        # Test directory paths
        test_paths = [
            "/deathlogs",
            "/logs/deathlogs",
            "/game/deathlogs",
            "/data/deathlogs",
            "/killfeed",
            "/logs/killfeed",
            "/game/logs",
            "/logs",
            f"/logs/{server_id}",
            f"/deathlogs/{server_id}",
            f"/killfeed/{server_id}",
            f"/game/logs/{server_id}",
            f"/data/logs/{server_id}"
        ]
        
        # Test each directory path
        for path in test_paths:
            exists = await sftp.directory_exists(path)
            if exists:
                logger.info(f"✅ Directory exists: {path}")
                # Verify we can list files in this directory
                files = await sftp.listdir(path)
                logger.info(f"  - Found {len(files)} files/dirs in {path}")
            else:
                logger.info(f"❌ Directory doesn't exist: {path}")
        
        # Disconnect when done
        await sftp.disconnect()
    
    logger.info("Directory existence testing complete")

if __name__ == "__main__":
    asyncio.run(test_directory_existence())e())