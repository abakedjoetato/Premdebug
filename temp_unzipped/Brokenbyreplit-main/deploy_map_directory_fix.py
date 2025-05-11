
#!/usr/bin/env python3
"""
Deployment script for map directory tracking fix

This script applies the map directory tracking fix and ensures the 
bot is properly restarted to apply the changes.
"""
import os
import sys
import time
import logging
import subprocess
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deploy_map_directory_fix.log")
    ]
)
logger = logging.getLogger("deploy_map_directory_fix")

async def run_command(cmd, shell=True):
    """Run a shell command and log output"""
    logger.info(f"Running command: {cmd}")
    
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=shell
        )
        
        stdout, stderr = await process.communicate()
        
        if stdout:
            logger.info(f"Command output: {stdout.decode().strip()}")
        
        if stderr:
            logger.warning(f"Command error: {stderr.decode().strip()}")
        
        return process.returncode == 0
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False

async def main():
    """Main deployment function"""
    logger.info("Starting map directory fix deployment")
    
    # Verify fix_map_directory_tracking.py exists
    if not os.path.exists("fix_map_directory_tracking.py"):
        logger.error("fix_map_directory_tracking.py not found - please create it first")
        return False
    
    # Make the script executable
    try:
        os.chmod("fix_map_directory_tracking.py", 0o755)
        logger.info("Made fix_map_directory_tracking.py executable")
    except Exception as e:
        logger.warning(f"Could not set executable permissions: {e}")
    
    # Run the fix script
    logger.info("Running map directory tracking fix script")
    fix_success = await run_command("python fix_map_directory_tracking.py")
    
    if not fix_success:
        logger.error("Fix script failed, aborting deployment")
        return False
    
    logger.info("Fix script completed successfully")
    
    # Check if the bot is running
    bot_running = await run_command("ps aux | grep 'python main.py' | grep -v grep")
    
    if bot_running:
        logger.info("Bot is running, restarting it to apply fixes")
        
        # Try graceful shutdown first
        await run_command("pkill -f 'python main.py'")
        
        # Wait for bot to shut down
        logger.info("Waiting for bot to shut down")
        await asyncio.sleep(5)
        
        # Forcefully kill if still running
        still_running = await run_command("ps aux | grep 'python main.py' | grep -v grep")
        if still_running:
            logger.warning("Bot still running, force killing")
            await run_command("pkill -9 -f 'python main.py'")
            await asyncio.sleep(2)
    else:
        logger.info("Bot is not running")
    
    # Start the bot
    logger.info("Starting the bot to apply fixes")
    await run_command("python main.py &")
    
    logger.info("Deployment completed successfully")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
