"""
Direct Tracking Fix for CSV Processing

This script directly modifies specific lines in the CSV processor
to ensure files found in map directories are properly processed.
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

def find_line(content, text):
    """Find the line number for a text pattern"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if text in line:
            return i
    return -1

def fix_file_processing_direct():
    """Apply direct fixes to the CSV processor file without using regex"""
    try:
        # Read the file
        with open(CSV_PROCESSOR_PATH, 'r') as f:
            content = f.readlines()
            
        # Fix 1: Modify the final file count calculation (around line 270-280)
        # Find the start of the block
        start_line = -1
        for i, line in enumerate(content):
            if "# Calculate total files found including map directories" in line:
                start_line = i
                break
                
        if start_line >= 0:
            # Extract indentation
            indentation = len(content[start_line]) - len(content[start_line].lstrip())
            indent = ' ' * indentation
            
            # Replace the entire block with our improved version
            end_line = start_line
            while end_line < len(content) and "total_found = max(files_found, map_files_count)" not in content[end_line]:
                end_line += 1
                
            if end_line < len(content):
                # Create new lines with proper indentation
                new_lines = [
                    f"{indent}# Calculate total files found including map directories\n",
                    f"{indent}total_files_found = files_found\n",
                    f"{indent}\n",
                    f"{indent}# Track all found files comprehensively\n",
                    f"{indent}map_files_count = 0\n",
                    f"{indent}sftp_files_count = 0\n",
                    f"{indent}\n",
                    f"{indent}# Count map directory files\n",
                    f"{indent}if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files:\n",
                    f"{indent}    map_files_count = len(self.all_map_csv_files)\n",
                    f"{indent}    logger.info(f\"Including {{map_files_count}} files from map directories in final count\")\n",
                    f"{indent}\n",
                    f"{indent}# Count SFTP files\n",
                    f"{indent}if hasattr(self, 'sftp_csv_files_found') and self.sftp_csv_files_found:\n",
                    f"{indent}    sftp_files_count = len(self.sftp_csv_files_found)\n",
                    f"{indent}    logger.info(f\"Including {{sftp_files_count}} files from SFTP in final count\")\n",
                    f"{indent}\n",
                    f"{indent}# Calculate the maximum found files from all sources\n",
                    f"{indent}total_found = max(files_found, map_files_count, sftp_files_count)\n",
                    f"{indent}\n",
                    f"{indent}# If we found files but processed 0, that indicates a potential issue\n",
                    f"{indent}if total_found > 0 and files_processed == 0:\n",
                    f"{indent}    logger.warning(f\"CRITICAL ISSUE: Found {{total_found}} files but processed 0. Check file filtering logic.\")\n"
                ]
                
                # Replace the original lines with our new ones
                content[start_line:end_line+1] = new_lines
                
                logger.info(f"Successfully replaced file count calculation at lines {start_line}-{end_line}")
            else:
                logger.warning("Couldn't find the end of the file count calculation block")
        else:
            logger.warning("Couldn't find the start of the file count calculation block")
            
        # Fix 2: Ensure map files are properly tracked
        map_dir_line = -1
        for i, line in enumerate(content):
            if "# If we found CSV files in any map directory" in line:
                map_dir_line = i
                break
                
        if map_dir_line >= 0:
            # Find the next line with "if self.all_map_csv_files:"
            if_line = map_dir_line + 1
            while if_line < len(content) and "if self.all_map_csv_files:" not in content[if_line]:
                if_line += 1
                
            if if_line < len(content):
                # Extract indentation
                indentation = len(content[if_line]) - len(content[if_line].lstrip())
                indent = ' ' * indentation
                
                # Insert our tracking line after this line
                tracking_line = f"{indent}    # CRITICAL FIX: Make sure we track these files properly\n{indent}    self.found_map_files = True\n"
                
                # Insert the tracking line
                content.insert(if_line + 1, tracking_line)
                
                logger.info(f"Successfully added map file tracking at line {if_line + 1}")
            else:
                logger.warning("Couldn't find the 'if self.all_map_csv_files:' line")
        else:
            logger.warning("Couldn't find the map directory check section")
            
        # Fix 3: Ensure that files are processed after being found
        process_line = -1
        for i, line in enumerate(content):
            if "if not csv_files or len(csv_files) == 0:" in line:
                process_line = i
                break
                
        if process_line >= 0:
            # Extract indentation
            indentation = len(content[process_line]) - len(content[process_line].lstrip())
            indent = ' ' * indentation
            
            # Create the new lines
            new_lines = [
                f"{indent}if not csv_files or len(csv_files) == 0:\n",
                f"{indent}    # CRITICAL FIX: Try to use map files if we found them but csv_files is empty\n",
                f"{indent}    if hasattr(self, 'all_map_csv_files') and self.all_map_csv_files:\n",
                f"{indent}        logger.info(f\"No direct CSV files found, but {{len(self.all_map_csv_files)}} map CSV files are available. Using those instead.\")\n",
                f"{indent}        full_path_csv_files = self.all_map_csv_files\n",
                f"{indent}        csv_files = [os.path.basename(f) for f in self.all_map_csv_files]\n",
                f"{indent}    else:\n"
            ]
            
            # Replace the original line with our new lines
            content[process_line:process_line+1] = new_lines
            
            logger.info(f"Successfully added file processing fallback at line {process_line}")
        else:
            logger.warning("Couldn't find the CSV files check line")
            
        # Fix 4: Update the final warning message
        warning_line = -1
        for i, line in enumerate(content):
            if 'logger.warning(f"CRITICAL DEBUG: CSV processing completed' in line and "Files Found=" in line:
                warning_line = i
                break
                
        if warning_line >= 0:
            # Extract indentation
            indentation = len(content[warning_line]) - len(content[warning_line].lstrip())
            indent = ' ' * indentation
            
            # Replace with our improved warning
            content[warning_line] = f'{indent}logger.warning(f"CRITICAL DEBUG: CSV processing completed. Files Found={{total_found}} (Map={{map_files_count}}, SFTP={{sftp_files_count}}, Regular={{files_found}}), Files Processed={{files_processed}}, Events={{events_processed}}")\n'
            
            logger.info(f"Successfully updated warning message at line {warning_line}")
        else:
            logger.warning("Couldn't find the warning message line")
            
        # Write the modified content back
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully applied direct file processing fixes")
        return True
    except Exception as e:
        logger.error(f"Error applying direct file processing fixes: {e}")
        return False

def main():
    """Main function to apply the direct fix"""
    logger.info("Starting Direct Tracking Fix")
    
    # Create a backup
    if not create_backup():
        logger.error("Failed to create backup, aborting")
        return
        
    # Apply the direct fix
    if fix_file_processing_direct():
        logger.info("Successfully applied Direct Tracking Fix. Please restart the bot to see the changes.")
    else:
        logger.error("Failed to apply Direct Tracking Fix")
        
if __name__ == "__main__":
    main()