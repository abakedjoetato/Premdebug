"""
Fix for Server Lookup Issue

This script enhances server lookup by implementing cross-collection lookup
and fixing issues with the way server lookups are performed in commands.

Key issues addressed:
1. Server lookups not checking across all collections consistently
2. Commands failing because they can't find servers in the database
3. Inconsistent server ID handling between collections

"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def connect_to_db():
    """Connect to the MongoDB database"""
    import os
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Get database connection string from environment
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        logger.error("MONGODB_URI environment variable not set")
        return None
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.get_default_database()
    logger.info(f"Connected to MongoDB database: {db.name}")
    return db

async def enhance_server_lookup():
    """Enhance the Server.get_by_id method to properly handle lookups across collections"""
    from utils.server_utils import standardize_server_id
    
    # Path to file
    file_path = "models/server.py"
    
    try:
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Make a backup
        with open(f"{file_path}.bak", 'w') as f:
            f.write(content)
            
        logger.info(f"Created backup of {file_path}")
        
        # Get the get_by_id method and identify where to insert our fix
        method_start = content.find("@classmethod\n    async def get_by_id")
        if method_start == -1:
            logger.error("Could not find get_by_id method in Server model")
            return False
        
        method_end = content.find("@classmethod", method_start + 1)
        if method_end == -1:
            logger.error("Could not find end of get_by_id method in Server model")
            return False
        
        # Extract method content
        method_content = content[method_start:method_end]
        
        # Check if our fix already exists
        if "Check servers collection (where CSV data is stored)" in method_content:
            logger.info("Server lookup fix already applied")
            return True
        
        # Add additional collection lookups - this is the key enhancement
        enhanced_method = """@classmethod
    async def get_by_id(cls, db, server_id: str, guild_id: Optional[str] = None) -> Optional['Server']:
        \"\"\"Get a server by server_id and optionally guild_id
        (This is an alias for get_by_server_id with additional guild_id filter)

        Args:
            db: Database connection
            server_id: Server ID
            guild_id: Optional Guild ID to verify ownership

        Returns:
            Server object or None if not found
        \"\"\"
        # Import standardize_server_id here to avoid circular imports
        from utils.server_utils import standardize_server_id
        
        # Standardize the server_id to ensure consistent formatting
        standardized_server_id = standardize_server_id(server_id)
        
        if standardized_server_id is None:
            logger.warning(f"Invalid server_id format: {server_id}")
            return None
            
        # Build the query with standardized server ID
        query = {"server_id": standardized_server_id}
        if guild_id is not None:
            # Ensure consistent string comparison for guild ID too
            query["guild_id"] = str(guild_id)
        
        # First try exact match in game_servers collection
        document = await db.game_servers.find_one(query)
        
        # If no results, try case-insensitive search
        if document is None:
            logger.debug(f"No exact match for server_id: {standardized_server_id}, trying case-insensitive search")
            # Create a new case-insensitive search query
            # MongoDB regex pattern for case-insensitive matching
            regex_query = query.copy()
            # We need to modify the dictionary as a whole to avoid type issues
            new_query = {
                **regex_query,
                "server_id": {"$regex": f"^{standardized_server_id}$", "$options": "i"}
            }
            document = await db.game_servers.find_one(new_query)
        
        # If still not found, check servers collection (where CSV data is stored)    
        if document is None:
            logger.debug(f"Server not found in game_servers, checking servers collection")
            
            # Try exact match in servers collection
            server_query = {"server_id": standardized_server_id}
            if guild_id is not None:
                server_query["guild_id"] = str(guild_id)
                
            document = await db.servers.find_one(server_query)
            
            # Try with regex if needed
            if document is None:
                regex_server_query = {
                    **server_query,
                    "server_id": {"$regex": f"^{standardized_server_id}$", "$options": "i"}
                }
                document = await db.servers.find_one(regex_server_query)
            
            # If document is found, map it to format expected by from_document
            if document is not None:
                logger.info(f"Found server {standardized_server_id} in servers collection")
                # Extract original server ID for path construction if available
                original_server_id = document.get("original_server_id")
                
                # Convert to expected format
                document = {
                    "server_id": document.get("server_id"),
                    "guild_id": document.get("guild_id"),
                    "name": document.get("name", "Unknown Server"),
                    "sftp_host": document.get("hostname") or document.get("sftp_host"),
                    "sftp_port": document.get("port") or document.get("sftp_port", 22),
                    "sftp_username": document.get("username") or document.get("sftp_username"),
                    "sftp_password": document.get("password") or document.get("sftp_password"),
                    "log_path": document.get("log_path") or document.get("sftp_path", ""),
                    "original_server_id": original_server_id,
                    "_id": document.get("_id")
                }
            
        # If still not found and guild_id is provided, look in the guild's servers list as fallback
        if document is None and guild_id is not None:
            logger.debug(f"Server not found in game_servers or servers, checking guild's server list")
            guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
            
            if guild_doc is not None and "servers" in guild_doc:
                for server in guild_doc.get("servers", []):
                    # Standardize server ID from guild.servers for comparison
                    server_id_in_guild = standardize_server_id(server.get("server_id"))
                    
                    # Check if server IDs match after standardization
                    if server_id_in_guild == standardized_server_id:
                        # Found server in guild.servers, create a server document
                        logger.info(f"Found server {standardized_server_id} in guild.servers but not in game_servers or servers")
                        # Extract the original numeric server ID for path construction
                        original_server_id = server.get("original_server_id")
                        
                        # If original_server_id is not found, try to extract it from server_id
                        if original_server_id is None:
                            # Check if server_id contains numeric segment that could be original ID
                            if server.get("server_id") and any(char.isdigit() for char in server.get("server_id", "")):
                                # Extract numeric part of server ID as fallback for original ID
                                numeric_parts = ''.join(filter(str.isdigit, server.get("server_id", "")))
                                if numeric_parts:
                                    original_server_id = numeric_parts
                                    logger.info(f"Extracted fallback original_server_id {original_server_id} from server_id {server.get('server_id')}")
                        
                        server_doc = {
                            "server_id": standardized_server_id,
                            "guild_id": str(guild_id),
                            "name": server.get("server_name", "Unknown Server"),
                            "sftp_host": server.get("sftp_host") or server.get("hostname"),
                            "sftp_port": server.get("sftp_port") or server.get("port", 22),
                            "sftp_username": server.get("sftp_username") or server.get("username"),
                            "sftp_password": server.get("sftp_password") or server.get("password"),
                            "log_path": server.get("log_path") or server.get("sftp_path", ""),
                            "original_server_id": original_server_id,  # Include original numeric server ID
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        document = server_doc
                        break
        
        return cls.from_document(document) if document is not None else None"""
        
        # Replace the method with our enhanced version
        new_content = content[:method_start] + enhanced_method + content[method_end:]
        
        # Write the new content
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Enhanced server lookup in Server.get_by_id method")
        return True
        
    except Exception as e:
        logger.error(f"Error enhancing server lookup: {e}")
        return False

async def fix_explicit_none_checks():
    """Fix missing explicit None checks for MongoDB objects in stats, rivalries, and factions cogs"""
    fixes = [
        {
            "file": "cogs/stats.py",
            "old": "if guild is None or not guild.check_feature_access(\"stats\"):",
            "new": "if guild is None or not guild.check_feature_access(\"stats\"):"
        },
        {
            "file": "cogs/rivalries.py",
            "old": "if guild is None or not guild.check_feature_access(\"rivalries\"):",
            "new": "if guild is None or not guild.check_feature_access(\"rivalries\"):"
        },
        {
            "file": "cogs/factions.py",
            "old": "if guild is None or not guild.check_feature_access(\"factions\"):",
            "new": "if guild is None or not guild.check_feature_access(\"factions\"):"
        }
    ]
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for fix in fixes:
        try:
            # Skip if old == new (we're only checking, not changing)
            if fix["old"] == fix["new"]:
                skipped_count += 1
                continue
                
            file_path = fix["file"]
            old_text = fix["old"]
            new_text = fix["new"]
            
            # Read file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Make a backup if not already made
            if not os.path.exists(f"{file_path}.bak"):
                with open(f"{file_path}.bak", 'w') as f:
                    f.write(content)
                logger.info(f"Created backup of {file_path}")
            
            # Replace text
            if old_text in content:
                new_content = content.replace(old_text, new_text)
                with open(file_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Applied fix to {file_path}")
                success_count += 1
            else:
                logger.warning(f"Text not found in {file_path}")
                skipped_count += 1
        
        except Exception as e:
            logger.error(f"Error fixing {fix['file']}: {e}")
            error_count += 1
    
    logger.info(f"Fixed {success_count} files, skipped {skipped_count} files, encountered {error_count} errors")
    return success_count, skipped_count, error_count

async def enhance_db_error_logging():
    """Enhance database error logging in Player methods"""
    file_path = "models/player.py"
    
    try:
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Make a backup
        if not os.path.exists(f"{file_path}.bak"):
            with open(f"{file_path}.bak", 'w') as f:
                f.write(content)
            logger.info(f"Created backup of {file_path}")
        
        # Find get_leaderboard method
        method_start = content.find("@classmethod\n    async def get_leaderboard")
        if method_start == -1:
            logger.error("Could not find get_leaderboard method in Player model")
            return False
        
        # Check if already fixed
        if "try:" in content[method_start:method_start+1000] and "Executing leaderboard aggregation" in content[method_start:method_start+1000]:
            logger.info("Player.get_leaderboard already enhanced with error logging")
            return True
        
        # Find method content
        method_end = content.find("@classmethod", method_start + 1)
        if method_end == -1:
            # If no more @classmethod after this, find the next method or class
            next_def = content.find("\n    def ", method_start + 1)
            if next_def == -1:
                logger.error("Could not find end of get_leaderboard method in Player model")
                return False
            method_end = next_def
        
        # Extract method content
        method_content = content[method_start:method_end]
        
        # Enhanced method with better error handling
        enhanced_method = """@classmethod
    async def get_leaderboard(cls, db, server_id: str, stat: str, limit: int = 10) -> List[Dict[str, Any]]:
        \"\"\"Get player leaderboard for a specific server and stat
        
        Args:
            db: Database connection
            server_id: Server ID
            stat: Stat to sort by (kills, deaths, kdr, etc.)
            limit: Maximum number of players to return
            
        Returns:
            List of player dictionaries with stats, sorted by the specified stat
        \"\"\"
        logger.info(f"Getting leaderboard for server {server_id}, stat {stat}, limit {limit}")
        
        try:
            # Ensure limit is an integer and is reasonable
            limit = min(max(1, int(limit)), 100)  # Between 1 and 100
            
            # Create aggregation pipeline
            pipeline = [
                {"$match": {"server_id": server_id}},
                {"$project": {
                    "player_id": 1,
                    "name": 1,
                    "kills": 1,
                    "deaths": 1,
                    "kdr": {"$cond": [
                        {"$eq": ["$deaths", 0]},
                        "$kills",  # If deaths is 0, KDR is just kills
                        {"$divide": ["$kills", "$deaths"]}  # Otherwise, KDR is kills/deaths
                    ]},
                    "longest_shot": 1,
                    "playtime": 1,
                    "headshots": 1,
                    "highest_killstreak": 1,
                    "created_at": 1,
                    "updated_at": 1
                }},
                {"$sort": {stat: -1}},  # Sort by specified stat (descending)
                {"$limit": limit}
            ]
            
            logger.debug(f"Executing leaderboard aggregation with pipeline: {pipeline}")
            
            # Execute aggregation
            result = await db[cls.collection_name].aggregate(pipeline).to_list(length=limit)
            
            logger.debug(f"Leaderboard result: {len(result)} players found")
            return result
            
        except Exception as e:
            logger.error(f"Error getting leaderboard for server {server_id}, stat {stat}: {e}")
            return []"""
        
        # Replace the method with our enhanced version
        new_content = content[:method_start] + enhanced_method + content[method_end:]
        
        # Write the new content
        with open(file_path, 'w') as f:
            f.write(new_content)
            
        logger.info("Enhanced error logging in Player.get_leaderboard method")
        return True
        
    except Exception as e:
        logger.error(f"Error enhancing db error logging: {e}")
        return False

async def main():
    """Main function to fix server lookup and database issues"""
    logger.info("Starting server lookup and database fixes")
    
    import os
    if not os.path.exists('models/server.py'):
        logger.error("models/server.py not found. Make sure you're running this script from the project root.")
        return
    
    # First, enhance the server lookup
    server_lookup_result = await enhance_server_lookup()
    logger.info(f"Server lookup enhancement: {'Successful' if server_lookup_result else 'Failed'}")
    
    # Fix explicit None checks in stats, rivalries, and factions cogs
    # We commented this out because our check showed that the None checks are already correct
    # await fix_explicit_none_checks()
    
    # Enhance database error logging
    db_logging_result = await enhance_db_error_logging()
    logger.info(f"Database error logging enhancement: {'Successful' if db_logging_result else 'Failed'}")
    
    logger.info("Fixes completed")

if __name__ == "__main__":
    asyncio.run(main())