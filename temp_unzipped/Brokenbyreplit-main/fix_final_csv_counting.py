"""
Final Fix for CSV File Counting in Final Stats

This script ensures that files found in map directories are properly counted
in the final stats.
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

def fix_final_map_file_counting():
    """Fix the final file counting to properly include map files"""
    try:
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.readlines()
            
        # Find the final output logs
        final_output_line = -1
        for i, line in enumerate(content):
            if "CRITICAL DEBUG: CSV processing completed. Files Found=" in line:
                final_output_line = i
                break
                
        if final_output_line < 0:
            logger.warning("Couldn't find the final output line")
            return False
            
        # Find where the total_found is calculated right before the final output
        total_found_calc_line = -1
        for i in range(final_output_line-10, final_output_line):
            if i >= 0 and "total_found = " in content[i]:
                total_found_calc_line = i
                break
                
        if total_found_calc_line < 0:
            logger.warning("Couldn't find the total_found calculation line")
            return False
            
        # Fix the calculation to include map_csv_files_found in addition to all_map_csv_files
        indentation = len(content[total_found_calc_line]) - len(content[total_found_calc_line].lstrip())
        indent = ' ' * indentation
        
        # Improve map file counting right before calculating total_found
        map_count_fix = [
            f"{indent}# Ensure we count map files from all sources\n",
            f"{indent}if hasattr(self, 'map_csv_files_found') and self.map_csv_files_found and len(self.map_csv_files_found) > map_files_count:\n",
            f"{indent}    logger.warning(f\"Found additional {{len(self.map_csv_files_found)}} map files in map_csv_files_found\")\n",
            f"{indent}    map_files_count = max(map_files_count, len(self.map_csv_files_found))\n",
            "\n"
        ]
        
        # Insert right before the total_found calculation
        for i, line in enumerate(map_count_fix):
            content.insert(total_found_calc_line + i, line)
            
        # Update the total_found calculation to include map_files_count
        # The line number changed after insertion
        total_found_calc_line += len(map_count_fix)
        
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully applied final map file counting fix")
        return True
    except Exception as e:
        logger.error(f"Error applying final map file counting fix: {e}")
        return False

def fix_map_files_tracking():
    """Fix how map files are tracked throughout processing"""
    try:
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.readlines()
            
        # Fix double initialization of map_files_count
        double_init_line = -1
        for i, line in enumerate(content):
            if "map_files_count = len(self.all_map_csv_files)" in line:
                if "map_files_count = 0" in content[i+1]:
                    double_init_line = i+1
                    break
                    
        if double_init_line >= 0:
            # Remove the redundant initialization
            content.pop(double_init_line)
            logger.info(f"Removed redundant map_files_count reset at line {double_init_line+1}")
            
        # Find where we check map_csv_files_found
        map_found_check = False
        for i, line in enumerate(content):
            if "hasattr(self, 'map_csv_files_found')" in line:
                map_found_check = True
                break
                
        # If we don't have that check, let's add it to key locations
        if not map_found_check:
            for i, line in enumerate(content):
                if "self.all_map_csv_files = []" in line:
                    # Add initialization for map_csv_files_found in the same place
                    indentation = len(line) - len(line.lstrip())
                    indent = ' ' * indentation
                    content.insert(i+1, f"{indent}self.map_csv_files_found = []\n")
                    logger.info(f"Added map_csv_files_found initialization at line {i+2}")
                    break
                    
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully fixed map files tracking")
        return True
    except Exception as e:
        logger.error(f"Error fixing map files tracking: {e}")
        return False

def main():
    """Main function to apply the fix"""
    logger.info("Starting Final CSV File Counting Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the fixes
    if fix_map_files_tracking() and fix_final_map_file_counting():
        logger.info("Successfully applied all final CSV file counting fixes. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply some fixes")
        
if __name__ == "__main__":
    main()