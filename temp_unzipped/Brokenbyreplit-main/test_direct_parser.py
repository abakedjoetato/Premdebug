#!/usr/bin/env python
"""
Lightweight test for the direct CSV parser without MongoDB dependencies
"""
import os
import sys
import logging
import glob
from typing import Dict, Any, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the parser function directly
try:
    from utils.direct_csv_handler import direct_parse_csv_file
except ImportError:
    logger.error("Could not import direct_parse_csv_file")
    sys.exit(1)

def find_csv_files(directory="attached_assets", days=365):
    """Find CSV files in the given directory"""
    if not os.path.exists(directory):
        logger.error(f"Directory {directory} does not exist")
        return []
        
    # Find all files with .csv extension
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files in {directory}")
    
    # Display the files
    for csv_file in csv_files:
        file_size = os.path.getsize(csv_file)
        logger.info(f"CSV file: {os.path.basename(csv_file)}, size: {file_size} bytes")
        
    return csv_files

def test_csv_parsing(csv_files: List[str], server_id="test_server_123"):
    """Test parsing each CSV file"""
    total_events = 0
    processed_files = 0
    
    for file_path in csv_files:
        try:
            logger.info(f"Testing parser with file: {os.path.basename(file_path)}")
            
            # Parse the file
            events, line_count = direct_parse_csv_file(file_path, server_id)
            
            # Print results
            event_count = len(events)
            logger.info(f"Parsed {event_count} events from {line_count} lines in {os.path.basename(file_path)}")
            
            if event_count > 0:
                # Show sample of first event
                logger.info(f"Sample event: {events[0]}")
                processed_files += 1
                total_events += event_count
                
        except Exception as e:
            logger.error(f"Error parsing {os.path.basename(file_path)}: {e}")
            
    return processed_files, total_events

def main():
    """Main test function"""
    try:
        logger.info("Starting direct CSV parser test")
        
        # Find CSV files
        csv_files = find_csv_files()
        if not csv_files:
            logger.error("No CSV files found to test")
            return False
            
        # Test parsing
        processed_files, total_events = test_csv_parsing(csv_files)
        
        # Report results
        logger.info(f"Test complete: Processed {processed_files}/{len(csv_files)} files, parsed {total_events} events")
        
        if processed_files > 0 and total_events > 0:
            logger.info("Direct CSV parser test PASSED!")
            return True
        else:
            logger.error("Direct CSV parser test FAILED! No events were parsed.")
            return False
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    # Run the main function
    success = main()
    sys.exit(0 if success else 1)