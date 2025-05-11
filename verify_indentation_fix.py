
#!/usr/bin/env python3
"""
Script to verify indentation in Python files after fixes
"""
import sys
import ast
from pathlib import Path

def check_file_indentation(file_path):
    """Check if a Python file has valid indentation by parsing it"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Try to parse the file - this will fail if there are indentation errors
        ast.parse(content)
        return True, None
    except IndentationError as e:
        return False, f"Line {e.lineno}, column {e.offset}: {e.msg}"
    except SyntaxError as e:
        return False, f"Line {e.lineno}, column {e.offset}: {e.msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    """Check indentation in critical files"""
    files_to_check = [
        "models/guild.py",
        "cogs/stats.py"
    ]
    
    all_correct = True
    
    for file_path in files_to_check:
        is_valid, error = check_file_indentation(file_path)
        if is_valid:
            print(f"✅ {file_path}: Indentation is correct")
        else:
            print(f"❌ {file_path}: Indentation error - {error}")
            all_correct = False
    
    if all_correct:
        print("\n✅ All files have correct indentation")
        return 0
    else:
        print("\n❌ Some files still have indentation errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
