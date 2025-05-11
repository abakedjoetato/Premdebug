"""
Force direct check of server configurations in the database.
This script bypasses the bot's internal database access methods and
directly checks the database for server configurations.
"""
import asyncio
import logging
import os
import motor.motor_asyncio
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('server_check')

async def force_check_server_configs():
    """Force direct check of server configurations"""
    try:
        # Connect to MongoDB
        mongo_uri = os.environ.get('MONGODB_URI')
        if not mongo_uri:
            logger.error("MONGODB_URI environment variable not set")
            return False
        
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db = client.emeralds_killfeed
        
        # Check collections
        logger.info("Checking collections...")
        collections = await db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check servers collection document structure
        logger.info("\nServers collection:")
        servers = await db.servers.find({}).to_list(length=100)
        logger.info(f"Found {len(servers)} total servers in servers collection")
        
        for i, server in enumerate(servers):
            logger.info(f"Server {i+1}:")
            for key, value in server.items():
                logger.info(f"  {key}: {value}")
            
        # Check for sftp_enabled with different capitalization or as string
        logger.info("\nChecking for SFTP enabled with different formats:")
        true_servers = await db.servers.find({"sftp_enabled": True}).to_list(length=100)
        logger.info(f"Found {len(true_servers)} servers with sftp_enabled=True")
        
        string_true_servers = await db.servers.find({"sftp_enabled": "True"}).to_list(length=100)
        logger.info(f"Found {len(string_true_servers)} servers with sftp_enabled='True'")
        
        string_true_lower_servers = await db.servers.find({"sftp_enabled": "true"}).to_list(length=100)
        logger.info(f"Found {len(string_true_lower_servers)} servers with sftp_enabled='true'")
        
        # Check game_servers collection document structure
        logger.info("\nGame servers collection:")
        game_servers = await db.game_servers.find({}).to_list(length=100)
        logger.info(f"Found {len(game_servers)} total servers in game_servers collection")
        
        for i, server in enumerate(game_servers):
            logger.info(f"Game Server {i+1}:")
            for key, value in server.items():
                logger.info(f"  {key}: {value}")
            
        # Try using fake query to confirm database is working
        logger.info("\nTesting with fake/non-existent field query:")
        fake_servers = await db.servers.find({"this_field_doesnt_exist": True}).to_list(length=100)
        logger.info(f"Found {len(fake_servers)} servers with this_field_doesnt_exist=True (should be 0)")
        
        # Try updating the sftp_enabled field for testing to ensure write permissions
        logger.info("\nAttempting to update a test server:")
        if len(servers) > 0:
            server_id = servers[0]["_id"]
            current_sftp = servers[0].get("sftp_enabled", False)
            logger.info(f"Current sftp_enabled for server {server_id}: {current_sftp}")
            
            # Toggle the value
            new_value = not current_sftp
            result = await db.servers.update_one({"_id": server_id}, {"$set": {"sftp_enabled": new_value}})
            logger.info(f"Update result: {result.modified_count} document(s) modified")
            
            # Toggle back to original value
            result = await db.servers.update_one({"_id": server_id}, {"$set": {"sftp_enabled": current_sftp}})
            logger.info(f"Restore result: {result.modified_count} document(s) modified")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking server configurations: {e}")
        return False

async def main():
    """Main entry point"""
    logger.info("Force checking server configurations...")
    success = await force_check_server_configs()
    if success:
        logger.info("Server configuration check completed successfully")
    else:
        logger.error("Server configuration check failed")

if __name__ == "__main__":
    asyncio.run(main())