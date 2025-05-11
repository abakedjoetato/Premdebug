"""
Final fix for CSV processing file count tracking

This script ensures that all CSV files found in map directories are properly counted in
the final stats so the user doesn't see "0 files found" when files were actually found.
"""
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV_PROCESSOR_PATH = "cogs/csv_processor.py"

def make_backup():
    """Create a backup of the file"""
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

def fix_file_count_tracking():
    """Fix the file count tracking in the final stats"""
    try:
        # Fix using string replacement
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            lines = f.readlines()
        
        fixed_lines = []
        for line in lines:
            # Fix reference to local all_map_csv_files vs self.all_map_csv_files in final logic
            if "full_path_csv_files = all_map_csv_files" in line:
                fixed_lines.append("                                full_path_csv_files = self.all_map_csv_files\n")
            elif "csv_files = [os.path.basename(f) for f in all_map_csv_files]" in line:
                fixed_lines.append("                                csv_files = [os.path.basename(f) for f in self.all_map_csv_files]\n")
            else:
                fixed_lines.append(line)
        
        # Write the fixed file
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(fixed_lines)
        
        logger.info("Successfully fixed file count tracking")
        return True
    except Exception as e:
        logger.error(f"Error fixing file count tracking: {e}")
        return False

def main():
    """Main function to apply the fix"""
    logger.info("Starting Final CSV Fix")
    
    # Create a backup
    if not make_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the fix
    if fix_file_count_tracking():
        logger.info("Successfully applied Final CSV Fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply Final CSV Fix")
        
if __name__ == "__main__":
    main()