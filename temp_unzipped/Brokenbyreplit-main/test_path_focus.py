#!/usr/bin/env python3
"""
Test Path Focus

This script tests that we're correctly focusing on the exact path structure:
/{hostname}_{server_id}/actual1/deathlogs

And specifically the map directories:
/{hostname}_{server_id}/actual1/deathlogs/world_0
/{hostname}_{server_id}/actual1/deathlogs/world_1
/{hostname}_{server_id}/actual1/deathlogs/world_2
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules to test
from utils.file_discovery import FileDiscovery

class MockSFTP:
    """Mock SFTP client for testing"""
    def __init__(self, hostname="server", server_id="12345", original_server_id="12345"):
        self.hostname = hostname
        self.server_id = server_id
        self.original_server_id = original_server_id
        
    async def directory_exists(self, path):
        """Mock directory_exists method"""
        logger.info(f"Checking if directory exists: {path}")
        
        # Create an exact path match
        server_dir = f"{self.hostname}_{self.original_server_id}"
        
        # These specific paths should exist
        expected_paths = [
            f"/{server_dir}/actual1/deathlogs",  # Base path
            f"/{server_dir}/actual1/deathlogs/world_0",  # Map 0
            f"/{server_dir}/actual1/deathlogs/world_1",  # Map 1
            f"/{server_dir}/actual1/deathlogs/world_2",  # Map 2
        ]
        
        # If it's a path we expect, return True
        if path in expected_paths:
            logger.info(f"  ✓ Directory exists: {path}")
            return True
            
        # Log other path checks for debugging
        logger.info(f"  ✗ Directory does not exist: {path}")
        return False
        
    async def list_directory(self, path):
        """Mock list_directory method"""
        logger.info(f"Listing directory: {path}")
        
        # Create the server directory string
        server_dir = f"{self.hostname}_{self.original_server_id}"
        
        # Return values based on path
        if path == f"/{server_dir}/actual1/deathlogs":
            # Return the map directories
            return ["world_0", "world_1", "world_2", "other_dir"]
            
        if path == f"/{server_dir}/actual1/deathlogs/world_0":
            # Return some CSV files for world_0
            return ["killfeed_20250510_1.csv", "killfeed_20250510_2.csv"]
            
        if path == f"/{server_dir}/actual1/deathlogs/world_1":
            # Return some CSV files for world_1
            return ["killfeed_20250510_1.csv"]
            
        if path == f"/{server_dir}/actual1/deathlogs/world_2":
            # Return some CSV files for world_2
            return ["killfeed_20250510_1.csv"]
            
        # Default empty list for other paths
        return []
        
    async def list_files(self, path, pattern=None):
        """Mock list_files method"""
        logger.info(f"Listing files in {path} with pattern: {pattern}")
        
        # Create the server directory string
        server_dir = f"{self.hostname}_{self.original_server_id}"
        
        # Return values based on path
        if path == f"/{server_dir}/actual1/deathlogs/world_0":
            # Return some CSV files for world_0
            return ["killfeed_20250510_1.csv", "killfeed_20250510_2.csv"]
            
        if path == f"/{server_dir}/actual1/deathlogs/world_1":
            # Return some CSV files for world_1
            return ["killfeed_20250510_1.csv"]
            
        if path == f"/{server_dir}/actual1/deathlogs/world_2":
            # Return some CSV files for world_2
            return ["killfeed_20250510_1.csv"]
            
        # Default empty list for other paths
        return []

async def test_single_base_path():
    """Test that we're focusing on a single base path"""
    logger.info("Testing single base path focus")
    
    # Create mock SFTP client
    sftp = MockSFTP(hostname="server", server_id="12345", original_server_id="12345")
    
    # Create file discovery instance
    discovery = FileDiscovery()
    
    # Get base paths in non-historical mode
    base_paths = await discovery._find_base_paths(sftp, "12345", False)
    
    # Log the base paths
    logger.info(f"Base paths: {base_paths}")
    
    # Check if it's focusing on the single correct path
    if len(base_paths) == 1 and "/server_12345/actual1/deathlogs" in base_paths[0]:
        logger.info("✓ Successfully focusing on single correct base path")
        return True
    else:
        logger.error("✗ Not focusing on single correct base path")
        return False

async def test_map_directory_focus():
    """Test that we're focusing on world_0, world_1, world_2 directories"""
    logger.info("Testing map directory focus")
    
    # Create mock SFTP client
    sftp = MockSFTP(hostname="server", server_id="12345", original_server_id="12345")
    
    # Create file discovery instance
    discovery = FileDiscovery()
    
    # Mock base paths
    base_paths = ["/server_12345/actual1/deathlogs"]
    
    # Find map directories
    map_dirs = await discovery._find_map_directories(sftp, base_paths)
    
    # Log the map directories
    logger.info(f"Map directories: {map_dirs}")
    
    # Get expected map directories
    expected_dirs = [
        "/server_12345/actual1/deathlogs/world_0",
        "/server_12345/actual1/deathlogs/world_1",
        "/server_12345/actual1/deathlogs/world_2"
    ]
    
    # Sort both lists for comparison
    map_dirs.sort()
    expected_dirs.sort()
    
    # Check if we're focusing on the correct map directories
    if len(map_dirs) == 3 and set(map_dirs) == set(expected_dirs):
        logger.info("✓ Successfully focusing on world_0, world_1, world_2 directories")
        return True
    else:
        logger.error("✗ Not focusing on world_0, world_1, world_2 directories")
        return False

async def test_full_discovery():
    """Test full file discovery with the single path focus"""
    logger.info("Testing full file discovery")
    
    # Create mock SFTP client
    sftp = MockSFTP(hostname="server", server_id="12345", original_server_id="12345")
    
    # Create file discovery instance
    discovery = FileDiscovery()
    
    # Run discovery
    csv_files, stats = await discovery.discover_csv_files(
        sftp=sftp,
        server_id="12345",
        historical_mode=True
    )
    
    # Log the discovered files
    logger.info(f"Discovered {len(csv_files)} CSV files")
    
    # Count files by map
    map_counts = {"world_0": 0, "world_1": 0, "world_2": 0, "other": 0}
    for path in csv_files:
        if "world_0" in path:
            map_counts["world_0"] += 1
        elif "world_1" in path:
            map_counts["world_1"] += 1
        elif "world_2" in path:
            map_counts["world_2"] += 1
        else:
            map_counts["other"] += 1
    
    # Log the counts by map
    for map_name, count in map_counts.items():
        logger.info(f"  - {map_name}: {count} files")
    
    # Check if we found files in all three world maps
    if map_counts["world_0"] > 0 and map_counts["world_1"] > 0 and map_counts["world_2"] > 0:
        logger.info("✓ Successfully found files in all three world maps")
        return True
    else:
        logger.error("✗ Did not find files in all three world maps")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting path focus tests")
    
    # Run tests
    base_path_test = await test_single_base_path()
    map_dir_test = await test_map_directory_focus()
    discovery_test = await test_full_discovery()
    
    # Log overall result
    if base_path_test and map_dir_test and discovery_test:
        logger.info("✓ All tests passed! Path focus is working correctly")
        return 0
    else:
        logger.error("✗ Some tests failed. Path focus is not working correctly")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)