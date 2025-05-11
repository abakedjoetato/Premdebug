"""
Database access debugging script.
This script directly checks the database connection and server configurations.
"""
import asyncio
import logging
import os
import motor.motor_asyncio
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('db_debug')

async def check_database_access():
    """
    Check direct database access for server configurations.
    """
    logger.info("Starting database access check")
    
    # Connect directly using environment variable
    mongo_uri = os.environ.get('MONGODB_URI')
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return False
    
    # Print connection details (without sensitive parts)
    parts = mongo_uri.split('@')
    if len(parts) > 1:
        safe_uri = f"mongodb+srv://xxx:xxx@{parts[1]}"
        logger.info(f"Connecting to: {safe_uri}")
    
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            mongo_uri, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000
        )
        
        # First check towerdb (old database)
        db_old = client.towerdb
        logger.info("Testing connection to towerdb...")
        try:
            await db_old.command("ping")
            logger.info("Successfully connected to towerdb")
            
            server_count = await db_old.servers.count_documents({})
            logger.info(f"Found {server_count} servers in towerdb.servers")
            
            sftp_servers = await db_old.servers.find({"sftp_enabled": True}).to_list(length=100)
            logger.info(f"Found {len(sftp_servers)} SFTP-enabled servers in towerdb.servers")
            
            if 'game_servers' in await db_old.list_collection_names():
                game_server_count = await db_old.game_servers.count_documents({})
                logger.info(f"Found {game_server_count} servers in towerdb.game_servers")
                
                sftp_game_servers = await db_old.game_servers.find({"sftp_enabled": True}).to_list(length=100)
                logger.info(f"Found {len(sftp_game_servers)} SFTP-enabled servers in towerdb.game_servers")
            else:
                logger.info("No game_servers collection in towerdb")
        
        except Exception as e:
            logger.error(f"Error testing towerdb: {e}")
        
        # Now check emeralds_killfeed (current database)
        db = client.emeralds_killfeed
        logger.info("Testing connection to emeralds_killfeed...")
        await db.command("ping")
        logger.info("Successfully connected to emeralds_killfeed")
        
        server_count = await db.servers.count_documents({})
        logger.info(f"Found {server_count} servers in emeralds_killfeed.servers")
        
        sftp_servers = await db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(sftp_servers)} SFTP-enabled servers in emeralds_killfeed.servers")
        
        # Log all fields in the server document
        if sftp_servers is not None:
            logger.info("Server document fields:")
            for key, value in sftp_servers[0].items():
                logger.info(f"  {key}: {value}")
        
        game_server_count = await db.game_servers.count_documents({})
        logger.info(f"Found {game_server_count} servers in emeralds_killfeed.game_servers")
        
        sftp_game_servers = await db.game_servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(sftp_game_servers)} SFTP-enabled servers in emeralds_killfeed.game_servers")
        
        # Log all fields in the game_server document
        if sftp_game_servers is not None:
            logger.info("Game Server document fields:")
            for key, value in sftp_game_servers[0].items():
                logger.info(f"  {key}: {value}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking database access: {e}")
        return False

async def main():
    """
    Main entry point
    """
    logger.info("Database access debug script started")
    success = await check_database_access()
    if success:
        logger.info("Database access check completed successfully")
    else:
        logger.error("Database access check failed")

if __name__ == "__main__":
    asyncio.run(main())