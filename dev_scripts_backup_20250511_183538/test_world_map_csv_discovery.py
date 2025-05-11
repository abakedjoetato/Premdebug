"""
# module: test_world_map_csv_discovery
Test for CSV file discovery focusing on world map directories

This script directly tests the CSV file discovery logic to ensure it
correctly identifies CSV files in the world_* directories.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('world_map_test.log')
    ]
)

logger = logging.getLogger('test_world_map_csv_discovery')

# Imports for testing
from utils.sftp import SFTPManager
from utils.file_discovery import FileDiscovery

async def test_world_map_discovery(sftp: SFTPManager, server_id: str) -> bool:
    """
    Test the discovery of CSV files in world map directories
    
    Args:
        sftp: SFTP connection to use
        server_id: Server ID to test with
        
    Returns:
        True if world map CSV files were found, False otherwise
    """
    logger.info("Testing world map CSV file discovery")
    
    file_discovery = FileDiscovery()
    
    # First, find base paths
    base_paths = await file_discovery._find_base_paths(sftp, server_id)
    logger.info(f"Found {len(base_paths)} base paths: {base_paths}")
    
    if not base_paths:
        logger.error("No base paths found")
        return False
    
    # Then, find map directories within those base paths
    map_dirs = await file_discovery._find_map_directories(sftp, base_paths, historical_mode=True)
    logger.info(f"Found {len(map_dirs)} map directories: {map_dirs}")
    
    # Count world_* directories
    world_dirs = [d for d in map_dirs if os.path.basename(d).startswith('world_')]
    logger.info(f"Found {len(world_dirs)} world_* directories: {world_dirs}")
    
    # Find CSV files in each map directory
    total_files = 0
    map_files = {}
    
    for directory in map_dirs:
        # Use exact pattern for test files
        csv_pattern = r'.*\.csv$'
        files = await file_discovery._list_csv_files(sftp, directory, csv_pattern)
        
        dir_name = os.path.basename(directory)
        map_files[dir_name] = files
        
        logger.info(f"Found {len(files)} CSV files in {dir_name}")
        
        # Log some sample files
        if files:
            sample = files[:5] if len(files) > 5 else files
            for file in sample:
                logger.info(f"  - {file}")
            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more")
        
        total_files += len(files)
    
    logger.info(f"Total CSV files found in all map directories: {total_files}")
    
    return total_files > 0

async def verify_file_attributes(sftp: SFTPManager, files: List[str]) -> None:
    """Verify attributes of discovered files"""
    logger.info("Verifying file attributes")
    
    # Get attributes for a sample of files
    sample = files[:5] if len(files) > 5 else files
    
    for file_path in sample:
        try:
            # Get file info
            file_info = await sftp.get_file_info(file_path)
            if file_info:
                logger.info(f"File info for {os.path.basename(file_path)}:")
                logger.info(f"  Size: {file_info.get('size', 'unknown')} bytes")
                logger.info(f"  Modified: {file_info.get('mtime', 'unknown')}")
                
                # Try to read the first few lines
                content = await sftp.read_file(file_path)
                if isinstance(content, bytes):
                    try:
                        text = content.decode('utf-8')
                        lines = text.splitlines()
                    except UnicodeDecodeError:
                        try:
                            text = content.decode('latin-1')
                            lines = text.splitlines()
                        except:
                            logger.warning(f"Could not decode file content")
                            continue
                elif isinstance(content, list):
                    lines = content
                else:
                    logger.warning(f"Unexpected content type: {type(content)}")
                    continue
                
                if lines:
                    logger.info(f"  First few lines:")
                    for i, line in enumerate(lines[:3]):
                        logger.info(f"    {i+1}. {line}")
                    if len(lines) > 3:
                        logger.info(f"    ... and {len(lines) - 3} more lines")
                else:
                    logger.warning(f"File is empty")
            else:
                logger.warning(f"Could not get file info for {file_path}")
        except Exception as e:
            logger.error(f"Error verifying file {file_path}: {e}")

async def main() -> None:
    """Main entry point"""
    logger.info("Starting world map CSV discovery test")
    
    # Get connection details from environment or use defaults for testing
    from os import environ
    
    # Default config (will be overridden by environment variables if available)
    config = {
        'hostname': 'your.server.hostname.com',
        'port': 22,
        'username': 'username',
        'password': 'password',
        'server_id': 'test-server-id',
        'original_server_id': '12345'
    }
    
    # Override with actual values if available
    if 'SFTP_HOSTNAME' in environ:
        config['hostname'] = environ['SFTP_HOSTNAME']
    if 'SFTP_PORT' in environ:
        config['port'] = int(environ['SFTP_PORT'])
    if 'SFTP_USERNAME' in environ:
        config['username'] = environ['SFTP_USERNAME']
    if 'SFTP_PASSWORD' in environ:
        config['password'] = environ['SFTP_PASSWORD']
    if 'SERVER_ID' in environ:
        config['server_id'] = environ['SERVER_ID']
    if 'ORIGINAL_SERVER_ID' in environ:
        config['original_server_id'] = environ['ORIGINAL_SERVER_ID']
    
    # Log config (excluding password)
    safe_config = {k: v for k, v in config.items() if k != 'password'}
    logger.info(f"Using config: {safe_config}")
    
    # Create SFTP connection
    sftp = SFTPManager(
        hostname=config['hostname'],
        port=config['port'],
        username=config['username'],
        password=config['password'],
        server_id=config['server_id'],
        original_server_id=config['original_server_id']
    )
    
    try:
        # Connect to the SFTP server
        connected = await sftp.connect()
        if not connected:
            logger.error("Failed to connect to SFTP server")
            return
        
        logger.info("Connected to SFTP server")
        
        # Test world map discovery
        world_maps_found = await test_world_map_discovery(sftp, config['server_id'])
        logger.info(f"World map discovery {'PASSED' if world_maps_found else 'FAILED'}")
        
        # Test full discovery process
        file_discovery = FileDiscovery()
        start_date = datetime.now() - timedelta(days=30)
        
        files, metadata = await file_discovery.discover_csv_files(
            sftp=sftp,
            server_id=config['server_id'],
            start_date=start_date,
            days_back=30,
            historical_mode=True
        )
        
        logger.info(f"Full discovery found {len(files)} files")
        logger.info(f"Discovery metadata: {metadata}")
        
        # Verify file attributes
        if files:
            await verify_file_attributes(sftp, files)
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Disconnect from the SFTP server
        await sftp.disconnect()
        logger.info("Disconnected from SFTP server")

if __name__ == "__main__":
    asyncio.run(main())