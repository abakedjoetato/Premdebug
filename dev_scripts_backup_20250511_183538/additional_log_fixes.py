#!/usr/bin/env python3
"""
Utility script to further reduce log levels for specific log messages
that weren't caught by the generic patterns.
"""
import re
import os

# Define files that need additional fixes
files_to_fix = {
    "cogs/log_processor.py": [
        # Database connection patterns
        (r'logger\.info\(f"Bot DB instance type: (.*?)"\)', r'logger.debug(f"Bot DB instance type: \1")'),
        (r'logger\.info\(f"Bot DB instance repr: (.*?)"\)', r'logger.debug(f"Bot DB instance repr: \1")'), 
        (r'logger\.info\(f"Database ping result: (.*?)"\)', r'logger.debug(f"Database ping result: \1")'),
        (r'logger\.info\(f"Available collections: (.*?)"\)', r'logger.debug(f"Available collections: \1")'),
        (r'logger\.info\(f"Retrieving server configurations..."\)', r'logger.debug(f"Retrieving server configurations...")'),
        (r'logger\.info\(f"Database instance: (.*?)"\)', r'logger.debug(f"Database instance: \1")'),
        (r'logger\.info\(f"Checking servers collection for SFTP-enabled servers..."\)', r'logger.debug(f"Checking servers collection for SFTP-enabled servers...")'),
        (r'logger\.info\(f"Checking game_servers collection for SFTP-enabled servers..."\)', r'logger.debug(f"Checking game_servers collection for SFTP-enabled servers...")'),
        (r'logger\.info\(f"Adding (\{.*?\}) unique servers from (.*?) collection"\)', r'logger.debug(f"Adding \1 unique servers from \2 collection")'),
        (r'logger\.info\(f"Creating new SFTPManager for server (.*?)"\)', r'logger.debug(f"Creating new SFTPManager for server \1")'),
        (r'logger\.info\(f"Using known numeric ID \'(.*?)\' from KNOWN_SERVERS mapping"\)', r'logger.debug(f"Using known numeric ID \'\1\' from KNOWN_SERVERS mapping")'),
        (r'logger\.info\(f"Creating new LogParser with server_id=(.*?), original_server_id=(.*?)"\)', r'logger.debug(f"Creating new LogParser with server_id=\1, original_server_id=\2")'),
        (r'logger\.info\(f"Log processing completed in (.*?) seconds"\)', r'logger.debug(f"Log processing completed in \1 seconds")'),
    ],
    "utils/log_parser.py": [
        (r'logger\.info\(f"LogParser initialized with base_path: (.*?) \(using original_server_id: (.*?)\)"\)', r'logger.debug(f"LogParser initialized with base_path: \1 (using original_server_id: \2)")'),
    ],
    "cogs/csv_processor.py": [
        (r'logger\.info\(f"SFTP connection successful for server (.*?)"\)', r'logger.debug(f"SFTP connection successful for server \1")'),
        (r'logger\.info\(f"Using known numeric ID \'(.*?)\' for server (.*?)"\)', r'logger.debug(f"Using known numeric ID \'\1\' for server \2")'),
        (r'logger\.info\(f"Using server directory: (.*?) with ID (.*?)"\)', r'logger.debug(f"Using server directory: \1 with ID \2")'),
        (r'logger\.info\(f"Found (\{.*?\}) CSV files in map directory (.*?)"\)', r'logger.debug(f"Found \1 CSV files in map directory \2")'),
        (r'logger\.info\(f"No additional CSV files found in predefined paths, (.*?)"\)', r'logger.debug(f"No additional CSV files found in predefined paths, \1")'),
    ],
    "utils/sftp.py": [
        (r'logger\.info\(f"Connected to SFTP server: (.*?) in (.*?)s"\)', r'logger.debug(f"Connected to SFTP server: \1 in \2s")'),
    ]
}

def fix_additional_logs():
    """Apply additional fixes to logging statements"""
    for filepath, patterns in files_to_fix.items():
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
            
        print(f"Processing additional fixes for {filepath}...")
        
        # Read the content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count original logger.info calls
        info_count = len(re.findall(r'logger\.info\(', content))
        print(f"  Found {info_count} INFO log statements")
        
        # Apply all replacements
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Count new logger.info calls
        new_info_count = len(re.findall(r'logger\.info\(', content))
        changes = info_count - new_info_count
        
        if changes > 0:
            print(f"  Reduced INFO logs from {info_count} to {new_info_count} ({changes} changed)")
            
            # Save the modified content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  Saved changes to {filepath}")
        else:
            print(f"  No changes made to {filepath}")

if __name__ == "__main__":
    fix_additional_logs()