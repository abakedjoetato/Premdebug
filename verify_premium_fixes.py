#!/usr/bin/env python3
"""
Script to verify premium feature access checking is working properly
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
logger = logging.getLogger(__name__)

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
        obj_check = await guild_obj.check_feature_access("stats")
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
            dict_check = await Guild.check_feature_access(dict_guild, "stats")
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
#!/usr/bin/env python3
"""
Verify that premium tier checks are working correctly across different contexts
"""
import asyncio
import logging
import sys
from typing import Dict, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("premium_verifier")

async def test_all_premium_checks(guild_id: str) -> bool:
    """Test premium tier checks in all contexts for a specific guild"""
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
            logger.error("Failed to connect to database")
            return False

        # Collect all test results
        tests_passed = 0
        tests_failed = 0
        test_results = {}

        # Step 1: Direct DB lookup
        logger.info("Test 1: Direct DB lookup")
        try:
            guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)})
            if not guild_doc:
                logger.error(f"Guild {guild_id} not found in database")
                test_results["db_lookup"] = False
                tests_failed += 1
            else:
                db_tier = guild_doc.get("premium_tier")
                logger.info(f"DB tier: {db_tier} (type: {type(db_tier).__name__})")
                test_results["db_lookup"] = True
                test_results["db_tier"] = db_tier
                tests_passed += 1
        except Exception as e:
            logger.error(f"Error in DB lookup: {e}")
            test_results["db_lookup"] = False
            tests_failed += 1

        # Step 2: Guild model retrieval
        logger.info("Test 2: Guild model retrieval")
        try:
            guild_model = await Guild.get_by_guild_id(db, guild_id)
            if not guild_model:
                logger.error(f"Failed to load Guild model for {guild_id}")
                test_results["model_retrieval"] = False
                tests_failed += 1
            else:
                model_tier = getattr(guild_model, "premium_tier", None)
                logger.info(f"Model tier: {model_tier} (type: {type(model_tier).__name__ if model_tier is not None else 'None'})")
                
                # Verify tier is an integer
                tier_is_int = isinstance(model_tier, int)
                logger.info(f"Model tier is integer: {tier_is_int}")
                test_results["model_retrieval"] = True
                test_results["model_tier"] = model_tier
                test_results["model_tier_is_int"] = tier_is_int
                
                # Check if model tier matches DB tier
                if "db_tier" in test_results:
                    try:
                        db_tier_int = int(test_results["db_tier"])
                        model_tier_int = int(model_tier) if model_tier is not None else 0
                        model_tier_matches = db_tier_int == model_tier_int
                        test_results["model_tier_matches_db"] = model_tier_matches
                        logger.info(f"Model tier matches DB tier: {model_tier_matches}")
                        if model_tier_matches:
                            tests_passed += 1
                        else:
                            tests_failed += 1
                    except (ValueError, TypeError):
                        logger.error("Error comparing tier values")
                        test_results["model_tier_matches_db"] = False
                        tests_failed += 1
        except Exception as e:
            logger.error(f"Error in Guild model retrieval: {e}")
            test_results["model_retrieval"] = False
            tests_failed += 1

        # Step 3: Dictionary conversion
        logger.info("Test 3: Dictionary conversion")
        try:
            if "model_retrieval" in test_results and test_results["model_retrieval"]:
                dict_guild = guild_model.to_dict()
                dict_tier = dict_guild.get("premium_tier")
                logger.info(f"Dictionary tier: {dict_tier} (type: {type(dict_tier).__name__ if dict_tier is not None else 'None'})")
                
                # Verify tier is an integer
                dict_tier_is_int = isinstance(dict_tier, int)
                logger.info(f"Dictionary tier is integer: {dict_tier_is_int}")
                test_results["dict_conversion"] = True
                test_results["dict_tier"] = dict_tier
                test_results["dict_tier_is_int"] = dict_tier_is_int
                
                # Check if dictionary tier matches model tier
                if "model_tier" in test_results:
                    try:
                        model_tier_int = int(test_results["model_tier"]) if test_results["model_tier"] is not None else 0
                        dict_tier_int = int(dict_tier) if dict_tier is not None else 0
                        dict_tier_matches = dict_tier_int == model_tier_int
                        test_results["dict_tier_matches_model"] = dict_tier_matches
                        logger.info(f"Dictionary tier matches model tier: {dict_tier_matches}")
                        if dict_tier_matches:
                            tests_passed += 1
                        else:
                            tests_failed += 1
                    except (ValueError, TypeError):
                        logger.error("Error comparing tier values")
                        test_results["dict_tier_matches_model"] = False
                        tests_failed += 1
        except Exception as e:
            logger.error(f"Error in dictionary conversion: {e}")
            test_results["dict_conversion"] = False
            tests_failed += 1

        # Step 4: Feature checks with model
        logger.info("Test 4: Feature checks with model")
        try:
            if "model_retrieval" in test_results and test_results["model_retrieval"]:
                # Feature check with has_feature_access
                model_has_feature = await has_feature_access(guild_model, "stats")
                logger.info(f"Model has_feature_access('stats'): {model_has_feature}")
                test_results["model_has_feature"] = model_has_feature
                
                # Feature check with validate_premium_feature
                model_validate, error_msg = await validate_premium_feature(guild_model, "stats")
                logger.info(f"Model validate_premium_feature('stats'): {model_validate}, error: {error_msg or 'None'}")
                test_results["model_validate_feature"] = model_validate
                
                # Feature check with check_feature_access method
                model_check_feature = await guild_model.check_feature_access("stats")
                logger.info(f"Model check_feature_access('stats'): {model_check_feature}")
                test_results["model_check_feature"] = model_check_feature
                
                # Check if all feature checks are consistent
                model_checks_consistent = (
                    model_has_feature == model_validate == model_check_feature
                )
                logger.info(f"Model feature checks are consistent: {model_checks_consistent}")
                test_results["model_checks_consistent"] = model_checks_consistent
                
                # Check if feature checks match tier
                if "model_tier" in test_results:
                    try:
                        model_tier_int = int(test_results["model_tier"]) if test_results["model_tier"] is not None else 0
                        expected_access = model_tier_int >= 1  # stats requires tier 1
                        model_access_correct = model_has_feature == expected_access
                        logger.info(f"Model feature access matches expected: {model_access_correct}")
                        test_results["model_access_correct"] = model_access_correct
                        if model_access_correct:
                            tests_passed += 1
                        else:
                            tests_failed += 1
                    except (ValueError, TypeError):
                        logger.error("Error checking feature access against tier")
                        test_results["model_access_correct"] = False
                        tests_failed += 1
        except Exception as e:
            logger.error(f"Error in model feature checks: {e}")
            test_results["model_feature_checks"] = False
            tests_failed += 1

        # Step 5: Feature checks with dictionary
        logger.info("Test 5: Feature checks with dictionary")
        try:
            if "dict_conversion" in test_results and test_results["dict_conversion"]:
                # Feature check with has_feature_access
                dict_has_feature = await has_feature_access(dict_guild, "stats")
                logger.info(f"Dictionary has_feature_access('stats'): {dict_has_feature}")
                test_results["dict_has_feature"] = dict_has_feature
                
                # Check if dictionary feature check matches model feature check
                if "model_has_feature" in test_results:
                    dict_matches_model = dict_has_feature == test_results["model_has_feature"]
                    logger.info(f"Dictionary feature check matches model: {dict_matches_model}")
                    test_results["dict_matches_model"] = dict_matches_model
                    if dict_matches_model:
                        tests_passed += 1
                    else:
                        tests_failed += 1
        except Exception as e:
            logger.error(f"Error in dictionary feature checks: {e}")
            test_results["dict_feature_checks"] = False
            tests_failed += 1

        # Step 6: check_tier_access
        logger.info("Test 6: check_tier_access")
        try:
            # Check tier access with required tier 1 (stats)
            tier_access, error_msg = await check_tier_access(db, guild_id, 1)
            logger.info(f"check_tier_access(1): {tier_access}, error: {error_msg or 'None'}")
            test_results["tier_access"] = tier_access
            
            # Check if tier access matches model feature check
            if "model_has_feature" in test_results:
                tier_access_matches = tier_access == test_results["model_has_feature"]
                logger.info(f"Tier access matches model feature check: {tier_access_matches}")
                test_results["tier_access_matches"] = tier_access_matches
                if tier_access_matches:
                    tests_passed += 1
                else:
                    tests_failed += 1
        except Exception as e:
            logger.error(f"Error in check_tier_access: {e}")
            test_results["tier_access_check"] = False
            tests_failed += 1

        # Step 7: Verify PREMIUM_FEATURES mapping
        logger.info("Test 7: PREMIUM_FEATURES mapping")
        try:
            # Check if stats feature is in PREMIUM_FEATURES
            stats_in_features = "stats" in PREMIUM_FEATURES
            logger.info(f"'stats' feature in PREMIUM_FEATURES: {stats_in_features}")
            test_results["stats_in_features"] = stats_in_features
            
            if stats_in_features:
                stats_tier = PREMIUM_FEATURES["stats"]
                logger.info(f"'stats' feature requires tier: {stats_tier}")
                test_results["stats_tier"] = stats_tier
                
                # Verify stats requires tier 1
                stats_tier_correct = stats_tier == 1
                logger.info(f"'stats' feature requires correct tier (1): {stats_tier_correct}")
                test_results["stats_tier_correct"] = stats_tier_correct
                if stats_tier_correct:
                    tests_passed += 1
                else:
                    tests_failed += 1
            else:
                tests_failed += 1
        except Exception as e:
            logger.error(f"Error checking PREMIUM_FEATURES: {e}")
            test_results["premium_features_check"] = False
            tests_failed += 1

        # Step 8: Overall check
        logger.info("Test 8: Overall check")
        try:
            if "db_tier" in test_results:
                db_tier = test_results["db_tier"]
                try:
                    db_tier_int = int(db_tier) if db_tier is not None else 0
                    expected_access = db_tier_int >= 1
                    
                    # Check if all feature checks match expected access
                    overall_correct = True
                    if "model_has_feature" in test_results:
                        overall_correct = overall_correct and (test_results["model_has_feature"] == expected_access)
                    if "dict_has_feature" in test_results:
                        overall_correct = overall_correct and (test_results["dict_has_feature"] == expected_access)
                    if "tier_access" in test_results:
                        overall_correct = overall_correct and (test_results["tier_access"] == expected_access)
                        
                    logger.info(f"Overall premium checks match expected access: {overall_correct}")
                    test_results["overall_correct"] = overall_correct
                    if overall_correct:
                        tests_passed += 1
                    else:
                        tests_failed += 1
                except (ValueError, TypeError):
                    logger.error("Error in overall check")
                    test_results["overall_correct"] = False
                    tests_failed += 1
        except Exception as e:
            logger.error(f"Error in overall check: {e}")
            test_results["overall_check"] = False
            tests_failed += 1

        # Final summary
        logger.info("="*50)
        logger.info(f"Tests passed: {tests_passed}")
        logger.info(f"Tests failed: {tests_failed}")
        
        # Consider the verification successful if all critical tests pass
        critical_tests = [
            "model_tier_matches_db",
            "dict_tier_matches_model",
            "model_access_correct",
            "dict_matches_model",
            "tier_access_matches",
            "stats_tier_correct",
            "overall_correct"
        ]
        
        critical_passed = [test for test in critical_tests if test in test_results and test_results[test]]
        all_critical_passed = len(critical_passed) == len(critical_tests)
        
        if all_critical_passed:
            logger.info("✅ All critical premium tier checks PASSED!")
            return True
        else:
            failed_tests = [test for test in critical_tests if test not in test_results or not test_results[test]]
            logger.error(f"❌ Some critical premium tier checks FAILED: {', '.join(failed_tests)}")
            return False

    except Exception as e:
        logger.error(f"Error testing premium checks: {e}", exc_info=True)
        return False

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        guild_id = sys.argv[1]
    else:
        guild_id = input("Enter guild ID to test premium checks: ").strip()

    logger.info(f"Testing premium checks for guild: {guild_id}")
    success = await test_all_premium_checks(guild_id)

    print("\n" + "="*50)
    print(f"TEST RESULT: {'SUCCESS' if success else 'FAILED'}")
    print("="*50)

    return 0 if success else 1

if __name__ == "__main__":
    asyncio.run(main())