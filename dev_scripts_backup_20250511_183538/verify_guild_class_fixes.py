
#!/usr/bin/env python3
"""
Script to verify the Guild class fixes and check for coroutine issues
"""
import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def verify_guild_class():
    """Verify Guild class methods and check for coroutine issues"""
    try:
        # Import required modules
        from utils.database import get_db
        from models.guild import Guild
        
        # Get database connection
        db = await get_db()
        if not db:
            logger.error("Failed to connect to database")
            return False
            
        # Check guild_id with a known valid guild
        guild_id = "1219706687980568769"  # Use a known guild ID
        
        # Test guild retrieval
        logger.info(f"Testing Guild.get_by_guild_id with {guild_id}")
        guild = await Guild.get_by_guild_id(db, guild_id)
        
        if guild is None:
            logger.error(f"Could not find guild with ID {guild_id}")
            return False
            
        logger.info(f"Successfully retrieved guild {guild_id}, premium_tier: {guild.premium_tier}")
        
        # Test feature access
        logger.info("Testing check_feature_access method")
        has_stats_access = await guild.check_feature_access("stats")
        logger.info(f"Guild has access to 'stats' feature: {has_stats_access}")
        
        # All checks passed
        logger.info("All Guild class checks passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in verification: {e}", exc_info=True)
        return False

async def main():
    """Run verification script"""
    success = await verify_guild_class()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
