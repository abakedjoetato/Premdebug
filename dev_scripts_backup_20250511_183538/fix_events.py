#!/usr/bin/env python3
"""
Script to fix line continuation errors in events.py
"""

import re

# Path to file
FILE_PATH = 'cogs/events.py'

# Backup the file first
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()
    
with open(f"{FILE_PATH}.bak", 'w', encoding='utf-8') as f:
    f.write(content)
    
print(f"Created backup of {FILE_PATH} to {FILE_PATH}.bak")

# Fix the problematic pattern
bad_pattern = r'if\s+not\s+events\s+if\s+events\s+is\s+not\s+None\s+else\s+\\2\)\s*==\s*0:'
replacement = 'if events is None or len(events) == 0:'

fixed_content = re.sub(bad_pattern, replacement, content)

# Write the fixed content
with open(FILE_PATH, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print(f"Fixed the problematic pattern in {FILE_PATH}")
