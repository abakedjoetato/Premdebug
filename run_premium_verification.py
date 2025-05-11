
#!/usr/bin/env python3
"""
Run the premium verification script to ensure tier checks work properly
"""
import asyncio
import os
import subprocess
import sys

async def run_verification():
    """Run the verification script"""
    print("Starting premium verification...")
    
    # Check if verify_premium_fixes.py exists
    if not os.path.exists("verify_premium_fixes.py"):
        print("Error: verify_premium_fixes.py not found!")
        return 1
    
    # Make the script executable
    os.chmod("verify_premium_fixes.py", 0o755)
    
    # Get guild ID from command line or use a default
    guild_id = sys.argv[1] if len(sys.argv) > 1 else "1219706687980568769"
    
    # Run the verification script
    result = subprocess.run(
        [sys.executable, "verify_premium_fixes.py", guild_id],
        capture_output=True,
        text=True
    )
    
    # Display the output
    print("\nVerification script output:")
    print("="*50)
    print(result.stdout)
    
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)
    
    print("="*50)
    
    # Return the exit code from the verification script
    return result.returncode

if __name__ == "__main__":
    exit_code = asyncio.run(run_verification())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Run a comprehensive verification of premium tier checks for the bot
"""
import asyncio
import logging
import time
import sys
from typing import Dict, Any, Optional, Union, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("premium_verification")

async def verify_guild_premium_tier(db, guild_id: str) -> Tuple[bool, Dict[str, Any]]:
    """Verify premium tier checks for a specific guild"""
    results = {
        "db_tier": None,
        "model_tier": None,
        "dict_tier": None,
        "has_feature": None,
        "validate_feature": None,
        "check_feature": None,
        "tier_required": None,
        "all_passed": False,
        "errors": []
    }
    
    try:
        # Step 1: Direct DB verification (source of truth)
        guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
        if not guild_doc:
            results["errors"].append(f"Guild {guild_id} not found in database")
            return False, results
            
        # Get tier from DB
        db_tier = guild_doc.get("premium_tier", 0)
        results["db_tier"] = db_tier
        logger.info(f"DB premium tier: {db_tier} (type: {type(db_tier).__name__})")
        
        # Step 2: Load with Guild model
        from models.guild import Guild
        guild_model = await Guild.get_by_guild_id(db, guild_id)
        
        if not guild_model:
            results["errors"].append(f"Failed to load Guild model for {guild_id}")
            return False, results
            
        # Get tier from model
        model_tier = getattr(guild_model, "premium_tier", None)
        results["model_tier"] = model_tier
        logger.info(f"Model premium tier: {model_tier} (type: {type(model_tier).__name__ if model_tier is not None else 'None'})")
        
        # Step 3: Convert to dictionary and check tier
        dict_guild = guild_model.to_dict()
        dict_tier = dict_guild.get("premium_tier", None)
        results["dict_tier"] = dict_tier
        logger.info(f"Dictionary premium tier: {dict_tier} (type: {type(dict_tier).__name__ if dict_tier is not None else 'None'})")
        
        # Step 4: Feature checks with each approach
        from utils.premium import has_feature_access, validate_premium_feature, check_tier_access, PREMIUM_FEATURES
        
        # Feature check 1: has_feature_access with model
        has_feature = await has_feature_access(guild_model, "stats")
        results["has_feature"] = has_feature
        logger.info(f"has_feature_access with model: {has_feature}")
        
        # Feature check 2: validate_premium_feature with model
        valid, error = await validate_premium_feature(guild_model, "stats")
        results["validate_feature"] = valid
        logger.info(f"validate_premium_feature with model: {valid}, error: {error}")
        
        # Feature check 3: check_feature_access method
        check_feature = guild_model.check_feature_access("stats")
        results["check_feature"] = check_feature
        logger.info(f"check_feature_access with model: {check_feature}")
        
        # Feature check 4: Using dictionary with has_feature_access
        dict_has_feature = await has_feature_access(dict_guild, "stats")
        results["dict_has_feature"] = dict_has_feature
        logger.info(f"has_feature_access with dictionary: {dict_has_feature}")
        
        # Feature check 5: Direct tier check
        required_tier = 1  # Stats feature requires tier 1
        tier_required, error = await check_tier_access(db, guild_id, required_tier)
        results["tier_required"] = tier_required
        logger.info(f"check_tier_access: {tier_required}, error: {error}")
        
        # Special diagnostic: Missing stats feature from premium_features?
        if "stats" not in PREMIUM_FEATURES:
            results["errors"].append("'stats' feature not found in PREMIUM_FEATURES mapping!")
            logger.error("CRITICAL ERROR: 'stats' feature missing from PREMIUM_FEATURES!")
        else:
            min_tier = PREMIUM_FEATURES.get("stats", None)
            logger.info(f"PREMIUM_FEATURES mapping for 'stats': requires tier {min_tier}")
            
        # Tier inheritance check - should grant tier 1 features for tier 4
        if db_tier >= 4 and not has_feature:
            results["errors"].append(f"Tier inheritance failing! Tier {db_tier} should have access to tier 1 features")
            logger.error(f"CRITICAL ERROR: Tier inheritance logic failing for tier {db_tier}")
            
        # Type conversion check
        try:
            if isinstance(model_tier, int) and isinstance(dict_tier, int):
                logger.info("Both model and dict tiers are integers - good!")
            elif isinstance(model_tier, str) or isinstance(dict_tier, str):
                logger.warning("String tier values detected - should be converted to integer")
                results["errors"].append("String tier values detected - needs type conversion")
        except Exception as e:
            logger.error(f"Error in type checking: {e}")
            
        # Determine if all checks passed
        core_checks_passed = all([
            model_tier == db_tier,
            dict_tier == db_tier,
            has_feature == (db_tier >= 1),
            valid == (db_tier >= 1),
            check_feature == (db_tier >= 1),
            dict_has_feature == (db_tier >= 1)
        ])
        
        results["all_passed"] = core_checks_passed and not results["errors"]
        
        if results["all_passed"]:
            logger.info("✅ All premium tier checks PASSED!")
        else:
            logger.error("❌ Some premium tier checks FAILED!")
            for error in results["errors"]:
                logger.error(f"Error: {error}")
                
        return results["all_passed"], results
        
    except Exception as e:
        logger.error(f"Error verifying premium tier: {e}", exc_info=True)
        results["errors"].append(f"Exception: {str(e)}")
        return False, results

async def fix_guild_premium_tier(db, guild_id: str, target_tier: int = None) -> bool:
    """Fix premium tier for a guild by ensuring DB and model are consistent"""
    logger.info(f"Attempting to fix premium tier for guild {guild_id}")
    
    try:
        # Get the guild document
        guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
        if not guild_doc:
            logger.error(f"Guild {guild_id} not found in database")
            return False
            
        # Get current tier from DB
        current_db_tier = guild_doc.get("premium_tier", 0)
        logger.info(f"Current DB tier: {current_db_tier} (type: {type(current_db_tier).__name__})")
        
        # Determine target tier
        if target_tier is None:
            # If no target specified, ensure current tier is an integer
            if isinstance(current_db_tier, int):
                target_tier = current_db_tier
            elif isinstance(current_db_tier, str) and current_db_tier.strip().isdigit():
                target_tier = int(current_db_tier.strip())
            else:
                try:
                    target_tier = int(current_db_tier)
                except (ValueError, TypeError):
                    # Default to tier 4 if conversion fails
                    target_tier = 4
                    logger.warning(f"Could not convert current tier {current_db_tier} to int, defaulting to tier 4")
        
        # Ensure tier is within valid range
        target_tier = max(0, min(5, target_tier))
        logger.info(f"Target tier: {target_tier}")
        
        # Update database with integer tier
        await db.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"premium_tier": target_tier}}
        )
        logger.info(f"Updated DB premium tier to {target_tier} (integer)")
        
        # Update model if available
        try:
            from models.guild import Guild
            guild_model = await Guild.get_by_guild_id(db, guild_id)
            if guild_model:
                guild_model.premium_tier = target_tier
                logger.info(f"Updated guild model premium tier to {target_tier}")
            else:
                logger.warning(f"Guild model not found for {guild_id}")
        except Exception as model_error:
            logger.error(f"Error updating guild model: {model_error}")
            
        # Verify the fix worked
        time.sleep(1)  # Brief pause to ensure DB write completes
        success, results = await verify_guild_premium_tier(db, guild_id)
        
        return success
    except Exception as e:
        logger.error(f"Error fixing premium tier: {e}", exc_info=True)
        return False

async def main():
    """Main function"""
    # Parse arguments
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        guild_id = input("Enter guild ID to verify premium tier: ").strip()
        
    # Get DB connection
    from utils.database import get_db
    db = await get_db()
    
    if not db:
        logger.error("Failed to connect to database")
        return 1
        
    # Run verification
    logger.info(f"Verifying premium tier for guild {guild_id}")
    success, results = await verify_guild_premium_tier(db, guild_id)
    
    if not success:
        if input("Would you like to fix the premium tier? (y/n) ").strip().lower() == 'y':
            tier_input = input("Enter target tier (1-4) or leave blank to use current tier: ").strip()
            target_tier = int(tier_input) if tier_input.isdigit() else None
            
            if await fix_guild_premium_tier(db, guild_id, target_tier):
                logger.info("✅ Premium tier fixed successfully!")
            else:
                logger.error("❌ Failed to fix premium tier")
    
    # Return appropriate exit code
    return 0 if success else 1
    
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
