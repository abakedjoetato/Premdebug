
import asyncio
import sys
import logging
from utils.database import get_db
from models.guild import Guild
from utils.premium import get_guild_premium_tier, has_feature_access
from config import PREMIUM_TIERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('premium_diagnosis')

async def diagnose_guild_premium(guild_id):
    """Run comprehensive premium tier diagnostics on a guild"""
    logger.info(f"Running premium tier diagnostics for guild ID: {guild_id}")
    
    # Get database connection
    db = await get_db()
    if not db:
        logger.error("Failed to connect to database")
        return
    
    # Step 1: Direct DB query
    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
    if guild_doc:
        logger.info(f"Direct DB query result: {guild_doc.get('premium_tier')}")
    else:
        logger.error(f"Guild {guild_id} not found in database")
        
        # Try alternate formats
        if str(guild_id).isdigit():
            guild_doc = await db.guilds.find_one({"guild_id": int(guild_id)})
            if guild_doc:
                logger.info(f"Found guild with numeric ID lookup: {guild_doc.get('premium_tier')}")
        
        # Try case-insensitive query
        regex_query = {"guild_id": {"$regex": f"^{str(guild_id)}$", "$options": "i"}}
        guild_doc = await db.guilds.find_one(regex_query)
        if guild_doc:
            logger.info(f"Found guild with case-insensitive regex: {guild_doc.get('premium_tier')}")
            
        if not guild_doc:
            logger.error("Guild not found after all query attempts")
            return
    
    # Step 2: Use get_guild_premium_tier
    premium_tier, tier_data = await get_guild_premium_tier(db, guild_id)
    logger.info(f"get_guild_premium_tier result: {premium_tier}")
    logger.info(f"Tier data: {tier_data.get('name')}, features: {tier_data.get('features', [])[0:3]}...")
    
    # Step 3: Load Guild model
    guild_model = await Guild.get_by_guild_id(db, guild_id)
    if guild_model:
        logger.info(f"Guild model loaded. Raw premium_tier: {guild_model.premium_tier}, type: {type(guild_model.premium_tier).__name__}")
        
        # Step 4: Check feature access
        for feature in ['killfeed', 'basic_stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                has_access = await has_feature_access(guild_model, feature)
                logger.info(f"Feature access check for '{feature}': {has_access}")
                
                direct_check = guild_model.check_feature_access(feature)
                logger.info(f"Direct model check for '{feature}': {direct_check}")
            except Exception as e:
                logger.error(f"Error checking feature '{feature}': {e}")
    else:
        logger.error("Failed to load Guild model")
    
    # Step 5: Verify premium tier consistency
    if guild_model:
        # Get raw value from document
        raw_premium_tier = guild_doc.get('premium_tier')
        model_premium_tier = guild_model.premium_tier
        
        logger.info(f"Premium tier value comparison:")
        logger.info(f"  - DB document raw value: {raw_premium_tier} ({type(raw_premium_tier).__name__})")
        logger.info(f"  - Guild model value: {model_premium_tier} ({type(model_premium_tier).__name__})")
        logger.info(f"  - get_guild_premium_tier: {premium_tier} ({type(premium_tier).__name__})")
        
        # Check for inconsistencies
        if raw_premium_tier != model_premium_tier or premium_tier != model_premium_tier:
            logger.error("INCONSISTENCY DETECTED: Premium tier values don't match")
            
            # Attempt to fix the inconsistency
            try:
                logger.info("Attempting to fix premium tier inconsistency")
                # Use the highest tier value to ensure proper access
                correct_tier = max(
                    int(raw_premium_tier) if raw_premium_tier is not None else 0,
                    int(model_premium_tier) if model_premium_tier is not None else 0,
                    premium_tier
                )
                
                logger.info(f"Setting premium tier to {correct_tier}")
                await guild_model.set_premium_tier(db, correct_tier)
                logger.info("Premium tier updated")
                
                # Verify the update
                updated_model = await Guild.get_by_guild_id(db, guild_id)
                logger.info(f"Updated model premium tier: {updated_model.premium_tier}")
            except Exception as e:
                logger.error(f"Error fixing premium tier: {e}")
        else:
            logger.info("Premium tier values are consistent across all checks")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python check_guild_premium_tier.py <guild_id>")
        return
    
    guild_id = sys.argv[1]
    await diagnose_guild_premium(guild_id)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Diagnostic script to check guild premium tier functionality.
This script tests the premium tier access checks for a specified guild.
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
logger = logging.getLogger(__name__)

async def main():
    """Main function to check guild premium tier functionality"""
    # Get command line arguments
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        # Default to test guild if none provided
        guild_id = "1219706687980568769"  # Example guild ID
    
    logger.info(f"Checking premium tier functionality for guild ID: {guild_id}")
    
    # Step 1: Connect to database
    from utils.database import get_db
    logger.info("Connecting to database...")
    db = await get_db()
    
    # Step 2: Get guild document directly
    logger.info(f"Fetching guild document for guild ID: {guild_id}")
    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
    if not guild_doc:
        logger.error(f"No guild found with ID: {guild_id}")
        return
    
    # Log raw premium tier data
    raw_premium_tier = guild_doc.get('premium_tier')
    logger.info(f"Raw premium_tier from DB: {raw_premium_tier}, type: {type(raw_premium_tier).__name__}")
    
    # Step 3: Load Guild model
    from models.guild import Guild
    logger.info("Creating Guild model from document...")
    guild_model = Guild.create_from_db_document(guild_doc, db)
    if guild_model:
        logger.info(f"Guild model loaded. Raw premium_tier: {guild_model.premium_tier}, type: {type(guild_model.premium_tier).__name__}")
        
        # Step 4: Check feature access
        for feature in ['killfeed', 'basic_stats', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                # Check using instance method
                direct_check = guild_model.check_feature_access(feature)
                logger.info(f"Direct model check for '{feature}': {direct_check}")
                
                # Check using utility function
                from utils.premium import has_feature_access
                utility_check = await has_feature_access(guild_model, feature)
                logger.info(f"Utility function check for '{feature}': {utility_check}")
            except Exception as e:
                logger.error(f"Error checking feature '{feature}': {e}")
    else:
        logger.error("Failed to create Guild model from document")
    
    # Step 5: Check guild via get_by_guild_id
    logger.info("Testing Guild.get_by_guild_id...")
    retrieved_guild = await Guild.get_by_guild_id(db, guild_id)
    if retrieved_guild:
        logger.info(f"Retrieved guild premium_tier: {retrieved_guild.premium_tier}")
        
        # Check feature access on the retrieved guild
        for feature in ['stats', 'leaderboards']:
            try:
                has_access = retrieved_guild.check_feature_access(feature)
                logger.info(f"Retrieved guild check for '{feature}': {has_access}")
            except Exception as e:
                logger.error(f"Error checking feature access on retrieved guild: {e}")
    else:
        logger.error("Failed to retrieve guild via get_by_guild_id")
    
    # Step 6: Test premium validation utility
    logger.info("Testing premium validation utility...")
    from utils.premium import validate_premium_feature
    for feature in ['stats', 'leaderboards']:
        try:
            has_access, error_msg = await validate_premium_feature(guild_model, feature)
            logger.info(f"Premium validation for '{feature}': access={has_access}, error={error_msg}")
        except Exception as e:
            logger.error(f"Error in premium validation for '{feature}': {e}")
    
    logger.info("Premium tier check completed.")

if __name__ == "__main__":
    asyncio.run(main())
