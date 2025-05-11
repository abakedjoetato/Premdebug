#!/usr/bin/env python3
"""
Targeted MongoDB Truth Testing Fix Script

This script focuses ONLY on the project's custom codebase, not touching 
any third-party libraries. It finds and fixes all potential MongoDB truth 
testing issues in the core directories (cogs, models, utils) and main files.
"""

import os
import re
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("mongodb_targeted_fixes.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Directories to process - ONLY project code, not third-party libraries
PROCESS_DIRS = [
    'cogs', 
    'models', 
    'utils'
]

# Individual files at root level to process
ROOT_FILES = [
    'main.py',
    'bot.py',
    'app.py',
    'database.py',
    'config.py',
    'commands.py'
]

# Patterns to replace
PATTERNS = [
    # if not variable:
    (r'if\s+not\s+([a-zA-Z0-9_]+)(?=\s*:|\s*\))', r'if \1 is None'),
    
    # if variable:
    (r'if\s+([a-zA-Z0-9_]+)(?=\s*:|\s*\))', r'if \1 is not None'),
    
    # variable or default
    (r'([a-zA-Z0-9_]+)\s+or\s+([^\n:]+?)(?=\s*[,)])', r'\1 if \1 is not None else \2'),
]

# MongoDB-related variable patterns (case insensitive)
MONGODB_VAR_PATTERNS = [
    r'.*db.*', r'.*server.*', r'.*guild.*', r'.*player.*', r'.*model.*',
    r'.*doc.*', r'.*result.*', r'.*record.*', r'.*collection.*', 
    r'.*cursor.*', r'.*faction.*', r'.*bounty.*', r'.*stats.*'
]

def is_mongodb_variable(var_name):
    """Check if a variable name is likely a MongoDB object"""
    var_name = var_name.lower()
    return any(re.match(pattern, var_name, re.IGNORECASE) for pattern in MONGODB_VAR_PATTERNS)

def is_proper_comparison(line, var_name):
    """Check if the line already has a proper 'is None' comparison"""
    patterns = [
        rf'{var_name}\s+is\s+None',
        rf'{var_name}\s+is\s+not\s+None',
        rf'isinstance\({var_name},',
        rf'hasattr\({var_name},',
        rf'getattr\({var_name},',
        rf'len\({var_name}\)',
        rf'{var_name}\.get\(',
        rf'{var_name}\[',
        rf'{var_name}\.find\(',
        rf'{var_name}\.find_one\(',
        r'==',
        r'!=',
        r'>=',
        r'<=',
        r' in ',
        r' and ',
        r' or ',
    ]
    return any(re.search(pattern, line) for pattern in patterns)

def fix_file(file_path):
    """Fix MongoDB truth testing issues in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        changed = False
        changes = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Check each pattern
            for pattern, replacement_template in PATTERNS:
                # Find MongoDB variables in this pattern
                matches = re.finditer(pattern, line)
                for match in matches:
                    var_name = match.group(1)
                    
                    # Only fix MongoDB-related variables and skip if already a proper comparison
                    if is_mongodb_variable(var_name) and not is_proper_comparison(line, var_name):
                        # Replace the specific match
                        full_match = match.group(0)
                        replacement = replacement_template.replace(r'\1', var_name)
                        new_line = line.replace(full_match, replacement, 1)
                        
                        # Only apply if it actually changed
                        if new_line != line:
                            line = new_line
                            changes.append((i+1, original_line.strip(), line.strip()))
                            break
            
            # Update the line in the array
            if line != original_line:
                lines[i] = line
                changed = True
        
        # Write back the changes if any were made
        if changed:
            # Backup the original file
            backup_path = f"{file_path}.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                with open(file_path, 'r', encoding='utf-8') as src:
                    f.write(src.read())
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"Fixed {len(changes)} MongoDB truth testing issues in {file_path}")
            for line_num, old, new in changes:
                logger.info(f"  Line {line_num}: {old} -> {new}")
            
            return len(changes)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0

def process_directory(directory):
    """Process all Python files in a directory recursively"""
    files_fixed = 0
    changes_made = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.endswith('.bak'):
                file_path = os.path.join(root, file)
                changes = fix_file(file_path)
                
                if changes > 0:
                    files_fixed += 1
                    changes_made += changes
    
    return files_fixed, changes_made

def main():
    """Main entry point"""
    logger.info("Starting targeted MongoDB truth testing fix")
    
    total_files_fixed = 0
    total_changes = 0
    
    # Process core directories
    for directory in PROCESS_DIRS:
        if os.path.exists(directory) and os.path.isdir(directory):
            logger.info(f"Processing directory: {directory}")
            files_fixed, changes = process_directory(directory)
            total_files_fixed += files_fixed
            total_changes += changes
    
    # Process individual root files
    for file in ROOT_FILES:
        if os.path.exists(file):
            logger.info(f"Processing file: {file}")
            changes = fix_file(file)
            if changes > 0:
                total_files_fixed += 1
                total_changes += changes
    
    logger.info(f"Fix complete. Made {total_changes} changes in {total_files_fixed} files.")
    return total_files_fixed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
