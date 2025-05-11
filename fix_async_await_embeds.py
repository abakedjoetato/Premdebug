"""
Fix async/await issues in the codebase.

This script adds missing awaits to EmbedBuilder method calls.
"""
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directories to search for Python files
DIRS_TO_SEARCH = ['cogs', 'utils', 'models']

# Patterns of function calls that need to be awaited
PATTERNS = [
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_error_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_base_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_success_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_info_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_warning_embed\()',
]

# Replacement pattern with await
REPLACEMENT = r'\1\2await \3'

def process_file(file_path):
    """Process a single file and fix the async/await issues."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Apply all patterns
    for pattern in PATTERNS:
        content = re.sub(pattern, REPLACEMENT, content)
    
    # Only write to the file if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        logger.info(f"Fixed async/await issues in {file_path}")
        return True
    return False

def main():
    """Main function to find and process Python files."""
    files_fixed = 0
    
    for directory in DIRS_TO_SEARCH:
        if not os.path.exists(directory):
            logger.warning(f"Directory {directory} does not exist, skipping.")
            continue
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if process_file(file_path):
                        files_fixed += 1
    
    logger.info(f"Completed fixing async/await issues in {files_fixed} files.")

if __name__ == "__main__":
    main()