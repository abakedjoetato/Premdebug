
#!/usr/bin/env python3
"""
Script to fix historical parsing running on bot startup
This script marks all existing servers as having had historical parsing done
"""
import asyncio
import logging
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("historical_parse_fix")

async def fix_historical_parse_flags():
    """Mark all existing servers as having had historical parsing done"""
    # Connect to MongoDB
    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return False
        
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emeralds_killfeed
        
        # Find all guilds with servers
        guilds = await db.guilds.find({"servers": {"$exists": True}}).to_list(length=None)
        
        total_servers = 0
        updated_servers = 0
        
        for guild in guilds:
            guild_id = guild.get("guild_id")
            servers = guild.get("servers", [])
            
            logger.info(f"Processing guild {guild_id} with {len(servers)} servers")
            total_servers += len(servers)
            
            for server in servers:
                server_id = server.get("server_id")
                
                # Skip servers that already have the flag set
                if server.get("historical_parse_done", False):
                    continue
                    
                # Update the server to set historical_parse_done flag
                result = await db.guilds.update_one(
                    {"guild_id": guild_id, "servers.server_id": server_id},
                    {"$set": {"servers.$.historical_parse_done": True}}
                )
                
                if result.modified_count > 0:
                    updated_servers += 1
                    logger.info(f"  - Updated server {server_id} in guild {guild_id}")
        
        logger.info(f"Historical parse fix complete - marked {updated_servers}/{total_servers} servers as done")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing historical parse flags: {e}")
        return False

async def main():
    """Main function"""
    success = await fix_historical_parse_flags()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
