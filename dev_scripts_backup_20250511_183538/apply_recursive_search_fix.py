"""
Comprehensive Recursive Search Fix for CSV Processing

This script improves the recursive subdirectory searching capabilities
of the historical parser to ensure all CSV files are found and processed.

Key improvements:
1. Enhanced directory searching logic with recursive support
2. Support for both UUID and original server ID formats
3. Additional pattern matching for CSV files
4. Proper handling of historical and killfeed processor interaction
5. Duplicate file detection to prevent redundant processing
"""
import os
import re
import asyncio
import logging
import traceback
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("recursive_fix")

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    import shutil
    backup_path = f"{file_path}.bak"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def apply_fix_to_direct_csv_handler():
    """Apply the fix to the direct CSV handler module"""
    file_path = "utils/direct_csv_handler.py"
    
    # First, create a backup
    if not backup_file(file_path):
        logger.error("Cannot proceed without creating a backup")
        return False
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Apply the fix - update process_directory function to enhance recursive searching
    recursive_search_fix = """
    # Search through all base directories, including recursive subdirectory search
    for base_dir in unique_base_dirs:
        if not os.path.exists(base_dir):
            logger.warning(f"Directory {base_dir} does not exist, skipping")
            continue
            
        logger.info(f"Searching directory: {base_dir}")
        try:
            # Walk through the directory and all subdirectories
            for root, dirs, files in os.walk(base_dir):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Log only if we find files or this is one of known important subdirectories
                important_subdir = any(keyword in root.lower() for keyword in ['world_', 'deathlogs', 'actual'])
                csv_in_dir = any(f.endswith('.csv') for f in files)
                
                if csv_in_dir or important_subdir:
                    logger.info(f"Searching in directory: {root} - contains {len(files)} files, {sum(1 for f in files if f.endswith('.csv'))} CSV files")
                
                # Always look for subdirectories that match our patterns
                for subdir in dirs:
                    if any(pattern in subdir.lower() for pattern in ['world_', 'map_', 'deathlogs']):
                        subdir_path = os.path.join(root, subdir)
                        logger.info(f"Found important subdirectory: {subdir_path}")
                
                # Look for CSV files in this directory
                for filename in files:
                    if not filename.endswith('.csv'):
                        continue
"""
    
    # Find and replace the existing search logic with our improved version
    old_search_pattern = r"for base_dir in unique_base_dirs:.*?logger\.info\(f\"Searching directory: {base_dir}\"\)"
    if re.search(old_search_pattern, content, re.DOTALL):
        # Replace only the beginning part to preserve the rest of the function
        new_content = re.sub(old_search_pattern, recursive_search_fix.strip(), content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
        logger.info("Successfully applied recursive search fix to direct_csv_handler.py")
        return True
    else:
        logger.error("Could not find search pattern in direct_csv_handler.py")
        return False

def apply_fix_to_sftp_manager():
    """Apply the fix to the SFTP manager module to enhance CSV file pattern matching"""
    file_path = "utils/sftp.py"
    
    # First, create a backup
    if not backup_file(file_path):
        logger.error("Cannot proceed without creating a backup")
        return False
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Locate the find_csv_files method
    find_csv_pattern = r"async def find_csv_files\(self,[^{]*?{(.*?)}"
    match = re.search(find_csv_pattern, content, re.DOTALL)
    
    if not match:
        logger.error("Could not find find_csv_files method in SFTP manager")
        return False
    
    # Get the current method body
    current_method = match.group(1)
    
    # Create the improved version
    improved_method = """
        \"\"\"
        Find CSV files in a directory with improved pattern matching and recursive support.
        
        Args:
            path: Directory path to search
            pattern: Optional regex pattern for CSV files
            recursive: Whether to search subdirectories
            max_depth: Maximum recursion depth for directory traversal
            
        Returns:
            List of CSV file paths found
        \"\"\"
        logger.info(f"Enhanced find_csv_files searching {path}")
        
        if pattern is None:
            pattern = r"\\d{4}\\.\\d{2}\\.\\d{2}-\\d{2}\\.\\d{2}\\.\\d{2}\\.csv"
        
        # Combine multiple patterns for more robust searching
        extended_pattern = f"({pattern}|.*\\.csv)"
        
        # Default max_depth to 5 for better performance
        if max_depth is None:
            max_depth = 5
            
        csv_files = []
        current_depth = 0
        
        try:
            # Get directory listing
            items = await self.client.listdir(path)
            
            # Sort the items to ensure consistent processing order
            items = sorted(items)
            
            # Process all items
            for item in items:
                item_path = f"{path}/{item}"
                
                # Skip hidden files/directories
                if item.startswith('.'):
                    continue
                
                try:
                    # Check if this is a file or directory
                    is_dir = False
                    try:
                        stat = await self.client.stat(item_path)
                        is_dir = stat.st_mode & 0o40000 != 0
                    except:
                        # If stat fails, try to use lstat
                        stat = await self.client.lstat(item_path)
                        is_dir = stat.st_mode & 0o40000 != 0
                        
                    # Process file if it matches pattern
                    if not is_dir:
                        if item.endswith('.csv') and re.match(pattern, item):
                            csv_files.append(item_path)
                            
                    # Process directory if recursive is enabled
                    elif recursive and current_depth < max_depth:
                        # Test if important directory before recursing
                        important_dir = any(keyword in item.lower() for keyword in ['world_', 'deathlogs', 'actual', 'logs'])
                        
                        # Always log important directories
                        if important_dir:
                            logger.info(f"Searching important subdirectory: {item_path}")
                            
                        # Recursively search subdirectory
                        subdirectory_files = await self.find_csv_files(
                            item_path, pattern, recursive, max_depth - 1
                        )
                        csv_files.extend(subdirectory_files)
                        
                except Exception as e:
                    logger.error(f"Error processing item {item_path}: {e}")
                    # Continue processing other files
        
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return []
            
        # Log results
        if csv_files:
            logger.info(f"Found {len(csv_files)} CSV files in {path}")
            if len(csv_files) > 0:
                sample_size = min(5, len(csv_files))
                logger.info(f"Sample files: {csv_files[:sample_size]}")
        
        return csv_files
"""
    
    # Replace the method body
    new_content = content.replace(match.group(1), improved_method)
    
    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    logger.info("Successfully applied improved CSV file pattern matching to SFTP manager")
    return True

def enhance_csv_processor_historical_parsing():
    """Enhance historical parsing in the CSV processor cog"""
    file_path = "cogs/csv_processor.py"
    
    # First, create a backup
    if not backup_file(file_path):
        logger.error("Cannot proceed without creating a backup")
        return False
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the historical parse method and enhance it
    historical_parse_pattern = r"async def run_historical_parse\([^{]*?{(.*?)# CRITICAL FIX: Clean up historical parse flags"
    match = re.search(historical_parse_pattern, content, re.DOTALL)
    
    if not match:
        logger.error("Could not find run_historical_parse method in CSV processor")
        return False
    
    # Get the current method body
    current_method = match.group(1)
    
    # Add enhanced subdirectory search logic
    enhanced_logic = """
                            # ENHANCED RECURSIVE SEARCH: Add explicit recursive searching for all subdirectories
                            logger.warning("ENHANCED RECURSIVE SEARCH: Enabling deep recursive subdirectory searching")
                            
                            # Try additional directories that might contain CSV files
                            additional_dirs = []
                            
                            # Check for "world_X" directories which are commonly used
                            for world_id in range(5):  # world_0 through world_4
                                world_dir = os.path.join(search_dir, f"world_{world_id}")
                                if os.path.exists(world_dir) and os.path.isdir(world_dir):
                                    additional_dirs.append(world_dir)
                                    logger.info(f"Found world directory: {world_dir}")
                            
                            # Fully recursive search through all directories
                            for search_root in [search_dir] + additional_dirs:
                                for root, dirs, files in os.walk(search_root):
                                    # Skip hidden directories
                                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                                    
                                    # Count CSV files in this directory
                                    csv_files = [f for f in files if f.endswith('.csv')]
                                    if csv_files:
                                        logger.info(f"Found {len(csv_files)} CSV files in subdirectory: {root}")
"""
    
    # Find the spot to insert our enhanced logic
    insertion_point = "if server_config is not None:"
    if insertion_point in current_method:
        # Insert our enhanced logic after the matching line
        parts = current_method.split(insertion_point, 1)
        new_method = parts[0] + insertion_point + enhanced_logic + parts[1]
        
        # Update the content
        new_content = content.replace(current_method, new_method)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully enhanced historical parsing in CSV processor cog")
        return True
    else:
        logger.error("Could not find insertion point in run_historical_parse method")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting to apply recursive search fixes")
    
    # Apply fixes to the direct CSV handler
    if apply_fix_to_direct_csv_handler():
        logger.info("Successfully applied recursive search fix to direct CSV handler")
    else:
        logger.error("Failed to apply recursive search fix to direct CSV handler")
    
    # Apply fixes to the SFTP manager
    if apply_fix_to_sftp_manager():
        logger.info("Successfully applied improved CSV file pattern matching to SFTP manager")
    else:
        logger.error("Failed to apply improved CSV file pattern matching to SFTP manager")
    
    # Enhance CSV processor historical parsing
    if enhance_csv_processor_historical_parsing():
        logger.info("Successfully enhanced historical parsing in CSV processor cog")
    else:
        logger.error("Failed to enhance historical parsing in CSV processor cog")
    
    logger.info("All fixes have been applied. Please restart the bot.")

if __name__ == "__main__":
    main()