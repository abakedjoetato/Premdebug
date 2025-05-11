#!/usr/bin/env python3
"""
Comprehensive script to find all MongoDB boolean context issues in the codebase
This script systematically searches for patterns where MongoDB objects might be used in boolean contexts
"""

import os
import re
import json
from collections import defaultdict

# Patterns to look for
PATTERNS = [
    # Pattern 1: Direct boolean usage
    r'if\s+not\s+([a-zA-Z0-9_]+)(?:\s*:|\s*\))',  # if not object:
    r'if\s+([a-zA-Z0-9_]+)(?:\s*:|\s*\)|\s+and|\s+or)', # if object: or if object) or if object and 
    r'([a-zA-Z0-9_]+)\s+or\s+None',  # object or None
    r'([a-zA-Z0-9_]+)\s+and\s+',     # object and ...
    r'bool\(([a-zA-Z0-9_]+)\)',      # bool(object)
    r'not\s+([a-zA-Z0-9_]+)(?:\s|,|\))', # not object followed by space, comma or parenthesis
]

# MongoDB related variable names to focus on
MONGODB_VAR_PATTERNS = [
    r'.*model.*', r'.*db.*', r'.*collection.*', r'.*cursor.*',
    r'.*document.*', r'.*record.*', r'.*server.*', r'.*guild.*',
    r'.*player.*', r'.*faction.*', r'.*doc.*', r'.*result.*'
]

def is_mongodb_variable(name):
    """Check if a variable name might be related to MongoDB"""
    name = name.lower()
    return any(re.match(pattern, name) for pattern in MONGODB_VAR_PATTERNS)

def scan_file(file_path):
    """Scan a file for potential MongoDB truth value testing issues"""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern in PATTERNS:
            matches = re.findall(pattern, line)
            for var_name in matches:
                if is_mongodb_variable(var_name):
                    # Check if it's a proper "is None" comparison
                    if re.search(rf'{var_name}\s+is\s+(?:not\s+)?None', line):
                        continue  # This is a proper comparison
                    
                    issues.append({
                        'line_num': line_num,
                        'line': line.strip(),
                        'var_name': var_name,
                        'fix_suggestion': line.replace(
                            f"if not {var_name}", f"if {var_name} is None"
                        ).replace(
                            f"if {var_name}:", f"if {var_name} is not None:"
                        )
                    })
    
    return issues

def scan_directory(dir_path, extensions=None):
    """Recursively scan a directory for potential MongoDB truth value testing issues"""
    if extensions is None:
        extensions = ['.py']
    
    all_issues = defaultdict(list)
    
    for root, _, files in os.walk(dir_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                issues = scan_file(file_path)
                if issues:
                    all_issues[file_path] = issues
    
    return all_issues

if __name__ == "__main__":
    # Directories to scan
    dirs_to_scan = ['cogs', 'models', 'utils', '.']
    
    all_results = {}
    
    # Scan each directory
    for dir_path in dirs_to_scan:
        if os.path.exists(dir_path):
            print(f"Scanning {dir_path}...")
            issues = scan_directory(dir_path)
            all_results.update(issues)
    
    # Count total issues
    total_issues = sum(len(issues) for issues in all_results.values())
    print(f"Found {total_issues} potential MongoDB truth value testing issues in {len(all_results)} files")
    
    # Print detailed results
    for file_path, issues in all_results.items():
        print(f"\n{file_path} ({len(issues)} issues):")
        for issue in issues:
            print(f"  Line {issue['line_num']}: {issue['line']}")
            print(f"    Variable: {issue['var_name']}")
            print(f"    Suggestion: {issue['fix_suggestion']}")
            print()
    
    # Save results to a file for easier review
    with open('mongodb_bool_issues.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Results saved to mongodb_bool_issues.json")
