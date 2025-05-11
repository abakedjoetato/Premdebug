"""
# module: fix_sftp_manager
Comprehensive SFTPManager Fix

This script fixes the SFTPManager and related components to ensure proper 
CSV file discovery while maintaining compatibility with the Deadside.log parser.

Key fixes:
1. Ensures consistent implementation of directory_exists method
2. Adds get_file_attrs method with proper error handling
3. Ensures clients in the connection pool are up to date
4. Clears Python module cache to ensure changes take effect
5. Cleans up any stale SFTP connections
"""
import asyncio
import importlib
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from typing import Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sftp_fix.log')
    ]
)
logger = logging.getLogger("sftp_fix")

def create_backup(file_path):
    """Create a backup of a file before modifying it
    
    Args:
        file_path: Path to the file to back up
        
    Returns:
        str: Path to the backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"sftp_manager_backup_{timestamp}"
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    # Get the filename from the path
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, filename)
    
    # Copy the file
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup of {file_path} at {backup_path}")
    
    return backup_path
    
def fix_sftp_module():
    """Fix the SFTP module with comprehensive improvements
    
    This function applies all necessary fixes to utils/sftp.py to ensure
    proper directory checking and file discovery.
    """
    file_path = "utils/sftp.py"
    
    # Create backup
    backup_path = create_backup(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        logger.info("Applying comprehensive fixes to SFTP module")
        
        # Ensure directory_exists method is properly implemented in SFTPManager
        if "async def directory_exists(self, path: str)" in content:
            logger.info("directory_exists method already exists, ensuring it has the latest implementation")
            
            # Extract the existing directory_exists method
            start_idx = content.find("async def directory_exists(self, path: str)")
            if start_idx == -1:
                logger.error("Could not find directory_exists method in the file")
                return False
                
            # Find the end of the method (next method definition or end of class)
            end_idx1 = content.find("async def", start_idx + 10)
            end_idx2 = content.find("def ", start_idx + 10)
            
            if end_idx1 != -1 and end_idx2 != -1:
                end_idx = min(end_idx1, end_idx2)
            elif end_idx1 != -1:
                end_idx = end_idx1
            elif end_idx2 != -1:
                end_idx = end_idx2
            else:
                # If we can't find the end, assume it's the end of the file
                end_idx = len(content)
                
            # Get the existing implementation
            existing_impl = content[start_idx:end_idx]
            
            # Create the new implementation
            new_impl = """    async def directory_exists(self, path: str) -> bool:
        \"\"\"Check if a directory exists on the remote server

        Args:
            path: Directory path to check

        Returns:
            bool: True if directory exists, False otherwise
        \"\"\"
        # Validate input
        if not path:
            logger.error("Path parameter is empty in directory_exists")
            return False

        # Ensure client is connected
        if not self.client:
            logger.info(f"Creating new SFTP client connection for directory_exists({path})")
            if not await self.connect():
                logger.error(f"Failed to establish SFTP connection for directory_exists({path})")
                return False

        # Retry logic for better reliability
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                # Check if path exists and is a directory
                try:
                    # First try to list the directory - if it succeeds, it's a directory
                    await self.listdir(path)
                    return True
                except Exception as list_err:
                    # If listing fails, try to get file attributes
                    try:
                        attrs = await self.get_file_attrs(path)
                        # Check if it's a directory
                        return attrs is not None and stat.S_ISDIR(attrs.permissions)
                    except Exception:
                        # If both methods fail, the directory doesn't exist
                        return False

            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Error checking if directory exists: {path} (attempt {attempt}/{max_attempts}): {e}")

                # If this isn't the last attempt, try reconnecting
                if attempt < max_attempts:
                    logger.info(f"Attempting to reconnect for directory_exists retry ({attempt}/{max_attempts})")
                    await self.disconnect()
                    await asyncio.sleep(1)  # Brief delay before retry
                    await self.connect()

        # If we get here, all attempts failed
        logger.warning(f"All attempts to check if directory exists failed: {path}")
        return False"""
            
            # Replace the existing implementation with the new one
            content = content.replace(existing_impl, new_impl)
            logger.info("Updated directory_exists method with latest implementation")
        else:
            logger.error("directory_exists method not found in the file, cannot update")
            return False
            
        # Ensure get_file_attrs method is properly implemented
        if "async def get_file_attrs(self, path: str)" in content:
            logger.info("get_file_attrs method already exists, ensuring it has the latest implementation")
            
            # Extract the existing get_file_attrs method
            start_idx = content.find("async def get_file_attrs(self, path: str)")
            if start_idx == -1:
                logger.error("Could not find get_file_attrs method in the file")
                return False
                
            # Find the end of the method (next method definition or end of class)
            end_idx1 = content.find("async def", start_idx + 10)
            end_idx2 = content.find("def ", start_idx + 10)
            
            if end_idx1 != -1 and end_idx2 != -1:
                end_idx = min(end_idx1, end_idx2)
            elif end_idx1 != -1:
                end_idx = end_idx1
            elif end_idx2 != -1:
                end_idx = end_idx2
            else:
                # If we can't find the end, assume it's the end of the file
                end_idx = len(content)
                
            # Get the existing implementation
            existing_impl = content[start_idx:end_idx]
            
            # Create the new implementation
            new_impl = """    async def get_file_attrs(self, path: str) -> Optional[Any]:
        \"\"\"Get file attributes from the SFTP server
        
        Args:
            path: Path to file or directory
            
        Returns:
            Optional[Any]: File attributes if found, None otherwise
        \"\"\"
        if not self.client:
            logger.error(f"SFTP client is missing when trying to get file attributes: {path}")
            return None
            
        try:
            # Try using the client's get_file_attrs method if available
            if hasattr(self.client, 'get_file_attrs'):
                return await self.client.get_file_attrs(path)
                
            # Otherwise, try to use stat() from asyncssh if available
            try:
                if hasattr(self.client, 'sftp'):
                    return await self.client.sftp.stat(path)
            except Exception:
                pass
                
            # As a fallback, use get_file_info and extract permissions
            file_info = await self.get_file_info(path)
            if file_info and isinstance(file_info, dict):
                # Create a simple object with permissions attribute
                class FileAttrs:
                    def __init__(self, permissions):
                        self.permissions = permissions
                
                # Check if it's a directory based on simple logic
                if file_info.get('is_dir', False) or file_info.get('directory', False):
                    return FileAttrs(0o755 | stat.S_IFDIR)
                else:
                    return FileAttrs(0o644 | stat.S_IFREG)
                    
            return None
        except Exception as e:
            logger.error(f"Error getting file attributes for {path}: {e}")
            return None"""
            
            # Replace the existing implementation with the new one
            content = content.replace(existing_impl, new_impl)
            logger.info("Updated get_file_attrs method with latest implementation")
        else:
            logger.error("get_file_attrs method not found in the file, cannot update")
            return False
            
        # Fix the SFTPClient implementation as well to ensure compatibility
        if "class SFTPClient" in content:
            logger.info("SFTPClient class found, ensuring it has the latest methods")
            
            # Find the end of the SFTPClient class
            start_idx = content.find("class SFTPClient")
            if start_idx == -1:
                logger.error("Could not find SFTPClient class in the file")
                return False
                
            # Find the end of the class (next class definition or end of file)
            end_idx = content.find("class ", start_idx + 10)
            if end_idx == -1:
                end_idx = len(content)
                
            # Get the existing class definition
            existing_class = content[start_idx:end_idx]
            
            # Check if directory_exists is in the class
            if "async def directory_exists(self, path: str)" not in existing_class:
                # Add directory_exists method to the class
                new_method = """
    async def directory_exists(self, path: str) -> bool:
        \"\"\"Check if a directory exists on the remote server

        Args:
            path: Directory path to check

        Returns:
            bool: True if directory exists, False otherwise
        \"\"\"
        await self.ensure_connected()
        
        try:
            # First try to list the directory - if it succeeds, it's a directory
            await self.listdir(path)
            return True
        except Exception:
            # If listing fails, try to get file attributes
            try:
                attrs = await self.get_file_attrs(path)
                # Check if it's a directory
                return attrs is not None and stat.S_ISDIR(attrs.permissions)
            except Exception:
                # If both methods fail, the directory doesn't exist
                return False"""
                
                # Add the method to the end of the class
                new_class = existing_class + new_method
                content = content.replace(existing_class, new_class)
                logger.info("Added directory_exists method to SFTPClient class")
                
            # Check if get_file_attrs is in the class
            if "async def get_file_attrs(self, path: str)" not in existing_class:
                # Add get_file_attrs method to the class
                new_method = """
    async def get_file_attrs(self, path: str) -> Optional[Any]:
        \"\"\"Get file attributes with permission information
        
        Args:
            path: File path
            
        Returns:
            File attributes or None if not found
        \"\"\"
        await self.ensure_connected()
        
        try:
            if self._sftp_client:
                # Get the file's stat information directly
                stat = await self._sftp_client.stat(path)
                return stat
            return None
        except Exception as e:
            return None"""
                
                # Find where to add the method 
                if "async def directory_exists(self, path: str)" in existing_class:
                    # Add it after directory_exists
                    dir_exists_idx = existing_class.find("async def directory_exists(self, path: str)")
                    dir_exists_end = existing_class.find("async def", dir_exists_idx + 10)
                    if dir_exists_end == -1:
                        dir_exists_end = len(existing_class)
                        
                    # Split the class at the end of directory_exists method
                    before = existing_class[:dir_exists_end]
                    after = existing_class[dir_exists_end:]
                    
                    # Combine with the new method
                    new_class = before + new_method + after
                else:
                    # Add it to the end of the class
                    new_class = existing_class + new_method
                    
                content = content.replace(existing_class, new_class)
                logger.info("Added get_file_attrs method to SFTPClient class")
                
        # Make sure stat module is imported
        if "import stat" not in content:
            # Add after the imports
            imports_end = content.find("\n\n", content.find("import "))
            if imports_end == -1:
                imports_end = content.find("# Configure module-specific logger")
                
            before = content[:imports_end]
            after = content[imports_end:]
            
            content = before + "\nimport stat" + after
            logger.info("Added stat module import")
            
        # Write the changes back to the file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info("Successfully applied all fixes to SFTP module")
        return True
    except Exception as e:
        logger.error(f"Error fixing SFTP module: {e}")
        # Restore from backup
        logger.info(f"Restoring SFTP module from backup {backup_path}")
        shutil.copy2(backup_path, file_path)
        return False
        
def fix_file_discovery():
    """Fix the file discovery module to ensure proper CSV file discovery
    
    This function applies all necessary fixes to utils/file_discovery.py to 
    ensure proper directory checking and file discovery.
    """
    file_path = "utils/file_discovery.py"
    
    # Create backup
    backup_path = create_backup(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        logger.info("Applying comprehensive fixes to file discovery module")
        
        # Fix _find_map_directories method to better handle directory checking
        if "async def _find_map_directories(self, sftp: SFTPManager, base_paths: List[str])" in content:
            logger.info("_find_map_directories method found, ensuring it has proper error handling")
            
            # Extract the method
            start_idx = content.find("async def _find_map_directories(self, sftp: SFTPManager, base_paths: List[str])")
            if start_idx == -1:
                logger.error("Could not find _find_map_directories method in the file")
                return False
                
            # Find the end of the method (next method definition)
            end_idx = content.find("async def", start_idx + 10)
            if end_idx == -1:
                logger.error("Could not find the end of _find_map_directories method")
                return False
                
            # Existing implementation
            existing_impl = content[start_idx:end_idx]
            
            # New implementation with better error handling
            new_impl = """    async def _find_map_directories(self, sftp: SFTPManager, base_paths: List[str]) -> List[str]:
        \"\"\"
        Find map directories that might contain CSV files.
        
        Args:
            sftp: The SFTP manager to use
            base_paths: List of base paths to search within
            
        Returns:
            List of map directories found
        \"\"\"
        # Known map directory names
        map_subdirs = [
            "world_0", "world0", "world_1", "world1", 
            "map_0", "map0", "main", "default", "maps", "custom_maps"
        ]
        
        map_dirs = []
        
        # Check each base path for map directories
        for base_path in base_paths:
            # First, directly check for known map directories
            for map_subdir in map_subdirs:
                map_path = os.path.join(base_path, map_subdir)
                try:
                    dir_exists = await sftp.directory_exists(map_path)
                    if dir_exists:
                        logger.debug(f"Found map directory: {map_path}")
                        map_dirs.append(map_path)
                except Exception as e:
                    logger.debug(f"Error checking map directory {map_path}: {e}")
                    continue
                    
            # Then try to list directories and look for patterns
            try:
                entries = await sftp.listdir(base_path)
                for entry in entries:
                    # Skip obvious non-map entries
                    if entry.startswith('.') or entry in ['logs', 'config', 'backups']:
                        continue
                        
                    # Check if it matches known map naming patterns
                    if re.search(r'(world|map|level|zone|region)[-_]?\d*', entry, re.IGNORECASE):
                        entry_path = os.path.join(base_path, entry)
                        try:
                            dir_exists = await sftp.directory_exists(entry_path)
                            if dir_exists:
                                logger.debug(f"Found map directory by pattern: {entry_path}")
                                map_dirs.append(entry_path)
                        except Exception as e:
                            logger.debug(f"Error checking directory {entry_path}: {e}")
                            continue
            except Exception as e:
                logger.debug(f"Error listing directory {base_path}: {e}")
                continue
                
        # Log what we found
        logger.info(f"Found {len(map_dirs)} map directories total")
        return map_dirs"""
            
            # Replace the implementation
            content = content.replace(existing_impl, new_impl)
            logger.info("Updated _find_map_directories method with improved error handling")
            
        # Fix _list_csv_files method to better handle directory checking
        if "async def _list_csv_files(self, sftp: SFTPManager, directory: str, pattern: str)" in content:
            logger.info("_list_csv_files method found, ensuring it has proper error handling")
            
            # Extract the method
            start_idx = content.find("async def _list_csv_files(self, sftp: SFTPManager, directory: str, pattern: str)")
            if start_idx == -1:
                logger.error("Could not find _list_csv_files method in the file")
                return False
                
            # Find the end of the method (next method definition)
            end_idx = content.find("async def", start_idx + 10)
            if end_idx == -1:
                end_idx = content.find("def ", start_idx + 10)
                if end_idx == -1:
                    logger.error("Could not find the end of _list_csv_files method")
                    return False
                
            # Existing implementation
            existing_impl = content[start_idx:end_idx]
            
            # New implementation with better error handling
            new_impl = """    async def _list_csv_files(self, sftp: SFTPManager, directory: str, pattern: str) -> List[str]:
        \"\"\"
        List CSV files in a directory matching a pattern.
        
        Args:
            sftp: The SFTP manager to use
            directory: The directory to search in
            pattern: Regex pattern to match files against
            
        Returns:
            List of full paths to matching files
        \"\"\"
        try:
            # Check if the directory exists first
            logger.debug(f"Checking if directory exists: {directory}")
            dir_exists = await sftp.directory_exists(directory)
            if not dir_exists:
                logger.debug(f"Directory does not exist: {directory}")
                return []
                
            # List files matching the pattern
            logger.debug(f"Listing files in directory: {directory} with pattern: {pattern}")
            files = await sftp.list_files(directory, pattern)
            logger.debug(f"Found {len(files)} files matching pattern in {directory}")
            
            # Convert to full paths if not already
            full_paths = []
            for file in files:
                if directory.endswith('/'):
                    path = f"{directory}{file}"
                else:
                    path = f"{directory}/{file}"
                full_paths.append(path)
                
            return full_paths
        except Exception as e:
            logger.error(f"Error listing CSV files in {directory}: {e}")
            return []"""
            
            # Replace the implementation
            content = content.replace(existing_impl, new_impl)
            logger.info("Updated _list_csv_files method with improved error handling")
            
        # Fix discover_csv_files method to keep track of files found in map directories
        if "async def discover_csv_files" in content:
            logger.info("discover_csv_files method found, ensuring it properly tracks map files")
            
            # Find the line that tracks map files
            map_files_idx = content.find("map_files = []")
            if map_files_idx != -1:
                # Find the section where map files are discovered
                map_search_idx = content.find("# Then search in map directories", map_files_idx)
                if map_search_idx != -1:
                    # Find the end of the map files processing
                    end_map_idx = content.find("# Filter files", map_search_idx)
                    if end_map_idx == -1:
                        end_map_idx = content.find("# Track discovered files", map_search_idx)
                        
                    if end_map_idx != -1:
                        # Extract the map files processing section
                        map_section = content[map_search_idx:end_map_idx]
                        
                        # Check if we're updating the map_directory_files tracking
                        if "self.map_directory_files[server_id].update(set(map_path_files))" not in map_section:
                            # Add the tracking code after the map files are found
                            add_idx = map_section.find("all_discovered_files.extend(map_path_files)")
                            if add_idx != -1:
                                before = map_section[:add_idx + len("all_discovered_files.extend(map_path_files)")]
                                after = map_section[add_idx + len("all_discovered_files.extend(map_path_files)"):]
                                
                                # Create the new section
                                new_section = before + "\n                    # Ensure map files are tracked in the map_directory_files set\n                    self.map_directory_files[server_id].update(set(map_path_files))" + after
                                
                                # Replace in the content
                                content = content.replace(map_section, new_section)
                                logger.info("Updated map file tracking in discover_csv_files method")
            
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info("Successfully applied all fixes to file discovery module")
        return True
    except Exception as e:
        logger.error(f"Error fixing file discovery module: {e}")
        # Restore from backup
        logger.info(f"Restoring file discovery module from backup {backup_path}")
        shutil.copy2(backup_path, file_path)
        return False

def fix_csv_processor():
    """Fix the CSV processor cog to ensure proper file tracking
    
    This function applies all necessary fixes to cogs/csv_processor.py to
    ensure proper tracking of files found and processed.
    """
    file_path = "cogs/csv_processor.py"
    
    # Create backup
    backup_path = create_backup(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        logger.info("Applying comprehensive fixes to CSV processor cog")
        
        # Ensure we're tracking map files correctly in the historical parse method
        if "async def run_historical_parse" in content:
            logger.info("run_historical_parse method found, ensuring it properly tracks map files")
            
            # Find the run_historical_parse method
            start_idx = content.find("async def run_historical_parse")
            if start_idx == -1:
                logger.error("Could not find run_historical_parse method in the file")
                return False
                
            # Find the end of the method
            end_idx = content.find("async def", start_idx + 10)
            if end_idx == -1:
                logger.error("Could not find the end of run_historical_parse method")
                return False
                
            # Existing implementation
            run_historical = content[start_idx:end_idx]
            
            # Check if we need to update the stats tracking
            if "stats['map_files_found'] = len(discovery.map_directory_files.get(server_id, []))" not in run_historical:
                # Find where stats are updated
                stats_idx = run_historical.find("# Store stats")
                if stats_idx != -1:
                    # Find the end of the stats block
                    end_stats_idx = run_historical.find("return", stats_idx)
                    if end_stats_idx != -1:
                        # Extract the stats block
                        stats_block = run_historical[stats_idx:end_stats_idx]
                        
                        # Create new stats block with map files tracking
                        new_stats_block = stats_block
                        if "stats['files_found'] = len(all_files)" in stats_block:
                            # Add map files tracking after files_found
                            add_idx = stats_block.find("stats['files_found'] = len(all_files)") + len("stats['files_found'] = len(all_files)")
                            before = stats_block[:add_idx]
                            after = stats_block[add_idx:]
                            
                            # Insert map files tracking
                            new_stats_block = before + "\n            # Track map files found separately\n            stats['map_files_found'] = len(discovery.map_directory_files.get(server_id, []))" + after
                        
                        # Replace in the method
                        new_run_historical = run_historical.replace(stats_block, new_stats_block)
                        
                        # Replace in the content
                        content = content.replace(run_historical, new_run_historical)
                        logger.info("Updated stats tracking in run_historical_parse method")
                        
        # Fix _get_sftp_manager method to ensure it properly recreates connections
        if "async def _get_sftp_manager" in content:
            logger.info("_get_sftp_manager method found, checking implementation")
            
            # Find the method
            start_idx = content.find("async def _get_sftp_manager")
            if start_idx == -1:
                logger.error("Could not find _get_sftp_manager method in the file")
                return False
                
            # Find the end of the method
            end_idx = content.find("async def", start_idx + 10)
            if end_idx == -1:
                end_idx = content.find("@app_commands", start_idx)
                if end_idx == -1:
                    logger.error("Could not find the end of _get_sftp_manager method")
                    return False
                    
            # Existing implementation
            existing_impl = content[start_idx:end_idx]
            
            # New implementation with improved error handling
            new_impl = """    async def _get_sftp_manager(self, server_id: str, config: Dict[str, Any]) -> Optional[SFTPManager]:
        \"\"\"Get or create an SFTP manager for a server
        
        Args:
            server_id: Server ID
            config: Server configuration with SFTP details
            
        Returns:
            SFTPManager: SFTP manager for this server, or None if creation fails
        \"\"\"
        # Check if we already have a connection
        if server_id in self.sftp_connections:
            sftp = self.sftp_connections[server_id]
            
            # Check if the connection is still valid
            try:
                if sftp.is_connected:
                    # Verify connection with a simple operation
                    if await sftp.directory_exists("/"):
                        return sftp
            except Exception as e:
                logger.warning(f"Existing SFTP connection for {server_id} failed check: {e}")
                
            # Connection is invalid, close it
            try:
                await sftp.close()
            except Exception as e:
                logger.warning(f"Error closing SFTP connection for {server_id}: {e}")
                
            # Remove it from our connections
            del self.sftp_connections[server_id]
        
        # Create a new connection
        try:
            from utils.sftp import get_sftp_client
            
            # Use the factory function to get a client
            sftp = await get_sftp_client(
                hostname=config["hostname"],
                port=config["port"],
                username=config["username"],
                password=config["password"],
                server_id=server_id,
                original_server_id=config.get("original_server_id"),
                force_new=True
            )
            
            if not sftp:
                logger.error(f"Failed to create SFTP manager for server {server_id}")
                return None
                
            # Store the connection for reuse
            self.sftp_connections[server_id] = sftp
            
            return sftp
        except Exception as e:
            logger.error(f"Failed to create SFTP manager for server {server_id}: {e}")
            return None"""
            
            # Replace in the content
            content = content.replace(existing_impl, new_impl)
            logger.info("Updated _get_sftp_manager method with improved connection handling")
            
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info("Successfully applied all fixes to CSV processor cog")
        return True
    except Exception as e:
        logger.error(f"Error fixing CSV processor cog: {e}")
        # Restore from backup
        logger.info(f"Restoring CSV processor cog from backup {backup_path}")
        shutil.copy2(backup_path, file_path)
        return False

def reload_modules():
    """Force reload of critical modules to ensure changes take effect"""
    modules_to_reload = [
        'utils.sftp',
        'utils.file_discovery',
        'utils.csv_processor_coordinator',
        'utils.csv_parser',
        'cogs.csv_processor'
    ]
    
    logger.info("Force reloading modules to ensure changes take effect")
    for module_name in modules_to_reload:
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            logger.info(f"Successfully reloaded module {module_name}")
        except Exception as e:
            logger.error(f"Error reloading module {module_name}: {e}")
            
    logger.info("All modules reloaded")
    
def restart_bot():
    """Kill any running bot processes and restart the bot"""
    logger.info("Restarting the Discord bot")
    
    try:
        # Kill any running bot processes
        os.system("pkill -f 'python.*bot.py'")
        os.system("pkill -f 'python.*run_discord_bot'")
        os.system("pkill -f 'python.*bot_wrapper.py'")
        
        logger.info("Killed existing bot processes")
        
        # Brief delay
        time.sleep(2)
        
        # Start the bot in the background using the wrapper script
        if os.path.exists("run_discord_bot.sh"):
            os.system("nohup bash run_discord_bot.sh > bot_restart.log 2>&1 &")
            logger.info("Started bot using run_discord_bot.sh")
        elif os.path.exists("bot_wrapper.py"):
            os.system("nohup python bot_wrapper.py > bot_restart.log 2>&1 &")
            logger.info("Started bot using bot_wrapper.py")
        else:
            os.system("nohup python bot.py > bot_restart.log 2>&1 &")
            logger.info("Started bot directly using bot.py")
            
        logger.info("Bot restart initiated")
        return True
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        return False
        
async def main():
    """Main function to apply all fixes"""
    logger.info("="*80)
    logger.info("STARTING COMPREHENSIVE CSV PROCESSING SYSTEM FIX")
    logger.info("="*80)
    
    # Step 1: Fix the SFTP module
    logger.info("\n## STEP 1: FIXING SFTP MODULE")
    sftp_fixed = fix_sftp_module()
    if not sftp_fixed:
        logger.error("Failed to fix SFTP module, aborting")
        return
        
    # Step 2: Fix the file discovery module
    logger.info("\n## STEP 2: FIXING FILE DISCOVERY MODULE")
    discovery_fixed = fix_file_discovery()
    if not discovery_fixed:
        logger.error("Failed to fix file discovery module, aborting")
        return
        
    # Step 3: Fix the CSV processor cog
    logger.info("\n## STEP 3: FIXING CSV PROCESSOR COG")
    processor_fixed = fix_csv_processor()
    if not processor_fixed:
        logger.error("Failed to fix CSV processor cog, aborting")
        return
        
    # Step 4: Reload modules to ensure changes take effect
    logger.info("\n## STEP 4: RELOADING MODULES")
    reload_modules()
    
    # Step 5: Restart the bot
    logger.info("\n## STEP 5: RESTARTING BOT")
    bot_restarted = restart_bot()
    if not bot_restarted:
        logger.error("Failed to restart bot")
        
    logger.info("\n## FIX COMPLETE")
    logger.info("Run debug_csv_discovery.py to verify the fix")
    
if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())