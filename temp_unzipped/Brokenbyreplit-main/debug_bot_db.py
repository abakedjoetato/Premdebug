"""
Bot Database Debug Script

This script simulates the bot's database connection to diagnose connection issues.
"""
import asyncio
import logging
import os
import motor.motor_asyncio
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('bot_db_debug')

async def test_bot_db_connection():
    """
    Test database connection similar to how the bot connects.
    """
    logger.info("Testing bot database connection method")
    
    mongo_uri = os.environ.get('MONGODB_URI')
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return False
    
    # Test database connection the way the bot does it in bot.py
    try:
        # Create client with same settings as bot.py
        client = motor.motor_asyncio.AsyncIOMotorClient(
            mongo_uri, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000
        )
        
        # First connect to emeralds_killfeed like we're fixing it to do
        emeralds_db = client.emeralds_killfeed
        await emeralds_db.command("ping")
        logger.info("Successfully connected to emeralds_killfeed database")
        
        # Check collections and contents
        servers = await emeralds_db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(servers)} SFTP-enabled servers in emeralds_killfeed.servers")
        
        game_servers = await emeralds_db.game_servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(game_servers)} SFTP-enabled servers in emeralds_killfeed.game_servers")
        
        # Now try with explicit database name hardcoded
        logger.info("Testing with explicit database name parameter")
        db = client["emeralds_killfeed"]
        await db.command("ping")
        
        servers = await db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(servers)} SFTP-enabled servers using explicit db name")
        
        # Check for case sensitivity issues
        sftp_true_servers = await db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(sftp_true_servers)} servers with sftp_enabled=True")
        
        sftp_string_true_servers = await db.servers.find({"sftp_enabled": "True"}).to_list(length=100)
        logger.info(f"Found {len(sftp_string_true_servers)} servers with sftp_enabled='True'")
        
        # Try to mimic the way log_processor is using it
        logger.info("Simulating log_processor collection access")
        all_servers = await db.servers.find({}).to_list(length=100)
        logger.info(f"Found {len(all_servers)} total servers in servers collection")
        for srv in all_servers:
            logger.info(f"Server: ID={srv.get('_id')}, sftp_enabled={srv.get('sftp_enabled')}, name={srv.get('server_name')}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing bot database connection: {e}")
        return False

async def simulate_database_manager():
    """
    Simulate the DatabaseManager from utils/database.py
    """
    logger.info("Simulating DatabaseManager")
    
    try:
        from utils.database import DatabaseManager, get_db, initialize_db
        
        # Create new instance like log_processor would use
        logger.info("Creating DatabaseManager instance directly")
        direct_manager = DatabaseManager()
        await direct_manager.initialize()
        
        # Check the database it's connected to
        logger.info(f"Direct manager db name: {direct_manager.db_name}")
        logger.info(f"Direct manager connected: {direct_manager._connected}")
        
        # Check collections
        servers = await direct_manager._db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(servers)} SFTP-enabled servers via direct manager")
        
        # Get singleton instance like most code uses
        logger.info("Getting singleton database manager")
        global_manager = await get_db()
        
        # Check the database it's connected to
        logger.info(f"Global manager db name: {global_manager.db_name}")
        logger.info(f"Global manager connected: {global_manager._connected}")
        
        # Check collections
        servers = await global_manager._db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(servers)} SFTP-enabled servers via global manager")
        
        return True
        
    except Exception as e:
        logger.error(f"Error simulating DatabaseManager: {e}")
        return False

async def main():
    """
    Main entry point
    """
    logger.info("Bot database debug script started")
    
    success1 = await test_bot_db_connection()
    if success1:
        logger.info("Bot database connection test completed successfully")
    else:
        logger.error("Bot database connection test failed")
    
    success2 = await simulate_database_manager()
    if success2:
        logger.info("DatabaseManager simulation completed successfully")
    else:
        logger.error("DatabaseManager simulation failed")

if __name__ == "__main__":
    asyncio.run(main())