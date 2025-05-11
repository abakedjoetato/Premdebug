#!/usr/bin/env python
"""
Enhanced CSV content processing fix

This script fixes the CSV content processing logic to ensure all valid data is parsed correctly.
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

def fix_content_processing():
    """Apply content processing improvements to CSV processor"""
    file_path = "cogs/csv_processor.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying content processing improvements...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Improve CSV content processing
        logger.info("Applying fix: Improve CSV content processing")
        
        pattern = r"# EMERGENCY FIX: ALWAYS process all lines.*?logger\.warning\(f\"NEW DIRECT HANDLER: Processed {len\(events\)} events from file with {total_lines} total lines\"\)"
        replacement = """# FIXED: Improved CSV processing with better error handling and mode support
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
                                                        total_lines = 0"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 2: Improve line position tracking
        logger.info("Applying fix: Improve line position tracking")
        
        pattern = r"# CRITICAL FIX: Update line position tracking.*?self\.last_processed_line_positions\[server_id\]\[os\.path\.basename\(file_path\)\] = total_lines"
        replacement = """# FIXED: Better line position tracking for all processing modes
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
                                                    self.file_line_positions[file_path] = total_lines"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied content processing fixes to CSV processor")
        return True
        
    except Exception as e:
        logger.error(f"Error applying content processing fixes: {e}")
        return False

def fix_direct_csv_parser():
    """Apply parser improvements to direct CSV handler"""
    file_path = "utils/direct_csv_handler.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying parser improvements to direct CSV handler...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix: Improve parser logic
        logger.info("Applying fix: Improve parser logic")
        
        pattern = r"try:\s+# Read file as binary\s+with open\(file_path, 'rb'\).*?delimiter = ';'.*?if commas > semicolons \* 2:\s+delimiter = ','"
        replacement = """try:
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
            logger.info(f"Selected semicolon as delimiter based on frequency or default: {semicolons} semicolons")"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied parser improvements to direct CSV handler")
        return True
        
    except Exception as e:
        logger.error(f"Error applying parser improvements: {e}")
        return False

def main():
    """Main function to apply all content processing fixes"""
    logger.info("Starting content processing fixes for CSV processing system")
    
    # Apply fixes to CSV processor
    if fix_content_processing():
        logger.info("Successfully applied content processing fixes to CSV processor")
    else:
        logger.error("Failed to apply content processing fixes to CSV processor")
        
    # Apply fixes to direct CSV handler
    if fix_direct_csv_parser():
        logger.info("Successfully applied parser improvements to direct CSV handler")
    else:
        logger.error("Failed to apply parser improvements to direct CSV handler")
        
    logger.info("Content processing fixes completed")

if __name__ == "__main__":
    main()