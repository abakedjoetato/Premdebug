
#!/usr/bin/env python
"""Premium System Diagnostic Utility

This script provides a comprehensive diagnosis of the premium tier system
and performs tests to verify that premium tiers are being correctly applied.
"""
import sys
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('premium_diagnostics.log')
    ]
)
logger = logging.getLogger("premium_diagnostics")

async def run_diagnostics(guild_id: str = None):
    """Run comprehensive premium diagnostics"""
    
    logger.info("=" * 60)
    logger.info("PREMIUM SYSTEM DIAGNOSTICS")
    logger.info("=" * 60)
    
    # Connect to database
    logger.info("Connecting to database...")
    try:
        from utils.database import get_db
        db = await get_db()
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    # If no guild ID provided, check all guilds and sample one with a premium tier
    if guild_id is None:
        logger.info("No guild ID provided, finding a guild with premium tier...")
        try:
            # Find any guild with premium tier > 0
            premium_guild = await db.guilds.find_one({"premium_tier": {"$gt": 0}})
            
            if premium_guild:
                guild_id = premium_guild.get("guild_id")
                logger.info(f"Found guild with premium tier: {guild_id} (Tier: {premium_guild.get('premium_tier')})")
            else:
                # Try to find any guild
                any_guild = await db.guilds.find_one({})
                if any_guild:
                    guild_id = any_guild.get("guild_id")
                    logger.info(f"No premium guilds found, using regular guild: {guild_id}")
                else:
                    logger.error("No guilds found in database!")
                    return
        except Exception as e:
            logger.error(f"Error finding guilds: {e}")
            return
    
    logger.info(f"Running diagnostics on guild ID: {guild_id}")
    
    # Phase 1: Check database value directly
    logger.info("\nPHASE 1: Checking database value")
    db_tier = None
    try:
        guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
        if guild_doc:
            db_tier = guild_doc.get("premium_tier")
            tier_type = type(db_tier).__name__
            logger.info(f"Database premium_tier value: {db_tier} (Type: {tier_type})")
            
            # Check if the tier is the correct type
            if not isinstance(db_tier, int):
                logger.warning(f"Premium tier should be an integer but found {tier_type}")
                
                # Try to fix if it's a string
                if isinstance(db_tier, str) and db_tier.strip().isdigit():
                    corrected_tier = int(db_tier.strip())
                    logger.info(f"Converting string tier '{db_tier}' to int: {corrected_tier}")
                    
                    # Update in database
                    update_result = await db.guilds.update_one(
                        {"_id": guild_doc["_id"]},
                        {"$set": {"premium_tier": corrected_tier}}
                    )
                    
                    logger.info(f"Updated database tier: {update_result.modified_count} document modified")
                    db_tier = corrected_tier
        else:
            logger.error(f"Guild document not found for ID: {guild_id}")
            return
    except Exception as e:
        logger.error(f"Error checking database value: {e}")
    
    # Phase 2: Test Guild model loading with proper tier values
    logger.info("\nPHASE 2: Testing Guild model loading")
    try:
        from models.guild import Guild
        
        # Test regular lookup
        guild_model = await Guild.get_by_guild_id(db, guild_id)
        if guild_model:
            model_tier = getattr(guild_model, 'premium_tier', None)
            model_tier_type = type(model_tier).__name__
            logger.info(f"Guild model premium_tier: {model_tier} (Type: {model_tier_type})")
            
            # Check if model value matches database value
            if model_tier != db_tier:
                logger.error(f"Model tier ({model_tier}) does not match database tier ({db_tier})")
            
            # Check if tier is correct type
            if not isinstance(model_tier, int):
                logger.warning(f"Model tier should be an integer but found {model_tier_type}")
        else:
            logger.error(f"Failed to load Guild model for ID: {guild_id}")
            return
    except Exception as e:
        logger.error(f"Error testing Guild model: {e}")
        return
    
    # Phase 3: Test premium feature access functions
    logger.info("\nPHASE 3: Testing premium feature access functions")
    try:
        from utils.premium import has_feature_access, validate_premium_feature, PREMIUM_FEATURES
        
        # Test basic features at different tier levels
        test_features = [
            "killfeed",       # Tier 0 (free)
            "basic_stats",    # Tier 1
            "leaderboards",   # Tier 1
            "rivalries",      # Tier 2
            "bounties",       # Tier 2
            "factions",       # Tier 3
            "nonexistent"     # Should be denied
        ]
        
        # Cache results for comparison
        access_results = {}
        validation_results = {}
        
        logger.info(f"Feature access check results for guild {guild_id} with tier {model_tier}:")
        for feature in test_features:
            # Test has_feature_access
            try:
                has_access = await has_feature_access(guild_model, feature)
                req_tier = PREMIUM_FEATURES.get(feature, 999)
                access_results[feature] = has_access
                logger.info(f"  has_feature_access('{feature}'): {has_access} (requires tier {req_tier})")
            except Exception as e:
                logger.error(f"Error in has_feature_access for '{feature}': {e}")
                
            # Test validate_premium_feature
            try:
                has_access, error_msg = await validate_premium_feature(guild_model, feature)
                validation_results[feature] = has_access
                logger.info(f"  validate_premium_feature('{feature}'): {has_access}")
                if error_msg:
                    logger.info(f"    Error message: {error_msg}")
            except Exception as e:
                logger.error(f"Error in validate_premium_feature for '{feature}': {e}")
                
            # Check if results match between methods
            if feature in access_results and feature in validation_results:
                if access_results[feature] != validation_results[feature]:
                    logger.error(f"INCONSISTENCY: Results don't match for '{feature}': " +
                                f"has_feature_access={access_results[feature]}, " +
                                f"validate_premium_feature={validation_results[feature]}")
                    
    except Exception as e:
        logger.error(f"Error testing premium feature access: {e}")
    
    # Phase 4: Test guild.check_feature_access method
    logger.info("\nPHASE 4: Testing guild.check_feature_access method")
    try:
        model_check_results = {}
        
        logger.info(f"Guild.check_feature_access results for guild {guild_id} with tier {model_tier}:")
        for feature in test_features:
            try:
                model_has_access = await guild_model.check_feature_access(feature)
                model_check_results[feature] = model_has_access
                logger.info(f"  guild_model.check_feature_access('{feature}'): {model_has_access}")
                
                # Check if result matches has_feature_access
                if feature in access_results and model_has_access != access_results[feature]:
                    logger.error(f"INCONSISTENCY: Results don't match for '{feature}': " +
                                f"guild.check_feature_access={model_has_access}, " +
                                f"has_feature_access={access_results[feature]}")
            except Exception as e:
                logger.error(f"Error in guild.check_feature_access for '{feature}': {e}")
    except Exception as e:
        logger.error(f"Error testing guild.check_feature_access: {e}")
    
    # Phase 5: Test tier inheritance
    logger.info("\nPHASE 5: Testing tier inheritance logic")
    try:
        # Get current tier
        current_tier = getattr(guild_model, 'premium_tier', 0)
        logger.info(f"Current guild tier: {current_tier}")
        
        # Test if the appropriate features are available at this tier
        all_features = list(PREMIUM_FEATURES.keys())
        
        accessible_features = []
        for feature in all_features:
            min_tier = PREMIUM_FEATURES.get(feature, 999)
            expected_access = current_tier >= min_tier
            actual_access = await has_feature_access(guild_model, feature)
            
            if expected_access != actual_access:
                logger.error(f"INHERITANCE ERROR: Feature '{feature}' (tier {min_tier}) " +
                           f"expected access={expected_access}, actual={actual_access}")
            
            if actual_access:
                accessible_features.append(feature)
        
        logger.info(f"Accessible features at tier {current_tier}: {accessible_features}")
    except Exception as e:
        logger.error(f"Error testing tier inheritance: {e}")
    
    # Phase 6: Test database vs model consistency when changing tiers
    if db_tier > 0:  # Only test this with premium guilds
        logger.info("\nPHASE 6: Testing tier update propagation")
        try:
            original_tier = getattr(guild_model, 'premium_tier', 0)
            test_tier = max(0, original_tier - 1)  # Use one tier lower for testing
            
            logger.info(f"Temporarily changing tier from {original_tier} to {test_tier}")
            
            # Update tier in model
            await guild_model.set_premium_tier(db, test_tier)
            
            # Verify model tier was updated
            updated_model_tier = getattr(guild_model, 'premium_tier', None)
            logger.info(f"Updated model tier: {updated_model_tier}")
            
            # Verify database was updated
            updated_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
            updated_db_tier = updated_doc.get("premium_tier") if updated_doc else None
            logger.info(f"Updated database tier: {updated_db_tier}")
            
            # Test feature access with new tier
            test_feature = next((f for f in PREMIUM_FEATURES if PREMIUM_FEATURES[f] == original_tier), None)
            if test_feature:
                new_access = await has_feature_access(guild_model, test_feature)
                expected_access = test_tier >= PREMIUM_FEATURES.get(test_feature, 999)
                logger.info(f"Feature '{test_feature}' access with tier {test_tier}: {new_access} (expected: {expected_access})")
                
                if new_access != expected_access:
                    logger.error(f"TIER UPDATE ERROR: Feature access didn't update properly for '{test_feature}'")
            
            # Restore original tier
            logger.info(f"Restoring original tier {original_tier}")
            await guild_model.set_premium_tier(db, original_tier)
            
            # Verify restoration
            restored_model = await Guild.get_by_guild_id(db, guild_id)
            restored_tier = getattr(restored_model, 'premium_tier', None)
            logger.info(f"Restored tier: {restored_tier}")
            
        except Exception as e:
            logger.error(f"Error testing tier update propagation: {e}")
            # Ensure we restore original tier even if there's an error
            try:
                await guild_model.set_premium_tier(db, original_tier)
            except:
                pass
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("PREMIUM DIAGNOSTICS SUMMARY")
    logger.info("=" * 60)
    
    # Count errors in the log
    error_count = sum(1 for handler in logger.handlers 
                    if isinstance(handler, logging.FileHandler) 
                    and "ERROR" in handler.stream.getvalue())
    
    if error_count > 0:
        logger.info(f"Diagnostics completed with {error_count} errors. Check the log for details.")
    else:
        logger.info("Diagnostics completed successfully! No issues detected.")
    
    logger.info("=" * 60)

