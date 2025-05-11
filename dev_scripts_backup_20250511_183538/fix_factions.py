#!/usr/bin/env python3
"""
Script to fix all MongoDB truth testing issues and line continuation errors in factions.py
"""

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Path to the file
FILE_PATH = 'cogs/factions.py'

# Backup the original file
def backup_file():
    """Create a backup of the original file"""
    with open(FILE_PATH, 'r', encoding='utf-8') as src:
        with open(f"{FILE_PATH}.bak", 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    logger.info(f"Created backup of {FILE_PATH} to {FILE_PATH}.bak")

# Fix the specific pattern with the problematic line continuation
def fix_line_continuation():
    """Fix line continuation errors in the file"""
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the specific pattern
    bad_pattern = r'if\s+not\s+factions\s+if\s+factions\s+is\s+not\s+None\s+else\s+\\2\)\s*==\s*0:'
    replacement = 'if factions is None or len(factions) == 0:'
    
    # Count and replace
    count = len(re.findall(bad_pattern, content))
    
    if count > 0:
        logger.info(f"Found {count} instances of the problematic pattern")
        fixed_content = re.sub(bad_pattern, replacement, content)
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        logger.info(f"Fixed {count} instances in {FILE_PATH}")
        return count
    else:
        logger.info("No problematic patterns found")
        return 0

def main():
    """Main entry point"""
    logger.info(f"Starting fix for {FILE_PATH}")
    
    # Create backup
    backup_file()
    
    # Fix patterns
    fixed_count = fix_line_continuation()
    
    if fixed_count > 0:
        logger.info(f"Successfully fixed {fixed_count} issues in {FILE_PATH}")
    else:
        logger.info(f"No issues found or fixed in {FILE_PATH}")

if __name__ == "__main__":
    main()
