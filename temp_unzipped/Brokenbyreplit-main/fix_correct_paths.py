#!/usr/bin/env python3
"""
Fix for Correct CSV File Paths

This script updates the CSV file discovery to use the correct path structure:
/hostname_serverid/actual1/deathlogs/world_0/*.csv
/hostname_serverid/actual1/deathlogs/world_1/*.csv

The current paths were completely wrong, which explains why no files were being found.
"""
import os
import sys
import logging
import shutil
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(path):
    """Create a backup of the file before modifying it"""
    if not os.path.exists(path):
        logger.error(f"Cannot backup non-existent file: {path}")
        return False
        
    backup_path = f"{path}.path_fix.bak"
    logger.info(f"Creating backup of {path} to {backup_path}")
    shutil.copy2(path, backup_path)
    return True

def fix_file_discovery_base_paths():
    """Fix the base paths in file discovery to match the correct structure"""
    file_path = "utils/file_discovery.py"
    
    # Backup the file
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the _find_base_paths method to replace the paths
        old_base_paths = """        # Start with standard paths for death logs
        base_paths = [
            "/deathlogs",
            "/logs/deathlogs",
            "/game/deathlogs",
            "/data/deathlogs",
            "/killfeed",
            "/logs/killfeed",
            "/game/logs",
            "/logs"
        ]"""
        
        # Replace with the correct path structure
        new_base_paths = """        # Use correct Tower of Temptation path structure:
        # /hostname_serverid/actual1/deathlogs/world_0/*.csv
        
        # Get server info for path construction
        clean_hostname = 'server'
        if hasattr(sftp, 'hostname') and sftp.hostname:
            clean_hostname = sftp.hostname.split(':')[0]
            
        path_server_id = ''
        if hasattr(sftp, 'original_server_id') and sftp.original_server_id:
            path_server_id = sftp.original_server_id
        elif hasattr(sftp, 'server_id') and sftp.server_id:
            path_server_id = sftp.server_id
            
        server_dir = f"{clean_hostname}_{path_server_id}"
        logger.info(f"Using server directory: {server_dir}")
        
        # Primary paths based on correct structure
        base_paths = [
            f"/{server_dir}/actual1/deathlogs",
            f"/{server_dir}/deathlogs",
            f"/{server_dir}/Logs/deathlogs",
            f"/{server_dir}/logs/deathlogs",
            f"/{server_dir}/game/deathlogs",
            f"/{server_dir}/actual1/logs"
        ]"""
        
        # Replace the base paths
        content = content.replace(old_base_paths, new_base_paths)
        
        # Also fix the historical mode paths
        old_historical = """        # If in historical mode, add even more possibilities
        if historical_mode:
            extra_paths = [
                "/",
                "/game",
                "/data",
                "/var/log",
                "/var/log/game",
                "/home/logs"
            ]
            base_paths.extend(extra_paths)"""
            
        new_historical = """        # If in historical mode, add even more possibilities
        if historical_mode:
            extra_paths = [
                f"/{server_dir}",
                f"/{server_dir}/actual1",
                f"/{server_dir}/game",
                f"/{server_dir}/data",
                f"/{server_dir}/logs"
            ]
            base_paths.extend(extra_paths)"""
            
        content = content.replace(old_historical, new_historical)
        
        # Save the updated file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Updated base paths in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing base paths: {e}")
        return False

def fix_map_directory_subdirs():
    """Fix the map directory subdirectories to match the correct structure"""
    file_path = "utils/file_discovery.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the map subdirectories
        old_map_subdirs = """        # Known map directory names, expanded for better detection
        map_subdirs = [
            "world_0", "world0", "world_1", "world1", "world", "world2", "world_2",
            "map_0", "map0", "map_1", "map1", "map", "map2", "map_2",
            "main", "default", "maps", "custom_maps", "gamedata", "levels",
            # Add more variations to increase coverage
            "world3", "world_3", "map3", "map_3", "zone", "region"
        ]"""
        
        # Update with the specific directories from the path structure
        new_map_subdirs = """        # Known map directory names specifically for ToT structure
        # Note: According to the path /hostname_serverid/actual1/deathlogs/world_0/*.csv
        # The critical directories are world_0, world_1, etc.
        map_subdirs = [
            "world_0", "world0", "world_1", "world1", "world", "world2", "world_2",
            "world3", "world_3", "world4", "world_4", "world5", "world_5",
            "level_0", "level0", "level_1", "level1", "level", "level2", "level_2",
            "map_0", "map0", "map_1", "map1", "map", "map2", "map_2"
        ]"""
        
        content = content.replace(old_map_subdirs, new_map_subdirs)
        
        # Save the updated file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Updated map subdirectories in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing map subdirectories: {e}")
        return False

def restart_bot():
    """Restart the bot to apply changes"""
    try:
        # Kill any existing Python processes
        os.system("pkill -9 -f 'python' || true")
        
        # Clear Python cache
        logger.info("Clearing Python cache...")
        os.system("find . -type d -name '__pycache__' -exec rm -rf {} +")
        
        # Start the bot
        logger.info("Starting the bot...")
        os.system("nohup python bot.py > bot_output.log 2>&1 &")
        
        logger.info("Bot restarted")
        return True
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting Path Structure Fix application")
    
    # Fix the file discovery base paths
    if not fix_file_discovery_base_paths():
        logger.error("Failed to fix file discovery base paths")
        return 1
        
    # Fix the map directory subdirectories
    if not fix_map_directory_subdirs():
        logger.error("Failed to fix map directory subdirectories")
        return 1
        
    logger.info("All path fixes applied successfully!")
    
    # Restart the bot
    restart_bot()
    
    logger.info("Bot restarted with new path structure. Check logs for results.")
    return 0

if __name__ == "__main__":
    sys.exit(main())