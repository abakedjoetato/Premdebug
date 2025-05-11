"""
Targeted fix for the CSV search conflict issue.

This script directly modifies the CSV processor to ensure:
1. Files found in map directories are correctly used and not overwritten
2. The final stats count all files that were actually found and processed
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
    backup_path = f"{CSV_PROCESSOR_PATH}.conflict.bak"
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

def apply_fixes():
    """Apply all fixes to the CSV processor"""
    try:
        # Read the file content
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.read()
            
        # Fix 1: Fix found file count display logic
        count_pattern = r"# Include map directory files in the count\n(.*?)total_found = files_found_total"
        
        new_count_logic = """                # Include map directory files in the count
                map_files_count = 0
                if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files:
                    map_files_count = len(self.all_map_csv_files)
                    logger.info(f"Including {map_files_count} files from map directories in final count")
                # Ensure we add the map files to the total count
                files_found_total = files_found + map_files_count
                total_found = files_found_total"""
                
        if "files_found_total" in content:
            # Use the correct pattern if the variable already exists
            content = re.sub(count_pattern, new_count_logic, content)
        else:
            # Fall back to simpler matching if the variable doesn't exist
            count_pattern = r"# Include map directory files in the count\n(.*?)total_found = "
            replacement = new_count_logic + "\n                "
            content = re.sub(count_pattern, replacement, content)
            
        # Fix 2: Fix all_map_csv_files reference to ensure it's a class property
        content = re.sub(r"full_path_csv_files = all_map_csv_files", 
                         "full_path_csv_files = self.all_map_csv_files", content)
        content = re.sub(r"csv_files = \[os\.path\.basename\(f\) for f in all_map_csv_files\]", 
                         "csv_files = [os.path.basename(f) for f in self.all_map_csv_files]", content)
                         
        # Fix 3: Fix the global logic for handling map files 
        content = re.sub(r"if self\.all_map_csv_files:(.*?)len\(self\.all_map_csv_files\)", 
                          lambda m: m.group(0).replace("self.all_map_csv_files", "self.all_map_csv_files"),
                          content, flags=re.DOTALL)
        
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.write(content)
            
        logger.info("Successfully applied all CSV search conflict fixes")
        return True
    except Exception as e:
        logger.error(f"Error applying fixes: {e}")
        return False

def main():
    """Main function to apply the fixes"""
    logger.info("Starting CSV Search Conflict Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply all fixes
    if apply_fixes():
        logger.info("Successfully applied CSV Search Conflict Fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply CSV Search Conflict Fix")
        
if __name__ == "__main__":
    main()