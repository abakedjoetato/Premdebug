#!/usr/bin/env python3
"""
Comprehensive Fix for CSV Processor Syntax Errors

This script completely rewrites the problematic sections of the CSV processor code
to fix all syntax and indentation issues that are preventing the bot from loading properly.
"""
import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a timestamped backup of the file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def fix_run_historical_parse_with_config(content):
    """Fix syntax in run_historical_parse_with_config method"""
    # Find the method definition
    method_pattern = r'async def run_historical_parse_with_config\(.*?\):'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if method_match:
        # Get the indentation level
        method_start = method_match.end()
        next_line = content[method_start:].lstrip('\n')
        indent = ""
        for char in next_line:
            if char in ' \t':
                indent += char
            else:
                break
        
        # Extract the entire method body
        next_method_pattern = r'async def [^(]+\('
        next_method_match = re.search(next_method_pattern, content[method_start:], re.DOTALL)
        
        if next_method_match:
            method_end = method_start + next_method_match.start()
            method_body = content[method_start:method_end]
            
            # Rewrite the method body with correct indentation and try/except blocks
            new_method_body = f"""
{indent}\"\"\"Run a historical parse for a server using direct configuration.

{indent}This enhanced method accepts a complete server configuration object to bypass resolution issues,
{indent}ensuring we have all the necessary details even for newly added servers.

{indent}Args:
{indent}    server_id: Server ID to process
{indent}    server_config: Complete server configuration with SFTP details
{indent}    days: Number of days to look back (default: 30)
{indent}    guild_id: Optional Discord guild ID for server isolation

{indent}Returns:
{indent}    Tuple[int, int]: Number of files processed and events processed
{indent}\"\"\"
{indent}logger.info(f"Running historical parse with direct config for server {server_id}")
{indent}start_date = datetime.now() - timedelta(days=days)
{indent}logger.info(f"Looking back {days} days (from {start_date})")

{indent}if not server_config:
{indent}    logger.error(f"No server configuration provided for historical parse with ID {server_id}")
{indent}    return 0, 0

{indent}# Set up historical parse tracking to avoid race conditions
{indent}if not hasattr(self, 'servers_with_active_historical_parse'):
{indent}    self.servers_with_active_historical_parse = set()

{indent}# If this server already has an active historical parse, wait
{indent}if server_id in self.servers_with_active_historical_parse:
{indent}    logger.warning(f"Historical parse already in progress for server {server_id}")
{indent}    return 0, 0

{indent}# Mark that we're starting a historical parse for this server
{indent}self.servers_with_active_historical_parse.add(server_id)
{indent}logger.warning(f"Added server {server_id} to active historical parse tracking")

{indent}try:
{indent}    # Resolve the server ID if needed
{indent}    resolved_server_id = server_id
{indent}    if hasattr(self.bot, 'resolve_server_id'):
{indent}        try:
{indent}            resolved_server_id = await self.bot.resolve_server_id(server_id)
{indent}            logger.info(f"Resolved server ID {server_id} to {resolved_server_id}")
{indent}        except Exception as resolve_err:
{indent}            logger.warning(f"Could not resolve server ID {server_id}: {resolve_err}")
{indent}            # Continue with original ID

{indent}    async with self.processing_lock:
{indent}        self.is_processing = True
{indent}        try:
{indent}            # Use the resolved configuration directly
{indent}            files_processed, events_processed = await self._process_server_csv_files(
{indent}                resolved_server_id, server_config, start_date=start_date
{indent}            )
{indent}            logger.info(f"Direct resolution historical parse complete for server {resolved_server_id}: "
{indent}                       f"processed {files_processed} files with {events_processed} events")
                
{indent}            # Track server activity for adaptive processing
{indent}            try:
{indent}                if hasattr(self, '_check_server_activity'):
{indent}                    await self._check_server_activity(server_id, events_processed)
{indent}            except Exception as e:
{indent}                logger.warning(f"Error tracking server activity: {e}")
                
{indent}            return files_processed, events_processed
{indent}        except Exception as e:
{indent}            logger.error(f"Error in direct resolution historical parse for server {resolved_server_id}: {e}")
{indent}            return 0, 0
{indent}        finally:
{indent}            self.is_processing = False
{indent}finally:
{indent}    # CRITICAL FIX: Always clean up historical parse tracking, even if the main try block fails
{indent}    if server_id in self.servers_with_active_historical_parse:
{indent}        self.servers_with_active_historical_parse.remove(server_id)
{indent}        logger.warning(f"Removed server {server_id} from active historical parse tracking")
"""
            # Replace the old method body with the new one
            new_content = content[:method_start] + new_method_body + content[method_end:]
            return new_content
    
    return content

