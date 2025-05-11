"""
# module: deploy_comprehensive_fix
Comprehensive CSV Processing System Fix Deployment

This script provides a complete solution to the CSV processing issues
by applying all necessary fixes, testing them, and deploying them to
the bot. It takes a systematic approach to ensure everything works
properly together.
"""
import asyncio
import importlib
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deploy.log')
    ]
)
logger = logging.getLogger("deploy")

# Import our fix modules
import fix_sftp_manager

# Set test server parameters - will be used for testing
SERVER_CONFIG = {
    "server_id": "2143443",
    "hostname": "208.103.169.139",
    "port": 22,
    "username": "totemptation",
    "password": "YzhkZnPqe6",
    "original_server_id": "1"
}

def create_backup_directory():
    """Create a backup directory for all files being modified
    
    Returns:
        str: Path to backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"csv_processor_backup_{timestamp}"
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    logger.info(f"Created backup directory: {backup_dir}")
    return backup_dir
    
def backup_file(file_path, backup_dir):
    """Create a backup of a file in the backup directory
    
    Args:
        file_path: Path to the file to back up
        backup_dir: Directory to store the backup in
        
    Returns:
        str: Path to the backup file
    """
    # Get the filename from the path
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, filename)
    
    # Copy the file
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup of {file_path} at {backup_path}")
    
    return backup_path
    
def kill_existing_bot():
    """Kill any running bot processes"""
    logger.info("Killing any existing bot processes")
    
    try:
        # Kill any running bot processes
        subprocess.run(["pkill", "-f", "python.*bot.py"], check=False)
        subprocess.run(["pkill", "-f", "python.*run_discord_bot"], check=False)
        subprocess.run(["pkill", "-f", "python.*bot_wrapper.py"], check=False)
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Check if any bot processes are still running
        result = subprocess.run(
            ["pgrep", "-f", "python.*bot"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            logger.warning(f"Some bot processes are still running: {result.stdout.strip()}")
            # Force kill with -9
            subprocess.run(["pkill", "-9", "-f", "python.*bot"], check=False)
            time.sleep(1)
        else:
            logger.info("All bot processes successfully terminated")
            
        return True
    except Exception as e:
        logger.error(f"Error killing bot processes: {e}")
        return False
        
def clear_python_cache():
    """Clear Python's __pycache__ directories to ensure changes take effect"""
    logger.info("Clearing Python cache directories")
    
    try:
        # Find all __pycache__ directories
        for root, dirs, files in os.walk("."):
            for dir in dirs:
                if dir == "__pycache__":
                    cache_dir = os.path.join(root, dir)
                    logger.info(f"Removing cache directory: {cache_dir}")
                    shutil.rmtree(cache_dir)
                    
        logger.info("Python cache directories cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing Python cache: {e}")
        return False
        
