
#!/usr/bin/env python3
"""
Verify syntax of Python files to catch errors before running
"""
import ast
import sys
import os
from pathlib import Path

def verify_syntax(file_path):
    """Check Python file for syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✅ {file_path} has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        line_num = e.lineno
        
        # Show context around the error
        if line_num:
            lines = content.splitlines()
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 2)
            
            print("Context:")
            for i in range(start, end):
                prefix = ">" if i + 1 == line_num else " "
                print(f"{prefix} {i+1}: {lines[i]}")
        
        return False

if __name__ == "__main__":
    # Check specific file if provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            sys.exit(1)
        
        result = verify_syntax(file_path)
        sys.exit(0 if result else 1)
    
    # Check critical files
    critical_files = [
        "cogs/stats.py",
        "models/guild.py",
        "utils/premium.py"
    ]
    
    failures = 0
    for file_path in critical_files:
        if not verify_syntax(file_path):
            failures += 1
    
    sys.exit(failures)
