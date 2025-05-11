#!/usr/bin/env python3
"""
Test Map Directory Focus

This script tests the file discovery process to ensure it's correctly
focused on world_0, world_1, and world_2 directories, and processes
files from each map correctly.
"""
import asyncio
import logging
import os
import sys

from utils.file_discovery import FileDiscovery
from utils.sftp import SFTPManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_map_directory_focus():
    """Test the map directory focus for file discovery"""
    logger.info("Starting map directory focus test")
    
    # Create instances
    discovery = FileDiscovery()
    
    # Create a sample server ID
    server_id = "test_server_123"
    server_dir = f"hostname_{server_id}"
    
    # Sample directories with different world maps
    directories = [
        f"/{server_dir}/actual1/deathlogs/world_0",
        f"/{server_dir}/actual1/deathlogs/world_1",
        f"/{server_dir}/actual1/deathlogs/world_2",
        f"/{server_dir}/actual1/deathlogs/other_dir"
    ]
    
    # Files in each directory
    files = {
        directories[0]: [
            f"{directories[0]}/killfeed_20250510_1.csv",
            f"{directories[0]}/killfeed_20250510_2.csv"
        ],
        directories[1]: [
            f"{directories[1]}/killfeed_20250510_1.csv"
        ],
        directories[2]: [
            f"{directories[2]}/killfeed_20250510_1.csv"
        ],
        directories[3]: [
            f"{directories[3]}/killfeed_20250510_1.csv"
        ]
    }
    
    # Create a mock SFTP manager
    class MockSFTPManager:
        """Mock SFTP manager for testing"""
        async def list_directory(self, path):
            """Mock list_directory method"""
            logger.info(f"MOCK: Listing directory: {path}")
            
            # Root directory
            if path == "/":
                return [server_dir.lstrip("/")]
            
            # Server directory
            if path == f"/{server_dir}":
                return ["actual1", "logs", "game"]
                
            # Actual1 directory
            if path == f"/{server_dir}/actual1":
                return ["deathlogs", "config", "backups"]
                
            # Deathlogs directory
            if path == f"/{server_dir}/actual1/deathlogs":
                return ["world_0", "world_1", "world_2", "other_dir"]
            
            # World directories
            if path in directories:
                return [os.path.basename(f) for f in files.get(path, [])]
            
            return []
            
        async def directory_exists(self, path):
            """Mock directory_exists method"""
            logger.info(f"MOCK: Checking directory: {path}")
            
            # Check exact matches
            if path in directories:
                return True
                
            # Check base paths
            base_paths = [
                "/",
                f"/{server_dir}",
                f"/{server_dir}/actual1",
                f"/{server_dir}/actual1/deathlogs"
            ]
            
            if path in base_paths:
                return True
                
            # All other base paths from the FileDiscovery module
            if path in [f"/logs/{server_id}", f"/deathlogs/{server_id}", 
                        f"/killfeed/{server_id}", f"/game/logs/{server_id}",
                        f"/data/logs/{server_id}"]:
                return False
                
            return False
            
        async def read_file(self, path):
            """Mock read_file method"""
            logger.info(f"MOCK: Reading file: {path}")
            # Return mock CSV content
            return "2025-05-10 12:00:00;Player1;123;Player2;456;Weapon;123;System1;System2"
            
        async def get_file_attrs(self, path):
            """Mock get_file_attrs method"""
            logger.info(f"MOCK: Getting file attributes: {path}")
            # Return mock file attributes
            return {
                "size": 100,
                "mtime": datetime.now().timestamp()
            }
    
    # Create mock SFTP manager
    sftp = MockSFTPManager()
    
    # Test historical mode (should find all files in world_0, world_1, world_2)
    logger.info("Testing historical mode (all files from all maps)")
    csv_files, stats = await discovery.discover_csv_files(
        sftp=sftp,
        server_id=server_id,
        historical_mode=True
    )
    
    # Check results
    logger.info(f"Found {len(csv_files)} files in historical mode")
    logger.info(f"Files by directory:")
    
    # Count files by directory
    file_counts = {"world_0": 0, "world_1": 0, "world_2": 0, "other": 0}
    for file_path in csv_files:
        if "world_0" in file_path:
            file_counts["world_0"] += 1
        elif "world_1" in file_path:
            file_counts["world_1"] += 1
        elif "world_2" in file_path:
            file_counts["world_2"] += 1
        else:
            file_counts["other"] += 1
    
    # Log counts by world
    for world, count in file_counts.items():
        logger.info(f"  - {world}: {count} files")
        
    # Test killfeed mode (should still find all files but sorted differently)
    logger.info("\nTesting killfeed mode (newest file across all maps)")
    csv_files, stats = await discovery.discover_csv_files(
        sftp=sftp,
        server_id=server_id,
        historical_mode=False
    )
    
    # Check results
    logger.info(f"Found {len(csv_files)} files in killfeed mode")
    logger.info(f"Files by directory:")
    
    # Count files by directory
    file_counts = {"world_0": 0, "world_1": 0, "world_2": 0, "other": 0}
    for file_path in csv_files:
        if "world_0" in file_path:
            file_counts["world_0"] += 1
        elif "world_1" in file_path:
            file_counts["world_1"] += 1
        elif "world_2" in file_path:
            file_counts["world_2"] += 1
        else:
            file_counts["other"] += 1
    
    # Log counts by world
    for world, count in file_counts.items():
        logger.info(f"  - {world}: {count} files")
        
    # Test if we're finding files in the right directories
    logger.info("\nVerifying map directory focus")
    world_0_found = any("world_0" in path for path in csv_files)
    world_1_found = any("world_1" in path for path in csv_files)
    world_2_found = any("world_2" in path for path in csv_files)
    other_found = any(not any(w in path for w in ["world_0", "world_1", "world_2"]) for path in csv_files)
    
    logger.info(f"world_0 files found: {world_0_found}")
    logger.info(f"world_1 files found: {world_1_found}")
    logger.info(f"world_2 files found: {world_2_found}")
    logger.info(f"other directories files found: {other_found}")
    
    if world_0_found and world_1_found and world_2_found and not other_found:
        logger.info("SUCCESS: Map directory focus is working correctly!")
        logger.info("Finding files only from world_0, world_1, and world_2")
        return True
    else:
        logger.error("FAILURE: Map directory focus is not working correctly!")
        if not world_0_found or not world_1_found or not world_2_found:
            logger.error("Not finding files from all expected world_* directories")
        if other_found:
            logger.error("Finding files from directories outside world_0, world_1, world_2")
        return False

def main():
    """Main function"""
    logger.info("Map Directory Focus Test")
    
    # Run the test
    success = asyncio.run(test_map_directory_focus())
    
    if success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())