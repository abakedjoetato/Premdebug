
#!/usr/bin/env python3
"""
Robust CSV Processing Fix Script

This script addresses issues with CSV processing and map directory handling:
1. Ensures map directories are properly detected
2. Fixes file path construction and tracking
3. Properly handles file discovery in map directories
4. Updates the database tracking for processed files
"""
import os
import sys
import re
import logging
import asyncio
import traceback
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("robust_csv_fix.log")
    ]
)
logger = logging.getLogger("robust_csv_fix")

# Critical file paths
CSV_PROCESSOR_PATH = "cogs/csv_processor.py"
FILE_DISCOVERY_PATH = "utils/file_discovery.py"
CSV_PARSER_PATH = "utils/csv_parser.py"

# Backup directory
BACKUP_DIR = f"backups/csv_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

async def connect_to_db():
    """Connect to the MongoDB database"""
    try:
        from utils.database import initialize_db
        db = await initialize_db()
        logger.info("Connected to MongoDB database")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def create_backup_directory() -> bool:
    """Create a backup directory for files"""
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            logger.info(f"Created backup directory: {BACKUP_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup directory: {e}")
        return False

def backup_file(file_path: str) -> bool:
    """Create a backup of a file"""
    if not os.path.exists(file_path):
        logger.error(f"Cannot backup non-existent file: {file_path}")
        return False
        
    try:
        # Create a backup in the backup directory
        basename = os.path.basename(file_path)
        backup_path = os.path.join(BACKUP_DIR, basename)
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup of {file_path} at {backup_path}")
        
        # Also create a .bak file in the original location
        bak_path = f"{file_path}.robust_fix.bak"
        shutil.copy2(file_path, bak_path)
        logger.info(f"Created backup at original location: {bak_path}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to backup {file_path}: {e}")
        return False

def read_file(file_path: str) -> Optional[str]:
    """Read a file with error handling"""
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully read file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None
        
