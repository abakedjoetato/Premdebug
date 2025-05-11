
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
