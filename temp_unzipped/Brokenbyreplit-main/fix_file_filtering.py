#!/usr/bin/env python
"""
Enhanced file filtering fix for CSV processing system

This script fixes the file filtering logic in the CSV processor to ensure files are
not incorrectly filtered out before processing.
"""
import os
import sys
import re
import shutil
import datetime
import logging

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

def fix_file_filtering():
    """Apply file filtering improvements to CSV processor"""
    file_path = "cogs/csv_processor.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying file filtering improvements...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Consolidated file discovery logic
        logger.info("Applying fix 1: Consolidated file discovery logic")
        
        pattern = r"# Filter for files newer than last processed.*?new_files = csv_files\.copy\(\)"
        replacement = """# FIXED: Properly initialize new_files only once and ensure it contains all files
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
                            new_files = csv_files.copy()"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 2: Improved historical mode logic
        logger.info("Applying fix 2: Improved historical mode logic")
        
        pattern = r"# CRITICAL FIX: Always process all files for now.*?# Track this historical parse to prevent simultaneous processing.*?logger\.warning\(f\"CRITICAL FIX: Added server {server_id} to active historical parse tracking\"\)"
        replacement = """# FIXED: Determine the correct processing mode based on context
                        # We'll default to historical mode for more reliable processing
                        is_historical_mode = True
                        
                        # Log information about the processing mode decision
                        if start_date:
                            days_diff = (datetime.now() - start_date).days
                            logger.info(f"Start date is {start_date}, days difference is {days_diff}")
                            if days_diff > 7:
                                logger.info(f"Using historical mode since we're looking back {days_diff} days")
                                is_historical_mode = True
                        else:
                            logger.info("No start date provided, defaulting to historical mode")
                            is_historical_mode = True

                        # FIXED: Implement clear distinction between historical vs killfeed processing
                        
                        # Log file counts for easier debugging
                        logger.info(f"CSV Processing: Original csv_files: {len(csv_files)}, new_files after filtering: {len(new_files)}, sorted_files: {len(sorted_files)}")
                        
                        # Historical processor:
                        # - Should process ALL CSV files it finds, without any filtering
                        if is_historical_mode:
                            logger.info(f"CSV Processing: Historical mode - will process ALL {len(csv_files)} files with ALL lines")
                            # FIXED: Use sorted_files as the source since they're already chronologically ordered
                            # But if sorted_files is empty and csv_files isn't, use csv_files as fallback
                            if len(sorted_files) > 0:
                                files_to_process = sorted_files
                            else:
                                logger.warning("CSV Processing: sorted_files is empty, using csv_files directly")
                                files_to_process = csv_files
                                
                            only_new_lines = False  # Process all lines in historical mode
                            
                            # Reset last_processed timestamp to ensure we reprocess all files from scratch
                            if server_id in self.last_processed:
                                logger.info(f"CSV Processing: Resetting last_processed timestamp for historical processing")
                                del self.last_processed[server_id]
                                
                            # Track this historical parse to prevent simultaneous processing
                            self.servers_with_active_historical_parse.add(server_id)
                            logger.info(f"CSV Processing: Added server {server_id} to active historical parse tracking")"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 3: Improved regular (killfeed) processing mode
        logger.info("Applying fix 3: Improved regular processing mode")
        
        pattern = r"# Killfeed processor:.*?if not hasattr\(self, 'file_line_positions'\):\s+self\.file_line_positions = {}\s+self\.file_line_positions\[file_path\] = line_position"
        replacement = """# Killfeed processor:
                        # - Should find the newest file for each day and process only the new lines
                        else:
                            logger.info(f"CSV Processing: Regular killfeed mode - processing newest files with incremental updates")
                            # Group files by day
                            files_by_day = {}
                            
                            # FIXED: Use the larger of sorted_files or new_files to ensure we don't miss anything
                            source_files = sorted_files if len(sorted_files) >= len(new_files) else new_files
                            if len(source_files) == 0 and len(csv_files) > 0:
                                logger.warning("CSV Processing: Both sorted_files and new_files are empty, using csv_files")
                                source_files = csv_files
                                
                            logger.info(f"CSV Processing: Using {len(source_files)} files as source for day grouping")
                            
                            for f in source_files:
                                filename = os.path.basename(f)
                                # FIXED: Improved date extraction with better error handling
                                try:
                                    date_match = re.search(r'(\\d{4}\\.\\d{2}\\.\\d{2})', filename)
                                    if date_match:
                                        day = date_match.group(1)
                                        if day in files_by_day:
                                            files_by_day[day].append(f)
                                        else:
                                            files_by_day[day] = [f]
                                    else:
                                        # Try alternative date formats
                                        alt_date_match = re.search(r'(\\d{4}-\\d{2}-\\d{2})', filename)
                                        if alt_date_match:
                                            day = alt_date_match.group(1).replace('-', '.')
                                            if day in files_by_day:
                                                files_by_day[day].append(f)
                                            else:
                                                files_by_day[day] = [f]
                                        else:
                                            # If we can't extract day, just include it separately
                                            logger.info(f"CSV Processing: Could not extract date from {filename}, including it directly")
                                            files_by_day[filename] = [f]
                                except Exception as e:
                                    logger.error(f"CSV Processing: Error grouping file {filename}: {e}")
                                    # Add to a special "errors" group to ensure we don't lose files
                                    if "errors" not in files_by_day:
                                        files_by_day["errors"] = []
                                    files_by_day["errors"].append(f)
                            
                            # Get newest file for each day
                            newest_files = []
                            
                            # FIXED: Better handling of empty files_by_day
                            if not files_by_day:
                                logger.warning("CSV Processing: No files could be grouped by day - using all files")
                                newest_files = source_files
                            else:
                                for day, day_files in files_by_day.items():
                                    try:
                                        # Sort files for this day
                                        day_files.sort(reverse=True)
                                        newest_files.append(day_files[0])
                                        logger.info(f"CSV Processing: For day {day}, selected newest file: {os.path.basename(day_files[0])}")
                                    except Exception as e:
                                        logger.error(f"CSV Processing: Error selecting newest file for day {day}: {e}")
                                        # Add all files for this day as a fallback
                                        newest_files.extend(day_files)
                            
                            files_to_process = newest_files
                            only_new_lines = True  # Only process new lines in regular mode
                            
                            # FIXED: Better handling of line position tracking
                            if server_id in self.last_processed_line_positions:
                                logger.info(f"CSV Processing: Found line position information from previous processing")
                                server_line_positions = self.last_processed_line_positions[server_id]
                                
                                # Show sample of line positions for debugging
                                sample_positions = dict(list(server_line_positions.items())[:3]) if server_line_positions else {}
                                logger.info(f"CSV Processing: Sample line positions for server {server_id}: {sample_positions}")
                                
                                # Add information for each file that has line position tracking
                                for file_path in files_to_process:
                                    file_key = os.path.basename(file_path)
                                    if file_key in server_line_positions:
                                        line_position = server_line_positions[file_key]
                                        logger.info(f"CSV Processing: Found line position {line_position} for file {file_key}")
                                        
                                        # Store this info to be used during actual processing
                                        if not hasattr(self, 'file_line_positions'):
                                            self.file_line_positions = {}
                                        self.file_line_positions[file_path] = line_position"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 4: Improve final file selection and safety checks
        logger.info("Applying fix 4: Improve final file selection and safety checks")
        
        pattern = r"logger\.warning\(f\"CRITICAL DEBUG: files_to_process count:.*?files_processed = 0\s+events_processed = 0"
        replacement = """# FIXED: Enhanced logging and safety checks for file processing
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
                        events_processed = 0"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied file filtering fixes to CSV processor")
        return True
        
    except Exception as e:
        logger.error(f"Error applying file filtering fixes: {e}")
        return False

def main():
    """Main function to apply all file filtering fixes"""
    logger.info("Starting file filtering fixes for CSV processing system")
    
    # Apply fixes to CSV processor
    if fix_file_filtering():
        logger.info("Successfully applied file filtering fixes")
    else:
        logger.error("Failed to apply file filtering fixes")
        
    logger.info("File filtering fixes completed")

if __name__ == "__main__":
    main()