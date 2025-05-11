
#!/usr/bin/env python
"""
Server Data Cleanup Script

This script performs comprehensive cleanup of server data:
1. Removes server entries with no associated guild
2. Cleans up historical parsing flags
3. Ensures consistency between collections
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cleanup.log")
    ]
)

logger = logging.getLogger("server_cleanup")

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

async def cleanup_orphaned_servers(db):
    """Clean up servers with no associated guild"""
    logger.info("Looking for orphaned servers (servers without a guild)...")
    
    # Find all servers in game_servers collection
    server_count = 0
    async for server in db.game_servers.find():
        server_id = server.get("server_id")
        guild_id = server.get("guild_id")
        
        # Check if guild exists
        if guild_id:
            guild = await db.guilds.find_one({"guild_id": guild_id})
            if not guild:
                logger.info(f"Found orphaned server {server_id} with non-existent guild {guild_id}")
                # Remove the server
                result = await db.game_servers.delete_one({"server_id": server_id})
                if result.deleted_count > 0:
                    logger.info(f"Removed orphaned server {server_id}")
                    server_count += 1
    
    logger.info(f"Removed {server_count} orphaned servers")
    return server_count

async def reset_historical_parse_flags(db):
    """Reset historical parse flags for all servers"""
    logger.info("Checking for servers with incorrect historical parse flags...")
    
    # Update all servers in standalone servers collection
    result1 = await db.servers.update_many(
        {"historical_parse_done": {"$ne": True}},
        {"$set": {"historical_parse_done": False}}
    )
    
    # Update all servers in guilds collection
    guilds_updated = 0
    server_count = 0
    
    async for guild in db.guilds.find({"servers": {"$exists": True}}):
        guild_id = guild.get("guild_id")
        servers = guild.get("servers", [])
        updated = False
        
        for i, server in enumerate(servers):
            if "historical_parse_done" not in server or server["historical_parse_done"] is None:
                servers[i]["historical_parse_done"] = False
                updated = True
                server_count += 1
        
        if updated:
            await db.guilds.update_one(
                {"guild_id": guild_id},
                {"$set": {"servers": servers}}
            )
            guilds_updated += 1
    
    logger.info(f"Reset historical parse flags for {result1.modified_count} standalone servers")
    logger.info(f"Reset historical parse flags for {server_count} servers in {guilds_updated} guilds")
    
    return result1.modified_count + server_count

async def synchronize_server_data(db):
    """Synchronize server data between collections"""
    logger.info("Synchronizing server data between collections...")
    
    # Get all servers from game_servers collection
    server_count = 0
    async for server in db.game_servers.find():
        server_id = server.get("server_id")
        guild_id = server.get("guild_id")
        original_id = server.get("original_server_id")
        
        if not original_id:
            logger.info(f"Server {server_id} missing original_server_id, attempting to derive it")
            
            # Try to derive original_server_id
            if "-" not in server_id:  # Not a UUID
                original_id = server_id
            else:
                # Try to extract from name
                server_name = server.get("name", "")
                for word in str(server_name).split():
                    if word.isdigit() and len(word) >= 4:
                        original_id = word
                        break
                
                if not original_id:
                    # Extract digits from UUID as fallback
                    digits = ''.join(filter(str.isdigit, server_id))
                    original_id = digits[-5:] if len(digits) >= 5 else digits
            
            # Update the server
            if original_id:
                await db.game_servers.update_one(
                    {"server_id": server_id},
                    {"$set": {"original_server_id": original_id}}
                )
                logger.info(f"Set original_server_id={original_id} for server {server_id}")
                
                # Also update in standalone servers collection
                await db.servers.update_one(
                    {"server_id": server_id},
                    {"$set": {"original_server_id": original_id}},
                    upsert=True
                )
                
                server_count += 1
    
    logger.info(f"Synchronized original_server_id for {server_count} servers")
    return server_count

async def main():
    """Main entry point"""
    logger.info("Starting server data cleanup")
    
    # Connect to database
    db = await connect_to_db()
    if not db:
        logger.error("Failed to connect to database, exiting")
        return 1
    
    try:
        # Clean up orphaned servers
        orphaned_count = await cleanup_orphaned_servers(db)
        
        # Reset historical parse flags
        flags_count = await reset_historical_parse_flags(db)
        
        # Synchronize server data
        sync_count = await synchronize_server_data(db)
        
        logger.info("Server data cleanup completed successfully")
        logger.info(f"Summary: Removed {orphaned_count} orphaned servers")
        logger.info(f"Summary: Reset {flags_count} historical parse flags")
        logger.info(f"Summary: Synchronized {sync_count} server IDs")
        
        return 0
    except Exception as e:
        logger.error(f"Error during server data cleanup: {e}")
        return 1
    finally:
        # Close database connection
        if hasattr(db, 'client') and hasattr(db.client, 'close'):
            db.client.close()
            logger.info("Closed database connection")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
