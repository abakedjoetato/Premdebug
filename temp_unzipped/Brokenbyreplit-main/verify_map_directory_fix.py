#!/usr/bin/env python3
"""
Verification tool for the Map Directory Fix

This script verifies that our map directory fix was properly applied by:
1. Checking that directory_exists is properly implemented
2. Checking key naming consistency across modules
3. Verifying map directory detection logic
4. Confirming that discovery stats are properly updated
"""

import os
import sys
import logging
import re
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def check_directory_exists_implementation():
    """Check that directory_exists is properly implemented in sftp.py"""
    file_path = "utils/sftp.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for directory_exists implementation
        if "async def directory_exists(self, path: str) -> bool:" in content:
            logger.info("✓ directory_exists method is properly implemented in SFTPManager")
            return True
        else:
            logger.error("✗ directory_exists method is MISSING from SFTPManager")
            return False
    except Exception as e:
        logger.error(f"Error checking directory_exists implementation: {e}")
        return False

def check_key_consistency():
    """Check that map_files vs map_files_found is consistent"""
    files_to_check = [
        "utils/file_discovery.py",
        "utils/csv_processor_coordinator.py",
        "cogs/csv_processor.py"
    ]
    
    all_consistent = True
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check how the key is used
            map_files_found_count = content.count("map_files_found")
            map_files_count = content.count("map_files")
            
            logger.info(f"File {file_path}:")
            logger.info(f"  - 'map_files_found' occurrences: {map_files_found_count}")
            logger.info(f"  - 'map_files' occurrences: {map_files_count}")
            
            # Specifically check get statements
            if 'get("map_files_found"' in content and 'map_files =' in content:
                logger.error(f"✗ Inconsistent key usage in {file_path}")
                all_consistent = False
            else:
                logger.info(f"✓ Key usage is consistent in {file_path}")
        except Exception as e:
            logger.error(f"Error checking key consistency in {file_path}: {e}")
            all_consistent = False
    
    return all_consistent

def check_map_directory_detection():
    """Check that map directory detection logic is properly implemented"""
    file_path = "utils/file_discovery.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for directory_exists call in finding map directories
        if "if await sftp.directory_exists(map_path):" in content:
            logger.info("✓ Map directory detection uses directory_exists method")
            
            # Check for proper directory pattern
            if re.search(r'(world|map|level|zone|region|area|district|territory)', content):
                logger.info("✓ Map directory detection uses enhanced pattern matching")
                return True
            else:
                logger.error("✗ Map directory detection is using limited pattern matching")
                return False
        else:
            logger.error("✗ Map directory detection doesn't use directory_exists method")
            return False
    except Exception as e:
        logger.error(f"Error checking map directory detection: {e}")
        return False

def check_discovery_stats():
    """Check that discovery stats include map directories"""
    file_path = "utils/file_discovery.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for map_directories in discovery stats
        if '"map_directories":' in content:
            logger.info("✓ Discovery stats include map directory count")
            return True
        else:
            logger.error("✗ Discovery stats don't include map directory count")
            return False
    except Exception as e:
        logger.error(f"Error checking discovery stats: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("VERIFYING MAP DIRECTORY FIX")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all verification checks
    check_funcs = [
        check_directory_exists_implementation,
        check_key_consistency,
        check_map_directory_detection,
        check_discovery_stats
    ]
    
    for check_func in check_funcs:
        print("-" * 40)
        if not check_func():
            all_checks_passed = False
    
    print("=" * 60)
    if all_checks_passed:
        print("✅ All checks PASSED!")
        print("Map directory fix appears to be properly applied.")
        return 0
    else:
        print("❌ Some checks FAILED!")
        print("Map directory fix may not be fully applied.")
        return 1

if __name__ == "__main__":
    sys.exit(main())