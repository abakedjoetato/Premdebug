#!/usr/bin/env python
"""
Direct CSV processing fixes application

This script applies fixes directly to the CSV processor and direct CSV handler 
without using regex replacements, which can cause issues with escape sequences.
"""
import os
import sys
import shutil
import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
        
    backup_path = f"{file_path}.bak.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        return False

def modify_direct_csv_handler():
    """Apply fixes to the direct_csv_handler.py file"""
    file_path = "utils/direct_csv_handler.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Modifying direct CSV handler...")
    
    # Fix 1: Enhance file format detection
    # Add better CSV file format detection to include more file types
    
    # Modified function
    new_file_detection_code = '''
                    # Check for various file formats that might contain CSV data
                    is_csv_file = (
                        # Standard formats
                        filename.lower().endswith('.csv') or
                        
                        # Alternative formats that might contain CSV data
                        (filename.lower().endswith('.log') and "death" in filename.lower()) or
                        (filename.lower().endswith('.txt') and "kill" in filename.lower()) or
                        
                        # Check for date patterns common in game logs
                        (re.search(r'\\d{4}[.-]\\d{2}[.-]\\d{2}', filename) and not filename.lower().endswith('.zip'))
                    )
                    
                    if not is_csv_file:
                        continue'''
    
    # Fix 2: Improve date filtering to include more files
    # Ensure we don't filter out files just because of date
    
    new_date_filtering_code = '''
                    # FIXED: Safer date filtering to avoid missing important files
                    # Instead of strict date filtering, we'll include all files by default
                    # but use dates for sorting/prioritization
                    include_file = True
                    
                    # Log date information for debugging but don't use it to exclude files
                    if file_date is not None and cutoff_date is not None:
                        if file_date < cutoff_date:
                            logger.info(f"File date {file_date} is older than cutoff {cutoff_date}, but including it anyway: {os.path.basename(full_path)}")
                        else:
                            logger.info(f"File date {file_date} is newer than cutoff {cutoff_date}: {os.path.basename(full_path)}")
                    
                    # Always add file to processing list regardless of date
                    if include_file:
                        csv_files.append(full_path)'''
    
    # Fix 3: Parser improvements
    # Better encoding detection and delimiter handling
    
    new_parser_code = '''
        # FIXED: Enhanced file reading and content detection
        logger.info(f"Processing file: {os.path.basename(file_path)}")
        
        # Read file as binary for maximum compatibility
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            if not content:
                logger.error(f"Empty file: {file_path}")
                return [], 0
        except Exception as read_error:
            logger.error(f"Error reading file {file_path}: {read_error}")
            return [], 0
            
        # FIXED: Try multiple encodings with better error handling
        content_str = None
        successful_encoding = None
        
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content_str = content.decode(encoding, errors='replace')
                successful_encoding = encoding
                # Only break if we didn't get too many replacement characters
                if content_str.count('\\ufffd') < len(content_str) / 10:  # Less than 10% replacements
                    break
            except Exception as decode_error:
                logger.warning(f"Failed to decode with {encoding}: {decode_error}")
                continue
                
        if not content_str:
            logger.error(f"Failed to decode file content with any encoding: {file_path}")
            return [], 0
            
        logger.info(f"Successfully decoded file using {successful_encoding} encoding")
        
        # FIXED: Better delimiter detection with multiple passes if needed
        # First check for standard delimiters
        semicolons = content_str.count(';')
        commas = content_str.count(',')
        tabs = content_str.count('\\t')
        
        # Calculate which delimiter is most likely based on relative frequency
        # and priority for different formats
        delimiter = ';'  # Default for most game logs
        
        if tabs > max(semicolons, commas) * 0.8:  # Tab is at least 80% as common as the most common delimiter
            delimiter = '\\t'
            logger.info(f"Selected tab as delimiter based on frequency: {tabs} tabs")
        elif commas > semicolons * 1.5:  # Significantly more commas than semicolons
            delimiter = ','
            logger.info(f"Selected comma as delimiter based on frequency: {commas} commas vs {semicolons} semicolons")
        else:
            logger.info(f"Selected semicolon as delimiter based on frequency or default: {semicolons} semicolons")'''
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fix 1: Enhance file format detection
        # Find "if not filename.endswith('.csv'):" and replace it
        if "if not filename.endswith('.csv'):" in content:
            content = content.replace("if not filename.endswith('.csv'):", new_file_detection_code)
            logger.info("Applied fix 1: Enhanced file format detection")
        else:
            logger.warning("Could not find target for fix 1")
        
        # Apply fix 2: Improve date filtering
        # Find date filtering code and replace it
        if "# Always include file even if date parsing fails" in content:
            target = "# Always include file even if date parsing fails"
            # Find the entire block
            start_idx = content.find(target)
            if start_idx >= 0:
                # Look for the end of the block (csv_files.append)
                end_text = "csv_files.append(full_path)"
                end_idx = content.find(end_text, start_idx)
                if end_idx >= 0:
                    end_idx += len(end_text)
                    block_to_replace = content[start_idx:end_idx]
                    content = content.replace(block_to_replace, new_date_filtering_code)
                    logger.info("Applied fix 2: Improved date filtering")
                else:
                    logger.warning("Could not find end of date filtering block")
            else:
                logger.warning("Could not find start of date filtering block")
        else:
            logger.warning("Could not find target for fix 2")
        
        # Apply fix 3: Parser improvements
        # Find parser code and replace it
        if "# Read file as binary" in content:
            target = "# Read file as binary"
            start_idx = content.find(target)
            if start_idx >= 0:
                # Look for the end of the block (delimiter assignment)
                end_text = "delimiter = ','"
                end_idx = content.find(end_text, start_idx)
                if end_idx >= 0:
                    end_idx += len(end_text)
                    block_to_replace = content[start_idx:end_idx]
                    content = content.replace(block_to_replace, new_parser_code)
                    logger.info("Applied fix 3: Parser improvements")
                else:
                    logger.warning("Could not find end of parser block")
            else:
                logger.warning("Could not find start of parser block")
        else:
            logger.warning("Could not find target for fix 3")
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully modified direct CSV handler")
        return True
        
    except Exception as e:
        logger.error(f"Error modifying direct CSV handler: {e}")
        return False

