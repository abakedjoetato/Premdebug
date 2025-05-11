#!/usr/bin/env python
"""
Enhanced directory search fix for CSV processing system

This script specifically fixes the directory search functionality in the CSV processing system
to ensure all CSV files are properly found and processed.
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

def fix_direct_csv_handler():
    """Apply directory search improvements to the direct CSV handler"""
    file_path = "utils/direct_csv_handler.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying directory search improvements...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Enhance file format detection
        logger.info("Applying fix 1: Enhance file format detection")
        
        pattern = r"if not filename\.endswith\('\.csv'\):\s+continue"
        replacement = """# Check for various file formats that might contain CSV data
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
                        continue"""
        
        content = re.sub(pattern, replacement, content)
        
        # Fix 2: Improve search directory handling
        logger.info("Applying fix 2: Improve search directory handling")
        
        pattern = r"# Remove duplicates from base_dirs while preserving order\s+unique_base_dirs = \[\]\s+for directory in base_dirs:.*?logger\.info\(f\"Searching for CSV files in {len\(unique_base_dirs\)} base directories\"\)"
        replacement = """# FIXED: Improved file discovery to handle more directory structures
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
                logger.info(f"Added server-specific directory: {potential_server_dir}")"""
                
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 3: Improve date filtering to include more files
        logger.info("Applying fix 3: Improve date filtering")
        
        pattern = r"# Always include file even if date parsing fails.*?csv_files\.append\(full_path\)"
        replacement = """# FIXED: Safer date filtering to avoid missing important files
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
                        csv_files.append(full_path)"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied fixes to direct CSV handler")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fixes to direct CSV handler: {e}")
        return False

def fix_csv_processor_directory_handling():
    """Apply directory handling improvements to CSV processor"""
    file_path = "cogs/csv_processor.py"
    
    if not backup_file(file_path):
        return False
        
    logger.info("Applying directory handling improvements to CSV processor...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Enhance directory search patterns
        logger.info("Applying fix: Enhance directory search patterns")
        
        pattern = r"# First try the most common location\s+csv_files = await sftp\.list_csv_files\(.*?# Add timestamp info for all found files"
        replacement = """# Enhanced directory search with multiple fallback patterns
                        # First try the most common location with expanded pattern matching
                        csv_files = await sftp.list_csv_files(
                            directory_patterns=[
                                # Standard patterns
                                "deathlogs",
                                "actual*/deathlogs",
                                "actual*/logs",
                                f"{server_id}*/deathlogs",
                                # Common pattern variations
                                "logs/kills",
                                "logs/deaths",
                                "data/logs",
                                "world_*/logs",
                                "map_*/logs",
                                # Root searches with server ID
                                f"{server_id}/logs",
                                f"{server_id}_*",
                                # Generic patterns as a last resort
                                "logs",
                                "data",
                                "",  # Root directory as a last resort
                            ],
                            file_pattern="*.csv"
                        )
                        
                        # If no files found, try again with expanded file patterns
                        if not csv_files:
                            logger.warning(f"No CSV files found with standard patterns, trying expanded patterns")
                            csv_files = await sftp.list_csv_files(
                                directory_patterns=[
                                    "deathlogs",
                                    "actual*/deathlogs",
                                    "logs",
                                ],
                                file_pattern="*.*"  # Try any file, we'll filter later
                            )
                            
                            # Filter out non-data files
                            csv_files = [f for f in csv_files if any(ext in f.lower() for ext in 
                                        ['.csv', '.txt', '.log']) or re.search(r'\\d{4}[.-]\\d{2}[.-]\\d{2}', os.path.basename(f))]
                            
                            logger.info(f"Found {len(csv_files)} potential data files with expanded patterns")
                            
                        # Add timestamp info for all found files"""
                        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info("Successfully applied fixes to CSV processor")
        return True
        
    except Exception as e:
        logger.error(f"Error applying fixes to CSV processor: {e}")
        return False

def main():
    """Main function to apply all directory search fixes"""
    logger.info("Starting directory search fixes for CSV processing system")
    
    # Apply fixes to direct CSV handler
    if fix_direct_csv_handler():
        logger.info("Successfully applied directory search fixes to direct CSV handler")
    else:
        logger.error("Failed to apply directory search fixes to direct CSV handler")
        
    # Apply fixes to CSV processor
    if fix_csv_processor_directory_handling():
        logger.info("Successfully applied directory search fixes to CSV processor")
    else:
        logger.error("Failed to apply directory search fixes to CSV processor")
        
    logger.info("Directory search fixes completed")

if __name__ == "__main__":
    main()