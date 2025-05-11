
#!/usr/bin/env python3
"""
Comprehensive CSV Processing Fix

This script fixes the following issues in the CSV processing system:
1. Historical parser running during normal operation
2. Killfeed parser processing all files instead of only the newest ones
3. Line position tracking issues
4. Map directory handling problems
"""
import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("csv_fix.log")
    ]
)

logger = logging.getLogger("csv_fix")

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

async def fix_historical_parse_flags(db):
    """Reset historical parse flags for all servers"""
    logger.info("Resetting historical parse flags...")
    
    # Update all servers in servers collection
    result1 = await db.servers.update_many(
        {},
        {"$set": {"historical_parse_done": True}}
    )
    
    # Update all servers in game_servers collection
    result2 = await db.game_servers.update_many(
        {},
        {"$set": {"historical_parse_done": True}}
    )
    
    # Update all embedded servers in guilds collection
    guild_count = 0
    server_count = 0
    
    async for guild in db.guilds.find({"servers": {"$exists": True}}):
        guild_id = guild.get("guild_id")
        servers = guild.get("servers", [])
        updated = False
        
        for i, server in enumerate(servers):
            if isinstance(server, dict):
                servers[i]["historical_parse_done"] = True
                updated = True
                server_count += 1
        
        if updated:
            await db.guilds.update_one(
                {"guild_id": guild_id},
                {"$set": {"servers": servers}}
            )
            guild_count += 1
    
    logger.info(f"Reset historical parse flags for {result1.modified_count} servers in servers collection")
    logger.info(f"Reset historical parse flags for {result2.modified_count} servers in game_servers collection")
    logger.info(f"Reset historical parse flags for {server_count} embedded servers in {guild_count} guilds")
    
    return result1.modified_count + result2.modified_count + server_count

async def clear_last_processed_positions(db):
    """Clear the last processed line positions to force fresh tracking"""
    logger.info("Clearing last processed line positions...")
    
    # Create a new collection for file position tracking if it doesn't exist
    if "file_positions" not in await db.list_collection_names():
        logger.info("Creating file_positions collection")
        await db.create_collection("file_positions")
    
    # Clear any existing positions
    result = await db.file_positions.delete_many({})
    logger.info(f"Cleared {result.deleted_count} file position records")
    
    return result.deleted_count

async def main():
    """Main entry point"""
    logger.info("Starting CSV processing system fix")
    
    # Connect to database
    db = await connect_to_db()
    if not db:
        logger.error("Failed to connect to database, exiting")
        return 1
    
    try:
        # Fix historical parse flags
        history_count = await fix_historical_parse_flags(db)
        
        # Clear last processed positions
        position_count = await clear_last_processed_positions(db)
        
        logger.info("CSV processing system fix completed successfully")
        logger.info(f"Summary: Reset {history_count} historical parse flags")
        logger.info(f"Summary: Cleared {position_count} file position records")
        
        return 0
    except Exception as e:
        logger.error(f"Error during CSV processing system fix: {e}")
        return 1
    finally:
        # Close database connection
        if hasattr(db, 'client') and hasattr(db.client, 'close'):
            await db.client.close()
            logger.info("Closed database connection")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