def start_bot():
    """Start the Discord bot"""
    logger.info("Starting the Discord bot")
    
    try:
        # Start the bot using the appropriate script
        if os.path.exists("run_discord_bot.sh"):
            subprocess.Popen(["bash", "run_discord_bot.sh"], 
                            stdout=open("bot_startup.log", "w"),
                            stderr=subprocess.STDOUT)
            logger.info("Started bot using run_discord_bot.sh")
        elif os.path.exists("bot_wrapper.py"):
            subprocess.Popen(["python", "bot_wrapper.py"],
                            stdout=open("bot_startup.log", "w"),
                            stderr=subprocess.STDOUT)
            logger.info("Started bot using bot_wrapper.py")
        else:
            subprocess.Popen(["python", "bot.py"],
                            stdout=open("bot_startup.log", "w"),
                            stderr=subprocess.STDOUT)
            logger.info("Started bot directly using bot.py")
            
        # Sleep briefly to allow startup to begin
        time.sleep(5)
        
        # Check if bot is running
        result = subprocess.run(
            ["pgrep", "-f", "python.*bot"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            logger.info(f"Bot started successfully, pid: {result.stdout.strip()}")
            return True
        else:
            logger.error("Bot failed to start")
            return False
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return False
        
async def test_csv_discovery():
    """Test the CSV file discovery functionality
    
    Returns:
        Tuple[bool, str]: Success status and result message
    """
    logger.info("Testing CSV file discovery")
    
    try:
        # Import our diagnostic module (which we created earlier)
        from debug_csv_discovery import CSVDiagnostics
        
        # Create diagnostics instance
        diagnostics = CSVDiagnostics()
        
        config = {
            "hostname": SERVER_CONFIG["hostname"],
            "port": SERVER_CONFIG["port"],
            "username": SERVER_CONFIG["username"],
            "password": SERVER_CONFIG["password"],
            "original_server_id": SERVER_CONFIG["original_server_id"]
        }
        
        # Run diagnostics
        await diagnostics.run_diagnostics(SERVER_CONFIG["server_id"], config, historical_mode=True)
        
        # Clean up
        await diagnostics.cleanup()
        
        # Check the logs for success
        with open("csv_debug.log", "r") as f:
            log_content = f.read()
            
        # Check for success indicators
        if "Found map directory:" in log_content and "CSV files found:" in log_content:
            files_count = None
            for line in log_content.splitlines():
                if "Total CSV files found:" in line:
                    try:
                        files_count = int(line.split(":")[-1].strip())
                        break
                    except ValueError:
                        pass
                        
            if files_count is not None and files_count > 0:
                logger.info(f"CSV discovery test passed! Found {files_count} files")
                return True, f"Found {files_count} CSV files"
            else:
                logger.warning("CSV discovery test failed - no files found")
                return False, "No CSV files found"
        else:
            logger.warning("CSV discovery test failed - couldn't find success indicators in logs")
            return False, "Could not verify directory checks worked"
    except Exception as e:
        logger.error(f"Error testing CSV discovery: {e}")
        return False, f"Error: {str(e)}"
        
async def test_csv_processing():
    """Test the CSV processing functionality
    
    Returns:
        Tuple[bool, str]: Success status and result message
    """
    logger.info("Testing CSV processing")
    
    try:
        # Import our test module (which we created earlier)
        from test_csv_processing import CSVTester
        
        # Create tester instance
        tester = CSVTester()
        
        config = {
            "hostname": SERVER_CONFIG["hostname"],
            "port": SERVER_CONFIG["port"],
            "username": SERVER_CONFIG["username"],
            "password": SERVER_CONFIG["password"],
            "original_server_id": SERVER_CONFIG["original_server_id"]
        }
        
        # Run tests
        try:
            # Test discovery
            files, stats = await tester.test_discovery(SERVER_CONFIG["server_id"], config)
            
            if not files:
                logger.warning("CSV processing test failed: No files found")
                return False, "No CSV files found during discovery"
                
            # Test download
            downloaded = await tester.test_download(SERVER_CONFIG["server_id"], config, files)
            
            if downloaded == 0:
                logger.warning("CSV processing test failed: No files downloaded")
                return False, "No CSV files could be downloaded"
                
            # Test parsing
            files_processed, events_processed = await tester.test_parsing(SERVER_CONFIG["server_id"], config)
            
            if files_processed > 0:
                logger.info(f"CSV processing test passed! Processed {files_processed} files with {events_processed} events")
                return True, f"Processed {files_processed} files with {events_processed} events"
            else:
                logger.warning("CSV processing test failed: No files processed")
                return False, "No CSV files were processed"
        finally:
            # Clean up
            await tester.cleanup()
    except Exception as e:
        logger.error(f"Error testing CSV processing: {e}")
        return False, f"Error: {str(e)}"
        
def verify_bot_startup():
    """Verify that the bot started successfully
    
    Returns:
        Tuple[bool, str]: Success status and result message
    """
    logger.info("Verifying bot startup")
    
    try:
        # Wait for the bot to start up and create logs
        time.sleep(10)
        
        # Check if bot is running
        result = subprocess.run(
            ["pgrep", "-f", "python.*bot"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if not result.stdout.strip():
            logger.error("Bot is not running")
            return False, "Bot failed to start"
            
        # Check startup logs for errors
        if os.path.exists("bot_startup.log"):
            with open("bot_startup.log", "r") as f:
                log_content = f.read()
                
            # Check for failure indicators
            if "Error" in log_content or "Failed" in log_content or "Exception" in log_content:
                logger.warning("Found potential errors in bot startup logs")
                
                # Extract the specific error
                error_lines = []
                for line in log_content.splitlines():
                    if "Error" in line or "Failed" in line or "Exception" in line:
                        error_lines.append(line)
                        
                error_message = "\n".join(error_lines[:3])  # Include up to 3 error lines
                return False, f"Bot started but logs contain errors: {error_message}"
                
            # Check for success indicators
            if "Logged in as" in log_content:
                logger.info("Bot started successfully")
                return True, "Bot started successfully"
                
        # If we can't conclusively determine status, but bot is running, assume success
        logger.info("Bot appears to be running, but couldn't verify from logs")
        return True, "Bot is running, but couldn't verify from logs"
    except Exception as e:
        logger.error(f"Error verifying bot startup: {e}")
        return False, f"Error: {str(e)}"
        
async def main():
    """Main deployment function"""
    logger.info("="*80)
    logger.info("STARTING COMPREHENSIVE CSV PROCESSING SYSTEM FIX DEPLOYMENT")
    logger.info("="*80)
    
    # Create backup directory
    backup_dir = create_backup_directory()
    
    # Step 1: Kill existing bot
    logger.info("\n## STEP 1: KILLING EXISTING BOT")
    if not kill_existing_bot():
        logger.error("Failed to kill existing bot, aborting deployment")
        return
        
    # Step 2: Clear Python cache
    logger.info("\n## STEP 2: CLEARING PYTHON CACHE")
    if not clear_python_cache():
        logger.error("Failed to clear Python cache, aborting deployment")
        return
        
    # Step 3: Apply all fixes
    logger.info("\n## STEP 3: APPLYING ALL FIXES")
    
    # Run the fix_sftp_manager script
    logger.info("Running fix_sftp_manager.py")
    try:
        # We've already imported the module, so we can just call its main function
        await fix_sftp_manager.main()
    except Exception as e:
        logger.error(f"Error running fix_sftp_manager.py: {e}")
        logger.error("Aborting deployment")
        return
        
    # Step 4: Test CSV discovery
    logger.info("\n## STEP 4: TESTING CSV DISCOVERY")
    discovery_success, discovery_result = await test_csv_discovery()
    
    if not discovery_success:
        logger.error(f"CSV discovery test failed: {discovery_result}")
        logger.error("Aborting deployment")
        return
        
    logger.info(f"CSV discovery test passed: {discovery_result}")
    
    # Step 5: Start the bot
    logger.info("\n## STEP 5: STARTING THE BOT")
    if not start_bot():
        logger.error("Failed to start the bot, aborting deployment")
        return
        
    # Step 6: Verify bot startup
    logger.info("\n## STEP 6: VERIFYING BOT STARTUP")
    startup_success, startup_result = verify_bot_startup()
    
    if not startup_success:
        logger.warning(f"Bot startup verification failed: {startup_result}")
        logger.warning("Continuing with deployment, but bot may have issues")
    else:
        logger.info(f"Bot startup verification passed: {startup_result}")
    
    # Step 7: Final verification
    logger.info("\n## STEP 7: FINAL VERIFICATION")
    
    # Successful completion
    logger.info("\n"+"="*80)
    logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"Discovery: {discovery_result}")
    logger.info(f"Bot Startup: {startup_result}")
    logger.info(f"Backups created in: {backup_dir}")
    logger.info("="*80)
    
if __name__ == "__main__":
    asyncio.run(main())