
#!/usr/bin/env python3
"""
Deployment script for robust CSV processing fix

This script safely applies the CSV processing fixes and restarts 
the bot only if the fixes were successfully applied.
"""
import os
import sys
import time
import logging
import subprocess
import asyncio
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deploy_robust_csv_fix.log")
    ]
)
logger = logging.getLogger("deploy_robust_csv_fix")

# Fix script path
FIX_SCRIPT = "fix_csv_processing_robust.py"

async def run_command(cmd, timeout=60):
    """Run a shell command with proper error handling and timeout"""
    logger.info(f"Running command: {cmd}")
    
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            
            if stdout:
                for line in stdout.decode().splitlines():
                    logger.info(f"Command output: {line}")
            
            if stderr:
                for line in stderr.decode().splitlines():
                    logger.warning(f"Command error: {line}")
            
            success = process.returncode == 0
            if success:
                logger.info(f"Command completed successfully with return code {process.returncode}")
            else:
                logger.error(f"Command failed with return code {process.returncode}")
                
            return success
        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout} seconds")
            process.kill()
            return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        traceback.print_exc()
        return False

async def is_bot_running():
    """Check if the bot is currently running"""
    check_cmd = "ps aux | grep 'python main.py' | grep -v grep"
    result = await run_command(check_cmd)
    return result

async def stop_bot():
    """Stop the bot"""
    logger.info("Stopping the bot")
    
    # Try graceful shutdown first
    await run_command("pkill -f 'python main.py'")
    
    # Wait for bot to shut down
    logger.info("Waiting for bot to shut down")
    await asyncio.sleep(5)
    
    # Check if it's still running
    if await is_bot_running():
        logger.warning("Bot is still running, force killing")
        await run_command("pkill -9 -f 'python main.py'")
        await asyncio.sleep(2)
    
    # Verify it's stopped
    if await is_bot_running():
        logger.error("Failed to stop the bot")
        return False
    else:
        logger.info("Bot stopped successfully")
        return True

async def start_bot():
    """Start the bot"""
    logger.info("Starting the bot")
    
    # Start in background
    await run_command("nohup python main.py > bot_restart.log 2>&1 &")
    
    # Wait a bit for startup
    await asyncio.sleep(5)
    
    # Verify it's running
    if await is_bot_running():
        logger.info("Bot started successfully")
        return True
    else:
        logger.error("Failed to start the bot")
        return False

async def apply_fix():
    """Apply the CSV processing fix"""
    logger.info(f"Applying CSV processing fix using {FIX_SCRIPT}")
    
    # Make sure the script exists
    if not os.path.exists(FIX_SCRIPT):
        logger.error(f"Fix script {FIX_SCRIPT} not found")
        return False
    
    # Make executable if needed
    try:
        os.chmod(FIX_SCRIPT, 0o755)
    except Exception as e:
        logger.warning(f"Could not set executable permissions: {e}")
    
    # Run the fix script
    fix_success = await run_command(f"python {FIX_SCRIPT}")
    
    if fix_success:
        logger.info("CSV processing fix applied successfully")
    else:
        logger.error("Failed to apply CSV processing fix")
    
    return fix_success

async def check_fix_logs():
    """Check the fix logs for success indicators"""
    try:
        with open("robust_csv_fix.log", "r") as f:
            log_content = f.read()
            
        if "Successfully applied CSV processing fixes" in log_content:
            logger.info("Found success message in fix logs")
            return True
        else:
            logger.warning("No success message found in fix logs")
            return False
    except Exception as e:
        logger.error(f"Error checking fix logs: {e}")
        return False

async def main():
    """Main deployment function"""
    start_time = datetime.now()
    logger.info(f"Starting deployment at {start_time}")
    
    try:
        # Check if bot is running
        bot_was_running = await is_bot_running()
        logger.info(f"Bot running status: {bot_was_running}")
        
        # Stop bot if it's running
        if bot_was_running:
            logger.info("Stopping bot before applying fixes")
            if not await stop_bot():
                logger.error("Failed to stop bot, continuing with caution")
        
        # Apply the fix
        logger.info("Applying CSV processing fix")
        fix_success = await apply_fix()
        
        # Verify fix logs
        logs_success = await check_fix_logs()
        
        # Determine overall success
        overall_success = fix_success and logs_success
        
        if overall_success:
            logger.info("✅ Fix applied and verified successfully!")
        else:
            logger.warning("❌ Fix application had issues")
        
        # Start bot if it was running before
        if bot_was_running:
            logger.info("Restarting bot")
            start_success = await start_bot()
            
            if start_success:
                logger.info("Bot restarted successfully")
            else:
                logger.error("Failed to restart bot")
        
        # Deployment complete
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Deployment completed in {duration:.2f} seconds")
        
        return overall_success
    except Exception as e:
        logger.error(f"Error during deployment: {e}")
        traceback.print_exc()
        
        # Try to ensure bot is running even if deployment failed
        if await is_bot_running():
            logger.info("Bot is still running despite deployment error")
        else:
            logger.warning("Bot is not running after deployment error, attempting to start")
            await start_bot()
            
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
