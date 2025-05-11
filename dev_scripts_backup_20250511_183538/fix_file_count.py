"""
Simple fix for the CSV file counting issue.
This script modifies the final output to correctly report the number of files found.
"""
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV_PROCESSOR_PATH = "cogs/csv_processor.py"

def create_backup():
    """Create a backup of the original file"""
    backup_path = f"{CSV_PROCESSOR_PATH}.final.bak"
    try:
        with open(CSV_PROCESSOR_PATH, 'r') as src:
            content = src.read()
            
        with open(backup_path, 'w') as dest:
            dest.write(content)
            
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def fix_final_output():
    """Fix the final output to correctly report the number of files found"""
    try:
        # Read the file content
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.readlines()
            
        # Find the final output line
        target_line = None
        for i, line in enumerate(content):
            if "CRITICAL DEBUG: CSV processing completed" in line and "Files Found=" in line:
                target_line = i
                break
                
        if target_line is None:
            logger.error("Couldn't find the target line")
            return False
            
        # Extract indentation
        indent = len(content[target_line]) - len(content[target_line].lstrip())
        spaces = ' ' * indent
        
        # Add code to count files from map directory
        count_lines = [
            f"{spaces}# Include map directory files in the count\n",
            f"{spaces}map_files_count = 0\n",
            f"{spaces}if hasattr(self, 'all_map_csv_files'):\n",
            f"{spaces}    map_files_count = len(self.all_map_csv_files) if self.all_map_csv_files else 0\n",
            f"{spaces}    logger.info(f\"Including {{map_files_count}} files from map directories in final count\")\n",
            f"{spaces}total_found = max(files_found, map_files_count)\n",
            f"{spaces}logger.warning(f\"CRITICAL DEBUG: CSV processing completed. Files Found={{total_found}}, Files Processed={{files_processed}}, Events={{events_processed}}\")\n"
        ]
        
        # Replace the original line
        content[target_line] = count_lines[0]
        
        # Insert the new lines
        for i, line in enumerate(count_lines[1:]):
            content.insert(target_line + i + 1, line)
            
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully fixed final output")
        return True
    except Exception as e:
        logger.error(f"Error fixing final output: {e}")
        return False

def main():
    """Main function to apply the fix"""
    logger.info("Starting File Count Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the fix
    if fix_final_output():
        logger.info("Successfully applied File Count Fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply File Count Fix")
        
if __name__ == "__main__":
    main()