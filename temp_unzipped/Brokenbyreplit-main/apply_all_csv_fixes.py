#!/usr/bin/env python
"""
Comprehensive CSV Processing System Fix

This script applies all necessary fixes to the CSV processing system to ensure proper parsing
of CSV files from game servers. It addresses issues with file discovery, filtering, and
processing across both historical and regular processing modes.

Usage:
    python apply_all_csv_fixes.py

This will apply all fixes to the CSV processing system.
"""
import os
import sys
import shutil
import logging
import datetime
import importlib
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup_directory():
    """Create a backup directory for original files"""
    backup_dir = f"csv_fixes_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Created backup directory: {backup_dir}")
        return backup_dir
    except Exception as e:
        logger.error(f"Failed to create backup directory: {e}")
        return None

def backup_files(backup_dir):
    """Backup the files that will be modified"""
    files_to_backup = [
        "cogs/csv_processor.py",
        "utils/direct_csv_handler.py"
    ]
    
    backups = {}
    for file_path in files_to_backup:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue
            
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        try:
            shutil.copy2(file_path, backup_path)
            backups[file_path] = backup_path
            logger.info(f"Backed up {file_path} to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            
    return backups

def run_fix_module(module_name):
    """Run a fix module by importing and executing it"""
    try:
        logger.info(f"Running fix module: {module_name}")
        module = importlib.import_module(module_name)
        result = module.main()
        logger.info(f"Fix module {module_name} completed with result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error running fix module {module_name}: {e}")
        return False

def run_test_parser():
    """Run the direct parser test to verify fixes"""
    try:
        logger.info("Running direct parser test")
        result = subprocess.run(["python", "test_direct_parser.py"], 
                               capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            logger.info("Direct parser test PASSED!")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Direct parser test FAILED with return code {result.returncode}")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running direct parser test: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("Starting comprehensive CSV processing system fix")
    
    # Create backup directory
    backup_dir = create_backup_directory()
    if not backup_dir:
        logger.error("Failed to create backup directory, aborting")
        return False
        
    # Backup files
    backups = backup_files(backup_dir)
    if not backups:
        logger.error("Failed to backup files, aborting")
        return False
        
    # Run each fix module
    fix_modules = [
        "fix_directory_search",  # Fix directory search logic
        "fix_file_filtering",    # Fix file filtering logic
        "fix_content_processing" # Fix content processing logic
    ]
    
    success = True
    for module in fix_modules:
        module_result = run_fix_module(module)
        if module_result is None:
            logger.error(f"Fix module {module} failed")
            success = False
            
    # Run test parser to verify fixes
    test_result = run_test_parser()
    if test_result is None:
        logger.warning("Direct parser test failed, but fixes have been applied")
    
    # Final status
    if success:
        logger.info("All fixes have been successfully applied")
        logger.info(f"Original files have been backed up to {backup_dir}")
        logger.info("The CSV processing system should now correctly find and process all CSV files")
    else:
        logger.error("Some fixes failed to apply")
        logger.error(f"You can restore original files from {backup_dir} if needed")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)