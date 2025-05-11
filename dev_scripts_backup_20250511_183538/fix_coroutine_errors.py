
"""
Fix Coroutine Errors

This script scans the codebase for common coroutine handling errors, particularly:
1. EmbedBuilder methods that return coroutines but aren't being awaited
2. Embed coroutines being passed directly to send methods without being awaited

Usage:
    python fix_coroutine_errors.py

This will:
1. Scan all Python files for potential coroutine issues
2. Make backups of files that need fixes
3. Apply automated fixes where possible
4. Report on fixes applied and any issues that need manual attention
"""
import asyncio
import os
import re
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("coroutine_fixer")

# Common patterns for embed creation that might be coroutines
EMBED_CREATION_PATTERNS = [
    r'(\s*)(\w+)\s*=\s*(EmbedBuilder\.create_\w+\(.*?\))(\s*(?:#.*)?)$',
    r'(\s*)embed\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*\.create_\w+\(.*?\))(\s*(?:#.*)?)$',
]

# Patterns for send methods that might be passed coroutines directly
SEND_METHOD_PATTERNS = [
    r'(\s*await\s+ctx\.send\()(\s*embed\s*=\s*)([a-zA-Z_][a-zA-Z0-9_]*\.create_\w+\(.*?\))(\s*,?.*?\))(\s*(?:#.*)?)$',
    r'(\s*await\s+interaction\.response\.send_message\()(\s*embed\s*=\s*)([a-zA-Z_][a-zA-Z0-9_]*\.create_\w+\(.*?\))(\s*,?.*?\))(\s*(?:#.*)?)$',
    r'(\s*await\s+interaction\.followup\.send\()(\s*embed\s*=\s*)([a-zA-Z_][a-zA-Z0-9_]*\.create_\w+\(.*?\))(\s*,?.*?\))(\s*(?:#.*)?)$',
]

async def main():
    """Main entry point for the coroutine fixer script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix coroutine handling issues in Python files')
    parser.add_argument('--directory', '-d', default='.', help='Directory to scan')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    parser.add_argument('--dryrun', '-n', action='store_true', help='Dry run (do not modify files)')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    logger.info(f"Scanning directory: {args.directory}")
    results = await scan_directory(args.directory)
    
    # Print summary
    fixed_files = [r for r in results if r['status'] == 'fixed']
    error_files = [r for r in results if r['status'] == 'error']
    
    logger.info(f"Scan complete: {len(results)} files processed")
    logger.info(f"Files fixed: {len(fixed_files)}")
    logger.info(f"Errors: {len(error_files)}")
    
    # Show details for fixed files
    for file in fixed_files:
        logger.info(f"Fixed {file['file_path']}: {file['fixes_applied']} issues fixed")
    
    # Show errors
    for file in error_files:
        logger.error(f"Error in {file['file_path']}: {file.get('error', 'Unknown error')}")
    
    return fixed_files

if __name__ == "__main__":
    asyncio.run(main())

def create_backup(file_path: str) -> str:
    """Create a backup of a file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

async def fix_embed_creation(content: str) -> Tuple[str, int]:
    """Fix embed creation coroutine issues"""
    fixed_content = content
    fixes_applied = 0
    
    for pattern in EMBED_CREATION_PATTERNS:
        matches = list(re.finditer(pattern, fixed_content, re.MULTILINE))
        
        # Process matches in reverse order to avoid offset issues when replacing
        for match in reversed(matches):
            # Check if there's an await before the creation
            line_start = fixed_content.rfind('\n', 0, match.start()) + 1
            line_before = fixed_content[line_start:match.start()]
            
            if 'await' not in line_before:
                # This is likely a coroutine that's not being awaited
                creation_part = match.group(3) if len(match.groups()) >= 3 else match.group(2)
                indentation = match.group(1)
                comment = match.group(4) if len(match.groups()) >= 4 else ''
                
                # Replace with awaited version
                if len(match.groups()) >= 3:
                    replacement = f"{indentation}{match.group(2)} = await {creation_part}{comment}"
                else:
                    replacement = f"{indentation}embed = await {creation_part}{comment}"
                
                fixed_content = fixed_content[:match.start()] + replacement + fixed_content[match.end():]
                fixes_applied += 1
    
    return fixed_content, fixes_applied

