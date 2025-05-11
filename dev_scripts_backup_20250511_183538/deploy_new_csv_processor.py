"""
# module: deploy_new_csv_processor
Deploy New CSV Processor

This script deploys the new stable CSV processor by:
1. Creating a backup of the existing CSV processor
2. Testing the new processor with sample data
3. Renaming the existing processor to _old
4. Installing the new processor

This ensures a safe deployment with rollback capability.
"""
import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment.log')
    ]
)
logger = logging.getLogger("deployment")

# Define file paths
CSV_PROCESSOR_PATH = "cogs/csv_processor.py"
NEW_CSV_PROCESSOR_PATH = "cogs/new_csv_processor.py"
BACKUP_DIR = f"csv_processor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def create_backup():
    """Create a backup of the existing CSV processor cog"""
    logger.info("Creating backup of existing CSV processor cog")
    
    # Create backup directory
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Backup the CSV processor cog
    if os.path.exists(CSV_PROCESSOR_PATH):
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(CSV_PROCESSOR_PATH))
        shutil.copy2(CSV_PROCESSOR_PATH, backup_path)
        logger.info(f"Created backup at {backup_path}")
        return True
    else:
        logger.error(f"CSV processor cog not found at {CSV_PROCESSOR_PATH}")
        return False

async def test_new_processor():
    """Test the new CSV processor with sample data"""
    logger.info("Testing new CSV processor with sample data")
    
    try:
        # Import and run the test script
        from test_new_csv_processor import main as test_main
        await test_main()
        logger.info("New CSV processor tests passed")
        return True
    except Exception as e:
        logger.error(f"Error testing new CSV processor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
def rename_existing_processor():
    """Rename the existing CSV processor to _old"""
    logger.info("Renaming existing CSV processor")
    
    try:
        # Check if the existing processor exists
        if os.path.exists(CSV_PROCESSOR_PATH):
            # Rename to _old
            old_path = f"{CSV_PROCESSOR_PATH}.old"
            shutil.move(CSV_PROCESSOR_PATH, old_path)
            logger.info(f"Renamed existing processor to {old_path}")
        return True
    except Exception as e:
        logger.error(f"Error renaming existing processor: {e}")
        return False
        
def install_new_processor():
    """Install the new CSV processor"""
    logger.info("Installing new CSV processor")
    
    try:
        # Copy the new processor to the cogs directory
        if os.path.exists(NEW_CSV_PROCESSOR_PATH):
            shutil.copy2(NEW_CSV_PROCESSOR_PATH, CSV_PROCESSOR_PATH)
            logger.info(f"Installed new processor at {CSV_PROCESSOR_PATH}")
            return True
        else:
            logger.error(f"New CSV processor not found at {NEW_CSV_PROCESSOR_PATH}")
            return False
    except Exception as e:
        logger.error(f"Error installing new processor: {e}")
        return False
        
def rollback():
    """Rollback to the previous CSV processor if deployment fails"""
    logger.warning("Rolling back to previous CSV processor")
    
    try:
        # Check if we have a backup
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(CSV_PROCESSOR_PATH))
        if os.path.exists(backup_path):
            # Remove the new processor if it exists
            if os.path.exists(CSV_PROCESSOR_PATH):
                os.remove(CSV_PROCESSOR_PATH)
                
            # Restore from backup
            shutil.copy2(backup_path, CSV_PROCESSOR_PATH)
            logger.info(f"Restored from backup at {backup_path}")
            return True
        else:
            logger.error(f"Backup not found at {backup_path}")
            return False
    except Exception as e:
        logger.error(f"Error rolling back: {e}")
        return False

async def main():
    """Main deployment function"""
    logger.info("Starting deployment of new CSV processor")
    
    # Create backup
    if not create_backup():
        logger.error("Failed to create backup, aborting deployment")
        return
        
    # Test new processor
    if not await test_new_processor():
        logger.error("New processor tests failed, aborting deployment")
        return
        
    # Rename existing processor
    if not rename_existing_processor():
        logger.error("Failed to rename existing processor, aborting deployment")
        return
        
    # Install new processor
    if not install_new_processor():
        logger.error("Failed to install new processor, rolling back")
        rollback()
        return
        
    logger.info("Deployment completed successfully")
    logger.info("Please restart the bot to load the new CSV processor")

if __name__ == "__main__":
    asyncio.run(main())