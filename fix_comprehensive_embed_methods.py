"""
Comprehensive fix for EmbedBuilder method calls in the codebase.

This script distinguishes between:
1. Static methods of EmbedBuilder (like .info(), .error(), .warning(), etc.) that don't need await
2. Async methods of EmbedBuilder (like .create_info_embed(), .create_error_embed(), etc.) that need await

It properly fixes each type of call, ensuring that static methods aren't awaited and async methods are.
"""
import os
import re
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directories to search for Python files
DIRS_TO_SEARCH = ['cogs', 'utils', 'models']

# List of static methods that should NOT be awaited
STATIC_METHODS = [
    'error',
    'success',
    'info',
    'warning',
    'neutral',
    'rivalry',
    'faction',
    'player',
    'bounty'
]

# Patterns for async methods that SHOULD be awaited
ASYNC_METHOD_PATTERNS = [
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_error_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_base_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_success_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_info_embed\()',
    r'(\s+)(embed\s*=\s*)(EmbedBuilder\.create_warning_embed\()',
]

# Replacement pattern to add await for async methods
ASYNC_REPLACEMENT = r'\1\2await \3'

def find_python_files() -> List[str]:
    """Find all Python files in the specified directories."""
    python_files = []
    
    for directory in DIRS_TO_SEARCH:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
    
    logger.info(f"Found {len(python_files)} Python files to check")
    return python_files

def fix_static_method_calls(content: str) -> Tuple[str, int]:
    """Fix static method calls that might have been incorrectly awaited."""
    original_content = content
    fixes_applied = 0
    
    # Find instances where static methods are incorrectly awaited
    for method in STATIC_METHODS:
        # Pattern to find incorrectly awaited static methods
        pattern = rf'(\s+)(embed\s*=\s*)await\s+(EmbedBuilder\.{method}\()'
        
        # Replace with version without await
        replacement = r'\1\2\3'
        
        # Apply the replacement
        updated_content = re.sub(pattern, replacement, content)
        
        if updated_content != content:
            fixes_applied += len(re.findall(pattern, content))
            content = updated_content
    
    return content, fixes_applied

def fix_async_method_calls(content: str) -> Tuple[str, int]:
    """Fix async method calls to ensure they're properly awaited."""
    original_content = content
    fixes_applied = 0
    
    # Apply all patterns for async methods
    for pattern in ASYNC_METHOD_PATTERNS:
        updated_content = re.sub(pattern, ASYNC_REPLACEMENT, content)
        
        if updated_content != content:
            fixes_applied += len(re.findall(pattern, content))
            content = updated_content
    
    return content, fixes_applied

def process_file(file_path: str) -> bool:
    """Process a single file and fix EmbedBuilder method calls."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix static method calls (remove incorrect awaits)
        content, static_fixes = fix_static_method_calls(content)
        
        # Fix async method calls (add missing awaits)
        content, async_fixes = fix_async_method_calls(content)
        
        # Only write to file if changes were made
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Fixed {static_fixes} static method calls and {async_fixes} async method calls in {file_path}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return False

def main():
    """Main function to find and process Python files."""
    logger.info("Starting comprehensive EmbedBuilder method fix")
    
    files = find_python_files()
    fixed_files = 0
    
    for file_path in files:
        if process_file(file_path):
            fixed_files += 1
    
    logger.info(f"Fixed EmbedBuilder method calls in {fixed_files} out of {len(files)} files")

if __name__ == "__main__":
    main()