async def fix_send_methods(content: str) -> Tuple[str, int]:
    """Fix send method coroutine issues"""
    fixed_content = content
    fixes_applied = 0
    
    for pattern in SEND_METHOD_PATTERNS:
        matches = list(re.finditer(pattern, fixed_content, re.MULTILINE))
        
        # Process matches in reverse order to avoid offset issues when replacing
        for match in reversed(matches):
            # Check if the embed argument is already being awaited
            embed_arg = match.group(3)
            if 'await' not in embed_arg:
                # This is likely a coroutine being passed directly without awaiting
                start_part = match.group(1)
                embed_key = match.group(2)
                rest_part = match.group(4)
                comment = match.group(5) if len(match.groups()) >= 5 else ''
                
                # Replace with awaited version
                replacement = f"{start_part}{embed_key}await {embed_arg}{rest_part}{comment}"
                
                fixed_content = fixed_content[:match.start()] + replacement + fixed_content[match.end():]
                fixes_applied += 1
    
    return fixed_content, fixes_applied

async def scan_and_fix_file(file_path: str) -> Dict[str, Any]:
    """Scan a file for coroutine issues and fix them"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Track file level metrics
        result = {
            'file_path': file_path,
            'creation_fixes': 0,
            'send_fixes': 0,
            'error': None,
            'backup': None
        }
        
        # Apply fixes
        fixed_content, creation_fixes = await fix_embed_creation(content)
        result['creation_fixes'] = creation_fixes
        
        fixed_content, send_fixes = await fix_send_methods(fixed_content)
        result['send_fixes'] = send_fixes
        
        # If we applied fixes, write the changes
        if creation_fixes > 0 or send_fixes > 0:
            # Create backup
            backup_path = create_backup(file_path)
            result['backup'] = backup_path
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fixing file {file_path}: {e}")
        return {
            'file_path': file_path,
            'creation_fixes': 0,
            'send_fixes': 0,
            'error': str(e),
            'backup': None
        }

async def scan_and_fix_file(file_path: str) -> Dict[str, Any]:
    """Scan and fix coroutine issues in a single file"""
    result = {
        "file_path": file_path,
        "fixes_applied": 0,
        "status": "unchanged"
    }
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            original_content = content
            
        # Fix send methods
        content, send_fixes = await fix_send_methods(content)
        
        # Fix embed creation
        content, embed_fixes = await fix_embed_creation(content)
        
        # Update the result
        total_fixes = send_fixes + embed_fixes
        result["fixes_applied"] = total_fixes
        
        if total_fixes > 0:
            # Create a backup
            backup_path = f"{file_path}.coroutine.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
                
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            result["status"] = "fixed"
            result["backup"] = backup_path
        
        return result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result

async def scan_directory(directory: str = '.', 
                         extensions: Set[str] = {'.py'}, 
                         exclude_dirs: Set[str] = {'venv', 'env', '__pycache__', '.git', 'temp_extracted'}) -> List[Dict[str, Any]]:
    """Scan a directory recursively for Python files and fix coroutine issues"""
    results = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                result = await scan_and_fix_file(file_path)
                results.append(result)
    
    return results

async def main():
    """Main entry point"""
    logger.info("Starting coroutine error fixer")
    
    # Scan and fix files
    results = await scan_directory()
    
    # Summarize results
    total_files = len(results)
    fixed_files = sum(1 for r in results if r['creation_fixes'] > 0 or r['send_fixes'] > 0)
    total_creation_fixes = sum(r['creation_fixes'] for r in results)
    total_send_fixes = sum(r['send_fixes'] for r in results)
    error_files = sum(1 for r in results if r['error'] is not None)
    
    logger.info(f"Scan complete: {total_files} files scanned, {fixed_files} files fixed")
    logger.info(f"Total fixes: {total_creation_fixes} embed creation issues, {total_send_fixes} send method issues")
    
    if fixed_files > 0:
        logger.info("Fixed files:")
        for result in results:
            if result['creation_fixes'] > 0 or result['send_fixes'] > 0:
                logger.info(f"  - {result['file_path']}: {result['creation_fixes']} creation fixes, {result['send_fixes']} send fixes")
    
    if error_files > 0:
        logger.warning("Files with errors:")
        for result in results:
            if result['error'] is not None:
                logger.warning(f"  - {result['file_path']}: {result['error']}")
    
    logger.info("Coroutine error fixer completed")

if __name__ == "__main__":
    asyncio.run(main())
