"""
Fix for CSV Searching Conflict

This script fixes the issue where CSV files are found in one part of the code
but then reported as not found in another part, resulting in zero processed files.

The issue is caused by two different code paths searching for CSV files:
1. One path finds the files but doesn't properly communicate the results
2. Another path can't find the files and overrides the first path's results
"""
import os
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File to modify
CSV_PROCESSOR_PATH = "cogs/csv_processor.py"

def find_file_path_and_line(file_path, search_text):
    """Find line number in file containing search text"""
    try:
        with open(file_path, 'r') as f:
            content = f.readlines()
            
        for i, line in enumerate(content):
            if search_text in line:
                return i, content
                
        return -1, content
    except Exception as e:
        logger.error(f"Error searching file: {e}")
        return -1, []

def fix_csv_processor_cog():
    """Fix the CSV processor cog to properly handle found files"""
    try:
        # Look for the problematic line that says "No CSV files found" when files are actually found
        line_num, content = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "No CSV files found in map directories yet, continuing with standard search"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the problematic line")
            return False
            
        # Get indentation
        indent = len(content[line_num]) - len(content[line_num].lstrip())
        spaces = ' ' * indent
        
        # Replace with an improved version
        original_line = content[line_num]
        content[line_num] = f"{spaces}# CRITICAL FIX: We now track CSV files properly through class properties\n"
        content.insert(line_num + 1, f"{spaces}logger.info(f\"Looking for additional CSV files beyond map directories\")\n")
        
        logger.info(f"Fixed 'No CSV files found' message at line {line_num}")
        
        # Find the section where files found in map directories are stored
        line_num, _ = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "all_map_csv_files.extend(map_full_paths)"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the map directory file storage line")
            return False
            
        # Get indentation
        indent = len(content[line_num]) - len(content[line_num].lstrip())
        spaces = ' ' * indent
        
        # Add class property update
        content.insert(line_num + 1, f"{spaces}# CRITICAL FIX: Store found files in class property\n")
        content.insert(line_num + 2, f"{spaces}self.map_csv_files_found.extend([os.path.basename(f) for f in map_full_paths])\n")
        content.insert(line_num + 3, f"{spaces}self.map_csv_full_paths_found.extend(map_full_paths)\n")
        
        logger.info(f"Added class property update at line {line_num}")
        
        # Now fix the final file list construction to prioritize already found files
        line_num, _ = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "# Enhanced list of possible paths to check"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the enhanced paths section")
            return False
            
        # Get indentation
        indent = len(content[line_num]) - len(content[line_num].lstrip())
        spaces = ' ' * indent
        
        # Add prioritization for already found files
        content.insert(line_num, f"{spaces}# CRITICAL FIX: If we already found files in map directories, use those\n")
        content.insert(line_num + 1, f"{spaces}if hasattr(self, 'map_csv_full_paths_found') and self.map_csv_full_paths_found:\n")
        content.insert(line_num + 2, f"{spaces}    logger.info(f\"Using {{len(self.map_csv_full_paths_found)}} CSV files found in map directories\")\n")
        content.insert(line_num + 3, f"{spaces}    full_path_csv_files = self.map_csv_full_paths_found\n")
        content.insert(line_num + 4, f"{spaces}    csv_files = self.map_csv_files_found\n")
        content.insert(line_num + 5, f"{spaces}    # Show a sample of the files we're using\n")
        content.insert(line_num + 6, f"{spaces}    if len(csv_files) > 0:\n")
        content.insert(line_num + 7, f"{spaces}        sample = csv_files[:5] if len(csv_files) > 5 else csv_files\n")
        content.insert(line_num + 8, f"{spaces}        logger.info(f\"Sample CSV files from map directories: {{sample}}\")\n")
        content.insert(line_num + 9, f"{spaces}    # Skip additional searching\n")
        content.insert(line_num + 10, f"{spaces}    found_files = True\n")
        content.insert(line_num + 11, f"{spaces}else:\n")
        
        logger.info(f"Added prioritization for map directory files at line {line_num}")
        
        # Fix the final report to count all files correctly
        line_num, _ = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "CSV processing completed in"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the final report line")
            return False
            
        # Get indentation
        indent = len(content[line_num]) - len(content[line_num].lstrip())
        spaces = ' ' * indent
        
        # Replace the final report
        content[line_num] = f"{spaces}# CRITICAL FIX: Report total counts including map directories\n"
        content.insert(line_num + 1, f"{spaces}total_found = len(csv_files) if csv_files else 0\n")
        content.insert(line_num + 2, f"{spaces}if hasattr(self, 'map_csv_files_found') and self.map_csv_files_found:\n")
        content.insert(line_num + 3, f"{spaces}    total_found = max(total_found, len(self.map_csv_files_found))\n")
        content.insert(line_num + 4, f"{spaces}logger.info(f\"CSV processing completed in {{duration:.2f}} seconds. Processed {{files_processed}} CSV files out of {{total_found}} found, with {{events_processed}} events.\")\n")
        
        logger.info(f"Updated final report at line {line_num}")
        
        # Fix the initialization of the class properties
        line_num, _ = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "def __init__(self, bot):"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the __init__ method")
            return False
            
        # Find the end of the __init__ method
        init_end = line_num
        inner_indent = None
        for i in range(line_num + 1, len(content)):
            line = content[i]
            # Skip empty lines
            if not line.strip():
                continue
                
            # Get the indentation of the first non-empty line after the method declaration
            if inner_indent is None:
                inner_indent = len(line) - len(line.lstrip())
                continue
                
            # Find a line with less indentation than the inner code, which marks the end of the method
            current_indent = len(line) - len(line.lstrip())
            if current_indent < inner_indent:
                init_end = i - 1
                break
        
        # Get proper indentation
        spaces = ' ' * inner_indent
        
        # Add initialization for the class properties
        content.insert(init_end, f"{spaces}# CRITICAL FIX: Initialize trackers for map directories\n")
        content.insert(init_end + 1, f"{spaces}self.map_csv_files_found = []\n")
        content.insert(init_end + 2, f"{spaces}self.map_csv_full_paths_found = []\n")
        content.insert(init_end + 3, f"{spaces}self.found_map_files = False\n")
        
        logger.info(f"Added class property initialization at line {init_end}")
        
        # Write the changes back to the file
        with open(CSV_PROCESSOR_PATH, 'w') as f:
            f.writelines(content)
            
        logger.info("Successfully fixed CSV processor cog")
        return True
    except Exception as e:
        logger.error(f"Error fixing CSV processor cog: {e}")
        return False

