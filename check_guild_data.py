import asyncio
import motor.motor_asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("guild_check")

async def check_guild():
    """Check if guild data exists in the database"""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.emeralds_killfeed
        
        # Check for guild with ID
        guild_id = '1219706687980568769'
        logger.info(f"Searching for guild with ID: {guild_id}")
        
        guild = await db.guilds.find_one({'guild_id': guild_id})
        logger.info(f"Guild data found: {guild is not None}")
        
        if guild:
            logger.info(f"Guild ID: {guild.get('guild_id')}")
            logger.info(f"Guild ID type: {type(guild.get('guild_id'))}")
            logger.info(f"Server count: {len(guild.get('servers', []))}")
        
        # Also try with integer ID
        int_guild_id = int(guild_id)
        logger.info(f"Searching for guild with integer ID: {int_guild_id}")
        
        guild = await db.guilds.find_one({'guild_id': int_guild_id})
        logger.info(f"Guild data found with integer ID: {guild is not None}")
        
        # Check all guilds in the collection
        guild_count = await db.guilds.count_documents({})
        logger.info(f"Total guild documents in database: {guild_count}")
        
        if guild_count > 0:
            logger.info("Listing all guild IDs:")
            async for g in db.guilds.find({}, {'guild_id': 1}):
                logger.info(f"Found guild: {g.get('guild_id')} (type: {type(g.get('guild_id'))})")
    
    except Exception as e:
        logger.error(f"Error checking guild: {e}")

if __name__ == "__main__":
    asyncio.run(check_guild())