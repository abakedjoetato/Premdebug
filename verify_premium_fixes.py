#!/usr/bin/env python3
"""
Diagnostic script to verify premium tier fixes.
This script tests that the check_feature_access method works correctly.
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

async def verify_premium_tier_fixes():
    """Verify that premium tier checks work properly"""
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
        logger.info("Testing check_feature_access method...")
        for feature in ['killfeed', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                has_access = guild_model.check_feature_access(feature)
                logger.info(f"Feature '{feature}' access check result: {has_access}")
            except Exception as e:
                logger.error(f"Error checking feature '{feature}': {e}")

        # Step 5: Test feature access via utility function
        logger.info("Testing has_feature_access utility function...")
        from utils.premium import has_feature_access
        for feature in ['killfeed', 'stats', 'leaderboards', 'rivalries', 'factions']:
            try:
                has_access = await has_feature_access(guild_model, feature)
                logger.info(f"Utility function check for '{feature}': {has_access}")
            except Exception as e:
                logger.error(f"Error in utility function check for '{feature}': {e}")

        # Step 6: Test premium validation
        logger.info("Testing premium validation utility...")
        from utils.premium import validate_premium_feature
        for feature in ['stats', 'leaderboards']:
            try:
                has_access, error_msg = await validate_premium_feature(guild_model, feature)
                logger.info(f"Premium validation for '{feature}': access={has_access}, error={error_msg}")
            except Exception as e:
                logger.error(f"Error in premium validation for '{feature}': {e}")
    else:
        logger.error("Failed to create Guild model from document")

    logger.info("Premium tier verification completed.")

async def main():
    await verify_premium_tier_fixes()

if __name__ == "__main__":
    asyncio.run(main())