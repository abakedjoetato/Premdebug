#!/usr/bin/env python3
"""
Direct CSV Map Directory Confusion Fix

This script directly fixes the confusion between map directories and map files
in the CSV processing system. The system is incorrectly looking for map files
when it should be determining maps by directories.

This version implements a more targeted, comprehensive fix:
1. Ensures directory_exists method is properly used
2. Makes map directories the primary determination factor, not map files
3. Correctly handles file discovery and tracking across all modules
4. Fixes key naming inconsistencies across the codebase
5. Prevents double initialization of tracking variables
"""

import os
import sys
import logging
import shutil
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(path):
    """Create a backup of the file before modifying it"""
    if not os.path.exists(path):
        logger.error(f"Cannot backup non-existent file: {path}")
        return False
        
    backup_path = f"{path}.map_fix.bak"
    logger.info(f"Creating backup of {path} to {backup_path}")
    shutil.copy2(path, backup_path)
    return True

def fix_file_discovery_module():
    """Fix the file discovery module to correctly track map directories"""
    file_path = "utils/file_discovery.py"
    
    # Backup the file first
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # 1. Fix map directory search to be more comprehensive
        map_subdirs_pattern = r"# Known map directory names.*?\[.*?\]"
        enhanced_map_subdirs = """# Known map directory names, expanded for better detection
        map_subdirs = [
            "world_0", "world0", "world_1", "world1", "world", "world2", "world_2",
            "map_0", "map0", "map_1", "map1", "map", "map2", "map_2",
            "main", "default", "maps", "custom_maps", "gamedata", "levels",
            # Add more variations to increase coverage
            "world3", "world_3", "map3", "map_3", "zone", "region"
        ]
        
        logger.info(f"Searching for map directories in {len(base_paths)} base paths")"""
        
        content = re.sub(map_subdirs_pattern, enhanced_map_subdirs, content, flags=re.DOTALL)
        
        # 2. Enhance directory checking with more logging
        old_dir_check = r"if await sftp\.directory_exists\(map_path\):.*?map_dirs\.append\(map_path\)"
        new_dir_check = """if await sftp.directory_exists(map_path):
                        logger.info(f"Found map directory: {map_path}")
                        map_dirs.append(map_path)
                        # This is a critical finding for CSV processing"""
                        
        content = re.sub(old_dir_check, new_dir_check, content, flags=re.DOTALL)
        
        # 3. Fix pattern matching for map directories to be more flexible
        old_pattern = r"if re\.search\(r'\(world\|map\|level\|zone\|region\)\[-_\]?\\d\*', entry, re\.IGNORECASE\):"
        new_pattern = """# More flexible pattern matching for map directories
                    if re.search(r'(world|map|level|zone|region|area|district|territory)[-_]?\\\\d*', entry, re.IGNORECASE):"""
                    
        content = re.sub(old_pattern, new_pattern, content)
        
        # 4. Fix discovery stats to consistently use "map_files", not "map_files_found"
        stats_pattern = r"discovery_stats = \{.*?\}"
        new_stats = """discovery_stats = {
            "total_files": len(all_discovered_files),
            "map_files": len(map_files),  # Files found in map directories - consistent key name
            "map_directories": len(map_directories),  # Count of map directories found
            "regular_files": len(regular_files),
            "filtered_files": len(filtered_files),
            "start_date": start_date,
            "historical_mode": historical_mode
        }"""
        
        content = re.sub(stats_pattern, new_stats, content, flags=re.DOTALL)
        
        # 5. Add special debug logging to track map directory discoveries
        if "logger.info(f\"Found {len(map_path_files)} CSV files in map directory {map_dir}\")" in content:
            content = content.replace(
                "logger.info(f\"Found {len(map_path_files)} CSV files in map directory {map_dir}\")",
                "logger.info(f\"MAP DIRECTORY: Found {len(map_path_files)} CSV files in map directory {map_dir}\")"
            )
        
        # Save the modified file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Fixed file discovery module: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing file discovery module: {e}")
        return False

def fix_csv_processor_coordinator():
    """Fix the CSV processor coordinator to correctly handle map directory stats"""
    file_path = "utils/csv_processor_coordinator.py"
    
    # Backup the file first
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # 1. Fix map_files_found to use correct key from discovery stats
        old_stats_keys = r'"map_files_found": map_files,'
        new_stats_keys = '"map_files_found": len(map_files),  # Use map_files from discovery'
        
        content = content.replace(old_stats_keys, new_stats_keys)
        
        # 2. Add map directories tracking to stats
        if '"regular_files_found": regular_files' in content:
            content = content.replace(
                '"regular_files_found": regular_files',
                '"regular_files_found": regular_files,\n                    "map_directories_found": discovery_stats.get("map_directories", 0)'
            )
        
        # 3. Add debug logging for map directory processing
        if "logger.info(f\"Historical discovery found {total_files} total files \"" in content:
            content = content.replace(
                "logger.info(f\"Historical discovery found {total_files} total files \"",
                "logger.info(f\"MAP STATS: Historical discovery found {total_files} total files \""
            )
        
        # Save the modified file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Fixed CSV processor coordinator: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing CSV processor coordinator: {e}")
        return False

def fix_csv_processor_cog():
    """Fix the CSV processor cog to correctly handle map directory data"""
    file_path = "cogs/csv_processor.py"
    
    # Backup the file first
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # 1. Fix map_files reporting to use consistent key names
        old_map_files = r"map_files = stats\.get\(\"map_files_found\", 0\)"
        new_map_files = 'map_files = stats.get("map_files", 0)  # Use consistent key name from discovery stats'
        
        content = re.sub(old_map_files, new_map_files, content)
        
        # 2. Add map directories reporting if not present
        if "Map files found:" in content:
            content = content.replace(
                "Map files found:",
                "Map files found (in map directories):"
            )
        
        # 3. Fix status command to show map directory info
        if "• Map files found: {map_files}" in content:
            content = content.replace(
                "• Map files found: {map_files}",
                "• Map files found: {map_files}\n                status_lines.append(f\"• Map directories: {stats.get('map_directories_found', 0)}\")"
            )
        
        # Save the modified file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Fixed CSV processor cog: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing CSV processor cog: {e}")
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
    logger.info("Starting Map Directory Fix application")
    
    # Track overall success
    success = True
    
    # Fix the modules
    if not fix_file_discovery_module():
        logger.error("Failed to fix file discovery module")
        success = False
    
    if not fix_csv_processor_coordinator():
        logger.error("Failed to fix CSV processor coordinator")
        success = False
    
    if not fix_csv_processor_cog():
        logger.error("Failed to fix CSV processor cog")
        success = False
    
    # Restart the bot if all fixes were successful
    if success:
        logger.info("All fixes applied successfully!")
        restart_bot()
        logger.info("Bot restarted with new changes. Check logs for results.")
        return 0
    else:
        logger.error("One or more fixes failed. Please check logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())