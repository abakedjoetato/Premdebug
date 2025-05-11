import os
import re
import glob

def fix_coroutine_issues(file_path):
    """
    Fix coroutine issues in the specified file by replacing static EmbedBuilder calls
    with proper awaited async calls to corresponding async methods.
    
    Args:
        file_path: Path to the file to fix
    
    Returns:
        int: Number of replacements made
    """
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    original_content = content
    
    # Define patterns and replacements for different EmbedBuilder methods
    replacements = [
        # info -> create_info_embed
        (r'([ \t]*)embed = EmbedBuilder\.info\(', r'\1embed = await EmbedBuilder.create_info_embed('),
        
        # error -> create_error_embed
        (r'([ \t]*)embed = EmbedBuilder\.error\(', r'\1embed = await EmbedBuilder.create_error_embed('),
        
        # success -> create_success_embed
        (r'([ \t]*)embed = EmbedBuilder\.success\(', r'\1embed = await EmbedBuilder.create_success_embed('),
        
        # warning -> create_warning_embed
        (r'([ \t]*)embed = EmbedBuilder\.warning\(', r'\1embed = await EmbedBuilder.create_warning_embed('),
        
        # faction -> create_faction_embed
        (r'([ \t]*)embed = EmbedBuilder\.faction\(', r'\1embed = await EmbedBuilder.create_faction_embed('),
        
        # rivalry -> create_rivalry_embed
        (r'([ \t]*)embed = EmbedBuilder\.rivalry\(', r'\1embed = await EmbedBuilder.create_rivalry_embed('),
        
        # player_stats -> create_stats_embed
        (r'([ \t]*)embed = EmbedBuilder\.player_stats\(', r'\1embed = await EmbedBuilder.create_stats_embed('),
        
        # Also check for non-embed variable names
        (r'([ \t]*)(\w+) = EmbedBuilder\.info\(', r'\1\2 = await EmbedBuilder.create_info_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.error\(', r'\1\2 = await EmbedBuilder.create_error_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.success\(', r'\1\2 = await EmbedBuilder.create_success_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.warning\(', r'\1\2 = await EmbedBuilder.create_warning_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.faction\(', r'\1\2 = await EmbedBuilder.create_faction_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.rivalry\(', r'\1\2 = await EmbedBuilder.create_rivalry_embed('),
        (r'([ \t]*)(\w+) = EmbedBuilder\.player_stats\(', r'\1\2 = await EmbedBuilder.create_stats_embed('),
    ]
    
    # Apply all replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Only write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as file:
            file.write(content)
        return 1
    return 0

def main():
    # Process all Python files in cogs/ directory
    cogs_files = glob.glob('cogs/*.py')
    total_files_changed = 0
    
    for file_path in cogs_files:
        changes = fix_coroutine_issues(file_path)
        if changes > 0:
            print(f"Fixed coroutine issues in {file_path}")
            total_files_changed += 1
    
    print(f"Total files fixed: {total_files_changed}")

if __name__ == "__main__":
    main()