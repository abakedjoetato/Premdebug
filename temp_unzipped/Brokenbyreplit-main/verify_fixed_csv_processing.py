"""
Verify Fixed CSV Processing

This script verifies that the fixed CSV processing system correctly locates, reads,
and processes CSV files from map directories.

Usage:
    python verify_fixed_csv_processing.py

This will:
1. Test the directory_exists method with proper error handling
2. Test path construction for world map directories
3. Test file listing within map directories
4. Test reading CSV files from map directories
5. Test CSV parsing with the exact 8-field format
"""
import os
import re
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
        logging.FileHandler('csv_fixes.log')
    ]
)
logger = logging.getLogger(__name__)

# Import necessary modules
try:
    # First ensure utils directory is in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import required modules
    from utils.sftp import SFTPManager
    from utils.file_discovery import FileDiscovery
    from utils.stable_csv_parser import StableCSVParser
    
    logger.info("Successfully imported required modules")
except Exception as e:
    logger.error(f"Failed to import modules: {e}")
    traceback.print_exc()
    sys.exit(1)

async def test_directory_exists(sftp, directory):
    """Test directory_exists method with proper error handling"""
    logger.info(f"Testing directory_exists for {directory}")
    try:
        exists = await sftp.directory_exists(directory)
        logger.info(f"Directory {directory} exists: {exists}")
        return exists
    except Exception as e:
        logger.error(f"Error checking if directory exists: {e}")
        traceback.print_exc()
        return False

async def test_path_construction(sftp, server_id, map_dirs=None):
    """Test path construction for world map directories"""
    if map_dirs is None:
        map_dirs = ["world_0", "world_1", "world_2"]
    
    logger.info(f"Testing path construction for server {server_id}")
    file_discovery = FileDiscovery()
    
    # Get base paths
    base_paths = await file_discovery._find_base_paths(sftp, server_id, True)
    logger.info(f"Found base paths: {base_paths}")
    
    # Test path construction
    for base_path in base_paths:
        for map_dir in map_dirs:
            # Construct path using os.path.join
            path = os.path.join(base_path, map_dir)
            logger.info(f"Constructed path: {path}")
            
            # Test if path exists
            exists = await test_directory_exists(sftp, path)
            if exists:
                logger.info(f"✅ Path exists: {path}")
            else:
                logger.info(f"❌ Path does not exist: {path}")

async def test_list_files(sftp, directory, pattern=None):
    """Test file listing within directories"""
    logger.info(f"Testing file listing for {directory}")
    try:
        files = await sftp.list_files(directory, pattern)
        logger.info(f"Found {len(files)} files in {directory}")
        
        # Log the first few files
        if files:
            logger.info(f"First few files: {files[:min(3, len(files))]}")
            
        return files
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        traceback.print_exc()
        return []

async def test_read_csv_file(sftp, file_path):
    """Test reading CSV files"""
    logger.info(f"Testing reading CSV file: {file_path}")
    try:
        content = await sftp.read_file(file_path)
        if content is None:
            logger.error(f"Failed to read file {file_path}")
            return None
        
        # Log content type and sample
        content_type = type(content)
        logger.info(f"Content type: {content_type}")
        
        # Convert bytes to string if needed
        if isinstance(content, bytes):
            try:
                # Try multiple encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        content_str = content.decode(encoding)
                        logger.info(f"Successfully decoded with {encoding}")
                        
                        # Log sample
                        sample = content_str[:min(200, len(content_str))]
                        logger.info(f"Content sample: {sample}")
                        
                        return content_str
                    except UnicodeDecodeError:
                        continue
                
                # If all fail, use replace
                content_str = content.decode('utf-8', errors='replace')
                logger.warning(f"Used fallback decoding with replacement")
                
                # Log sample
                sample = content_str[:min(200, len(content_str))]
                logger.info(f"Content sample: {sample}")
                
                return content_str
            except Exception as e:
                logger.error(f"Error decoding content: {e}")
                traceback.print_exc()
                return None
        elif isinstance(content, list):
            # Content is already a list of strings or bytes
            logger.info(f"Content is a list of {len(content)} items")
            
            # Log sample of first item
            if content:
                first_item = content[0]
                if isinstance(first_item, bytes):
                    try:
                        first_item = first_item.decode('utf-8')
                    except:
                        try:
                            first_item = first_item.decode('latin-1')
                        except:
                            first_item = str(first_item)
                
                logger.info(f"First item: {first_item}")
            
            # Join items into a single string
            content_str = "\n".join(str(item) for item in content)
            
            return content_str
        else:
            # Content is already a string
            logger.info(f"Content is a string")
            
            # Log sample
            sample = str(content)[:min(200, len(str(content)))]
            logger.info(f"Content sample: {sample}")
            
            return str(content)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        traceback.print_exc()
        return None

async def test_csv_parsing(content, file_path, server_id):
    """Test CSV parsing with the exact 8-field format"""
    logger.info(f"Testing CSV parsing for {file_path}")
    try:
        parser = StableCSVParser()
        events, total_lines = parser.parse_file_content(
            content=content,
            file_path=file_path,
            server_id=server_id,
            start_line=0
        )
        
        logger.info(f"Parsed {len(events)} events from {total_lines} lines")
        
        # Log the first event
        if events is not None:
            logger.info(f"First event: {events[0]}")
            
            # Validate all events have required fields
            required_fields = ['timestamp', 'killer_name', 'killer_id', 'victim_name', 'victim_id', 'weapon', 'distance']
            valid_count = 0
            for event in events:
                if all(field in event for field in required_fields):
                    valid_count += 1
            
            logger.info(f"Found {valid_count}/{len(events)} valid events with all required fields")
            
        return events
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        traceback.print_exc()
        return []

async def main():
    """Main test function"""
    logger.info("Starting fixed CSV processing verification")
    
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
        
        # Test path construction
        await test_path_construction(sftp, server_id)
        
        # Test file discovery
        file_discovery = FileDiscovery()
        
        # Use our discover_csv_files method with historical mode for thorough search
        start_date = datetime.now()
        csv_files, discovery_stats = await file_discovery.discover_csv_files(
            sftp=sftp,
            server_id=server_id,
            start_date=start_date,
            days_back=30,
            historical_mode=True
        )
        
        # Log discovery results
        logger.info(f"Found {len(csv_files)} CSV files")
        logger.info(f"Discovery stats: {discovery_stats}")
        
        # Test the first few files
        for i, file_path in enumerate(csv_files[:min(3, len(csv_files))]):
            logger.info(f"Testing file {i+1}: {file_path}")
            
            # Read file
            content = await test_read_csv_file(sftp, file_path)
            if content:
                # Parse CSV
                events = await test_csv_parsing(content, file_path, server_id)
                if events is not None:
                    logger.info(f"✅ Successfully parsed events from {file_path}")
                else:
                    logger.warning(f"❌ Failed to parse events from {file_path}")
            else:
                logger.error(f"❌ Failed to read file {file_path}")
        
        # Overall test status
        if csv_files:
            logger.info("✅ CSV file discovery and processing verification: PASSED")
        else:
            logger.error("❌ CSV file discovery and processing verification: FAILED - No CSV files found")
    
    except Exception as e:
        logger.error(f"Error running test: {e}")
        traceback.print_exc()
    finally:
        # Disconnect from the server
        await sftp.disconnect()
        logger.info("Disconnected from SFTP server")

if __name__ == "__main__":
    asyncio.run(main())