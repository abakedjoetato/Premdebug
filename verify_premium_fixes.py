
#!/usr/bin/env python3
"""
Diagnostic script to verify premium tier feature access fixes.
This script tests the premium tier access checks for leaderboards and other features.
"""
import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("premium_verification")

async def main():
    """Main function to verify premium tier fixes"""
    # Get command line arguments
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        # Default to test guild if none provided
        guild_id = "1219706687980568769"  # Example guild ID
    
    logger.info(f"Verifying premium tier fixes for guild ID: {guild_id}")
    
    # Step 1: Connect to database
    from utils.database import get_db
    logger.info("Connecting to database...")
    db = await get_db()
    
    # Step 2: Get raw guild document
    logger.info(f"Fetching raw guild document for guild ID: {guild_id}")
    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
    if not guild_doc:
        logger.error(f"No guild found with ID: {guild_id}")
        return
    
    # Show raw premium tier value from DB
    raw_premium_tier = guild_doc.get('premium_tier')
    logger.info(f"Raw premium_tier from DB: {raw_premium_tier}, type: {type(raw_premium_tier).__name__}")
    
    # Step 3: Load Guild model
    from models.guild import Guild
    logger.info("Creating Guild model from document...")
    guild_model = Guild.create_from_db_document(guild_doc, db)
    if guild_model:
        logger.info(f"Guild model loaded. Raw premium_tier: {guild_model.premium_tier}, type: {type(guild_model.premium_tier).__name__}")
        
        # Step 4: Test feature access via direct model check
        for feature in ['killfeed', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                # Direct model check
                has_access = guild_model.check_feature_access(feature)
                logger.info(f"Direct model check for '{feature}': {has_access}")
            except Exception as e:
                logger.error(f"Error in direct feature check for '{feature}': {e}")
                
        # Step 5: Test feature access via utility function
        from utils.premium import has_feature_access
        for feature in ['killfeed', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                # Utility function check (cached)
                has_access = await has_feature_access(guild_model, feature)
                logger.info(f"Utility function check for '{feature}': {has_access}")
            except Exception as e:
                logger.error(f"Error in utility function check for '{feature}': {e}")
                
        # Step 6: Test premium validation utility
        from utils.premium import validate_premium_feature
        for feature in ['killfeed', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                # Premium validation check
                has_access, error_msg = await validate_premium_feature(guild_model, feature)
                logger.info(f"Premium validation for '{feature}': access={has_access}, error={error_msg}")
            except Exception as e:
                logger.error(f"Error in premium validation for '{feature}': {e}")
                
        # Step 7: Verify leaderboard functionality (which was causing errors)
        logger.info("Testing leaderboard functionality...")
        try:
            # Getting a small leaderboard
            pipeline = [
                {"$match": {"server_id": {"$exists": True}}},
                {"$project": {"name": 1, "server_id": 1, "kills": 1}},
                {"$sort": {"kills": -1}},
                {"$limit": 5}
            ]
            cursor = db.players.aggregate(pipeline)
            entries = await cursor.to_list(length=5)
            
            # Process entries with our new defensive approach
            leaderboard_str = ""
            for i, entry in enumerate(entries, 1):
                player_name = entry.get('name', entry.get('player_name', entry.get('_id', 'Unknown Player')))
                player_value = entry.get('kills', entry.get('value', entry.get('count', 0)))
                leaderboard_str += f"{i} **{player_name}**: {player_value}\n"
                
            logger.info(f"Successfully generated leaderboard:\n{leaderboard_str}")
        except Exception as e:
            logger.error(f"Error testing leaderboard functionality: {e}")
    else:
        logger.error("Failed to create Guild model from document")

if __name__ == "__main__":
    asyncio.run(main())
