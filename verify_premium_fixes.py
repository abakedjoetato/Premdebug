#!/usr/bin/env python3
"""
Script to verify premium tier checks are working correctly 
for both Guild objects and dictionary guild data
"""
import asyncio
import logging
import sys
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("premium_verifier")

async def test_premium_checks(guild_id: str) -> Tuple[bool, str]:
    """Test premium tier checks for a specific guild"""
    try:
        # Import required modules
        from utils.database import get_db
        from models.guild import Guild
        from utils.premium import has_feature_access, validate_premium_feature

        # Get database connection
        db = await get_db()
        if not db:
            return False, "Failed to connect to database"

        # Get guild document directly
        guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
        if not guild_doc:
            return False, f"Guild {guild_id} not found in database"

        # Step 1: Test premium tier in DB
        db_tier = guild_doc.get("premium_tier", 0)
        logger.info(f"Direct DB premium tier: {db_tier} (type: {type(db_tier).__name__})")

        # Step 2: Test with Guild object
        guild_obj = await Guild.get_by_guild_id(db, guild_id)
        guild_obj_tier = getattr(guild_obj, "premium_tier", None)
        logger.info(f"Guild object premium tier: {guild_obj_tier} (type: {type(guild_obj_tier).__name__ if guild_obj_tier is not None else 'None'})")

        # Step 3: Test has_feature_access with Guild object
        obj_access = await has_feature_access(guild_obj, "stats")
        logger.info(f"has_feature_access with Guild object: {obj_access}")

        # Step 4: Test validate_premium_feature with Guild object
        obj_valid, obj_error = await validate_premium_feature(guild_obj, "stats")
        logger.info(f"validate_premium_feature with Guild object: {obj_valid}, error: {obj_error}")

        # Step 5: Test Guild.check_feature_access with Guild object
        obj_check = guild_obj.check_feature_access("stats")
        logger.info(f"Guild.check_feature_access with Guild object: {obj_check}")

        # Step 6: Test with dictionary
        dict_guild = dict(guild_doc)
        dict_tier = dict_guild.get("premium_tier", 0)
        logger.info(f"Dictionary premium tier: {dict_tier} (type: {type(dict_tier).__name__})")

        # Step 7: Test has_feature_access with dictionary
        dict_access = await has_feature_access(dict_guild, "stats")
        logger.info(f"has_feature_access with dictionary: {dict_access}")

        # Step 8: Test with dictionary in check_feature_access method
        try:
            # Need to manually call this since dict doesn't have methods
            from models.guild import Guild
            dict_check = Guild.check_feature_access(dict_guild, "stats")
            logger.info(f"Guild.check_feature_access with dictionary: {dict_check}")
        except Exception as e:
            logger.error(f"Error in Guild.check_feature_access with dictionary: {e}")
            dict_check = False

        # Create final result summary
        if obj_access and obj_valid and obj_check and dict_access and dict_check:
            return True, "All premium tier checks passed successfully!"
        else:
            return False, "Some premium tier checks failed. See log for details."

    except Exception as e:
        logger.error(f"Error testing premium checks: {e}", exc_info=True)
        return False, f"Error: {str(e)}"

async def main():
    """Run premium verification tests"""
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        guild_id = input("Enter guild ID to test premium checks: ").strip()

    logger.info(f"Testing premium checks for guild: {guild_id}")
    success, message = await test_premium_checks(guild_id)

    print("\n" + "="*50)
    print(f"TEST RESULT: {'SUCCESS' if success else 'FAILED'}")
    print(message)
    print("="*50)

    return 0 if success else 1

if __name__ == "__main__":
    asyncio.run(main())