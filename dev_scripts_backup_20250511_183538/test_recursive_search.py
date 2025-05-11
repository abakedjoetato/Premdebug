"""
Test script for the enhanced recursive subdirectory search functionality.
This test uses the improved direct_csv_handler.py implementation.
"""
import asyncio
import logging
import os
import glob
import json
import traceback
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("recursive_test")

async def run_test():
    """Run the test for recursive subdirectory CSV file searching"""
    try:
        from utils.database import initialize_db
        from utils.direct_csv_handler import process_directory
        from utils.server_identity import resolve_server_id
        
        # Initialize the database
        db_manager = await initialize_db()
        db = db_manager.db
        logger.info("Connected to database")
        
        # Test IDs to use
        server_ids = [
            "7020",  # Known numeric ID
            "5251382d-8bce-4abd-8bcb-cdef73698a46",  # UUID form
        ]
        
        results = {}
        
        # Test with each server ID
        for server_id in server_ids:
            logger.info(f"\n\n=== TESTING WITH SERVER ID: {server_id} ===\n")
            
            # Resolve the server ID to make sure we're using the right one
            resolution = await resolve_server_id(db, server_id)
            
            if resolution:
                logger.info(f"Server ID resolution: {json.dumps(resolution, default=str)}")
                resolved_id = resolution.get("server_id", server_id)
            else:
                logger.info(f"No resolution found for {server_id}, using as-is")
                resolved_id = server_id
            
            # Looking back 30 days
            days = 30
            logger.info(f"Testing recursive search with {days} days lookback")
            
            # Process all directories and get results
            start_time = datetime.now()
            files_processed, events_imported = await process_directory(db, resolved_id, days)
            end_time = datetime.now()
            
            # Calculate processing time
            elapsed = (end_time - start_time).total_seconds()
            
            # Save results
            results[server_id] = {
                "resolved_id": resolved_id,
                "files_processed": files_processed,
                "events_imported": events_imported,
                "processing_time": f"{elapsed:.2f} seconds"
            }
            
            logger.info(f"Results for {server_id}: Processed {files_processed} files with {events_imported} events in {elapsed:.2f} seconds")
        
        # Display final summary
        logger.info("\n=== FINAL RESULTS ===")
        for server_id, result in results.items():
            logger.info(f"Server ID {server_id} → Resolved ID {result['resolved_id']}")
            logger.info(f"  Files processed: {result['files_processed']}")
            logger.info(f"  Events imported: {result['events_imported']}")
            logger.info(f"  Processing time: {result['processing_time']}")
            
    except Exception as e:
        logger.error(f"Error running test: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(run_test())))