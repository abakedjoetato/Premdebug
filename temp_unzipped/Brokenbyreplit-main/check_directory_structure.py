"""
Check Directory Structure for CSV Files

This script checks if the expected directory structure for CSV files exists on the game server.
It specifically looks for the /hostname_serverid/actual1/deathlogs/world_*/ structure.

Usage:
    python check_directory_structure.py

"""
import os
import sys
import asyncio
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('directory_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Import necessary modules
try:
    # First ensure utils directory is in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import required modules
    from utils.sftp import SFTPManager
    
    logger.info("Successfully imported required modules")
except Exception as e:
    logger.error(f"Failed to import modules: {e}")
    traceback.print_exc()
    sys.exit(1)

async def check_directories(sftp, server_id, original_server_id):
    """Check if the expected directory structure exists"""
    # Define the expected paths
    if original_server_id is None:
        logger.warning("No original server ID provided, using UUID format")
        base_path = f"/hostname_{server_id}/actual1/deathlogs"
    else:
        logger.info(f"Using original server ID: {original_server_id}")
        base_path = f"/hostname_{original_server_id}/actual1/deathlogs"
    
    logger.info(f"Checking base path: {base_path}")
    
    # Check if base path exists
    base_exists = await sftp.directory_exists(base_path)
    if not base_exists:
        logger.error(f"Base path does not exist: {base_path}")
        # Try alternate naming schemes
        alt_base = base_path.replace('/hostname_', '/')
        logger.info(f"Trying alternate base path: {alt_base}")
        alt_base_exists = await sftp.directory_exists(alt_base)
        if alt_base_exists:
            logger.info(f"Found alternate base path: {alt_base}")
            base_path = alt_base
        else:
            # Try listing root to see what's available
            logger.info("Listing root directory to see what's available")
            try:
                root_contents = await sftp.list_files("/")
                logger.info(f"Root directory contents: {root_contents}")
            except Exception as e:
                logger.error(f"Error listing root directory: {e}")
            return None, []
    else:
        logger.info(f"✅ Base path exists: {base_path}")
    
    # Check for world_* directories
    world_dirs = []
    for world in ["world_0", "world_1", "world_2"]:
        world_path = os.path.join(base_path, world)
        exists = await sftp.directory_exists(world_path)
        if exists:
            logger.info(f"✅ World path exists: {world_path}")
            world_dirs.append(world_path)
        else:
            logger.warning(f"❌ World path does not exist: {world_path}")
    
    return base_path, world_dirs

async def list_directory_contents(sftp, directory):
    """List contents of a directory for debugging"""
    logger.info(f"Listing contents of directory: {directory}")
    try:
        contents = await sftp.list_files(directory)
        logger.info(f"Directory {directory} contains {len(contents)} items")
        for item in contents:
            logger.info(f" - {item}")
        return contents
    except Exception as e:
        logger.error(f"Error listing directory {directory}: {e}")
        traceback.print_exc()
        return []

async def find_csv_files(sftp, directory):
    """Find CSV files in a directory"""
    logger.info(f"Finding CSV files in: {directory}")
    try:
        # Use exact file pattern from the screenshots
        pattern = r'\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}\.csv'
        files = await sftp.list_files(directory, pattern)
        logger.info(f"Found {len(files)} CSV files in {directory}")
        
        # Log the first few files
        if files:
            logger.info(f"First few files: {files[:min(3, len(files))]}")
        
        return files
    except Exception as e:
        logger.error(f"Error finding CSV files in {directory}: {e}")
        traceback.print_exc()
        return []

async def main():
    """Main function"""
    logger.info("Starting directory structure check")
    
    # Test with simple server config
    server_config = {
        'hostname': '79.127.236.1',
        'port': 8822,
        'username': 'baked',
        'password': 'emerald',
        'sftp_path': '/logs',
        'original_server_id': '7020'
    }
    
    server_id = '5251382d-8bce-4abd-8bcb-cdef73698a46'
    
    # Create SFTP manager
    sftp = SFTPManager(
        hostname=server_config['hostname'],
        port=server_config['port'],
        username=server_config['username'],
        password=server_config['password'],
        server_id=server_id,
        original_server_id=server_config.get('original_server_id')
    )
    
    try:
        # Connect to the server
        logger.info(f"Connecting to SFTP server {server_config['hostname']}:{server_config['port']}")
        connected = await sftp.connect()
        if not connected:
            logger.error("Failed to connect to SFTP server")
            return
        
        logger.info("✅ Successfully connected to SFTP server")
        
        # Check for the standard directory structure
        base_path, world_dirs = await check_directories(sftp, server_id, server_config.get('original_server_id'))
        
        if not base_path:
            logger.error("Failed to find base directory structure")
            return
        
        # Check each world directory for CSV files
        for world_dir in world_dirs:
            # List contents of the directory
            await list_directory_contents(sftp, world_dir)
            
            # Find CSV files
            csv_files = await find_csv_files(sftp, world_dir)
            
            # Report results
            if csv_files:
                logger.info(f"✅ Found {len(csv_files)} CSV files in {world_dir}")
            else:
                logger.warning(f"❌ No CSV files found in {world_dir}")
        
        if world_dirs:
            logger.info("✅ Directory structure check: PASSED")
        else:
            logger.error("❌ Directory structure check: FAILED - No world directories found")
    
    except Exception as e:
        logger.error(f"Error running check: {e}")
        traceback.print_exc()
    finally:
        # Disconnect from the server
        await sftp.disconnect()
        logger.info("Disconnected from SFTP server")

if __name__ == "__main__":
    asyncio.run(main())