def write_file(file_path: str, content: str) -> bool:
    """Write to a file with error handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully wrote to file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write to file {file_path}: {e}")
        return False

async def fix_csv_processor() -> bool:
    """Fix issues in the CSV processor"""
    logger.info("Applying fixes to CSV processor...")
    
    # Backup the file
    if not backup_file(CSV_PROCESSOR_PATH):
        return False
        
    # Read the file
    content = read_file(CSV_PROCESSOR_PATH)
    if content is None:
        return False
    
    original_content = content
    fix_count = 0
    
    # Fix 1: Ensure map files are properly added to tracking lists
    try:
        # This is a critical fix for map directory file tracking
        find_pattern = r"""if map_csv_files:.*?logger\.(?:info|warning)\(f"Found \{len\(map_csv_files\)\} CSV files in map directory \{map_dir\}"\).*?self\.all_map_csv_files\.extend\(map_full_paths\)"""
        
        replacement = """if map_csv_files:
                                            # CRITICAL FIX: Track map files properly
                                            logger.warning(f"Found {len(map_csv_files)} CSV files in map directory {map_dir}")
                                            
                                            # Convert to full paths
                                            map_full_paths = [
                                                os.path.join(map_dir, f) for f in map_csv_files
                                                if not f.startswith('/')  # Only relative paths need joining
                                            ]
                                            
                                            # Add to multiple tracking lists for redundancy
                                            if not hasattr(self, 'all_map_csv_files'):
                                                self.all_map_csv_files = []
                                            self.all_map_csv_files.extend(map_full_paths)
                                            
                                            # Add to all_discovered_files to ensure processing
                                            if not hasattr(self, 'all_discovered_files'):
                                                self.all_discovered_files = []
                                            self.all_discovered_files.extend(map_full_paths)
                                            
                                            # Also add to map_csv_files_found 
                                            if not hasattr(self, 'map_csv_files_found'):
                                                self.map_csv_files_found = []
                                            self.map_csv_files_found.extend(map_csv_files)
                                            
                                            # Set flag to track that we found map files
                                            self.found_map_files = True
                                            
                                            # Log detailed information
                                            logger.warning(f"Added {len(map_full_paths)} CSV files from map directory {map_dir} to tracking lists")"""
        
        # Use regex with dot-all mode to match across lines
        new_content = re.sub(find_pattern, replacement, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 1: Map files tracking")
        else:
            logger.warning("Fix 1: Could not apply map files tracking fix - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 1: {e}")
    
    # Fix 2: Properly set files_to_process
    try:
        # This fix ensures that files_to_process gets properly set when map files are found
        find_pattern = r"""# If we found files in map directories.*?self\.files_to_process = self\.map_csv_full_paths_found"""
        
        replacement = """# If we found files in map directories, store them for processing
                            if csv_files and len(csv_files) > 0:
                                logger.warning(f"Successfully found {len(csv_files)} CSV files in map directories")
                                self.map_csv_files_found = csv_files.copy()
                                self.map_csv_full_paths_found = full_path_csv_files.copy()
                                
                                # CRITICAL FIX: Properly set files_to_process and ensure it's used
                                self.files_to_process = full_path_csv_files.copy()
                                
                                # Also update all_discovered_files to ensure these files are included
                                if not hasattr(self, 'all_discovered_files'):
                                    self.all_discovered_files = []
                                self.all_discovered_files.extend(full_path_csv_files)
                                
                                # Set flag to track that we found files
                                self.found_map_files = True
                                logger.warning(f"Found {len(self.files_to_process)} map directory CSV files, added to processing queue")"""
        
        new_content = re.sub(find_pattern, replacement, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 2: Files to process assignment")
        else:
            logger.warning("Fix 2: Could not apply files_to_process fix - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 2: {e}")
    
    # Fix 3: Add emergency file count verification
    try:
        find_pattern = r"""async def process_csv_files\(self, is_historical_mode=False, only_new_lines=True\):"""
        
        replacement = """async def process_csv_files(self, is_historical_mode=False, only_new_lines=True):
        # CRITICAL FIX: Add emergency file verification
        async def verify_map_files_emergency():
            """Emergency verification of map files to ensure they're not lost"""
            try:
                if not hasattr(self, 'map_csv_full_paths_found') or not self.map_csv_full_paths_found:
                    logger.warning("Emergency check: No map files found, attempting emergency discovery")
                    # Try emergency discovery
                    await self.discover_csv_files(force_check=True)
                    
                # Final verification
                map_files = getattr(self, 'map_csv_full_paths_found', [])
                if map_files:
                    logger.warning(f"Emergency check found {len(map_files)} map files")
                    return map_files
                return []
            except Exception as e:
                logger.error(f"Error in emergency map file verification: {e}")
                return []"""
                
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 3: Emergency file verification")
        else:
            logger.warning("Fix 3: Could not apply emergency verification - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 3: {e}")
    
    # Fix 4: Add final file count validation
    try:
        find_pattern = r"""logger\.warning\(f"DEBUG: Final total_found = \{total_found\} \(files_found=\{files_found\} \+ map_files_count=\{map_files_count\}\)"\)"""
        
        replacement = """logger.warning(f"CRITICAL CHECK: Final files found = {total_found} (normal={files_found}, map={map_files_count})")
                            
                            # CRITICAL FIX: Ensure we have files to process if the count is zero
                            if total_found == 0 and hasattr(self, 'map_csv_full_paths_found') and self.map_csv_full_paths_found:
                                map_files = self.map_csv_full_paths_found
                                logger.warning(f"Critical recovery: Using {len(map_files)} previously found map files")
                                files_to_process = map_files
                                total_found = len(map_files)"""
                                
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 4: Final file count validation")
        else:
            logger.warning("Fix 4: Could not apply file count validation - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 4: {e}")
    
    # Only write the file if we made changes
    if fix_count > 0:
        if content != original_content:
            if write_file(CSV_PROCESSOR_PATH, content):
                logger.info(f"Successfully applied {fix_count} fixes to CSV processor")
                return True
            else:
                logger.error("Failed to write updated CSV processor")
                return False
        else:
            logger.warning("No changes were made to CSV processor")
            return False
    else:
        logger.warning("No fixes could be applied to CSV processor")
        return False

async def fix_file_discovery() -> bool:
    """Fix issues in the file discovery module"""
    logger.info("Applying fixes to file discovery module...")
    
    # Backup the file
    if not backup_file(FILE_DISCOVERY_PATH):
        return False
        
    # Read the file
    content = read_file(FILE_DISCOVERY_PATH)
    if content is None:
        return False
    
    original_content = content
    fix_count = 0
    
    # Fix 1: Update map directory regex pattern
    try:
        find_pattern = r"""if re\.search\(r'\(world\|map\|level\|zone\|region\).*?', entry, re\.IGNORECASE\):"""
        
        replacement = """# CRITICAL FIX: More specific regex for map directories
                if re.search(r'(world)[-_]?\\d*', entry, re.IGNORECASE):  # Focus only on world directories"""
                
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 1: Map directory regex pattern")
        else:
            logger.warning("Fix 1: Could not apply map directory regex fix - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 1 to file discovery: {e}")
    
    # Fix 2: Fix consistent key naming in stats
    try:
        find_pattern = r"""discovery_stats = \{[^}]*?"map_files(?:_found)?": [^}]*?\}"""
        
        replacement = """discovery_stats = {
            "total_files": len(all_discovered_files),
            "map_files": len(map_files),  # Consistent key naming
            "map_directories": len(map_directories),
            "regular_files": len(regular_files),
            "filtered_files": len(filtered_files),
            "start_date": start_date,
            "historical_mode": historical_mode
        }"""
        
        new_content = re.sub(find_pattern, replacement, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 2: Stats key naming consistency")
        else:
            logger.warning("Fix 2: Could not apply stats key naming fix - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 2 to file discovery: {e}")
    
    # Fix 3: Enhance directory checking
    try:
        find_pattern = r"""def directory_exists\(.*?\):"""
        next_line = r"""[^\n]*?sftp_client[^\n]*?"""
        
        replacement = """def directory_exists(sftp_client, path):
    """Check if a directory exists via SFTP with improved error handling"""
    try:
        # CRITICAL FIX: More robust directory existence check
        if not path or path == '/' or path == '.':
            logger.warning(f"Invalid directory path: '{path}', treating as non-existent")
            return False
            
        # Standardize path format
        path = path.rstrip('/')"""
        
        new_content = re.sub(find_pattern + next_line, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 3: Enhanced directory checking")
        else:
            logger.warning("Fix 3: Could not apply directory checking enhancement - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 3 to file discovery: {e}")
    
    # Fix 4: Focus specifically on world_* directories
    try:
        find_pattern = r"""map_subdirs = \[[^\]]*?\]"""
        
        replacement = """map_subdirs = [
            "world_0",  # Primary map
            "world_1",  # Secondary map
            "world_2",  # Future proofing
            "world0",   # Alternative format
            "world1",   # Alternative format
            "world2"    # Alternative format
        ]  # CRITICAL FIX: Focus only on world directories"""
        
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 4: Focused world directory list")
        else:
            logger.warning("Fix 4: Could not apply world directory list fix - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 4 to file discovery: {e}")
    
    # Only write the file if we made changes
    if fix_count > 0:
        if content != original_content:
            if write_file(FILE_DISCOVERY_PATH, content):
                logger.info(f"Successfully applied {fix_count} fixes to file discovery")
                return True
            else:
                logger.error("Failed to write updated file discovery")
                return False
        else:
            logger.warning("No changes were made to file discovery")
            return False
    else:
        logger.warning("No fixes could be applied to file discovery")
        return False

async def fix_csv_parser() -> bool:
    """Fix issues in the CSV parser"""
    logger.info("Applying fixes to CSV parser...")
    
    # Backup the file
    if not backup_file(CSV_PARSER_PATH):
        return False
        
    # Read the file
    content = read_file(CSV_PARSER_PATH)
    if content is None:
        return False
    
    original_content = content
    fix_count = 0
    
    # Fix 1: Enhance file position tracking
    try:
        find_pattern = r"""async def get_last_processed_position\(self, file_path\):"""
        
        replacement = """async def get_last_processed_position(self, file_path):
        """Get the last processed position of a file with improved reliability"""
        # CRITICAL FIX: Normalize file path to ensure consistent lookup
        if file_path:
            # Remove any double slashes
            while '//' in file_path:
                file_path = file_path.replace('//', '/')
            # Convert backslashes to forward slashes
            file_path = file_path.replace('\\', '/')"""
        
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 1: Enhanced file position tracking")
        else:
            logger.warning("Fix 1: Could not apply file position tracking enhancement - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 1 to CSV parser: {e}")
    
    # Fix 2: Improve CSV delimiter detection
    try:
        find_pattern = r"""def parse_csv_line\(self, line\):"""
        
        replacement = """def parse_csv_line(self, line):
        """Parse a CSV line with improved delimiter detection"""
        # CRITICAL FIX: Better delimiter detection
        if not line or line.isspace():
            return None
            
        # Check for both comma and semicolon delimiters
        comma_count = line.count(',')
        semicolon_count = line.count(';')
        
        # Use the delimiter that appears more frequently
        delimiter = ',' if comma_count >= semicolon_count else ';'"""
        
        new_content = re.sub(find_pattern, replacement, content)
        if new_content != content:
            content = new_content
            fix_count += 1
            logger.info("Applied Fix 2: Improved CSV delimiter detection")
        else:
            logger.warning("Fix 2: Could not apply CSV delimiter detection improvement - pattern not found")
    except Exception as e:
        logger.error(f"Error applying Fix 2 to CSV parser: {e}")
    
    # Only write the file if we made changes
    if fix_count > 0:
        if content != original_content:
            if write_file(CSV_PARSER_PATH, content):
                logger.info(f"Successfully applied {fix_count} fixes to CSV parser")
                return True
            else:
                logger.error("Failed to write updated CSV parser")
                return False
        else:
            logger.warning("No changes were made to CSV parser")
            return False
    else:
        logger.warning("No fixes could be applied to CSV parser")
        return False

async def reset_database_tracking(db):
    """Reset database tracking for files"""
    if db is None:
        logger.error("Database connection not available")
        return False
        
    try:
        logger.info("Resetting database file position tracking...")
        
        # Clear file positions collection
        if "file_positions" in await db.list_collection_names():
            delete_result = await db.file_positions.delete_many({})
            logger.info(f"Cleared {delete_result.deleted_count} file positions")
        else:
            # Create collection if it doesn't exist
            await db.create_collection("file_positions")
            logger.info("Created file_positions collection")
        
        # Reset historical parse flags in all server collections
        servers_update = await db.servers.update_many(
            {},
            {"$set": {"historical_parse_done": True}}
        )
        logger.info(f"Reset historical_parse_done flag for {servers_update.modified_count} servers")
        
        game_servers_update = await db.game_servers.update_many(
            {},
            {"$set": {"historical_parse_done": True}}
        )
        logger.info(f"Reset historical_parse_done flag for {game_servers_update.modified_count} game servers")
        
        return True
    except Exception as e:
        logger.error(f"Error resetting database tracking: {e}")
        traceback.print_exc()
        return False

async def verify_fixes():
    """Verify that the fixes were applied successfully"""
    logger.info("Verifying applied fixes...")
    
    verification_results = {}
    
    # Verify CSV processor fixes
    try:
        csv_processor_content = read_file(CSV_PROCESSOR_PATH)
        if csv_processor_content:
            verification_results["map_files_tracking"] = "Added" in csv_processor_content and "map directory" in csv_processor_content
            verification_results["emergency_check"] = "Emergency check" in csv_processor_content
            verification_results["critical_recovery"] = "Critical recovery" in csv_processor_content
    except Exception as e:
        logger.error(f"Error verifying CSV processor fixes: {e}")
    
    # Verify file discovery fixes
    try:
        file_discovery_content = read_file(FILE_DISCOVERY_PATH)
        if file_discovery_content:
            verification_results["world_directories"] = "world_0" in file_discovery_content and "world_1" in file_discovery_content
            verification_results["map_directory_regex"] = "CRITICAL FIX: More specific regex" in file_discovery_content
    except Exception as e:
        logger.error(f"Error verifying file discovery fixes: {e}")
    
    # Verify CSV parser fixes
    try:
        csv_parser_content = read_file(CSV_PARSER_PATH)
        if csv_parser_content:
            verification_results["file_position_tracking"] = "Normalize file path" in csv_parser_content
            verification_results["delimiter_detection"] = "delimiter that appears more frequently" in csv_parser_content
    except Exception as e:
        logger.error(f"Error verifying CSV parser fixes: {e}")
    
    # Log verification results
    all_verified = all(verification_results.values())
    logger.info(f"Verification results: {verification_results}")
    
    if all_verified:
        logger.info("✅ All fixes verified successfully!")
    else:
        failed = [key for key, value in verification_results.items() if not value]
        logger.warning(f"❌ Some fixes could not be verified: {failed}")
    
    return all_verified

async def main():
    """Main function to apply all fixes"""
    logger.info("Starting robust CSV processing fix")
    
    # Create backup directory
    if not create_backup_directory():
        logger.error("Failed to create backup directory, aborting")
        return False
    
    # Connect to database
    db = await connect_to_db()
    
    try:
        # Apply fixes to each module
        csv_processor_fixed = await fix_csv_processor()
        file_discovery_fixed = await fix_file_discovery()
        csv_parser_fixed = await fix_csv_parser()
        
        # Reset database tracking if we have a database connection
        db_reset = False
        if db is not None:
            db_reset = await reset_database_tracking(db)
        
        # Verify the fixes
        fixes_verified = await verify_fixes()
        
        # Log results
        results = {
            "csv_processor_fixed": csv_processor_fixed,
            "file_discovery_fixed": file_discovery_fixed,
            "csv_parser_fixed": csv_parser_fixed,
            "db_reset": db_reset,
            "fixes_verified": fixes_verified
        }
        
        logger.info(f"Fix results: {results}")
        
        overall_success = csv_processor_fixed or file_discovery_fixed or csv_parser_fixed
        if overall_success:
            logger.info("✅ Successfully applied CSV processing fixes!")
        else:
            logger.warning("❌ No fixes were applied")
        
        return overall_success
    except Exception as e:
        logger.error(f"Error during fix application: {e}")
        traceback.print_exc()
        return False
    finally:
        # Close database connection
        if db is not None and hasattr(db, 'client') and hasattr(db.client, 'close'):
            await db.client.close()
            logger.info("Closed database connection")

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
