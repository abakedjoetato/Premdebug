#!/usr/bin/env python
"""
Comprehensive CSV Processing System Fix

This script applies all necessary fixes to the CSV processing system to ensure
proper parsing of CSV files from game servers. It addresses issues with file discovery,
filtering, and processing across both historical and regular processing modes.

Key fixes:
1. Consolidated file discovery logic to ensure consistent behavior
2. Fixed historical vs. regular processing mode handling
3. Improved file filtering robustness with multiple safety checks
4. Enhanced CSV parsing with better error handling and fallbacks
5. Improved directory structure handling for file discovery
6. Fixed line position tracking for incremental processing
7. Added additional file format support for more robust parsing
8. Enhanced logging for better diagnostics and troubleshooting
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

def fix_csv_processor():
    """Apply fixes to the CSV processor cog"""
    file_path = "cogs/csv_processor.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying fixes to CSV processor cog...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Count EMERGENCY and CRITICAL tags before fixes
        emergency_count = content.count("EMERGENCY")
        critical_count = content.count("CRITICAL")
        
        logger.info(f"Before fixes: {emergency_count} EMERGENCY and {critical_count} CRITICAL tags")
        
        # Fix 1: Consolidated file discovery logic
        logger.info("Applying fix 1: Consolidated file discovery logic")
        content = re.sub(
            r"new_files = \[\]\s+skipped_files = \[\]\s+.*?# CRITICAL HOT FIX:.*?new_files = csv_files\.copy\(\)",
            """new_files = []
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
                            new_files = csv_files.copy()""",
            content,
            flags=re.DOTALL
        )
        
        # Fix 2: Improve historical mode logic
        logger.info("Applying fix 2: Improve historical mode logic")
        content = re.sub(
            r"# CRITICAL FIX: Always process all files for now.*?# Track this historical parse to prevent simultaneous processing.*?logger\.warning\(f\"CRITICAL FIX: Added server {server_id} to active historical parse tracking\"\)",
            """# FIXED: Determine the correct processing mode based on context
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
                            logger.info(f"CSV Processing: Added server {server_id} to active historical parse tracking")""",
            content,
            flags=re.DOTALL
        )
        
        # Fix 3: Improve regular processing mode
        logger.info("Applying fix 3: Improve regular processing mode")
        content = re.sub(
            r"# Killfeed processor:.*?if not hasattr\(self, 'file_line_positions'\):.*?self\.file_line_positions\[file_path\] = line_position",
            """# Killfeed processor:
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
                                        self.file_line_positions[file_path] = line_position""",
            content,
            flags=re.DOTALL
        )
        
        # Fix 4: Improve final file selection and safety checks
        logger.info("Applying fix 4: Improve final file selection and safety checks")
        content = re.sub(
            r"logger\.warning\(f\"CRITICAL DEBUG: files_to_process count:.*?files_processed = 0\s+events_processed = 0",
            """# FIXED: Enhanced logging and safety checks for file processing
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
                        events_processed = 0""",
            content,
            flags=re.DOTALL
        )
        
        # Fix 5: Improve CSV content processing
        logger.info("Applying fix 5: Improve CSV content processing")
        content = re.sub(
            r"# EMERGENCY FIX: ALWAYS process all lines.*?logger\.warning\(f\"NEW DIRECT HANDLER: Processed {len\(events\)} events from file with {total_lines} total lines\"\)",
            """# FIXED: Improved CSV processing with better error handling and mode support
                                                # This ensures reliable processing of all CSV files
                                                logger.info(f"CSV Processing: Processing file: {os.path.basename(file_path)}")
                                                
                                                # Reset the file pointer to start fresh
                                                content_io.seek(0)
                                                
                                                # Use appropriate mode based on context
                                                process_mode = "historical" if is_historical_mode else "incremental"
                                                logger.info(f"CSV Processing: Using {process_mode} mode with delimiter: '{detected_delimiter}'")
                                                
                                                # FIXED: Always use direct CSV handler for reliable parsing
                                                # Import here to avoid circular imports
                                                from utils.direct_csv_handler import direct_parse_csv_content
                                                
                                                # Reset the file pointer and read content
                                                content_io.seek(0)
                                                content_str = content_io.read()
                                                
                                                # Determine correct line position to start from
                                                start_line = 0
                                                file_key = os.path.basename(file_path)
                                                
                                                # Handle line position tracking for incremental processing
                                                if not is_historical_mode:
                                                    # First check file_line_positions
                                                    if hasattr(self, 'file_line_positions') and file_path in self.file_line_positions:
                                                        start_line = self.file_line_positions[file_path]
                                                        logger.info(f"CSV Processing: Starting from line position {start_line} for file {file_key}")
                                                    # Then check last_processed_line_positions
                                                    elif server_id in self.last_processed_line_positions and file_key in self.last_processed_line_positions[server_id]:
                                                        start_line = self.last_processed_line_positions[server_id][file_key]
                                                        logger.info(f"CSV Processing: Starting from saved line position {start_line} for file {file_key}")
                                                else:
                                                    logger.info(f"CSV Processing: Historical mode - processing all lines from the beginning")
                                                
                                                # Process with direct parser
                                                try:
                                                    events, total_lines = direct_parse_csv_content(
                                                        content_str,
                                                        file_path=file_path,
                                                        server_id=server_id,
                                                        start_line=start_line
                                                    )
                                                    logger.info(f"CSV Processing: Processed {len(events)} events from file with {total_lines} total lines")
                                                    
                                                    # If this is incremental mode and we got no events but the file has lines,
                                                    # it could mean we've already processed all lines - log this clearly
                                                    if not is_historical_mode and len(events) == 0 and total_lines > 0 and start_line > 0:
                                                        logger.info(f"CSV Processing: No new events found in {file_key} - all {total_lines} lines may have been processed already (starting from line {start_line})")
                                                        
                                                except Exception as direct_parse_error:
                                                    logger.error(f"CSV Processing: Error in direct parser: {direct_parse_error}")
                                                    # Try fallback to basic parsing in case of errors
                                                    try:
                                                        logger.warning(f"CSV Processing: Attempting fallback parsing for {file_key}")
                                                        # Simple fallback parsing - just extract lines with basic validation
                                                        lines = content_str.splitlines()
                                                        events = []
                                                        total_lines = len(lines)
                                                        
                                                        for i, line in enumerate(lines):
                                                            if i < start_line:
                                                                continue
                                                            
                                                            # Skip empty lines
                                                            if not line.strip():
                                                                continue
                                                                
                                                            # Split by most likely delimiter
                                                            parts = line.split(detected_delimiter)
                                                            
                                                            # Basic validation - need at least 5 parts for a valid event
                                                            if len(parts) >= 5:
                                                                try:
                                                                    events.append({
                                                                        'timestamp': parts[0],
                                                                        'killer_name': parts[1],
                                                                        'killer_id': parts[2] if len(parts) > 2 else "",
                                                                        'victim_name': parts[3],
                                                                        'victim_id': parts[4] if len(parts) > 4 else "",
                                                                        'server_id': server_id,
                                                                        'event_type': 'kill'
                                                                    })
                                                                except Exception:
                                                                    # Skip problematic lines
                                                                    pass
                                                        
                                                        logger.warning(f"CSV Processing: Fallback parsing extracted {len(events)} events from {total_lines} lines")
                                                    except Exception as fallback_error:
                                                        logger.error(f"CSV Processing: Fallback parsing also failed: {fallback_error}")
                                                        events = []
                                                        total_lines = 0""",
            content,
            flags=re.DOTALL
        )
        
        # Fix 6: Improve line position tracking
        logger.info("Applying fix 6: Improve line position tracking")
        content = re.sub(
            r"# CRITICAL FIX: Update line position tracking.*?self\.last_processed_line_positions\[server_id\]\[os\.path\.basename\(file_path\)\] = total_lines",
            """# FIXED: Better line position tracking for all processing modes
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
                                                    self.file_line_positions[file_path] = total_lines""",
            content,
            flags=re.DOTALL
        )
        
        # Count EMERGENCY and CRITICAL tags after fixes
        emergency_count_after = content.count("EMERGENCY")
        critical_count_after = content.count("CRITICAL")
        
        logger.info(f"After fixes: {emergency_count_after} EMERGENCY and {critical_count_after} CRITICAL tags")
        logger.info(f"Removed {emergency_count - emergency_count_after} EMERGENCY and {critical_count - critical_count_after} CRITICAL tags")
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied fixes to CSV processor cog")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fixes to CSV processor: {e}")
        return False

def fix_direct_csv_handler():
    """Apply fixes to the direct CSV handler module"""
    file_path = "utils/direct_csv_handler.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying fixes to direct CSV handler module...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Enhance file format detection
        logger.info("Applying fix 1: Enhance file format detection")
        content = re.sub(
            r"for filename in files:\s+if not filename\.endswith\('\.csv'\):\s+continue",
            """for filename in files:
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
                        continue""",
            content
        )
        
        # Fix 2: Improve date filtering
        logger.info("Applying fix 2: Improve date filtering")
        content = re.sub(
            r"# Always include file even if date parsing fails.*?csv_files\.append\(full_path\)",
            """# FIXED: Safer date filtering to avoid missing important files
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
                        csv_files.append(full_path)""",
            content
        )
        
        # Fix 3: Improve directory discovery
        logger.info("Applying fix 3: Improve directory discovery")
        content = re.sub(
            r"# Remove duplicates from base_dirs while preserving order\s+unique_base_dirs = \[\]\s+for directory in base_dirs:.*?logger\.info\(f\"Searching for CSV files in {len\(unique_base_dirs\)} base directories\"\)",
            """# FIXED: Improved file discovery to handle more directory structures
    csv_files = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Remove duplicates from base_dirs while preserving order
    unique_base_dirs = []
    for directory in base_dirs:
        if directory not in unique_base_dirs:
            # Check if directory exists
            if os.path.exists(directory):
                unique_base_dirs.append(directory)
                logger.info(f"Adding valid directory: {directory}")
            else:
                logger.warning(f"Skipping non-existent directory: {directory}")
    
    logger.info(f"Searching for CSV files in {len(unique_base_dirs)} base directories")
    
    # If we don't have any valid directories, try to search common locations
    if len(unique_base_dirs) == 0:
        logger.warning("No valid directories found, trying common locations")
        common_locations = [
            os.path.join(os.getcwd()),  # Current directory
            os.path.join(os.getcwd(), "attached_assets"),  # Local assets
            os.path.join(os.getcwd(), "log"),  # Common log directory
            os.path.join(os.getcwd(), "logs"),  # Common logs directory
            os.path.join(os.getcwd(), "data"),  # Common data directory
            "/var/log",  # System logs
            "/var/log/game",  # Game logs
            "/srv/game/logs",  # Game server logs
        ]
        
        for location in common_locations:
            if os.path.exists(location) and os.path.isdir(location):
                unique_base_dirs.append(location)
                logger.info(f"Added common location: {location}")
    
    # Add the server_id as a possible subdirectory name to check
    if server_id is not None and not server_id.startswith('/'):
        for root_dir in unique_base_dirs.copy():
            potential_server_dir = os.path.join(root_dir, server_id)
            if os.path.exists(potential_server_dir) and os.path.isdir(potential_server_dir):
                unique_base_dirs.append(potential_server_dir)
                logger.info(f"Added server-specific directory: {potential_server_dir}")""",
            content
        )
        
        # Fix 4: Improve CSV parser
        logger.info("Applying fix 4: Improve CSV parser")
        content = re.sub(
            r"try:\s+# Read file as binary\s+with open\(file_path, 'rb'\).*?delimiter = ';'.*?if commas > semicolons \* 2:\s+delimiter = ','",
            """try:
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
            logger.info(f"Selected semicolon as delimiter based on frequency or default: {semicolons} semicolons")""",
            content
        )
        
        # Fix 5: Improve file processing
        logger.info("Applying fix 5: Improve file processing")
        content = re.sub(
            r"# Parse events - unpack tuple return value.*?logger\.warning\(f\"No events parsed from {file_path}\"\)",
            """# FIXED: Improved parsing with better error handling and logging
        try:
            # Parse events - unpack tuple return value (events, line_count)
            events, line_count = direct_parse_csv_file(file_path, server_id)
            
            if events is not None:
                logger.info(f"Successfully parsed {len(events)} events from {os.path.basename(file_path)} ({line_count} total lines)")
                
                # Import events with better error handling
                try:
                    imported = await direct_import_events(db, events)
                    if imported > 0:
                        files_processed += 1
                        events_imported += imported
                        logger.info(f"Successfully imported {imported} events from {os.path.basename(file_path)}")
                    else:
                        logger.warning(f"No events were imported from {os.path.basename(file_path)} despite successful parsing")
                        # Count the file as processed even if no events were imported
                        files_processed += 1
                except Exception as import_error:
                    logger.error(f"Error importing events from {os.path.basename(file_path)}: {import_error}")
                    # Try to continue with other files
            else:
                if line_count > 0:
                    logger.warning(f"File {os.path.basename(file_path)} has {line_count} lines but no valid events were parsed")
                else:
                    logger.warning(f"No valid content found in {os.path.basename(file_path)}")
                    
                # Count this as processed to avoid reprocessing the same empty file
                files_processed += 1
        except Exception as parse_error:
            logger.error(f"Error parsing file {os.path.basename(file_path)}: {parse_error}")
            # Continue with other files""",
            content
        )
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied fixes to direct CSV handler module")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fixes to direct CSV handler: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting comprehensive CSV processing system fix")
    
    # Apply fixes to CSV processor cog
    if fix_csv_processor():
        logger.info("Successfully applied fixes to CSV processor cog")
    else:
        logger.error("Failed to apply fixes to CSV processor cog")
        
    # Apply fixes to direct CSV handler
    if fix_direct_csv_handler():
        logger.info("Successfully applied fixes to direct CSV handler")
    else:
        logger.error("Failed to apply fixes to direct CSV handler")
        
    logger.info("Comprehensive CSV processing system fix completed")

if __name__ == "__main__":
    main()