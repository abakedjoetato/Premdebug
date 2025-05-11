"""
Final Map Files Fix for CSV Processing

This script makes direct modifications to ensure that files found in map directories
are properly counted in the final statistics.
"""
import logging
import os
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV_PROCESSOR_PATH = "cogs/csv_processor.py"

def create_backup():
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"csv_fixes_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    backup_path = os.path.join(backup_dir, os.path.basename(CSV_PROCESSOR_PATH))
    try:
        shutil.copy2(CSV_PROCESSOR_PATH, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def fix_map_file_discovery():
    """Add line to save map files when they're found"""
    try:
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.readlines()
            
        # Find the line that logs "Found X CSV files in map directory"
        map_files_line = -1
        for i, line in enumerate(content):
            if "Found" in line and "CSV files in map directory" in line:
                map_files_line = i
                break
                
        if map_files_line < 0:
            logger.warning("Couldn't find the 'Found X CSV files in map directory' line")
            return False
            
        # Extract the indentation
        indent_level = len(content[map_files_line]) - len(content[map_files_line].lstrip())
        indent = ' ' * indent_level
        
        # Add a line after this to explicitly set the map_csv_files_found
        track_line = f"{indent}self.map_csv_files_found = self.all_map_csv_files.copy() if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files else []\n"
        content.insert(map_files_line + 1, track_line)
        
        logger.info(f"Added map files tracking at line {map_files_line + 1}")
        
        # Find the line where final output is being printed
        final_output_line = -1
        for i, line in enumerate(content):
            if "CRITICAL DEBUG: CSV processing completed" in line and "Files Found=" in line:
                final_output_line = i
                break
                
        if final_output_line < 0:
            logger.warning("Couldn't find the final output line")
            return False
            
        # Find where map_files_count is being calculated
        map_count_lines = []
        for i, line in enumerate(content):
            if "map_files_count" in line:
                map_count_lines.append(i)
                
        # If we don't have proper map file counting, add it
        if not map_count_lines:
            # Find a good place to insert it - before the final output line
            indent_level = len(content[final_output_line]) - len(content[final_output_line].lstrip())
            indent = ' ' * indent_level
            
            new_lines = [
                f"{indent}# Ensure map files are counted\n",
                f"{indent}map_files_count = 0\n",
                f"{indent}if hasattr(self, 'map_csv_files_found') and self.map_csv_files_found:\n",
                f"{indent}    map_files_count = len(self.map_csv_files_found)\n",
                f"{indent}    logger.info(f\"Final count includes {{map_files_count}} files from map directories\")\n",
                f"{indent}    # Ensure files_found reflects these files\n",
                f"{indent}    files_found = max(files_found, map_files_count)\n",
                f"{indent}    # Ensure total_found includes map files\n",
                f"{indent}    total_found = files_found\n",
                "\n"
            ]
            
            # Insert the lines before the final output
            for i, line in enumerate(new_lines):
                content.insert(final_output_line + i, line)
                
            logger.info(f"Added map files counting logic before final output")
        
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully applied map file discovery fix")
        return True
    except Exception as e:
        logger.error(f"Error applying map file discovery fix: {e}")
        return False

def main():
    """Main function to apply the fix"""
    logger.info("Starting Final Map Files Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the fix
    if fix_map_file_discovery():
        logger.info("Successfully applied final map files fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply final map files fix")
        
if __name__ == "__main__":
    main()