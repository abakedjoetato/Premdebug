"""
Direct test script for historical parsing functionality.
This will directly call the historical parse function in the CSVProcessor cog.
"""
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Main test function
async def run_test():
    """Run the historical parse test"""
    logger.info("Starting historical parse test")
    
    # Access the database directly
    from utils.database import initialize_db
    from utils.direct_csv_handler import process_directory
    
    # Initialize database connection
    db_manager = await initialize_db()
    if db_manager is None:
        logger.error("Failed to connect to database")
        return
        
    # Get database reference
    db = db_manager.db
    
    logger.info("Connected to database")
    
    # Use original server ID for testing
    server_id = "7020"
    days = 30
    
    logger.info(f"Starting historical parse for server {server_id} with {days} days lookback")
    start_time = datetime.now()
    
    # Process directory and get results
    files_processed, events_imported = await process_directory(db, server_id, days)
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    logger.info(f"Historical parse completed in {elapsed:.2f} seconds")
    logger.info(f"Files processed: {files_processed}")
    logger.info(f"Events imported: {events_imported}")
    
    # Return results for potential assertion in tests
    return files_processed, events_imported

# Run the test
if __name__ == "__main__":
    asyncio.run(run_test())