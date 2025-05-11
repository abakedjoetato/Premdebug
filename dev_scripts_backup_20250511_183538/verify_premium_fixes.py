#!/usr/bin/env python3
"""
Verify that premium tier checks are working correctly across different contexts
"""
import asyncio
import logging
import sys
from typing import Dict, Any, Union, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("premium_verifier")

async def verify_premium_access(guild_id: str, feature_name: str = "leaderboards") -> Tuple[bool, str]:
    """Verify premium access across different contexts for the given guild and feature"""
    try:
        # Import required modules
        from utils.database import get_db
        from models.guild import Guild
        from utils.premium import (
            has_feature_access, 
            validate_premium_feature, 
            check_tier_access,
            PREMIUM_FEATURES
        )

        # Get database connection
        db = await get_db()
        if not db:
            return False, "Failed to connect to database"

        # Get guild model
        guild_model = await Guild.get_by_guild_id(db, guild_id)
        if guild_model is None:
            return False, f"Guild {guild_id} not found in database, consider running /setup"

        # Store all test results
        results = {}

        # 1. Verify guild_model premium_tier
        tier_info = f"Guild model premium_tier: {guild_model.premium_tier} (type: {type(guild_model.premium_tier).__name__})"
        logger.info(tier_info)
        results["tier_info"] = tier_info

        # 2. Verify has_feature_access (utility function)
        util_access = await has_feature_access(guild_model, feature_name)
        util_info = f"has_feature_access result: {util_access}"
        logger.info(util_info)
        results["utility_access"] = util_access
        results["utility_info"] = util_info

        # 3. Verify check_feature_access (Guild method)
        guild_access = await guild_model.check_feature_access(feature_name)
        guild_info = f"Guild.check_feature_access result: {guild_access}"
        logger.info(guild_info)
        results["guild_access"] = guild_access
        results["guild_info"] = guild_info

        # 4. Verify validate_premium_feature (validation function)
        has_access, error_message = await validate_premium_feature(guild_model, feature_name)
        validation_info = f"validate_premium_feature result: {has_access}, error: {error_message or 'None'}"
        logger.info(validation_info)
        results["validation_access"] = has_access
        results["validation_info"] = validation_info

        # 5. Check direct database tier value
        db_doc = await db.guilds.find_one({"guild_id": str(guild_id)}, {"premium_tier": 1})
        db_tier = db_doc.get("premium_tier") if db_doc else None
        db_info = f"Database premium_tier: {db_tier} (type: {type(db_tier).__name__ if db_tier is not None else 'None'})"
        logger.info(db_info)
        results["db_tier"] = db_tier
        results["db_info"] = db_info

        # 6. Check PREMIUM_FEATURES mapping for minimum tier
        min_tier_required = PREMIUM_FEATURES.get(feature_name, 999)
        feature_info = f"Feature '{feature_name}' requires tier {min_tier_required}"
        logger.info(feature_info)
        results["min_tier_required"] = min_tier_required
        results["feature_info"] = feature_info

        # 7. Check if all results are consistent
        all_access_results = [
            results["utility_access"],
            results["guild_access"],
            results["validation_access"]
        ]

        is_consistent = all(access == all_access_results[0] for access in all_access_results)
        consistency_info = f"Premium check results are {'consistent' if is_consistent else 'inconsistent'}"
        logger.info(consistency_info)
        results["is_consistent"] = is_consistent
        results["consistency_info"] = consistency_info

        # 8. Check if the tier and feature access match expectations
        if db_tier is not None:
            try:
                numeric_tier = int(db_tier)
                tier_sufficient = numeric_tier >= min_tier_required
                expected_info = f"Tier {numeric_tier} should {'grant' if tier_sufficient else 'deny'} access to feature requiring tier {min_tier_required}"
                tier_match = tier_sufficient == all_access_results[0]
                logger.info(expected_info)
                if not tier_match:
                    logger.error(f"MISMATCH: Expected access={tier_sufficient} but got access={all_access_results[0]}")
                results["tier_sufficient"] = tier_sufficient
                results["tier_match"] = tier_match
                results["expected_info"] = expected_info
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting DB tier to int: {e}")
                results["tier_match"] = False

        # Summarize results
        if is_consistent and results.get("tier_match", False):
            summary = "All premium checks are consistent and produce the expected results"
            success = True
        elif is_consistent:
            summary = "Premium checks are consistent but may not match the expected tier results"
            success = True
        else:
            summary = "Premium checks are inconsistent, the system may produce unexpected results"
            success = False

        return success, summary

    except Exception as e:
        logger.error(f"Error verifying premium access: {e}", exc_info=True)
        return False, f"Error: {str(e)}"

async def main():
    """Run premium verification"""
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        guild_id = input("Enter guild ID to check premium access: ").strip()

    feature = "leaderboards"  # Use leaderboards as default test feature

    logger.info(f"Verifying premium access for guild: {guild_id}, feature: {feature}")
    success, message = await verify_premium_access(guild_id, feature)

    print("\n" + "=" * 60)
    print(f"VERIFICATION RESULT: {'SUCCESS' if success else 'ISSUE DETECTED'}")
    print(message)
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    asyncio.run(main())