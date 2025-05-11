"""
# module: verify_csv_processing
Verification Script for CSV Processing

This script provides a direct test of the CSV processing pipeline to verify
that our fixes have successfully solved the issues with directory checking
and file discovery.
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
        logging.FileHandler('verify_csv.log')
    ]
)
logger = logging.getLogger('verify_csv')

# Import the components we need to test
from utils.sftp import SFTPManager
from utils.file_discovery import FileDiscovery

# Test server configuration - edit with real server details
TEST_SERVER = {
    "server_id": "2143443",
    "hostname": "208.103.169.139",
    "port": 22,
    "username": "totemptation",
    "password": "YzhkZnPqe6",
    "original_server_id": "1"
}

async def test_directory_exists():
    """Test the directory_exists method"""
    logger.info("Testing directory_exists method")
    
    # Create SFTP manager
    sftp = SFTPManager(
        hostname=TEST_SERVER["hostname"],
        port=TEST_SERVER["port"],
        username=TEST_SERVER["username"],
        password=TEST_SERVER["password"],
        server_id=TEST_SERVER["server_id"],
        original_server_id=TEST_SERVER["original_server_id"]
    )
    
    # Connect to server
    try:
        await sftp.connect()
        logger.info("Connected to SFTP server successfully")
        
        # Test directories to check
        test_dirs = [
            "/",
            "/logs",
            "/Logs",
            "/data",
            "/game",
            "/logs/killfeed",
            "/killfeed",
            "/nonexistent_directory"
        ]
        
        # Check each directory
        for directory in test_dirs:
            exists = await sftp.directory_exists(directory)
            logger.info(f"Directory {directory} exists: {exists}")
            
        logger.info("directory_exists test completed")
        return True
    except Exception as e:
        logger.error(f"Error testing directory_exists: {e}")
        return False
    finally:
        # Close connection
        await sftp.close()

async def test_file_discovery():
    """Test the file discovery process"""
    logger.info("Testing file discovery")
    
    # Create SFTP manager
    sftp = SFTPManager(
        hostname=TEST_SERVER["hostname"],
        port=TEST_SERVER["port"],
        username=TEST_SERVER["username"],
        password=TEST_SERVER["password"],
        server_id=TEST_SERVER["server_id"],
        original_server_id=TEST_SERVER["original_server_id"]
    )
    
    # Create file discovery
    discovery = FileDiscovery()
    
    try:
        # Connect to server
        await sftp.connect()
        logger.info("Connected to SFTP server successfully")
        
        # Set up discovery parameters
        days_back = 30  # Historical mode - look back 30 days
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Run discovery
        logger.info("Running file discovery...")
        files, stats = await discovery.discover_csv_files(
            sftp=sftp,
            server_id=TEST_SERVER["server_id"],
            start_date=start_date,
            days_back=days_back,
            historical_mode=True
        )
        
        # Log results
        logger.info(f"Discovery stats: {stats}")
        logger.info(f"Found {len(files)} CSV files")
        
        if files:
            logger.info("Sample CSV files found:")
            for file in files[:5]:  # Show first 5 files
                logger.info(f"  - {file}")
            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more")
        else:
            logger.warning("No CSV files found during discovery")
            
        # Check if map files were found
        map_files = discovery.map_directory_files.get(TEST_SERVER["server_id"], set())
        logger.info(f"Map directory files found: {len(map_files)}")
        
        if map_files:
            logger.info("Sample map directory CSV files:")
            for file in list(map_files)[:5]:  # Show first 5 files
                logger.info(f"  - {file}")
            if len(map_files) > 5:
                logger.info(f"  ... and {len(map_files) - 5} more")
                
        return len(files) > 0
    except Exception as e:
        logger.error(f"Error testing file discovery: {e}")
        return False
    finally:
        # Close connection
        await sftp.close()

async def test_csv_download():
    """Test downloading discovered CSV files"""
    logger.info("Testing CSV file download")
    
    # Create SFTP manager
    sftp = SFTPManager(
        hostname=TEST_SERVER["hostname"],
        port=TEST_SERVER["port"],
        username=TEST_SERVER["username"],
        password=TEST_SERVER["password"],
        server_id=TEST_SERVER["server_id"],
        original_server_id=TEST_SERVER["original_server_id"]
    )
    
    # Create file discovery
    discovery = FileDiscovery()
    
    try:
        # Connect to server
        await sftp.connect()
        logger.info("Connected to SFTP server successfully")
        
        # Discover files first
        days_back = 30
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Run discovery
        logger.info("Running file discovery for download test...")
        files, _ = await discovery.discover_csv_files(
            sftp=sftp,
            server_id=TEST_SERVER["server_id"],
            start_date=start_date,
            days_back=days_back,
            historical_mode=True
        )
        
        if not files:
            logger.warning("No files found to download")
            return False
            
        # Test downloading a sample file
        sample_file = files[0]
        logger.info(f"Attempting to download: {sample_file}")
        
        # Create a local directory for downloaded files
        os.makedirs("downloaded_csv", exist_ok=True)
        local_path = os.path.join("downloaded_csv", os.path.basename(sample_file))
        
        # Download the file
        success = await sftp.download_file(sample_file, local_path)
        
        if success:
            logger.info(f"Successfully downloaded {sample_file} to {local_path}")
            
            # Check the file content
            with open(local_path, 'r') as f:
                content = f.read(500)  # Read first 500 chars
                logger.info(f"File content preview: {content}")
                
            return True
        else:
            logger.error(f"Failed to download {sample_file}")
            return False
    except Exception as e:
        logger.error(f"Error testing CSV download: {e}")
        return False
    finally:
        # Close connection
        await sftp.close()

async def run_tests():
    """Run all tests"""
    logger.info("="*60)
    logger.info("STARTING CSV PROCESSING VERIFICATION")
    logger.info("="*60)
    
    # Test 1: Directory exists
    logger.info("\n## TEST 1: DIRECTORY_EXISTS METHOD")
    directory_exists_success = await test_directory_exists()
    
    # Test 2: File discovery
    logger.info("\n## TEST 2: FILE DISCOVERY")
    file_discovery_success = await test_file_discovery()
    
    # Test 3: CSV download
    logger.info("\n## TEST 3: CSV DOWNLOAD")
    download_success = await test_csv_download()
    
    # Log overall results
    logger.info("\n## TEST RESULTS")
    logger.info(f"Directory exists test: {'PASSED' if directory_exists_success else 'FAILED'}")
    logger.info(f"File discovery test: {'PASSED' if file_discovery_success else 'FAILED'}")
    logger.info(f"CSV download test: {'PASSED' if download_success else 'FAILED'}")
    
    # Overall status
    if directory_exists_success and file_discovery_success and download_success:
        logger.info("\n## OVERALL RESULT: ALL TESTS PASSED")
        logger.info("CSV processing system is working correctly!")
        return True
    else:
        logger.info("\n## OVERALL RESULT: SOME TESTS FAILED")
        logger.info("CSV processing system still has issues to fix")
        return False

if __name__ == "__main__":
    asyncio.run(run_tests())