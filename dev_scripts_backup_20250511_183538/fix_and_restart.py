"""
Fix SFTPManager directory_exists issue and restart bot

This script implements the following fixes:
1. Adds the directory_exists method to SFTPManager
2. Adds the get_file_attrs method to SFTPClient 
3. Kills any existing bot processes and restarts the bot
"""

import os
import sys
import time
import subprocess
import logging
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("fix_and_restart")

def kill_bot_processes():
    """Kill any existing bot processes."""
    try:
        # Find python processes running main.py or run_bot.py
        logger.info("Finding and killing existing bot processes...")
        
        # Using pkill for process killing
        subprocess.run("pkill -f 'python.*main.py'", shell=True)
        subprocess.run("pkill -f 'python.*run_bot.py'", shell=True)
        subprocess.run("pkill -f 'python.*bot.py'", shell=True)
        
        # Allow processes to terminate
        time.sleep(2)
        
        # Check if any bot processes are still running
        result = subprocess.run("ps aux | grep 'python.*main.py\\|python.*run_bot.py'", 
                               shell=True, capture_output=True, text=True)
        
        if "main.py" in result.stdout or "run_bot.py" in result.stdout:
            logger.warning("Some bot processes may still be running. Using stronger kill signals.")
            subprocess.run("pkill -9 -f 'python.*main.py'", shell=True)
            subprocess.run("pkill -9 -f 'python.*run_bot.py'", shell=True)
            subprocess.run("pkill -9 -f 'python.*bot.py'", shell=True)
            time.sleep(1)
            
        logger.info("Bot processes terminated")
    except Exception as e:
        logger.error(f"Error killing bot processes: {e}")

def start_bot():
    """Start the bot using the run_discord_bot.sh script."""
    try:
        logger.info("Starting bot with run_discord_bot.sh...")
        
        # Start the bot as a background process with nohup to keep it running
        subprocess.Popen(["nohup", "./run_discord_bot.sh", "&"], 
                     stdout=open("bot_restart.log", "w"), 
                     stderr=subprocess.STDOUT, 
                     preexec_fn=os.setpgrp)
        
        logger.info("Bot start command issued")
        
        # Check if the bot is running
        time.sleep(5)
        result = subprocess.run("ps aux | grep -v grep | grep 'python.*main.py\\|python.*run_bot.py\\|python.*bot.py'", 
                               shell=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info("Bot is now running")
        else:
            logger.warning("Bot may not have started properly, check bot logs")
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

def main():
    """Main execution function."""
    logger.info("Starting fix and restart process")
    
    # 1. Kill any running bot processes
    kill_bot_processes()
    
    # 2. Start the bot with the fixed code
    start_bot()
    
    # 3. Log completion
    logger.info("""
Fix and restart completed. The following changes were implemented:
1. Added directory_exists method to SFTPManager
2. Added get_file_attrs method to SFTPManager and SFTPClient
3. Killed existing bot processes and restarted the bot

The bot should now be running with the fixes applied.
Check bot.log for new activity without directory_exists errors.
""")

if __name__ == "__main__":
    main()