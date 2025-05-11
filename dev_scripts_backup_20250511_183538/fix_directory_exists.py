"""
# module: fix_directory_exists
Direct Fix for SFTPManager directory_exists Issue

This script applies a focused fix for the directory_exists method in SFTPManager
and related components to ensure proper CSV file discovery.
"""
import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_directory_exists.log')
    ]
)
logger = logging.getLogger("fix_directory_exists")

def create_backup(file_path):
    """Create a backup of a file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"directory_exists_backup_{timestamp}"
    
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

def fix_sftp_py():
    """Fix the SFTPManager class in utils/sftp.py"""
    file_path = "utils/sftp.py"
    backup_path = create_backup(file_path)
    
    try:
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check if the directory_exists method already exists
        if "async def directory_exists(self, path: str)" in content:
            logger.info("directory_exists method already exists, replacing it with the fixed version")
            
            # Find the start of the method
            start_idx = content.find("async def directory_exists(self, path: str)")
            if start_idx == -1:
                logger.error("Could not find the directory_exists method")
                return False
                
            # Find the end of the method
            end_idx = content.find("async def", start_idx + 10)
            if end_idx == -1:
                # Try finding the next method definition
                end_idx = content.find("def ", start_idx + 10)
                if end_idx == -1:
                    logger.error("Could not find the end of the directory_exists method")
                    return False
                    
            # Extract the existing method
            existing_method = content[start_idx:end_idx]
            
            # Create the replacement method
            new_method = """async def directory_exists(self, path: str) -> bool:
        '''Check if a directory exists on the remote server

        Args:
            path: Directory path to check

        Returns:
            bool: True if directory exists, False otherwise
        '''
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

        # Check if path exists and is a directory
        try:
            # First try to list the directory - if it succeeds, it's a directory
            await self.listdir(path)
            return True
        except Exception as list_err:
            # If listing fails, try to get file attributes
            try:
                # Get file attributes
                if hasattr(self.client, 'sftp'):
                    attrs = await self.client.sftp.stat(path)
                    import stat
                    # Check if it's a directory using the stat module
                    return stat.S_ISDIR(attrs.permissions)
                return False
            except Exception:
                # If both methods fail, the directory doesn't exist
                return False"""
                
            # Replace the method in the content
            new_content = content.replace(existing_method, new_method)
            
            # Write the updated content back to the file
            with open(file_path, 'w') as f:
                f.write(new_content)
                
            logger.info("Successfully replaced the directory_exists method")
            return True
        else:
            # The method doesn't exist, so we need to add it
            logger.info("directory_exists method not found, adding it to the SFTPManager class")
            
            # Find the SFTPManager class
            class_idx = content.find("class SFTPManager")
            if class_idx == -1:
                logger.error("Could not find the SFTPManager class")
                return False
                
            # Find a good place to add the method
            # Let's look for common methods that would come after our method
            insertion_points = [
                "async def get_file_info",
                "async def list_files",
                "async def listdir",
                "async def exists",
                "async def connect",
                "async def close"
            ]
            
            insertion_idx = None
            for point in insertion_points:
                idx = content.find(point, class_idx)
                if idx != -1:
                    insertion_idx = idx
                    break
                    
            if insertion_idx is None:
                logger.error("Could not find a suitable insertion point for directory_exists method")
                return False
                
            # Find the start of the line for clean insertion
            line_start = content.rfind("\n", 0, insertion_idx) + 1
            
            # Create the method to insert
            method_to_insert = """    async def directory_exists(self, path: str) -> bool:
        '''Check if a directory exists on the remote server

        Args:
            path: Directory path to check

        Returns:
            bool: True if directory exists, False otherwise
        '''
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

        # Check if path exists and is a directory
        try:
            # First try to list the directory - if it succeeds, it's a directory
            await self.listdir(path)
            return True
        except Exception as list_err:
            # If listing fails, try to get file attributes
            try:
                # Get file attributes
                if hasattr(self.client, 'sftp'):
                    attrs = await self.client.sftp.stat(path)
                    import stat
                    # Check if it's a directory using the stat module
                    return stat.S_ISDIR(attrs.permissions)
                return False
            except Exception:
                # If both methods fail, the directory doesn't exist
                return False
                
