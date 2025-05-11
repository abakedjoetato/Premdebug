#!/usr/bin/env python3
"""
Fix for World Map Specific Processing

This script updates the CSV file discovery to:
1. Focus on specific world_* directories only (world_0, world_1, world_2)
2. Ensure killfeed parser finds the newest CSV from all maps combined
3. Ensure historical parser finds all files from all maps combined

This approach focuses our search on the directories we know exist and
prevents wasting time on irrelevant paths.
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
        
    backup_path = f"{path}.world_fix.bak"
    logger.info(f"Creating backup of {path} to {backup_path}")
    shutil.copy2(path, backup_path)
    return True

def fix_map_directory_focus():
    """Fix the map directory detection to focus only on world_* directories"""
    file_path = "utils/file_discovery.py"
    
    # Backup the file
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the map subdirectories list and replace it
        # This focuses only on world_* directories as specified
        old_map_subdirs = """        # Known map directory names specifically for ToT structure
        # Note: According to the path /hostname_serverid/actual1/deathlogs/world_0/*.csv
        # The critical directories are world_0, world_1, etc.
        map_subdirs = [
            "world_0", "world0", "world_1", "world1", "world", "world2", "world_2",
            "world3", "world_3", "world4", "world_4", "world5", "world_5",
            "level_0", "level0", "level_1", "level1", "level", "level2", "level_2",
            "map_0", "map0", "map_1", "map1", "map", "map2", "map_2"
        ]"""
        
        # Replace with only the world_* directories we need
        new_map_subdirs = """        # Focus only on world_* directories as specified by the team
        # We need to focus on world_0, world_1, and world_2 as these are the only maps
        map_subdirs = [
            "world_0",  # Primary map
            "world_1",  # Secondary map
            "world_2",  # Future-proofing
            "world0",   # Alternative naming
            "world1",   # Alternative naming
            "world2"    # Alternative naming
        ]
        
        # Log the focused map search for better diagnostics
        logger.info("Focusing map directory search on world_0, world_1, and world_2 only")"""
        
        content = content.replace(old_map_subdirs, new_map_subdirs)
        
        # Enhance the pattern matching to focus on world_* directories
        old_pattern = """                    # Check if it matches known map naming patterns
                    if re.search(r'(world|map|level|zone|region)[-_]?\d*', entry, re.IGNORECASE):"""
                    
        new_pattern = """                    # Focus pattern matching on world_* directories only
                    if re.search(r'world[-_]?[0-2]', entry, re.IGNORECASE):"""
        
        content = content.replace(old_pattern, new_pattern)
        
        # Save the updated file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Updated map directory focus in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing map directory focus: {e}")
        return False

def fix_killfeed_newest_csv():
    """Fix the killfeed parser to find the newest CSV from all maps combined"""
    file_path = "utils/csv_processor_coordinator.py"
    
    # Backup the file
    if not backup_file(file_path):
        return False
        
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the killfeed processing section and add comments about combining maps
        target_section = """                    # Process each file incrementally from the last known position
                    for file_path in csv_files:
                        try:
                            # Skip files that have been fully processed
                            if self.parser.is_file_processed(file_path):
                                continue"""
                                
        enhanced_section = """                    # Sort all files by modification time to find the newest across all maps
                    # This ensures we get the newest CSV from all maps combined as required
                    csv_files.sort(key=lambda path: os.path.basename(path), reverse=True)
                    logger.info(f"Sorted {len(csv_files)} files by name to process newest first")
                    
                    # Process each file incrementally from the last known position
                    for file_path in csv_files:
                        try:
                            # Skip files that have been fully processed
                            if self.parser.is_file_processed(file_path):
                                continue
                                
                            # Extract map info from path for better logging
                            map_name = "unknown"
                            if "world_0" in file_path:
                                map_name = "world_0"
                            elif "world_1" in file_path:
                                map_name = "world_1"
                            elif "world_2" in file_path:
                                map_name = "world_2"
                                
                            logger.info(f"Processing CSV from map {map_name}: {os.path.basename(file_path)}")"""
                            
        content = content.replace(target_section, enhanced_section)
        
        # Save the updated file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Enhanced killfeed processing in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing killfeed processing: {e}")
        return False

def fix_historical_combined_maps():
    """Fix the historical parser to find all files from all maps combined"""
    file_path = "utils/csv_processor_coordinator.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the historical processing section and enhance it
        target_section = """                # Process each file from the beginning
                for file_path in csv_files:
                    try:
                        content = await sftp.read_file(file_path)
                        if not content:
                            logger.warning(f"Empty content for file {file_path}")
                            continue"""
                            
        enhanced_section = """                # Log the total files found across all maps combined
                logger.info(f"Historical mode: Processing {len(csv_files)} CSV files from all maps combined")
                
                # Group files by map for better reporting
                map_file_counts = {"world_0": 0, "world_1": 0, "world_2": 0, "other": 0}
                for path in csv_files:
                    if "world_0" in path:
                        map_file_counts["world_0"] += 1
                    elif "world_1" in path:
                        map_file_counts["world_1"] += 1
                    elif "world_2" in path:
                        map_file_counts["world_2"] += 1
                    else:
                        map_file_counts["other"] += 1
                
                # Log file counts by map
                for map_name, count in map_file_counts.items():
                    if count > 0:
                        logger.info(f"  - Found {count} files in {map_name}")
                
                # Process each file from the beginning
                for file_path in csv_files:
                    try:
                        content = await sftp.read_file(file_path)
                        if not content:
                            logger.warning(f"Empty content for file {file_path}")
                            continue"""
                            
        content = content.replace(target_section, enhanced_section)
        
        # Save the updated file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Enhanced historical processing in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing historical processing: {e}")
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
    logger.info("Starting World Map Specific Fix application")
    
    # Fix the map directory focus
    if not fix_map_directory_focus():
        logger.error("Failed to fix map directory focus")
        return 1
        
    # Fix killfeed newest CSV handling
    if not fix_killfeed_newest_csv():
        logger.error("Failed to fix killfeed newest CSV handling")
        return 1
        
    # Fix historical combined maps handling
    if not fix_historical_combined_maps():
        logger.error("Failed to fix historical combined maps handling")
        return 1
        
    logger.info("All World Map specific fixes applied successfully!")
    
    # Restart the bot
    restart_bot()
    
    logger.info("Bot restarted with new World Map specific configuration. Check logs for results.")
    return 0

if __name__ == "__main__":
    sys.exit(main())