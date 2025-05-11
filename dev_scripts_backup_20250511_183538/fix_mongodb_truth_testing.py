#!/usr/bin/env python3
"""
Comprehensive MongoDB Truth Testing Fix Script

This script finds and fixes all potential MongoDB truth testing issues in the entire codebase.
Instead of focusing on specific files or patterns, it systematically examines all Python files
and fixes problematic boolean truthiness checks for objects that might be MongoDB documents.

The script also creates detailed logs of all changes made for verification.
"""

import os
import re
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("mongodb_fixes.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# MongoDB-related variable name patterns
MONGODB_VARS = [
    r'.*_model$', r'.*server.*', r'.*guild.*', r'.*player.*',
    r'.*faction.*', r'.*document.*', r'.*doc.*', r'.*record.*',
    r'.*result.*', r'.*db[_.].*', r'.*collection.*', r'.*cursor.*',
    r'.*db$', r'events?', r'bounty', r'economy', r'stats', r'faction',
]

# Patterns to identify MongoDB truthiness tests
BOOLEAN_PATTERNS = [
    # if var:
    (r'if\s+([a-zA-Z0-9_]+)(?=\s*:)', r'if \1 is not None'),
    # if not var:
    (r'if\s+not\s+([a-zA-Z0-9_]+)(?=\s*:)', r'if \1 is None'),
    # var or default
    (r'([a-zA-Z0-9_]+)\s+or\s+([^:]+?)(?=\s*[,)])', r'\1 if \1 is not None else \2'),
    # if var and other:
    (r'if\s+([a-zA-Z0-9_]+)(?=\s+and\b)', r'if \1 is not None'),
    # if not var or 
    (r'if\s+not\s+([a-zA-Z0-9_]+)(?=\s+or\b)', r'if \1 is None'),
    # bool(var)
    (r'bool\(([a-zA-Z0-9_]+)\)', r'\1 is not None'),
]

# Directories to exclude
EXCLUDE_DIRS = set(['.git', 'venv', 'temp', 'tmp', '__pycache__', 'node_modules'])

# Path patterns to exclude
EXCLUDE_PATH_PATTERNS = [
    r'.*\.git.*', r'.*\.venv.*', r'.*\.bak$', r'.*\.tmp$', r'.*\.log$'
]

def should_process_path(path: str) -> bool:
    """Check if a path should be processed"""
    # Skip excluded directories
    parts = Path(path).parts
    if any(exclude in parts for exclude in EXCLUDE_DIRS):
        return False
    
    # Skip excluded path patterns
    if any(re.match(pattern, path) for pattern in EXCLUDE_PATH_PATTERNS):
        return False
    
    return True

def is_mongodb_var(var_name: str) -> bool:
    """Check if a variable name is likely to be a MongoDB object"""
    var_name = var_name.lower()
    return any(re.match(pattern, var_name, re.IGNORECASE) for pattern in MONGODB_VARS)

def fix_file(file_path: str) -> Tuple[int, List[str]]:
    """Fix MongoDB truthiness issues in a file"""
    if not os.path.exists(file_path) or not file_path.endswith('.py'):
        return 0, []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        change_details = []
        
        # Process line by line to maintain proper context
        lines = content.split('\n')
        for i, line in enumerate(lines):
            original_line = line
            
            # Apply each pattern
            for pattern, replacement_template in BOOLEAN_PATTERNS:
                # Find all variables in this pattern
                matches = re.finditer(pattern, line)
                for match in matches:
                    var_name = match.group(1)
                    
                    # Only fix MongoDB-related variables
                    if is_mongodb_var(var_name):
                        # Create a specific replacement for this match
                        full_match = match.group(0)
                        replacement = replacement_template.replace(r'\1', var_name)
                        
                        # Only replace the specific match, not all occurrences
                        line = line.replace(full_match, replacement, 1)
                        
                        if line != original_line:
                            changes_made += 1
                            change_details.append(f"Line {i+1}: '{original_line}' -> '{line}'")
                            break  # Only apply one fix per line to avoid cascading changes
            
            # Update the line
            lines[i] = line
        
        # If changes were made, write the file
        if changes_made > 0:
            # Create backup
            backup_path = f"{file_path}.mongodb.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            logger.info(f"Fixed {changes_made} MongoDB truth testing issues in {file_path}")
            
        return changes_made, change_details
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0, [f"ERROR: {str(e)}"]

def process_directory(directory: str) -> Dict[str, List[str]]:
    """Process all Python files in a directory recursively"""
    changes = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                if not should_process_path(file_path):
                    continue
                
                changes_count, change_details = fix_file(file_path)
                
                if changes_count > 0:
                    changes[file_path] = change_details
    
    return changes

def main():
    """Main entry point"""
    logger.info("Starting comprehensive MongoDB truth testing fix")
    
    # Process main directories
    dirs_to_process = ['.', 'cogs', 'models', 'utils']
    
    total_files_changed = 0
    total_changes = 0
    all_changes = {}
    
    for directory in dirs_to_process:
        if os.path.exists(directory) and os.path.isdir(directory):
            logger.info(f"Processing directory: {directory}")
            changes = process_directory(directory)
            
            total_files_changed += len(changes)
            for file_path, details in changes.items():
                total_changes += len(details)
            
            all_changes.update(changes)
    
    # Log summary
    logger.info(f"Fix complete. Made {total_changes} changes in {total_files_changed} files.")
    
    # Write detailed report
    with open('mongodb_truth_testing_fixes.txt', 'w') as f:
        f.write(f"MongoDB Truth Testing Fixes Report\n")
        f.write(f"--------------------------------\n\n")
        f.write(f"Total files changed: {total_files_changed}\n")
        f.write(f"Total changes made: {total_changes}\n\n")
        
        for file_path, details in all_changes.items():
            f.write(f"\n{file_path} ({len(details)} changes):\n")
            for change in details:
                f.write(f"  - {change}\n")
    
    return total_files_changed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
