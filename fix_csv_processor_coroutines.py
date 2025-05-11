import os
import re

def fix_csv_processor_coroutines():
    """
    Fix coroutine issues in csv_processor.py by replacing static EmbedBuilder calls
    with proper awaited async calls to corresponding async methods.
    """
    file_path = 'cogs/csv_processor.py'
    
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()
    
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
    ]
    
    # Apply all replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Fixed CSV processor coroutine issues in {file_path}")

if __name__ == "__main__":
    fix_csv_processor_coroutines()