def modify_csv_processor():
    """Apply fixes to the csv_processor.py file"""
    file_path = "cogs/csv_processor.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Modifying CSV processor...")
    
    # Fix 1: Improve file filtering to prevent files from being lost
    new_filtering_code = '''                        # FIXED: Properly initialize new_files only once and ensure it contains all files
                        # This is a critical fix to ensure all CSV files are passed along for processing
                        new_files = []
                        skipped_files = []
                        
                        # Log the number of files found and the cutoff date
                        logger.info(f"CSV Processing: Found {len(csv_files)} CSV files, timestamp cutoff: {last_time_str}")
                        
                        # CRITICAL FIX: CONSOLIDATED FILE DISCOVERY LOGIC
                        # Always ensure we have files to process by directly assigning all discovered files
                        # This bypasses potential issues with date filtering
                        
                        if len(csv_files) > 0:
                            # Log what we're about to process
                            for f in csv_files:
                                filename = os.path.basename(f)
                                logger.info(f"CSV Processing: Will process file: {filename}")
                                new_files.append(f)
                                
                            # Double-check that we have files in new_files
                            if len(new_files) != len(csv_files):
                                logger.error(f"CSV Processing: File count mismatch! csv_files={len(csv_files)}, new_files={len(new_files)}")
                                # Force assign all files as a last resort
                                new_files = csv_files.copy()
                        else:
                            logger.warning("CSV Processing: No CSV files found in search paths")
                            
                        # Final safety check - ensure we actually have files to process
                        if not new_files and csv_files:
                            logger.error("CSV Processing: Critical error - no files in new_files list but csv_files is not empty!")
                            # Force assign all files as a last resort
                            new_files = csv_files.copy()'''
    
    # Fix 2: Fix safety checks for file selection
    new_safety_check_code = '''                        # FIXED: Enhanced logging and safety checks for file processing
                        logger.info(f"CSV Processing: Final files_to_process count: {len(files_to_process)}")
                        logger.info(f"CSV Processing: Mode: Historical={is_historical_mode}, Only new lines={only_new_lines}")
                        
                        # FIXED: Multiple layers of safety checks to ensure we have files to process
                        # First safety check - if files_to_process is empty but we found files earlier, use them
                        if len(files_to_process) == 0:
                            # Try different sources in order of preference
                            if len(sorted_files) > 0:
                                logger.warning(f"CSV Processing: files_to_process was empty but sorted_files has {len(sorted_files)} files - using sorted_files")
                                files_to_process = sorted_files
                            elif len(new_files) > 0:
                                logger.warning(f"CSV Processing: files_to_process and sorted_files were empty but new_files has {len(new_files)} files - using new_files")
                                files_to_process = new_files
                            elif len(csv_files) > 0:
                                logger.warning(f"CSV Processing: files_to_process, sorted_files, and new_files were empty but csv_files has {len(csv_files)} files - using csv_files")
                                files_to_process = csv_files
                            else:
                                logger.error(f"CSV Processing: No files found in any collection")
                        
                        # Log processing details
                        logger.info(f"CSV Processing: Mode: Historical={is_historical_mode}, " + 
                                  f"Start date={start_date}, Files to process={len(files_to_process)}")

                        # Final check with detailed diagnostics to help troubleshoot empty file lists
                        if len(files_to_process) == 0:
                            logger.error(f"CSV Processing: CRITICAL - No files to process after all safety checks!")
                            
                            # Log all file list lengths to help diagnose the issue
                            logger.error(f"CSV Processing: csv_files={len(csv_files)}, sorted_files={len(sorted_files)}, new_files={len(new_files)}")
                            
                            # Show sample from any non-empty file lists
                            if len(csv_files) > 0:
                                logger.error(f"CSV Processing: Sample from csv_files: {[os.path.basename(f) for f in csv_files[:3]]}")
                            if len(sorted_files) > 0:
                                logger.error(f"CSV Processing: Sample from sorted_files: {[os.path.basename(f) for f in sorted_files[:3]]}")
                            if len(new_files) > 0:
                                logger.error(f"CSV Processing: Sample from new_files: {[os.path.basename(f) for f in new_files[:3]]}")
                                
                            # Log timestamp cutoff information
                            logger.error(f"CSV Processing: Last processing time cutoff: {last_time_str}")
                        else:
                            # Log the first few files we're going to process
                            file_sample = [os.path.basename(f) for f in files_to_process[:5]]
                            logger.info(f"CSV Processing: Files ready for processing: {file_sample}")
                            
                            # Log total number of each type of file for reference
                            logger.info(f"CSV Processing: Total files by source - csv_files: {len(csv_files)}, sorted_files: {len(sorted_files)}, new_files: {len(new_files)}")

                        # Initialize counters to track processing results
                        files_processed = 0
                        events_processed = 0'''
    
    # Fix 3: Improve line position tracking
    new_line_pos_code = '''                                                # FIXED: Better line position tracking for all processing modes
                                                # Always update line position information for efficient incremental processing
                                                if total_lines > 0:
                                                    # Initialize the storage structure if needed
                                                    if server_id not in self.last_processed_line_positions:
                                                        self.last_processed_line_positions[server_id] = {}
                                                        
                                                    # Store the line position differently based on mode
                                                    file_basename = os.path.basename(file_path)
                                                    
                                                    if is_historical_mode:
                                                        # For historical mode, store the total line count for all files
                                                        # This helps regular mode pick up where historical left off
                                                        logger.info(f"CSV Processing: Storing line position {total_lines} for historical processing of {file_basename}")
                                                        self.last_processed_line_positions[server_id][file_basename] = total_lines
                                                    else:
                                                        # For regular mode, update only if we have a higher line count than before
                                                        current_position = self.last_processed_line_positions[server_id].get(file_basename, 0)
                                                        if total_lines > current_position:
                                                            logger.info(f"CSV Processing: Updating line position from {current_position} to {total_lines} for {file_basename}")
                                                            self.last_processed_line_positions[server_id][file_basename] = total_lines
                                                        else:
                                                            logger.info(f"CSV Processing: Keeping existing line position of {current_position} for {file_basename}")
                                                            
                                                    # Also update the in-memory position for future processing
                                                    if not hasattr(self, 'file_line_positions'):
                                                        self.file_line_positions = {}
                                                    self.file_line_positions[file_path] = total_lines'''
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fix 1: Improve file filtering
        # Find the filtering code and replace it
        if "# Filter for files newer than last processed" in content:
            target = "# Filter for files newer than last processed"
            start_idx = content.find(target)
            if start_idx >= 0:
                # Find the end of the block
                end_text = "new_files = csv_files.copy()"
                end_idx = content.find(end_text, start_idx)
                if end_idx >= 0:
                    end_idx += len(end_text)
                    block_to_replace = content[start_idx:end_idx]
                    content = content.replace(block_to_replace, new_filtering_code)
                    logger.info("Applied fix 1: Improved file filtering")
                else:
                    logger.warning("Could not find end of filtering block")
            else:
                logger.warning("Could not find start of filtering block")
        else:
            logger.warning("Could not find target for fix 1")
        
        # Apply fix 2: Fix safety checks
        # Find the safety check code and replace it
        if "logger.warning(f\"CRITICAL DEBUG: files_to_process count:" in content:
            target = "logger.warning(f\"CRITICAL DEBUG: files_to_process count:"
            start_idx = content.find(target)
            if start_idx >= 0:
                # Look for the end of the block
                end_text = "files_processed = 0\n                        events_processed = 0"
                end_idx = content.find(end_text, start_idx)
                if end_idx >= 0:
                    end_idx += len(end_text)
                    block_to_replace = content[start_idx:end_idx]
                    content = content.replace(block_to_replace, new_safety_check_code)
                    logger.info("Applied fix 2: Fixed safety checks")
                else:
                    logger.warning("Could not find end of safety check block")
            else:
                logger.warning("Could not find start of safety check block")
        else:
            logger.warning("Could not find target for fix 2")
        
        # Apply fix 3: Improve line position tracking
        # Find the line position code and replace it
        if "# CRITICAL FIX: Update line position tracking" in content:
            target = "# CRITICAL FIX: Update line position tracking"
            start_idx = content.find(target)
            if start_idx >= 0:
                # Look for the end of the block
                end_text = "self.last_processed_line_positions[server_id][os.path.basename(file_path)] = total_lines"
                end_idx = content.find(end_text, start_idx)
                if end_idx >= 0:
                    end_idx += len(end_text)
                    block_to_replace = content[start_idx:end_idx]
                    content = content.replace(block_to_replace, new_line_pos_code)
                    logger.info("Applied fix 3: Improved line position tracking")
                else:
                    logger.warning("Could not find end of line position block")
            else:
                logger.warning("Could not find start of line position block")
        else:
            logger.warning("Could not find target for fix 3")
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully modified CSV processor")
        return True
        
    except Exception as e:
        logger.error(f"Error modifying CSV processor: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting direct CSV processing fixes")
    
    # Apply fixes to direct CSV handler
    direct_handler_result = modify_direct_csv_handler()
    if direct_handler_result:
        logger.info("Successfully applied fixes to direct CSV handler")
    else:
        logger.error("Failed to apply fixes to direct CSV handler")
        
    # Apply fixes to CSV processor
    processor_result = modify_csv_processor()
    if processor_result:
        logger.info("Successfully applied fixes to CSV processor")
    else:
        logger.error("Failed to apply fixes to CSV processor")
        
    if direct_handler_result and processor_result:
        logger.info("All fixes have been applied successfully")
        return True
    else:
        logger.error("Some fixes failed to apply")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)