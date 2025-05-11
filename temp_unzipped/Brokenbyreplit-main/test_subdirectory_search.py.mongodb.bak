"""
Test script to test the subdirectory recursive searching functionality
of the historical parser.
"""
import asyncio
import logging
import os
import glob
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test():
    """Run the test"""
    from utils.database import initialize_db
    
    # Initialize database
    db_manager = await initialize_db()
    db = db_manager.db
    
    # Test with numeric server ID first
    await test_with_id(db, "7020", "numeric")
    
    # Test with UUID format
    await test_with_id(db, "5251382d-8bce-4abd-8bcb-cdef73698a46", "uuid")
    
async def test_with_id(db, server_id, id_type):
    """Test historical parsing with the given server ID"""
    # First, scan all possible locations to find CSV files
    base_dirs = [
        os.path.join(os.getcwd(), "attached_assets"),  # Local assets
        os.path.join(os.getcwd(), "zipbot_temp"),      # Temp directory
        os.path.join("/", f"79.127.236.1_{server_id}"),  # Standard server directory
        os.path.join("/", f"79.127.236.1_{server_id}", "actual1", "deathlogs"),  # Common path
        os.path.join("/", f"79.127.236.1_{server_id}", "deathlogs"),  # Direct deathlogs
    ]
    
    days = 30
    start_date = datetime.now() - timedelta(days=days)
    
    logger.info(f"Testing subdirectory search with {id_type} ID: {server_id}")
    logger.info(f"Looking back {days} days from {start_date.strftime('%Y-%m-%d')}")
    
    total_files = 0
    csv_files = []
    
    # Check all base directories
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            logger.info(f"Directory {base_dir} does not exist, skipping")
            continue
            
        logger.info(f"Scanning directory: {base_dir}")
        
        # First, search directly in this directory
        dir_files = glob.glob(os.path.join(base_dir, "*.csv"))
        if dir_files:
            logger.info(f"Found {len(dir_files)} CSV files directly in {base_dir}")
            csv_files.extend(dir_files)
            
        # Now, do a recursive walk
        for root, dirs, files in os.walk(base_dir):
            csv_count = sum(1 for f in files if f.endswith('.csv'))
            if csv_count > 0:
                logger.info(f"Found {csv_count} CSV files in subdirectory {root}")
                for f in files:
                    if f.endswith('.csv'):
                        full_path = os.path.join(root, f)
                        csv_files.append(full_path)
                        
    # Remove duplicates
    csv_files = list(set(csv_files))
    total_files = len(csv_files)
    
    logger.info(f"Total unique CSV files found: {total_files}")
    if total_files > 0:
        logger.info(f"Sample files: {csv_files[:5]}")
    
    # Now try to parse a sample file to verify the parsing logic
    if csv_files:
        from utils.direct_csv_handler import direct_parse_csv_file
        sample_file = csv_files[0]
        logger.info(f"Parsing sample file: {sample_file}")
        
        try:
            events, line_count = direct_parse_csv_file(sample_file, server_id)
            logger.info(f"Successfully parsed {len(events)} events from {line_count} lines")
            
            if events:
                logger.info(f"Sample event: {events[0]}")
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
    
    logger.info(f"Complete subdirectory search test for {id_type} ID: {server_id}")
    logger.info("-" * 50)
    
if __name__ == "__main__":
    asyncio.run(run_test())