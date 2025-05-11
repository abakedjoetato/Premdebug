#!/usr/bin/env python
"""
Test script to verify CSV processing system fixes
"""
import os
import sys
import logging
import asyncio
import datetime
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Attempt to import required modules
try:
    from utils.direct_csv_handler import process_directory
except ImportError:
    logger.error("Could not import process_directory from utils.direct_csv_handler")
    sys.exit(1)

async def test_csv_processing():
    """Test the CSV processing with the attached test files"""
    logger.info("Testing CSV processing with known test files")
    
    # Create a test server ID
    server_id = "test_server_123"
    
    # Use a mock DB for testing
    mock_db = MockDB()
    
    # Process the attached assets directory
    logger.info("Processing files in attached_assets directory")
    files_processed, events_imported = await process_directory(mock_db, server_id, days=365)
    
    logger.info(f"Processed {files_processed} files, imported {events_imported} events")
    
    if files_processed > 0 and events_imported > 0:
        logger.info("CSV processing test PASSED!")
        return True
    else:
        logger.error("CSV processing test FAILED!")
        return False

class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.events = []
        
    async def game_servers(self):
        return self
        
    async def find_one(self, query):
        return {"server_id": "test_server_123", "original_server_id": "123"}
        
    async def insert_one(self, doc):
        self.events.append(doc)
        return True
        
    async def insert_many(self, docs):
        self.events.extend(docs)
        return len(docs)

async def main():
    """Main test function"""
    try:
        logger.info("Starting CSV processing test")
        
        # Ensure we have test CSV files
        assets_dir = "attached_assets"
        if not os.path.exists(assets_dir):
            logger.error(f"Directory {assets_dir} does not exist")
            return False
            
        csv_files = [f for f in os.listdir(assets_dir) if f.endswith('.csv')]
        if not csv_files:
            logger.error(f"No CSV files found in {assets_dir}")
            return False
            
        logger.info(f"Found {len(csv_files)} CSV files in {assets_dir}")
        
        # Run the test
        result = await test_csv_processing()
        
        if result:
            logger.info("All tests PASSED")
            return True
        else:
            logger.error("Tests FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    # Run the main function
    success = asyncio.run(main())
    sys.exit(0 if success else 1)