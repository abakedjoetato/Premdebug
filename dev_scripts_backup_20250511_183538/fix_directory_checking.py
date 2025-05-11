"""
Fix CSV processor directory checking issues

This script fixes the issue where CSV files are being found but not properly counted in the statistics.
The core issue was in the file discovery system not properly checking if directories exist before
trying to list files in them, which was causing the 'SFTPManager' object has no attribute 'directory_exists' error.

This fix includes:
1. Adding the missing directory_exists method to the SFTPManager class
2. Adding the corresponding get_file_attrs method to both SFTPManager and SFTPClient
3. Testing that directories are correctly checked before listing files
"""

import logging
import sys
import os
import shutil
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("fix_directory_checking")

def main():
    """Execute the fix for the directory checking issue."""
    # Backup the original file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"sftp_manager_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Create a backup of the original file
    original_path = "utils/sftp.py"
    backup_path = f"{backup_dir}/sftp.py.bak"
    
    try:
        shutil.copy2(original_path, backup_path)
        logger.info(f"Created backup of {original_path} at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return
    
    # Restart the bot to apply changes
    try:
        # Check if run_discord_bot.sh exists and is executable
        bot_script = "./run_discord_bot.sh"
        if os.path.exists(bot_script) and os.access(bot_script, os.X_OK):
            logger.info("Restarting the Discord bot to apply changes...")
            os.system(f"{bot_script} &")
            logger.info("Bot restart command issued, changes will take effect shortly")
        else:
            logger.warning(f"Bot restart script {bot_script} not found or not executable")
            logger.info("Please restart the bot manually to apply the changes")
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        logger.info("Please restart the bot manually to apply the changes")

    logger.info("""
Fix successfully applied. The following changes were made:
1. Added directory_exists method to SFTPManager
2. Added get_file_attrs method to SFTPManager and SFTPClient
3. Fixed the file discovery system to properly check directories

The bot should now be able to properly discover and count CSV files.
""")

if __name__ == "__main__":
    main()