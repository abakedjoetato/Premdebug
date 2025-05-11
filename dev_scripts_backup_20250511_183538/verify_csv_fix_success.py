
#!/usr/bin/env python3
"""
Verification script for CSV processing fixes

This script checks that the CSV processing fixes were applied 
and are working correctly by examining logs and file contents.
"""
import os
import re
import sys
import logging
import asyncio
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("verify_csv_fix.log")
    ]
)
logger = logging.getLogger("verify_csv_fix")

# Files to check
CSV_PROCESSOR_PATH = "cogs/csv_processor.py"
FILE_DISCOVERY_PATH = "utils/file_discovery.py"
CSV_PARSER_PATH = "utils/csv_parser.py"
BOT_LOG_PATH = "bot.log"

def check_file_content(file_path, patterns):
    """Check if patterns exist in file content"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        results = {}
        for name, pattern in patterns.items():
            found = pattern in content
            results[name] = found
            if found:
                logger.info(f"✓ {name} check passed in {file_path}")
            else:
                logger.error(f"✗ {name} check failed in {file_path}")
        
        all_passed = all(results.values())
        if all_passed:
            logger.info(f"All checks passed for {file_path}")
        else:
            failed = [name for name, result in results.items() if not result]
            logger.error(f"Failed checks for {file_path}: {failed}")
            
        return all_passed
    except Exception as e:
        logger.error(f"Error checking {file_path}: {e}")
        return False

def check_code_fixes():
    """Check that code fixes were properly applied"""
    logger.info("Checking code fixes...")
    
    # Check CSV processor fixes
    csv_processor_patterns = {
        "map_files_tracking": "Added {len(map_full_paths)} CSV files from map directory",
        "emergency_check": "Emergency check: No map files found",
        "critical_recovery": "Critical recovery: Using",
        "files_processing": "Found {len(self.files_to_process)} map directory CSV files"
    }
    csv_processor_check = check_file_content(CSV_PROCESSOR_PATH, csv_processor_patterns)
    
    # Check file discovery fixes
    file_discovery_patterns = {
        "world_directories": "world_0",
        "world_regex": "CRITICAL FIX: More specific regex for map directories",
        "stats_keys": "map_files",
        "discovery_stats": "discovery_stats"
    }
    file_discovery_check = check_file_content(FILE_DISCOVERY_PATH, file_discovery_patterns)
    
    # Check CSV parser fixes
    csv_parser_patterns = {
        "file_position": "Normalize file path",
        "delimiter_detection": "delimiter that appears more frequently"
    }
    csv_parser_check = check_file_content(CSV_PARSER_PATH, csv_parser_patterns)
    
    # Overall code fixes check
    all_code_fixes = csv_processor_check and file_discovery_check and csv_parser_check
    
    if all_code_fixes:
        logger.info("✅ All code fixes verified successfully")
    else:
        logger.error("❌ Some code fixes could not be verified")
    
    return all_code_fixes

def check_bot_logs():
    """Check bot logs for successful operation after fixes"""
    if not os.path.exists(BOT_LOG_PATH):
        logger.error(f"Bot log not found: {BOT_LOG_PATH}")
        return False
        
    try:
        # Get the last 1000 lines of the log to check recent operation
        with open(BOT_LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            log_lines = f.readlines()
            recent_log = "".join(log_lines[-1000:])
        
        # Check for critical error patterns
        error_patterns = [
            "Error in csv_processor",
            "Failed to process CSV files",
            "Exception processing map directory",
            "Failed to discover CSV files"
        ]
        
        for pattern in error_patterns:
            if pattern in recent_log:
                logger.error(f"Found error pattern in logs: {pattern}")
                return False
        
        # Check for success patterns
        success_patterns = [
            "Successfully found",
            "Files Found=",
            "Adding CSV files to processing queue",
            "Map directory traversal complete"
        ]
        
        success_found = False
        for pattern in success_patterns:
            if pattern in recent_log:
                logger.info(f"Found success pattern in logs: {pattern}")
                success_found = True
                break
        
        if success_found:
            logger.info("✅ Bot logs indicate successful operation")
            return True
        else:
            logger.warning("⚠ No clear success patterns found in bot logs")
            return False
    except Exception as e:
        logger.error(f"Error checking bot logs: {e}")
        return False

async def main():
    """Main verification function"""
    logger.info("Starting CSV fix verification")
    
    # Check that the bot is running
    logger.info("Waiting 10 seconds for bot to be fully operational...")
    time.sleep(10)  # Wait for bot to be fully operational
    
    # Verify code fixes
    code_fixes_verified = check_code_fixes()
    
    # Verify bot logs
    logs_verified = check_bot_logs()
    
    # Overall verification result
    overall_success = code_fixes_verified and logs_verified
    
    if overall_success:
        logger.info("✅ CSV processing fixes verified successfully!")
    else:
        logger.warning("⚠ CSV processing fixes verification had issues")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    print("=" * 60)
    print(f"Verification {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
    sys.exit(0 if success else 1)
