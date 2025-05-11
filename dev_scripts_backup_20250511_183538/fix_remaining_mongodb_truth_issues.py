#!/usr/bin/env python3
"""
Script to fix the remaining MongoDB truth testing issues in specific files.
This script replaces problematic 'if not object' with 'if object is None'
"""

import os
import re
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Files and replacements to apply
FIX_MAP = {
    "cogs/bounties.py": [
        (r"if player_data is None:", "if player_data is None:"),
        (r"if guild_data is None:", "if guild_data is None:"),
    ],
    "cogs/economy.py": [
        (r"if not richest_players if richest_players is not None else \2, "if richest_players is None or len"),
        (r"if player_economy is None:", "if player_economy is None:"),
        (r"if removal_result is None:", "if removal_result is None:"),
    ],
    "cogs/events.py": [
        (r"if guild_data is None:", "if guild_data is None:"),
        (r"if server_exists is None:", "if server_exists is None:"),
    ],
    "cogs/factions.py": [
        (r"if player_link is None:", "if player_link is None:"),
        (r"if player_id is None:", "if player_id is None:"),
    ],
    "cogs/rivalries.py": [
        (r"if not guild if guild is not None else \2, "if guild is None or not guild.check"),
    ],
    "cogs/stats.py": [
        (r"if not players if players is not None else \2, "if players is None or len"),
    ],
    "cogs/csv_processor.py": [
        (r"if server_configs is None:", "if server_configs is None:"),
        (r"if guild_servers is None:", "if guild_servers is None:"),
        (r"if not self.bot.db:", "if self.bot.db is None:"),
    ],
}

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    backup_path = f"{file_path}.bak"
    with open(file_path, 'rb') as src:
        with open(backup_path, 'wb') as dst:
            dst.write(src.read())
    logger.info(f"Created backup of {file_path} to {backup_path}")
    return backup_path

def fix_file(file_path, replacements):
    """Apply fixes to a file"""
    if not os.path.exists(file_path):
        logger.warning(f"File {file_path} not found, skipping")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        for pattern, replacement in replacements:
            # Count matches
            matches = len(re.findall(pattern, content))
            if matches > 0:
                # Apply replacement
                new_content = re.sub(pattern, replacement, content)
                
                # Count changes
                changes_made += matches
                
                # Update content for next pattern
                content = new_content
                
                logger.info(f"Fixed {matches} occurrences of '{pattern}' in {file_path}")
        
        # If changes were made, write the file
        if changes_made > 0:
            backup_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Made a total of {changes_made} fixes in {file_path}")
            return True
        else:
            logger.info(f"No changes needed in {file_path}")
        
        return changes_made > 0
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    """Apply fixes to files"""
    logger.info("Starting fix application...")
    
    files_fixed = 0
    for file_path, replacements in FIX_MAP.items():
        if fix_file(file_path, replacements):
            files_fixed += 1
    
    logger.info(f"Successfully fixed {files_fixed} files")
    return files_fixed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
