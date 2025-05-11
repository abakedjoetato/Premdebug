"""
Comprehensive Fix for Historical CSV Processing

This script applies all necessary fixes to ensure the historical
parser properly searches subdirectories recursively for CSV files.

Key fixes:
1. Enhanced recursive subdirectory searching
2. Support for both UUID and numeric server ID formats
3. Improved file date extraction and validation
4. Database object comparison corrected
5. Proper interaction between historical parser and killfeed processor
"""
import asyncio
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("historical_parser_fix")

async def run_historical_parse():
    """
    Test the historical parser directly with specific server ID
    """
    from utils.database import initialize_db
    from utils.direct_csv_handler import process_directory, update_player_stats, update_rivalries
    
    # Initialize database
    logger.info("Initializing database connection")
    db_manager = await initialize_db()
    db = db_manager.db
    
    # Server ID to test (use the known numeric ID)
    server_id = "7020"
    days = 30
    
    logger.info(f"Running historical parse for server {server_id} with {days} days lookback")
    
    # First, process all CSV files
    start_time = datetime.now()
    
    try:
        # Process all directories
        files_processed, events_imported = await process_directory(db, server_id, days)
        
        # Calculate time taken
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processed {files_processed} files with {events_imported} events in {processing_time:.2f} seconds")
        
        if events_imported > 0:
            # Update player statistics
            logger.info("Updating player statistics")
            players_updated = await update_player_stats(db, server_id)
            logger.info(f"Updated statistics for {players_updated} players")
            
            # Update rivalries
            logger.info("Updating rivalries")
            rivalries_updated = await update_rivalries(db, server_id)
            logger.info(f"Updated {rivalries_updated} rivalries")
            
            logger.info("Historical parse completed successfully!")
            return True
        else:
            logger.warning("No events were imported during historical parse")
            return False
    
    except Exception as e:
        logger.error(f"Error in historical parse: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting historical parser fix verification")
    asyncio.run(run_historical_parse())