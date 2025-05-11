#!/usr/bin/env python3
"""
Utility script to reduce logging levels from INFO to DEBUG
across multiple modules in the Discord bot.

This helps minimize console output for non-critical messages.
"""
import re
import os
import sys
import glob

def reduce_log_levels(file_path):
    """
    Reduce logging levels from INFO to DEBUG in the specified file.
    
    Args:
        file_path: Path to the file to modify
    """
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"  Skipping binary or non-UTF-8 file: {file_path}")
        return
    except Exception as e:
        print(f"  Error reading file {file_path}: {e}")
        return
    
    # Count original logger.info calls
    info_count = len(re.findall(r'logger\.info\(', content))
    if info_count == 0:
        print(f"  No INFO logs found, skipping file")
        return
    
    print(f"  Found {info_count} INFO log statements")
    
    # Common replacements for all modules
    common_replacements = [
        # Debug and status information
        (r'logger\.info\(f"Memory optimization: freed (\{.*?\}) objects after (.*?)"\)', r'logger.debug(f"Memory optimization: freed \1 objects after \2")'),
        (r'logger\.info\(f"Processing (.*?) for (\{.*?\}) servers"\)', r'logger.debug(f"Processing \1 for \2 servers")'),
        (r'logger\.info\(f"Found (\{.*?\}) (.*?) in (.*?) collection"\)', r'logger.debug(f"Found \1 \2 in \3 collection")'),
        
        # File processing details
        (r'logger\.info\(f"Downloaded content type: (\{.*?\}), length: (\{.*?\})"\)', r'logger.debug(f"Downloaded content type: \1, length: \2")'),
        (r'logger\.info\(f"Found (\{.*?\}) (.*?) files in (.*?)"\)', r'logger.debug(f"Found \1 \2 files in \3")'),
        (r'logger\.info\(f"Using detected delimiter: \'(.*?)\' for file (.*?)"\)', r'logger.debug(f"Using detected delimiter: \'\1\' for file \2")'),
        
        # SFTP and file operations
        (r'logger\.info\(f"Using original server ID \'(.*?)\' for path construction"\)', r'logger.debug(f"Using original server ID \'\1\' for path construction")'),
        (r'logger\.info\(f"Using numeric original_server_id \'(.*?)\' for path construction"\)', r'logger.debug(f"Using numeric original_server_id \'\1\' for path construction")'),
        (r'logger\.info\(f"Detected AsyncSSH SFTP client, using optimized methods"\)', r'logger.debug(f"Detected AsyncSSH SFTP client, using optimized methods")'),
        (r'logger\.info\(f"Downloaded (.*?) using AsyncSSH open\+read \((\{.*?\}) bytes\)"\)', r'logger.debug(f"Downloaded \1 using AsyncSSH open+read (\2 bytes)")'),
        (r'logger\.info\(f"Downloaded (\{.*?\}) bytes from file (.*?)"\)', r'logger.debug(f"Downloaded \1 bytes from file \2")'),
        
        # Server and configuration details
        (r'logger\.info\(f"Server in \'(.*?)\': ID=(.*?), sftp_enabled=(.*?), name=(.*?)"\)', r'logger.debug(f"Server in \'\1\': ID=\2, sftp_enabled=\3, name=\4")'),
        (r'logger\.info\(f"Looking for (.*?) in path: (.*?)"\)', r'logger.debug(f"Looking for \1 in path: \2")'),
        (r'logger\.info\(f"Found (.*?) at: (.*?)"\)', r'logger.debug(f"Found \1 at: \2")'),
    ]
    
    # Module-specific replacements
    module_specific_replacements = {
        "csv_processor.py": [
            # CSV processor specific logs
            (r'logger\.info\(f"Using batch processing for (\{.*?\}) events"\)', r'logger.debug(f"Using batch processing for \1 events")'),
            (r'logger\.info\(f"Categorized events: (\{.*?\}) kills, (\{.*?\}) suicides"\)', r'logger.debug(f"Categorized events: \1 kills, \2 suicides")'),
            (r'logger\.info\(f"Updating stats for (\{.*?\}) unique players"\)', r'logger.debug(f"Updating stats for \1 unique players")'),
            (r'logger\.info\(f"Updating nemesis/prey relationships"\)', r'logger.debug(f"Updating nemesis/prey relationships")'),
            (r'logger\.info\(f"CSV content sample: (.*?)"\)', r'logger.debug(f"CSV content sample: \1")'),
            (r'logger\.info\(f"Added (\{.*?\}) CSV files from (.*?) to tracking lists"\)', r'logger.debug(f"Added \1 CSV files from \2 to tracking lists")'),
            (r'logger\.info\(f"Total tracked (.*?) files now: (\{.*?\})"\)', r'logger.debug(f"Total tracked \1 files now: \2")'),
        ],
        "log_processor.py": [
            # Log processor specific logs
            (r'logger\.info\(f"Final path_server_id: (.*?)"\)', r'logger.debug(f"Final path_server_id: \1")'),
            (r'logger\.info\(f"Building server directory with resolved server ID: (.*?)"\)', r'logger.debug(f"Building server directory with resolved server ID: \1")'),
            (r'logger\.info\(f"Using default directory structure with ID (.*?): (.*?)"\)', r'logger.debug(f"Using default directory structure with ID \1: \2")'),
            (r'logger\.info\(f"Getting stats for log file: (.*?)"\)', r'logger.debug(f"Getting stats for log file: \1")'),
        ],
        "sftp.py": [
            # SFTP manager specific logs
            (r'logger\.info\(f"SFTPClient using known numeric ID \'(.*?)\' for path construction instead of \'(.*?)\'"\)', r'logger.debug(f"SFTPClient using known numeric ID \'\1\' for path construction instead of \'\2\'")'),
            (r'logger\.info\(f"Using original server ID \'(.*?)\' for path construction instead of standardized ID \'(.*?)\'"\)', r'logger.debug(f"Using original server ID \'\1\' for path construction instead of standardized ID \'\2\'")'),
            (r'logger\.info\(f"Found (.*?) at: (.*?)"\)', r'logger.debug(f"Found \1 at: \2")'),
            (r'logger\.info\(f"Total (.*?) files found after deduplication: (\{.*?\}) \(from (\{.*?\}) total\)"\)', r'logger.debug(f"Total \1 files found after deduplication: \2 (from \3 total)")'),
        ],
        "direct_csv_handler.py": [
            # Direct CSV handler specific logs
            (r'logger\.info\(f"Direct parsing CSV content from file: (.*?)"\)', r'logger.debug(f"Direct parsing CSV content from file: \1")'),
            (r'logger\.info\(f"Using delimiter \'(.*?)\' for content parsing \((.*?)\)"\)', r'logger.debug(f"Using delimiter \'\1\' for content parsing (\2)")'),
            (r'logger\.info\(f"Directly parsed (\{.*?\}) events from (\{.*?\}) rows in CSV content"\)', r'logger.debug(f"Directly parsed \1 events from \2 rows in CSV content")'),
        ],
        "csv_parser.py": [
            # CSV parser specific logs
            (r'logger\.info\(f"Parsing CSV file: (.*?)"\)', r'logger.debug(f"Parsing CSV file: \1")'),
            (r'logger\.info\(f"Detected delimiter: \'(.*?)\' \((.*?)\)"\)', r'logger.debug(f"Detected delimiter: \'\1\' (\2)")'),
            (r'logger\.info\(f"Parsed (\{.*?\}) events from (\{.*?\}) rows in (.*?)"\)', r'logger.debug(f"Parsed \1 events from \2 rows in \3")'),
        ],
    }
    
    # Apply common replacements
    for pattern, replacement in common_replacements:
        content = re.sub(pattern, replacement, content)
    
    # Apply module-specific replacements
    filename = os.path.basename(file_path)
    if filename in module_specific_replacements:
        for pattern, replacement in module_specific_replacements[filename]:
            content = re.sub(pattern, replacement, content)
    
    # Count new logger.info calls
    new_info_count = len(re.findall(r'logger\.info\(', content))
    changes = info_count - new_info_count
    
    if changes > 0:
        print(f"  Reduced INFO logs from {info_count} to {new_info_count} ({changes} changed)")
        
        # Save the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Saved changes to {file_path}")
    else:
        print(f"  No changes made to {file_path}")

def find_python_files(directory):
    """Find all Python files in the directory and its subdirectories"""
    return glob.glob(f"{directory}/**/*.py", recursive=True)

if __name__ == "__main__":
    # Define base directories to search for Python files
    base_directories = [
        "cogs",
        "utils",
        "models"
    ]
    
    # If specific files are provided as arguments, process only those
    if len(sys.argv) > 1:
        files_to_process = sys.argv[1:]
    else:
        # Otherwise, find all Python files in the specified directories
        files_to_process = []
        for directory in base_directories:
            if os.path.exists(directory):
                files_to_process.extend(find_python_files(directory))
    
    # Filter out non-existent files
    files_to_process = [f for f in files_to_process if os.path.exists(f)]
    
    print(f"Found {len(files_to_process)} Python files to process")
    
    # Process each file
    for file_path in files_to_process:
        reduce_log_levels(file_path)