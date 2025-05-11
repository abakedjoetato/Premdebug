
#!/usr/bin/env python3
"""
Comprehensive diagnostic script to verify premium tier fixes.
This script performs extensive tests on the premium feature validation system.
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def verify_guild_tier_consistency(db, guild_id: str) -> bool:
    """Verify that guild tier is consistent across all retrieval methods"""
    logger.info(f"Verifying tier consistency for guild ID: {guild_id}")
    
    # Method 1: Direct database query
    logger.info("Method 1: Direct DB query")
    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
    if not guild_doc:
        logger.error(f"No guild found with ID: {guild_id}")
        return False
        
    db_tier = guild_doc.get('premium_tier')
    logger.info(f"DB tier value: {db_tier}, type: {type(db_tier).__name__}")
    
    # Method 2: Guild model via get_by_guild_id
    logger.info("Method 2: Guild.get_by_guild_id")
    from models.guild import Guild
    guild_model = await Guild.get_by_guild_id(db, guild_id)
    if not guild_model:
        logger.error("Failed to retrieve guild model")
        return False
        
    model_tier = guild_model.premium_tier
    logger.info(f"Model tier value: {model_tier}, type: {type(model_tier).__name__}")
    
    # Method 3: Premium utils get_guild_premium_tier
    logger.info("Method 3: get_guild_premium_tier utility")
    from utils.premium import get_guild_premium_tier
    util_tier, tier_data = await get_guild_premium_tier(db, guild_id)
    logger.info(f"Utility tier value: {util_tier}, type: {type(util_tier).__name__}")
    
    # Check consistency
    try:
        # Convert to integers for comparison
        db_tier_int = int(db_tier) if db_tier is not None else 0
        model_tier_int = int(model_tier) if model_tier is not None else 0
        
        logger.info(f"Comparing tier values: DB={db_tier_int}, Model={model_tier_int}, Util={util_tier}")
        
        consistent = (db_tier_int == model_tier_int == util_tier)
        if consistent:
            logger.info("✅ Tier values are consistent across all methods")
        else:
            logger.error("❌ Tier values are inconsistent:")
            logger.error(f"  - DB tier: {db_tier_int}")
            logger.error(f"  - Model tier: {model_tier_int}")
            logger.error(f"  - Util tier: {util_tier}")
        
        return consistent
    except (ValueError, TypeError) as e:
        logger.error(f"Error comparing tier values: {e}")
        return False

async def verify_feature_access_methods(db, guild_id: str, features: List[str]) -> bool:
    """Verify that different methods of checking feature access are consistent"""
    logger.info(f"Verifying feature access methods for guild ID: {guild_id}")
    
    from models.guild import Guild
    from utils.premium import has_feature_access, validate_premium_feature
    
    guild_model = await Guild.get_by_guild_id(db, guild_id)
    if not guild_model:
        logger.error("Failed to retrieve guild model")
        return False
    
    success = True
    for feature in features:
        logger.info(f"Testing feature: {feature}")
        
        # Method 1: Direct model check
        model_access = guild_model.check_feature_access(feature)
        logger.info(f"Method 1 (model.check_feature_access): {model_access}")
        
        # Method 2: Utility function check
        util_access = await has_feature_access(guild_model, feature)
        logger.info(f"Method 2 (has_feature_access utility): {util_access}")
        
        # Method 3: Validation method
        validate_access, error_msg = await validate_premium_feature(guild_model, feature)
        logger.info(f"Method 3 (validate_premium_feature): access={validate_access}, error={error_msg}")
        
        # Check consistency
        if model_access == util_access == validate_access:
            logger.info(f"✅ Feature access is consistent for {feature}: {model_access}")
        else:
            logger.error(f"❌ Feature access is inconsistent for {feature}:")
            logger.error(f"  - Model check: {model_access}")
            logger.error(f"  - Utility check: {util_access}")
            logger.error(f"  - Validation check: {validate_access}")
            success = False
    
    return success

async def test_premium_tier_changes(db, guild_id: str) -> bool:
    """Test setting premium tier and verifying it updates correctly"""
    logger.info(f"Testing premium tier changes for guild ID: {guild_id}")
    
    from models.guild import Guild
    from utils.premium import has_feature_access
    
    # Get initial guild model
    guild_model = await Guild.get_by_guild_id(db, guild_id)
    if not guild_model:
        logger.error("Failed to retrieve guild model")
        return False
    
    # Record initial tier
    initial_tier = guild_model.premium_tier
    logger.info(f"Initial premium tier: {initial_tier}")
    
    try:
        # Test increasing tier
        test_tier = min(4, initial_tier + 1)  # Don't go beyond tier 4
        logger.info(f"Setting tier to {test_tier}")
        
        success = await guild_model.set_premium_tier(db, test_tier)
        if not success:
            logger.error(f"Failed to set premium tier to {test_tier}")
            return False
            
        # Verify tier was updated in DB
        updated_model = await Guild.get_by_guild_id(db, guild_id)
        if updated_model.premium_tier != test_tier:
            logger.error(f"Premium tier not updated in database. Expected: {test_tier}, Got: {updated_model.premium_tier}")
            return False
            
        logger.info(f"Successfully set tier to {test_tier}")
        
        # Test a feature that should be available at this tier
        test_feature = "stats" if test_tier >= 1 else "killfeed"
        has_access = await has_feature_access(updated_model, test_feature)
        logger.info(f"Access to {test_feature} at tier {test_tier}: {has_access}")
        
        # Restore original tier
        logger.info(f"Restoring original tier: {initial_tier}")
        success = await updated_model.set_premium_tier(db, initial_tier)
        if not success:
            logger.error(f"Failed to restore original tier {initial_tier}")
            return False
            
        # Verify restoration
        final_model = await Guild.get_by_guild_id(db, guild_id)
        if final_model.premium_tier != initial_tier:
            logger.error(f"Failed to restore original tier. Expected: {initial_tier}, Got: {final_model.premium_tier}")
            return False
            
        logger.info(f"Successfully restored tier to {initial_tier}")
        return True
            
    except Exception as e:
        logger.error(f"Error during tier change test: {e}")
        # Try to restore original tier
        try:
            await guild_model.set_premium_tier(db, initial_tier)
        except:
            pass
        return False

async def run_direct_premium_tests(db, guild_id: str) -> bool:
    """Run direct tests of the premium validation functions"""
    logger.info(f"Running direct tests of premium functions for guild ID: {guild_id}")
    
    from utils.premium import check_tier_access, get_minimum_tier_for_feature
    
    # Test tier access for different tiers
    all_passed = True
    
    # Get current guild tier
    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
    if not guild_doc:
        logger.error(f"No guild found with ID: {guild_id}")
        return False
        
    current_tier = int(guild_doc.get('premium_tier', 0))
    logger.info(f"Current guild tier: {current_tier}")
    
    # Test tier access
    logger.info("Testing check_tier_access function...")
    for test_tier in range(0, 5):
        has_access, error_msg = await check_tier_access(db, guild_id, test_tier)
        expected_access = current_tier >= test_tier
        
        if has_access == expected_access:
            logger.info(f"✅ Tier {test_tier} access check correct: {has_access}")
        else:
            logger.error(f"❌ Tier {test_tier} access check incorrect: got {has_access}, expected {expected_access}")
            logger.error(f"   Error message: {error_msg}")
            all_passed = False
    
    # Test feature tier requirements
    logger.info("Testing get_minimum_tier_for_feature function...")
    test_features = ["killfeed", "stats", "leaderboards", "rivalries", "factions"]
    for feature in test_features:
        min_tier = get_minimum_tier_for_feature(feature)
        if min_tier is not None:
            logger.info(f"✅ Feature '{feature}' requires minimum tier: {min_tier}")
        else:
            logger.error(f"❌ Failed to get minimum tier for feature '{feature}'")
            all_passed = False
    
    return all_passed

async def verify_all_premium_fixes(guild_id: Optional[str] = None):
    """Comprehensive verification of all premium tier fixes"""
    # Get command line arguments for guild ID
    if guild_id is None:
        if len(sys.argv) > 1:
            guild_id = sys.argv[1]
        else:
            # Default to test guild if none provided
            guild_id = "1219706687980568769"  # Default test guild ID

    logger.info(f"Beginning comprehensive premium tier verification for guild ID: {guild_id}")

    # Step 1: Connect to database
    from utils.database import get_db
    logger.info("Connecting to database...")
    db = await get_db()
    
    # Step 2: Verify guild tier consistency
    logger.info("Step 2: Verifying tier consistency...")
    tier_consistent = await verify_guild_tier_consistency(db, guild_id)
    
    # Step 3: Verify feature access methods
    logger.info("Step 3: Verifying feature access methods...")
    features_to_test = ["killfeed", "stats", "leaderboards", "rivalries", "factions"]
    access_consistent = await verify_feature_access_methods(db, guild_id, features_to_test)
    
    # Step 4: Test premium tier changes
    logger.info("Step 4: Testing premium tier changes...")
    tier_changes_work = await test_premium_tier_changes(db, guild_id)
    
    # Step 5: Run direct premium function tests
    logger.info("Step 5: Running direct premium function tests...")
    direct_tests_pass = await run_direct_premium_tests(db, guild_id)
    
    # Final results
    logger.info("\n===== VERIFICATION RESULTS =====")
    logger.info(f"Tier Consistency: {'✅ PASS' if tier_consistent else '❌ FAIL'}")
    logger.info(f"Feature Access Methods: {'✅ PASS' if access_consistent else '❌ FAIL'}")
    logger.info(f"Tier Changes: {'✅ PASS' if tier_changes_work else '❌ FAIL'}")
    logger.info(f"Direct Function Tests: {'✅ PASS' if direct_tests_pass else '❌ FAIL'}")
    
    all_passed = tier_consistent and access_consistent and tier_changes_work and direct_tests_pass
    logger.info(f"\nOVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        logger.info("\nRecommended actions:")
        if not tier_consistent:
            logger.info("- Fix tier inconsistency between DB and model")
        if not access_consistent:
            logger.info("- Fix feature access method inconsistencies")
        if not tier_changes_work:
            logger.info("- Fix premium tier update mechanism")
        if not direct_tests_pass:
            logger.info("- Fix premium utility functions")

async def main():
    await verify_all_premium_fixes()

if __name__ == "__main__":
    asyncio.run(main())
