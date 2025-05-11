import os
import re

def fix_rivalries_coroutines():
    """
    Fix coroutine issues in rivalries.py by replacing static EmbedBuilder.rivalry calls
    with proper awaited async calls to EmbedBuilder.create_rivalry_embed.
    """
    file_path = 'cogs/rivalries.py'
    
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Pattern to match EmbedBuilder.rivalry calls
    pattern = r'([ \t]*)embed = EmbedBuilder\.rivalry\('
    replacement = r'\1embed = await EmbedBuilder.create_rivalry_embed('
    
    # Another pattern for a specific rivalry embed call
    rivalry_pattern = r'([ \t]*)rivalry_embed = EmbedBuilder\.rivalry\('
    rivalry_replacement = r'\1rivalry_embed = await EmbedBuilder.create_rivalry_embed('
    
    # Apply replacements
    content = re.sub(pattern, replacement, content)
    content = re.sub(rivalry_pattern, rivalry_replacement, content)
    
    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Fixed rivalry coroutine issues in {file_path}")

if __name__ == "__main__":
    fix_rivalries_coroutines()