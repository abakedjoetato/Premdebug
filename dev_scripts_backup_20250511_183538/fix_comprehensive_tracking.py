"""
Comprehensive Fix for CSV File Tracking and Processing

This script fixes the issue where files found in map directories are not properly
tracked in the final count and not processed correctly.
"""
import logging
import re
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

def fix_file_tracking():
    """Fix the file tracking throughout the CSV processor"""
    try:
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.read()
            
        # Fix 1: Ensure map files are tracked properly in the overall count
        # Replace the code around line 270-280 where the final count is calculated
        count_calculation_pattern = r'# Calculate total files found including map directories\s+total_files_found.*?\s+total_found = max\(files_found, map_files_count\)'
        replacement = """# Calculate total files found including map directories
                total_files_found = files_found
                
                # Track all found files comprehensively
                map_files_count = 0
                sftp_files_count = 0
                
                # Count map directory files
                if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files:
                    map_files_count = len(self.all_map_csv_files)
                    logger.info(f"Including {map_files_count} files from map directories in final count")
                
                # Count SFTP files
                if hasattr(self, 'sftp_csv_files_found') and self.sftp_csv_files_found:
                    sftp_files_count = len(self.sftp_csv_files_found)
                    logger.info(f"Including {sftp_files_count} files from SFTP in final count")
                
                # Calculate the maximum found files from all sources
                total_found = max(files_found, map_files_count, sftp_files_count)
                
                # If we found files but processed 0, that indicates a potential issue
                if total_found > 0 and files_processed == 0:
                    logger.warning(f"CRITICAL ISSUE: Found {total_found} files but processed 0. Check file filtering logic.")"""
                
        content = re.sub(count_calculation_pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 2: Make sure that map files are not lost during processing
        # Add code to ensure that if we found files in map directories, they are properly transferred to the main processing variables
        transfer_pattern = r'# If we found CSV files in any map directory\s+if self\.all_map_csv_files:'
        replacement = """# If we found CSV files in any map directory
                            if self.all_map_csv_files:
                                # CRITICAL FIX: Make sure we track these files properly
                                self.found_map_files = True"""
                                
        content = re.sub(transfer_pattern, replacement, content)
        
        # Fix 3: Ensure that files are processed after being found
        # Modify the code that determines if files should be processed to include map files
        process_pattern = r'if not csv_files or len\(csv_files\) == 0:'
        replacement = """if not csv_files or len(csv_files) == 0:
                            # CRITICAL FIX: Try to use map files if we found them but csv_files is empty
                            if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files:
                                logger.info(f"No direct CSV files found, but {len(self.all_map_csv_files)} map CSV files are available. Using those instead.")
                                full_path_csv_files = self.all_map_csv_files
                                csv_files = [os.path.basename(f) for f in self.all_map_csv_files]
                            else:"""
                            
        content = re.sub(process_pattern, replacement, content)
        
        # Fix 4: Update the final warning message to include detailed information about all sources
        warning_pattern = r'logger\.warning\(f"CRITICAL DEBUG: CSV processing completed\. Files Found={total_found}, Files Processed={files_processed}, Events={events_processed}"\)'
        replacement = """logger.warning(f"CRITICAL DEBUG: CSV processing completed. Files Found={total_found} (Map={map_files_count}, SFTP={sftp_files_count}, Regular={files_found}), Files Processed={files_processed}, Events={events_processed}")"""
                            
        content = re.sub(warning_pattern, replacement, content)
        
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.write(content)
            
        logger.info("Successfully fixed file tracking in CSV processor")
        return True
    except Exception as e:
        logger.error(f"Error fixing file tracking: {e}")
        return False

def main():
    """Main function to apply the fix"""
    logger.info("Starting Comprehensive Tracking Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the fix
    if fix_file_tracking():
        logger.info("Successfully applied Comprehensive Tracking Fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply Comprehensive Tracking Fix")
        
if __name__ == "__main__":
    main()