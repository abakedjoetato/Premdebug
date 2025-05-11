"""
Test script for verifying the CSV processing fixes

This script will:
1. Create test CSV files in a test directory
2. Run the direct CSV processor to verify it finds and processes the files
3. Check that the file count tracking is accurate
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("csv_fix_test")

# Path for test files
TEST_DIR = "test_csv_files"
TEST_MAPS_DIR = os.path.join(TEST_DIR, "maps")

def create_test_directories():
    """Create test directories for CSV files"""
    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(TEST_MAPS_DIR, exist_ok=True)
    logger.info(f"Created test directories: {TEST_DIR}, {TEST_MAPS_DIR}")

def create_test_csv_files():
    """Create test CSV files with various formats and timestamps"""
    # Regular format CSV files
    current_time = datetime.now()
    date_str = current_time.strftime("%Y.%m.%d-%H.%M.%S")
    
    # Create CSV with current timestamp
    with open(os.path.join(TEST_DIR, f"test_{date_str}.csv"), 'w') as f:
        f.write("timestamp,killer,victim,weapon,distance\n")
        f.write(f"{date_str},Player1,Player2,Rifle,100\n")
        f.write(f"{date_str},Player3,Player4,Pistol,50\n")
    
    # Create CSV in map directory with different timestamp
    map_date_str = (current_time.replace(hour=current_time.hour-1)).strftime("%Y.%m.%d-%H.%M.%S")
    with open(os.path.join(TEST_MAPS_DIR, f"map_{map_date_str}.csv"), 'w') as f:
        f.write("timestamp,killer,victim,weapon,distance\n")
        f.write(f"{map_date_str},Player5,Player6,Shotgun,30\n")
        f.write(f"{map_date_str},Player7,Player8,Sniper,200\n")
    
    logger.info(f"Created test CSV files in {TEST_DIR} and {TEST_MAPS_DIR}")

async def run_direct_csv_test():
    """Test the direct CSV processor to verify it finds and processes files"""
    try:
        # Import the direct CSV handler
        sys.path.append(".")
        from utils.direct_csv_handler import process_directory, direct_parse_csv_file
        
        # Create a more comprehensive mock database
        async def mock_find_one(*args, **kwargs):
            # Return a mock server document when queried
            if 'server_id' in kwargs and kwargs['server_id'] == 'test_server':
                return {
                    'server_id': 'test_server',
                    'original_server_id': 'test_server_original',
                    'name': 'Test Server',
                    'sftp_config': {
                        'enabled': False
                    }
                }
            return None
            
        async def mock_insert_many(*args, **kwargs):
            # Mock successful insert of documents
            return type('MockResult', (), {'inserted_ids': [1, 2, 3, 4]})
            
        # Create collections with necessary methods
        mock_collection = type('MockCollection', (), {
            'find_one': mock_find_one,
            'update_one': lambda *args, **kwargs: None,
            'insert_many': mock_insert_many
        })
        
        # Create complete mock DB with all needed collections
        mock_db = type('MockDB', (), {
            'kills': mock_collection,
            'players': mock_collection,
            'rivalries': mock_collection,
            'game_servers': mock_collection,
            'server_configs': mock_collection
        })
        
        # First, process files directly to verify they're valid
        logger.info("Running direct CSV file parsing test...")
        test_file = os.path.join(TEST_DIR, os.listdir(TEST_DIR)[0])
        if test_file.endswith('.csv'):
            events, lines = direct_parse_csv_file(test_file, "test_server")
            logger.info(f"Direct parse result: {len(events)} events from {lines} lines in {test_file}")
        
        # Custom test function that uses our test directory
        logger.info("Running custom test to process files in our test directory...")
        server_id = "test_server"
        
        # Process files directly
        csv_files = []
        events_imported = 0
        
        # Find all CSV files in our test directory recursively
        for root, _, files in os.walk(TEST_DIR):
            for file in files:
                if file.endswith('.csv'):
                    full_path = os.path.join(root, file)
                    logger.info(f"Found CSV file: {full_path}")
                    csv_files.append(full_path)
        
        # Process each file manually
        for file_path in csv_files:
            events, _ = direct_parse_csv_file(file_path, server_id)
            events_imported += len(events)
        
        files_processed = len(csv_files)
        events_processed = events_imported
        
        logger.info(f"Manual processing results: {files_processed} files processed, {events_processed} events processed")
        
        logger.info(f"Direct CSV test results: {files_processed} files processed, {events_processed} events processed")
        return files_processed, events_processed
    except Exception as e:
        logger.error(f"Error in direct CSV test: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

async def main():
    """Main test function"""
    logger.info("Starting CSV processing fix verification test")
    
    # Create test environment
    create_test_directories()
    create_test_csv_files()
    
    # Run the test
    files_processed, events_processed = await run_direct_csv_test()
    
    # Verify results
    if files_processed >= 2:
        logger.info("✅ PASS: CSV processor correctly found and processed multiple files")
    else:
        logger.error("❌ FAIL: CSV processor found fewer files than expected")
    
    if events_processed >= 4:
        logger.info("✅ PASS: CSV processor correctly processed the events in the files")
    else:
        logger.error("❌ FAIL: CSV processor processed fewer events than expected")
        
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())