async def main():
    """Main entry point"""
    try:
        # Get guild ID from command line arguments
        guild_id = sys.argv[1] if len(sys.argv) > 1 else None
        
        # Run diagnostics
        await run_diagnostics(guild_id)
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""
Run the premium tier diagnostics script to verify fixes are working correctly.
"""
import asyncio
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("diagnostic_runner")

# Run the diagnostic script with the specified guild ID
if len(sys.argv) > 1:
    guild_id = sys.argv[1]
    logger.info(f"Running premium diagnostic with guild ID: {guild_id}")
    subprocess.run(["python", "verify_premium_fixes.py", guild_id])
else:
    logger.info("Running premium diagnostic with default guild ID")
    subprocess.run(["python", "verify_premium_fixes.py"])
#!/usr/bin/env python3
"""
Run the premium tier diagnostics script to verify fixes are working correctly.
"""
import asyncio
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("diagnostic_runner")

# Run the diagnostic script with the specified guild ID
if len(sys.argv) > 1:
    guild_id = sys.argv[1]
    logger.info(f"Running premium diagnostic with guild ID: {guild_id}")
    subprocess.run(["python", "verify_premium_fixes.py", guild_id])
else:
    logger.info("Running premium diagnostic with default guild ID")
    subprocess.run(["python", "verify_premium_fixes.py"])