def fix_run_historical_parse(content):
    """Fix syntax in run_historical_parse method"""
    # Find the method definition
    method_pattern = r'async def run_historical_parse\(.*?\):'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if method_match:
        # Get the indentation level
        method_start = method_match.end()
        next_line = content[method_start:].lstrip('\n')
        indent = ""
        for char in next_line:
            if char in ' \t':
                indent += char
            else:
                break
        
        # Extract the entire method body
        next_method_pattern = r'async def [^(]+\('
        next_method_match = re.search(next_method_pattern, content[method_start:], re.DOTALL)
        
        if next_method_match:
            method_end = method_start + next_method_match.start()
            method_body = content[method_start:method_end]
            
            # Rewrite the method body with correct indentation and try/except blocks
            new_method_body = f"""
{indent}\"\"\"Run a historical parse for a server, checking further back in time

{indent}This function is meant to be called when setting up a new server to process
{indent}older historical data going back further than the normal processing window.
{indent}
{indent}CRITICAL FIX: This method now pauses the regular CSV processing for this server
{indent}while the historical parse is running, then resumes it when done. This prevents
{indent}race conditions between the historical parser and regular parser when a server
{indent}is first added.

{indent}Args:
{indent}    server_id: Server ID to process (can be UUID or numeric ID)
{indent}    days: Number of days to look back (default: 30)
{indent}    guild_id: Optional Discord guild ID for server isolation

{indent}Returns:
{indent}    Tuple[int, int]: Number of files processed and events processed
{indent}\"\"\"
{indent}logger.info(f"Running historical parse for server {server_id}")
{indent}
{indent}# Get server configuration
{indent}server_configs = await self._get_server_configs()
{indent}
{indent}if server_id not in server_configs:
{indent}    logger.error(f"Could not find configuration for server {server_id}")
{indent}    return 0, 0
{indent}
{indent}server_config = server_configs[server_id]
{indent}
{indent}# Use the enhanced direct configuration method to process historical data
{indent}return await self.run_historical_parse_with_config(server_id, server_config, days, guild_id)
"""
            # Replace the old method body with the new one
            new_content = content[:method_start] + new_method_body + content[method_end:]
            return new_content
    
    return content

def fix_process_server_csv_files(content):
    """Fix syntax in _process_server_csv_files method"""
    # Find the method definition
    method_pattern = r'async def _process_server_csv_files\(.*?\):'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    # Find the end of the method by looking for activity tracking code
    tracking_pattern = r'# Track server activity for adaptive processing\s+recommended_interval = await self\._check_server_activity\(server_id, events_processed\)'
    tracking_match = re.search(tracking_pattern, content, re.DOTALL)
    
    if tracking_match:
        # Get position and surrounding context
        pos = tracking_match.start()
        context_before = content[:pos].rfind("        # Keep the connection open for the next operation")
        context_after = content[tracking_match.end():].find("        # Finalization code moved outside")
        
        if context_before > 0 and context_after > 0:
            # Extract the section to replace
            end_pos = tracking_match.end() + context_after
            section_to_replace = content[context_before:end_pos]
            
            # Create the replacement with proper try/except structure
            replacement = """        # Keep the connection open for the next operation
                
                # Track server activity for adaptive processing
                try:
                    if hasattr(self, '_check_server_activity'):
                        await self._check_server_activity(server_id, events_processed)
                except Exception as e:
                    logger.warning(f"Error tracking server activity: {e}")
                
                return files_processed, events_processed
            except Exception as e:
                logger.error(f"SFTP error for server {server_id}: {str(e)}")
                # Run garbage collection before returning
                try:
                    import gc
                    collected = gc.collect()
                    logger.debug(f"Memory optimization: freed {collected} objects after CSV error")
                except:
                    pass
                # CRITICAL FIX: Also clean up historical parse tracking in error path
                if is_historical_mode and server_id in self.servers_with_active_historical_parse:
                    try:
                        logger.warning(f"CRITICAL FIX: Error path - removing server {server_id} from active historical parse tracking")
                        self.servers_with_active_historical_parse.remove(server_id)
                    except Exception as e:
                        logger.error(f"Error removing server from historical tracking in error path: {e}")
                
                # Set empty results
                files_processed = 0
                events_processed = 0
                
                # Return error results
                return files_processed, events_processed"""
                
            # Replace the section
            new_content = content[:context_before] + replacement + content[end_pos:]
            return new_content
    
    return content

def fix_csv_processor():
    """Fix syntax issues in the CSV processor"""
    file_path = "cogs/csv_processor.py"
    
    # Backup the file
    backup_file(file_path)
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix each method
    content = fix_run_historical_parse_with_config(content)
    content = fix_run_historical_parse(content)
    content = fix_process_server_csv_files(content)
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed syntax issues in {file_path}")

if __name__ == "__main__":
    fix_csv_processor()