def fix_csv_processor_final_output():
    """Fix the misleading final output in CSV processor"""
    try:
        # Create a backup first
        backup_path = f"{CSV_PROCESSOR_PATH}.final.bak"
        with open(CSV_PROCESSOR_PATH, 'r') as src_file:
            content = src_file.read()
            
        with open(backup_path, 'w') as backup_file:
            backup_file.write(content)
            
        logger.info(f"Created backup at {backup_path}")
        
        # Look for the WARNING message
        line_num, content = find_file_path_and_line(
            CSV_PROCESSOR_PATH, 
            "WARNING - CRITICAL DEBUG: CSV processing completed"
        )
        
        if line_num < 0:
            logger.error("Couldn't find the warning message")
            return False
            
        # Get the line and check if our fix needs to be applied
        warning_line = content[line_num]
        
        # If the fix is already applied, skip
        if "self.total_files_found" in warning_line or "total_found" in warning_line:
            logger.info("Fix already applied to warning message")
        else:
            # Get indentation
            indent = len(warning_line) - len(warning_line.lstrip())
            spaces = ' ' * indent
            
            # Replace with improved message
            content[line_num] = f"{spaces}logger.warning(f\"CRITICAL DEBUG: CSV processing completed. Files Found={{total_found}}, Files Processed={{files_processed}}, Events={{events_processed}}\")\n"
            
            logger.info(f"Fixed warning message at line {line_num}")
            
            # Write the changes back to the file
            with open(CSV_PROCESSOR_PATH, 'w') as f:
                f.writelines(content)
                
            logger.info("Successfully fixed CSV processor final output")
            
        return True
    except Exception as e:
        logger.error(f"Error fixing CSV processor final output: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting CSV search conflict fix")
    
    # Fix the CSV processor cog
    if not fix_csv_processor_cog():
        logger.error("Failed to fix CSV processor cog")
        return
        
    # Fix the final output
    if not fix_csv_processor_final_output():
        logger.error("Failed to fix CSV processor final output")
        return
        
    logger.info("All fixes applied successfully. Please restart the bot to apply changes.")

if __name__ == "__main__":
    main()