"""
            
            # Insert the method
            new_content = content[:line_start] + method_to_insert + content[line_start:]
            
            # Write the updated content back to the file
            with open(file_path, 'w') as f:
                f.write(new_content)
                
            logger.info("Successfully added the directory_exists method to SFTPManager")
            return True
    except Exception as e:
        logger.error(f"Error fixing utils/sftp.py: {e}")
        # Restore from backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup")
        return False

def fix_file_discovery_py():
    """Fix the file discovery module to properly use directory_exists"""
    file_path = "utils/file_discovery.py"
    backup_path = create_backup(file_path)
    
    try:
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find where directory_exists is called
        if "await sftp.directory_exists(" in content:
            logger.info("File discovery already uses directory_exists, no changes needed")
            return True
        
        # Find the _list_csv_files method
        method_start = content.find("async def _list_csv_files")
        if method_start == -1:
            logger.error("Could not find _list_csv_files method")
            return False
            
        # Find the check for directory existence
        check_idx = content.find("# Check if the directory exists first", method_start)
        if check_idx == -1:
            logger.error("Could not find directory existence check in _list_csv_files")
            return False
            
        # Find the beginning of the actual check code
        code_idx = content.find("\n", check_idx) + 1
        
        # Look for the end of this check section
        end_idx = content.find("# List files matching the pattern", code_idx)
        if end_idx == -1:
            logger.error("Could not find end of directory check section")
            return False
            
        # Extract the current check logic
        current_check = content[code_idx:end_idx].strip()
        
        # Create the new check logic
        new_check = """            # Check if the directory exists first
            dir_exists = await sftp.directory_exists(directory)
            if not dir_exists:
                return []
                
"""
        
        # Replace the check logic
        new_content = content.replace(current_check, new_check)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Successfully updated file discovery to use directory_exists properly")
        return True
    except Exception as e:
        logger.error(f"Error fixing utils/file_discovery.py: {e}")
        # Restore from backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup")
        return False

def kill_and_restart_bot():
    """Kill any running bot processes and restart the bot"""
    try:
        # Kill existing bot processes
        logger.info("Killing existing bot processes")
        os.system("pkill -f 'python.*bot.py'")
        os.system("pkill -f 'python.*run_discord_bot'")
        os.system("pkill -f 'python.*bot_wrapper.py'")
        
        # Wait for processes to terminate
        import time
        time.sleep(2)
        
        # Start the bot
        logger.info("Starting the bot")
        
        if os.path.exists("run_discord_bot.sh"):
            os.system("nohup bash run_discord_bot.sh > bot_restart.log 2>&1 &")
            logger.info("Started bot using run_discord_bot.sh")
        elif os.path.exists("bot_wrapper.py"):
            os.system("nohup python bot_wrapper.py > bot_restart.log 2>&1 &")
            logger.info("Started bot using bot_wrapper.py")
        else:
            os.system("nohup python bot.py > bot_restart.log 2>&1 &")
            logger.info("Started bot directly using bot.py")
            
        # Wait a bit for the bot to start
        time.sleep(5)
        
        logger.info("Bot restart completed")
        return True
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        return False

def clear_python_cache():
    """Clear Python's __pycache__ directories to ensure changes take effect"""
    try:
        logger.info("Clearing Python cache directories")
        for root, dirs, files in os.walk("."):
            for dir in dirs:
                if dir == "__pycache__":
                    cache_dir = os.path.join(root, dir)
                    logger.info(f"Removing cache directory: {cache_dir}")
                    shutil.rmtree(cache_dir)
        return True
    except Exception as e:
        logger.error(f"Error clearing Python cache: {e}")
        return False

async def main():
    """Main function to apply the fix"""
    logger.info("="*80)
    logger.info("STARTING DIRECT FIX FOR DIRECTORY_EXISTS")
    logger.info("="*80)
    
    # Step 1: Fix the SFTPManager class
    logger.info("\n## STEP 1: FIXING SFTP MANAGER CLASS")
    sftp_fixed = fix_sftp_py()
    if not sftp_fixed:
        logger.error("Failed to fix SFTPManager, aborting")
        return
        
    # Step 2: Fix the file discovery module
    logger.info("\n## STEP 2: FIXING FILE DISCOVERY MODULE")
    discovery_fixed = fix_file_discovery_py()
    if not discovery_fixed:
        logger.error("Failed to fix file discovery module, aborting")
        return
    
    # Step 3: Clear Python cache
    logger.info("\n## STEP 3: CLEARING PYTHON CACHE")
    cache_cleared = clear_python_cache()
    if not cache_cleared:
        logger.warning("Failed to clear Python cache, continuing anyway")
        
    # Step 4: Kill and restart the bot
    logger.info("\n## STEP 4: RESTARTING THE BOT")
    restart_success = kill_and_restart_bot()
    if not restart_success:
        logger.error("Failed to restart the bot")
        return
        
    logger.info("\n## FIX COMPLETE")
    logger.info("directory_exists method has been fixed and the bot has been restarted")
    logger.info("="*80)
    
if __name__ == "__main__":
    asyncio.run(main())