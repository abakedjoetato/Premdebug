
"""
Syntax validation script for Guild model.
This ensures code is syntactically correct before restarting the bot.
"""
import ast
import sys

def verify_syntax(file_path):
    """Check if a Python file has valid syntax by parsing it with ast"""
    try:
        with open(file_path, 'r') as file:
            source = file.read()
        
        # Try to parse the file - this will fail if there are syntax errors
        ast.parse(source)
        print(f"✅ {file_path} has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path} at line {e.lineno}, column {e.offset}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False

if __name__ == "__main__":
    result = verify_syntax("models/guild.py")
    sys.exit(0 if result else 1)
