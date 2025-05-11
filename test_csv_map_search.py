#!/usr/bin/env python3
"""
Simple test for CSV map directory search focus

This tests that we're correctly focusing on the world_* directories
"""
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pattern_matching():
    """Test the regex pattern for map directory matching"""
    # This is the pattern we're using in file_discovery.py
    pattern = r'world[-_]?[0-2]'
    
    # Test cases that should match (world_0, world_1, world_2)
    should_match = [
        'world_0', 'world_1', 'world_2',
        'world0', 'world1', 'world2',
        'WORLD_0', 'WORLD_1', 'WORLD_2',
        'World_0', 'World_1', 'World_2'
    ]
    
    # Test cases that should NOT match
    should_not_match = [
        'world_3', 'world_4', 'world_5',
        'world3', 'world4', 'world5',
        'level_0', 'level_1', 'level_2',
        'map_0', 'map_1', 'map_2',
        'other_dir', 'config', 'backups'
    ]
    
    # Test matching cases
    logger.info("Testing directories that SHOULD match:")
    for directory in should_match:
        if re.search(pattern, directory, re.IGNORECASE):
            logger.info(f"  ✓ {directory} - MATCHED (correct)")
        else:
            logger.error(f"  ✗ {directory} - NOT MATCHED (incorrect)")
    
    # Test non-matching cases
    logger.info("\nTesting directories that should NOT match:")
    for directory in should_not_match:
        if not re.search(pattern, directory, re.IGNORECASE):
            logger.info(f"  ✓ {directory} - NOT MATCHED (correct)")
        else:
            logger.error(f"  ✗ {directory} - MATCHED (incorrect)")

def main():
    """Main function"""
    logger.info("Testing map directory pattern matching")
    test_pattern_matching()
    logger.info("Test complete")

if __name__ == "__main__":
    main()