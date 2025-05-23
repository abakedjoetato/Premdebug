"""
Premium feature validation utilities for Tower of Temptation PvP Statistics Discord Bot.

This module provides robust utilities for checking premium feature access,
managing tier limitations, and providing useful error messages about premium features.

Key enhancements:
1. Multi-level caching to minimize database queries
2. Thread-safe access with proper locks
3. Graceful degradation during database outages
4. Type-safe feature validation
5. Detailed error reporting for premium limitations
"""
import logging
import asyncio
import functools
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Set, Callable, Awaitable
from datetime import datetime, timedelta

from config import PREMIUM_TIERS
from utils.async_utils import AsyncCache, retryable

logger = logging.getLogger(__name__)

# Feature registry with tier requirements mapped from config.PREMIUM_TIERS
# This provides a direct mapping from feature name to minimum tier required
PREMIUM_FEATURES = {
    # Base features (tier 0 - Scavenger)
    "killfeed": 0,

    # Tier 1 features (Survivor)
    "basic_stats": 1,
    "stats": 1,  # Alias for basic_stats
    "leaderboards": 1,


    # Tier 1 features (Survivor)
    "basic_stats": 1,
    "stats": 1,  # Alias for basic_stats
    "leaderboards": 1,

    # Tier 2 features (Mercenary)
    "rivalries": 2,
    "bounties": 2,
    "bounty_notifications": 2,  # Related to bounties feature
    "player_links": 2,
    "economy": 2,
    "advanced_analytics": 2,

    # Tier 3 features (Warlord)
    "factions": 3,
    "events": 3,  # Custom server events feature
    "connections": 3,  # External connections feature

    # Additional helpers
    "max_servers": 0,  # Base tier feature
    "premium_support": 1  # Available from Tier 1
}

# Enhanced cache configuration
FEATURE_ACCESS_CACHE_TTL = 300  # 5 minutes (short-term cache)
PREMIUM_TIER_CACHE_TTL = 1800  # 30 minutes (medium-term cache)
GUILD_INFO_CACHE_TTL = 3600  # 1 hour (long-term cache)

# In-memory cache for ultra-fast lookups (process-level cache)
_LOCAL_PREMIUM_CACHE = {}
_LOCAL_CACHE_LOCK = asyncio.Lock()
_LAST_CACHE_CLEANUP = time.time()
_CACHE_CLEANUP_INTERVAL = 600  # 10 minutes

# Additional internal features not directly in config.PREMIUM_TIERS
# If needed, these can be mapped to existing features in config.PREMIUM_TIERS
# But the source of truth should be PREMIUM_TIERS in config.py

# Cache for feature access results
FEATURE_ACCESS_CACHE = AsyncCache(ttl=FEATURE_ACCESS_CACHE_TTL)

async def cleanup_local_cache():
    """Periodically cleanup the local cache to prevent memory leaks"""
    global _LAST_CACHE_CLEANUP

    # Only clean up if it's been long enough since the last cleanup
    now = time.time()
    if now - _LAST_CACHE_CLEANUP < _CACHE_CLEANUP_INTERVAL:
        return

    async with _LOCAL_CACHE_LOCK:
        # Clean up expired entries
        expired_keys = []
        for key, (value, expiry) in _LOCAL_PREMIUM_CACHE.items():
            if expiry < now:
                expired_keys.append(key)

        # Remove expired entries
        for key in expired_keys:
            _LOCAL_PREMIUM_CACHE.pop(key, None)

        # Update last cleanup time
        _LAST_CACHE_CLEANUP = now
        logger.debug(f"Local premium cache cleanup: removed {len(expired_keys)} expired entries")

# Re-enable caching with a shorter TTL to balance performance and freshness
@FEATURE_ACCESS_CACHE.cached(ttl=60)  # 60 seconds cache
async def has_feature_access(guild_model, feature_name: str) -> bool:
    """
    Check if a guild has access to a premium feature with multi-level caching.

    This method implements proper tier inheritance, ensuring that
    higher tiers have access to all features from lower tiers.

    Args:
        guild_model: Guild model instance
        feature_name: Name of the feature to check

    Returns:
        bool: True if the guild has access to the feature
    """
    # Add detailed diagnostic information
    guild_id = None
    
    # Get guild_id with better error handling for any input type
    try:
        if hasattr(guild_model, 'guild_id'):
            guild_id = getattr(guild_model, 'guild_id')
        elif isinstance(guild_model, dict) and 'guild_id' in guild_model:
            guild_id = guild_model['guild_id']
        # Default to unknown if not found
        if guild_id is None:
            guild_id = 'unknown'
    except Exception:
        guild_id = 'unknown'

    # Validate inputs
    if feature_name is None or not isinstance(feature_name, str) or not feature_name.strip():
        logger.warning(f"[PREMIUM_DEBUG] Invalid feature name: {feature_name!r}")
        return False

    # Quick returns for common cases
    if guild_model is None:
        logger.warning("[PREMIUM_DEBUG] Cannot check feature access: guild_model is None")
        return False

    # CRITICAL FIX: Get and standardize the premium tier with enhanced type safety
    guild_tier = 0  # Default tier
    premium_tier_value = None
    try:
        # First try to get premium_tier from class attribute
        if hasattr(guild_model, 'premium_tier'):
            premium_tier_value = guild_model.premium_tier
            logger.info(f"[PREMIUM_DEBUG] Object guild model has premium_tier: {premium_tier_value}, type: {type(premium_tier_value).__name__}")
        # Then try getting it from dictionary
        elif isinstance(guild_model, dict) and 'premium_tier' in guild_model:
            premium_tier_value = guild_model['premium_tier']
            logger.info(f"[PREMIUM_DEBUG] Dictionary guild model has premium_tier: {premium_tier_value}, type: {type(premium_tier_value).__name__}")
        # If guild_model is just an integer already (sometimes passes in just the tier)
        elif isinstance(guild_model, int):
            premium_tier_value = guild_model
            logger.info(f"[PREMIUM_DEBUG] Guild model is already an integer tier: {premium_tier_value}")

        # Standardize premium_tier to integer value with robust type conversion
        if premium_tier_value is not None:
            if isinstance(premium_tier_value, int):
                guild_tier = premium_tier_value
            elif isinstance(premium_tier_value, str) and premium_tier_value.strip().isdigit():
                guild_tier = int(premium_tier_value.strip())
            else:
                try:
                    guild_tier = int(premium_tier_value)
                except (ValueError, TypeError):
                    # Default to 0 if conversion fails
                    guild_tier = 0
                    logger.warning(f"[PREMIUM_DEBUG] Failed to convert premium_tier {premium_tier_value} to int, defaulting to 0")
        
        # Ensure tier is in valid range
        guild_tier = max(0, min(5, guild_tier))
        logger.info(f"[PREMIUM_DEBUG] Guild {guild_id} standardized tier: {guild_tier}")
        
    except Exception as e:
        logger.error(f"[PREMIUM_DEBUG] Error inspecting premium_tier: {e}")
        guild_tier = 0

    # CRITICAL TIER CHECKS IN ORDER OF PRIORITY (most common checks first for performance)
    
    # 1. Fast-path for high tiers - Tiers 4+ (Overseer) get access to all features always
    if guild_tier >= 4:
        logger.info(f"[PREMIUM_DEBUG] Auto-granting access to '{feature_name}' for highest tier {guild_tier}")
        return True

    # 2. Fast-path for essential features (most used premium features)
    if feature_name in ['leaderboards', 'stats', 'basic_stats'] and guild_tier >= 1:
        logger.info(f"[PREMIUM_DEBUG] Fast-path access granted for essential feature '{feature_name}' at tier {guild_tier}")
        return True

    # 3. Get the minimum tier required for this feature
    min_tier_required = 999  # Default to very high if feature not found
    if feature_name in PREMIUM_FEATURES:
        min_tier_required = PREMIUM_FEATURES.get(feature_name, 999)
    else:
        logger.warning(f"[PREMIUM_DEBUG] Feature '{feature_name}' not found in PREMIUM_FEATURES, access denied")
        return False

    # 4. Direct DB verification for the most accurate premium tier if we have a valid ID
    # This handles cases where the model tier is incorrect or outdated
    db_premium_tier = None
    db = None
    
    # Only do DB query if we know we need a higher tier (optimized access path)
    if guild_tier < min_tier_required and guild_id != 'unknown':
        try:
            # Try to get a database connection from various sources
            if hasattr(guild_model, 'db') and guild_model.db is not None:
                db = guild_model.db
            elif isinstance(guild_model, dict) and 'db' in guild_model and guild_model['db'] is not None:
                db = guild_model['db']
            
            # If no DB yet, try to get it from utils
            if db is None:
                try:
                    from utils.database import get_db
                    db = await get_db()
                except Exception as db_err:
                    logger.error(f"[PREMIUM_DEBUG] Error getting database: {db_err}")
            
            # Now query the database for premium tier if we have a valid guild_id and DB
            if db is not None:
                try:
                    # Directly query the database to get the most up-to-date premium tier
                    guild_doc = await db.guilds.find_one({"guild_id": str(guild_id)}, {"premium_tier": 1})
                    if guild_doc is not None and "premium_tier" in guild_doc:
                        db_tier_value = guild_doc.get("premium_tier")
                        if db_tier_value is not None:
                            try:
                                db_premium_tier = int(db_tier_value)
                                logger.info(f"[PREMIUM_DEBUG] Direct DB verification for guild {guild_id}: premium_tier={db_premium_tier}")
                            except (ValueError, TypeError) as e:
                                logger.error(f"[PREMIUM_DEBUG] Error converting DB premium_tier '{db_tier_value}': {e}")
                except Exception as db_query_error:
                    logger.error(f"[PREMIUM_DEBUG] Database query error: {db_query_error}")

                # If the direct query didn't work, try an alternative approach
                if db_premium_tier is None and str(guild_id).isdigit():
                    try:
                        # Try with both string and integer ID variants
                        guild_doc = await db.guilds.find_one({
                            "$or": [
                                {"guild_id": str(guild_id)}, 
                                {"guild_id": int(guild_id)}
                            ]
                        }, {"premium_tier": 1})

                        if guild_doc is not None and "premium_tier" in guild_doc:
                            db_tier_value = guild_doc.get("premium_tier")
                            if db_tier_value is not None:
                                try:
                                    db_premium_tier = int(db_tier_value)
                                    logger.info(f"[PREMIUM_DEBUG] Alternative DB verification for guild {guild_id}: premium_tier={db_premium_tier}")
                                except (ValueError, TypeError):
                                    logger.error(f"[PREMIUM_DEBUG] Failed to convert alternative DB tier to int: {db_tier_value}")
                    except Exception as alt_error:
                        logger.error(f"[PREMIUM_DEBUG] Alternative query error: {alt_error}")
        except Exception as e:
            logger.error(f"[PREMIUM_DEBUG] Error in direct DB verification: {e}")

        # If DB lookup found a higher tier, use it and update the model
        if db_premium_tier is not None and db_premium_tier > guild_tier:
            logger.info(f"[PREMIUM_DEBUG] Using higher DB tier {db_premium_tier} instead of model tier {guild_tier}")
            guild_tier = db_premium_tier
            
            # Update the model's tier if possible to avoid future lookups
            try:
                if hasattr(guild_model, 'premium_tier'):
                    guild_model.premium_tier = guild_tier
                elif isinstance(guild_model, dict):
                    guild_model['premium_tier'] = guild_tier
            except Exception as update_err:
                logger.error(f"[PREMIUM_DEBUG] Error updating tier on model: {update_err}")
    
    # 5. Final check - does the guild tier meet or exceed the required tier?
    # This is the core of tier inheritance - higher tiers access lower tier features
    has_access = guild_tier >= min_tier_required
    
    # Log the final decision with clear reasoning
    logger.info(f"[PREMIUM_DEBUG] Feature '{feature_name}' requires tier {min_tier_required}, guild has tier {guild_tier}, access: {has_access}")
    return has_access


async def validate_premium_feature(guild_model, feature_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate access to a premium feature and provide a user-friendly error message.

    This method implements tier inheritance, ensuring higher tiers have access
    to all features from lower tiers.

    Args:
        guild_model: Guild model instance
        feature_name: Name of the feature to check

    Returns:
        Tuple[bool, Optional[str]]: (has_access, error_message)
    """
    # Validate inputs
    if feature_name is None or not isinstance(feature_name, str) or not feature_name.strip():
        logger.warning(f"[PREMIUM_DEBUG] Invalid feature name in validate_premium_feature: {feature_name!r}")
        return False, "Invalid feature requested. Please contact an administrator."

    # Enhanced error handling for None guild_model
    if guild_model is None:
        logger.warning(f"[PREMIUM_DEBUG] validate_premium_feature called with None guild_model for feature: {feature_name}")
        return False, "Server not registered with the bot. Please run `/setup` first."

    # Check feature access with early return optimization using the improved has_feature_access method
    # which now implements proper tier inheritance
    try:
        # First try the cached path - for performance and consistency
        if await has_feature_access(guild_model, feature_name):
            logger.info(f"[PREMIUM_DEBUG] Feature access GRANTED: {feature_name} for guild {getattr(guild_model, 'guild_id', 'unknown')} with tier {getattr(guild_model, 'premium_tier', 0)}")
            return True, None
    except Exception as e:
        logger.error(f"[PREMIUM_DEBUG] Error in has_feature_access: {e}")
        # Continue with best-effort processing

    # If has_feature_access failed, let's do our own tier inheritance check
    try:
        current_tier = getattr(guild_model, 'premium_tier', 0)
        # Ensure it's a valid integer
        if not isinstance(current_tier, int):
            logger.warning(f"Invalid premium_tier type: {type(current_tier).__name__}, value: {current_tier!r}")
            current_tier = 0

        # CRITICAL FIX: Direct tier inheritance check
        # First get the minimum tier required for this feature
        min_tier_needed = None
        if feature_name in PREMIUM_FEATURES:
            min_tier_needed = PREMIUM_FEATURES.get(feature_name)

        # If we found the minimum tier needed, check if current tier is sufficient
        if min_tier_needed is not None and current_tier >= min_tier_needed:
            logger.debug(f"Direct tier inheritance check PASSED: Current tier {current_tier} >= required tier {min_tier_needed} for feature {feature_name}")
            return True, None

    except Exception as e:
        logger.error(f"Error in direct tier inheritance check: {e}")
        # Continue with detailed error message generation

    # Get current tier info with enhanced NULL handling    
    try:
        current_tier = getattr(guild_model, 'premium_tier', 0)
        # Ensure it's a valid integer
        if not isinstance(current_tier, int):
            logger.warning(f"Invalid premium_tier type: {type(current_tier).__name__}, value: {current_tier!r}")
            current_tier = 0
    except Exception as e:
        logger.error(f"Error accessing premium_tier: {e}")
        current_tier = 0

    # Safer tier name lookup with multiple fallbacks
    tier_data = PREMIUM_TIERS.get(current_tier)
    if tier_data is None:
        logger.error(f"No tier data found for tier {current_tier}")
        current_tier_name = f"Tier {current_tier}"
    else:
        current_tier_name = tier_data.get("name")
        if current_tier_name is None:
            current_tier_name = f"Tier {current_tier}"

    # First attempt to use PREMIUM_FEATURES for direct lookup - most efficient
    min_tier_needed = None
    if feature_name in PREMIUM_FEATURES:
        min_tier_needed = PREMIUM_FEATURES.get(feature_name)

    # If not found in direct mapping, search through PREMIUM_TIERS
    min_tier_name = None
    if min_tier_needed is None:
        try:
            for tier, tier_data in sorted(PREMIUM_TIERS.items()):
                if tier_data is None:
                    logger.warning(f"NULL tier_data for tier {tier} in PREMIUM_TIERS")
                    continue

                features = tier_data.get("features")
                if features is None:
                    logger.warning(f"NULL features for tier {tier} in PREMIUM_TIERS")
                    continue

                if feature_name in features:
                    min_tier_needed = tier
                    min_tier_name = tier_data.get("name")
                    if min_tier_name is None:
                        min_tier_name = f"Tier {tier}"
                    break
        except Exception as e:
            logger.error(f"Error finding minimum tier for feature {feature_name}: {e}")
            # Continue with best-effort values

    if min_tier_needed is None:
        # Feature doesn't exist in any tier or couldn't be determined
        logger.warning(f"Feature '{feature_name}' not found in any premium tier")
        return False, f"Feature '{feature_name}' is not available in any premium tier."

    # Get the tier name if we don't have it yet
    if min_tier_name is None:
        tier_info = PREMIUM_TIERS.get(min_tier_needed)
        if tier_info:
            min_tier_name = tier_info.get("name", f"Tier {min_tier_needed}")
        else:
            min_tier_name = f"Tier {min_tier_needed}"

    # Do a final check for tier inheritance
    if current_tier >= min_tier_needed:
        logger.info(f"Final tier inheritance check PASSED: {current_tier} >= {min_tier_needed} for feature {feature_name}")
        return True, None

    # Return a detailed message about the premium requirement
    return False, (
        f"⚠️ **Premium Feature Required** ⚠️\n"
        f"The `{feature_name}` feature requires the **{min_tier_name}** tier or higher.\n"
        f"Your server is currently on the **{current_tier_name}** tier."
    )


async def validate_server_limit(guild_model, server_count: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate if a guild has reached its server limit and provide a user-friendly error message.

    Args:
        guild_model: Guild model instance
        server_count: Optional manually provided server count (if None, calculated from model)

    Returns:
        Tuple[bool, Optional[str]]: (has_capacity, error_message)
    """
    # Enhanced error handling for None guild_model
    if guild_model is None:
        logger.warning("validate_server_limit called with None guild_model")
        return False, "Server not registered with the bot. Please run `/setup` first."

    # Get tier limits with enhanced NULL handling
    try:
        current_tier = getattr(guild_model, 'premium_tier', 0)
        # Ensure it's a valid integer
        if not isinstance(current_tier, int):
            logger.warning(f"Invalid premium_tier type: {type(current_tier).__name__}, value: {current_tier!r}")
            current_tier = 0
    except Exception as e:
        logger.error(f"Error accessing premium_tier in validate_server_limit: {e}")
        current_tier = 0

    # Enhanced tier info retrieval with NULL checks
    tier_info = PREMIUM_TIERS.get(current_tier)
    if tier_info is None:
        logger.error(f"No tier data found for tier {current_tier} in validate_server_limit")
        # Create fallback tier info
        tier_info = {
            "name": f"Tier {current_tier}",
            "max_servers": 1
        }

    max_servers = tier_info.get("max_servers")
    if max_servers is None:
        logger.warning(f"max_servers not defined for tier {current_tier}, using default of 1")
        max_servers = 1

    tier_name = tier_info.get("name")
    if tier_name is None:
        tier_name = f"Tier {current_tier}"
        logger.warning(f"name not defined for tier {current_tier}, using default: {tier_name}")

    # Calculate current server count with error handling
    try:
        if server_count is not None:
            current_count = server_count
        else:
            servers = getattr(guild_model, 'servers', [])
            if servers is None:
                logger.warning("servers attribute is None in guild_model")
                servers = []
            current_count = len(servers)
    except Exception as e:
        logger.error(f"Error calculating server count: {e}")
        current_count = 0

    # Check if limit is reached
    if current_count < max_servers:
        return True, None

    # Find next tier with higher limit with enhanced error handling
    next_tier = None
    next_tier_name = None
    next_tier_limit = None

    try:
        for tier, tier_data in sorted(PREMIUM_TIERS.items()):
            if tier_data is None:
                logger.warning(f"NULL tier_data for tier {tier} in PREMIUM_TIERS")
                continue

            if tier <= current_tier:
                continue

            tier_max_servers = tier_data.get("max_servers")
            if tier_max_servers is None:
                logger.warning(f"max_servers not defined for tier {tier}")
                continue

            if tier_max_servers > max_servers:
                next_tier = tier
                next_tier_name = tier_data.get("name", f"Tier {tier}")
                next_tier_limit = tier_max_servers
                break
    except Exception as e:
        logger.error(f"Error finding next tier: {e}")
        # Continue with best-effort values

    if next_tier is None:
        # No higher tier available
        return False, (
            f"⚠️ **Server Limit Reached** ⚠️\n"
            f"Your **{tier_name}** tier allows a maximum of {max_servers} server(s).\n"
            f"You are currently using {current_count} server(s)."
        )

    # Return message about limit and next tier
    return False, (
        f"⚠️ **Server Limit Reached** ⚠️\n"
        f"Your **{tier_name}** tier allows a maximum of {max_servers} server(s).\n"
        f"You are currently using {current_count} server(s).\n"
        f"Upgrade to **{next_tier_name}** tier to increase your limit to {next_tier_limit} server(s)."
    )


def get_feature_tier_requirements() -> Dict[str, List[int]]:
    """
    Get a mapping of all features to the tiers they're available in.

    Returns:
        Dict[str, List[int]]: Mapping of feature_name -> list of tier numbers
    """
    feature_tiers = {}

    try:
        for tier, tier_data in PREMIUM_TIERS.items():
            # Skip NULL tier data
            if tier_data is None:
                logger.warning(f"NULL tier_data for tier {tier} in PREMIUM_TIERS")
                continue

            # Get features with NULL check
            features = tier_data.get("features")
            if features is None:
                logger.warning(f"features not defined for tier {tier} in get_feature_tier_requirements")
                continue

            # Process each feature
            for feature in features:
                # Skip empty or invalid features
                if feature is None or feature == "" or not isinstance(feature, str):
                    logger.warning(f"Invalid feature in tier {tier}: {feature!r}")
                    continue

                if feature not in feature_tiers:
                    feature_tiers[feature] = []
                feature_tiers[feature].append(tier)
    except Exception as e:
        logger.error(f"Error building feature tier requirements: {e}")
        # Continue with best-effort feature_tiers

    # Sort tier lists with error handling
    try:
        for feature, tiers in feature_tiers.items():
            feature_tiers[feature] = sorted(tiers)
    except Exception as e:
        logger.error(f"Error sorting tier lists: {e}")
        # Continue with unsorted lists

    return feature_tiers


def get_minimum_tier_for_feature(feature_name: str) -> Optional[int]:
    """
    Get the minimum tier required for a specific feature.

    This method is important for the tier inheritance system, as it identifies
    the lowest tier that provides a given feature, allowing higher tiers
    to automatically include it.

    Args:
        feature_name: Name of the feature

    Returns:
        Optional[int]: Minimum tier number or None if feature doesn't exist
    """
    # Handle NULL or empty feature name
    if feature_name is None or feature_name == "":
        logger.warning(f"Invalid feature name in get_minimum_tier_for_feature: {feature_name!r}")
        return None

    try:
        # Method 1: Direct lookup from the PREMIUM_FEATURES dictionary (most efficient)
        # This is the primary source of truth for feature tier requirements
        if feature_name in PREMIUM_FEATURES:
            min_tier = PREMIUM_FEATURES[feature_name]
            logger.debug(f"Direct lookup: Feature '{feature_name}' requires minimum tier {min_tier}")
            return min_tier

        # Method 2: Check via tier requirements from config as fallback
        # This is useful if a feature is defined in PREMIUM_TIERS but not in PREMIUM_FEATURES
        feature_tiers = get_feature_tier_requirements()

        # Check if feature exists and has tiers
        if feature_name in feature_tiers and feature_tiers[feature_name]:
            try:
                # Find minimum tier
                min_tier = min(feature_tiers[feature_name])
                logger.debug(f"Tier lookup: Feature '{feature_name}' requires minimum tier {min_tier}")
                return min_tier
            except Exception as e:
                logger.error(f"Error finding minimum tier for feature {feature_name}: {e}")
                return None
        else:
            # Log when feature is not found for debugging
            logger.debug(f"Feature not found in any tier: {feature_name}")
            return None
    except Exception as e:
        logger.error(f"Error in get_minimum_tier_for_feature: {e}")
        return None


def premium_tier_required(min_tier: int = 1, feature_name: Optional[str] = None):
    """
    Decorator to require a minimum premium tier for a command.

    This decorator implements tier inheritance, ensuring that higher tiers
    have access to all features from lower tiers. It can check either:
    1. Direct tier level (min_tier) - user's tier must be >= min_tier
    2. Feature access (feature_name) - user's tier must include the feature

    Args:
        min_tier: Minimum premium tier required (default: 1)
        feature_name: Optional feature name to check instead of tier

    Returns:
        Command decorator
    """
    def decorator(command_function):
        @functools.wraps(command_function)
        async def wrapper(self, ctx, *args, **kwargs):
            try:
                # Get guild from context
                guild = ctx.guild
                if guild is None:
                    await ctx.send("This command can only be used in a server.")
                    return

                # Get guild model
                from utils.database import get_db
                db = await get_db()

                from models.guild import Guild
                guild_model = await Guild.get_by_guild_id(db, str(guild.id))

                if guild_model is None:
                    await ctx.send("This server is not set up. Please use the `/setup` command first.")
                    return

                # Check premium access based on feature name or tier level
                if feature_name:
                    # Feature-based access check uses the updated validate_premium_feature
                    # which implements tier inheritance correctly
                    has_access, error_message = await validate_premium_feature(guild_model, feature_name)
                else:
                    # Direct tier level check - tier inheritance is simpler here,
                    # as we just need to check if user's tier >= required tier
                    try:
                        guild_tier = int(getattr(guild_model, 'premium_tier', 0))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid premium_tier value in decorator: {getattr(guild_model, 'premium_tier', 0)}, defaulting to 0")
                        guild_tier = 0

                    has_access = guild_tier >= min_tier
                    logger.debug(f"Tier check: guild tier {guild_tier}, required tier {min_tier}, has access: {has_access}")

                    # Initialize error_message to ensure it's always defined
                    error_message = None

                    if not has_access:
                        tier_data = PREMIUM_TIERS.get(min_tier, {"name": f"Tier {min_tier}"})
                        tier_name = tier_data.get("name", f"Tier {min_tier}")
                        current_tier_data = PREMIUM_TIERS.get(guild_tier, {"name": f"Tier {guild_tier}"})
                        current_tier_name = current_tier_data.get("name", f"Tier {guild_tier}")

                        error_message = (
                            f"⚠️ **Premium Tier Required** ⚠️\n"
                            f"This command requires the **{tier_name}** tier or higher.\n"
                            f"Your server is currently on the **{current_tier_name}** tier."
                        )

                if not has_access:
                    await ctx.send(error_message)
                    return

                # Run the command
                return await command_function(self, ctx, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in premium_tier_required: {e}")
                await ctx.send("An error occurred while checking premium access.")
                raise

        return wrapper
    return decorator


def format_tier_info(tier: int) -> str:
    """
    Format tier information for display.

    Args:
        tier: Tier number

    Returns:
        str: Formatted tier information
    """
    # Handle non-integer tier values
    try:
        tier_int = int(tier)
    except (TypeError, ValueError):
        logger.warning(f"Invalid tier value in format_tier_info: {tier!r}")
        tier_int = 0

    # Constrain to valid range
    tier_int = max(0, min(5, tier_int))

    # Enhanced tier data retrieval with NULL handling
    tier_data = PREMIUM_TIERS.get(tier_int)
    if tier_data is None:
        logger.error(f"No tier data found for tier {tier_int} in format_tier_info")
        return f"Tier {tier_int} (Unknown)"

    # Extract tier information with NULL checks    
    tier_name = tier_data.get("name")
    if tier_name is None:
        tier_name = f"Tier {tier_int}"
        logger.warning(f"name not defined for tier {tier_int} in format_tier_info")

    tier_price = tier_data.get("price")
    if tier_price is None:
        tier_price = "Unknown"
        logger.warning(f"price not defined for tier {tier_int} in format_tier_info")

    max_servers = tier_data.get("max_servers")
    if max_servers is None:
        max_servers = 0
        logger.warning(f"max_servers not defined for tier {tier_int} in format_tier_info")

    features = tier_data.get("features")
    if features is None:
        features = []
        logger.warning(f"features not defined for tier {tier_int} in format_tier_info")

    # Format and return tier information    
    try:
        features_str = ', '.join(features)
    except Exception as e:
        logger.error(f"Error joining features: {e}, features: {features!r}")
        features_str = "(Error formatting features)"

    return (
        f"**{tier_name}** ({tier_price})\n"
        f"• Max Servers: {max_servers}\n"
        f"• Features: {features_str}"
    )


def invalidate_feature_access_cache(guild_id: str) -> int:
    """
    Invalidate cache for feature access checks when a guild's tier changes.

    Args:
        guild_id: Guild ID

    Returns:
        int: Number of cache entries invalidated
    """
    return AsyncCache.invalidate_pattern(has_feature_access, [None, None])


@retryable(max_retries=2, delay=1.0, backoff=1.5, 
           exceptions=[asyncio.TimeoutError, ConnectionError])
async def get_guild_premium_tier(db, guild_id: Union[str, int, None]) -> Tuple[int, Optional[dict]]:
    """
    Get a guild's premium tier with caching and error handling.

    Args:
        db: Database connection
        guild_id: Guild ID (can be string, int, or None)

    Returns:
        Tuple[int, Optional[dict]]: (premium_tier, tier_data)
    """
    # CRITICAL FIX: Clear caches periodically to prevent stale data
    # This is a temporary solution until we identify the specific caching issue
    try:
        # Every 10% of requests, clear all caches to ensure fresh data
        import random
        if random.random() < 0.1:
            async with _LOCAL_CACHE_LOCK:
                _LOCAL_PREMIUM_CACHE.clear()
                logger.info("[PREMIUM_DEBUG] Cleared local premium cache for fresh tier data")
    except Exception as e:
        logger.error(f"[PREMIUM_DEBUG] Error clearing caches: {e}")

    # Fast path for None guild_id - immediately return tier 0
    if guild_id is None:
        logger.warning("[PREMIUM_DEBUG] get_guild_premium_tier called with None guild_id, defaulting to tier 0")
        return (0, PREMIUM_TIERS.get(0, {}))

    # Enhanced standardization of guild ID with better error handling
    try:
        if isinstance(guild_id, int):
            str_guild_id = str(guild_id)
            logger.info(f"[PREMIUM_DEBUG] Converted int guild_id {guild_id} to string: {str_guild_id}")
        elif isinstance(guild_id, str):
            str_guild_id = guild_id.strip()
            logger.info(f"[PREMIUM_DEBUG] Using string guild_id: {str_guild_id}")
        else:
            # Handle other types by converting to string
            str_guild_id = str(guild_id)
            logger.warning(f"[PREMIUM_DEBUG] Unexpected guild_id type: {type(guild_id).__name__}, value: {guild_id!r}")
    except Exception as e:
        logger.error(f"[PREMIUM_DEBUG] Error converting guild_id to string: {e}, value: {guild_id!r}, type: {type(guild_id).__name__}")
        # Fallback: Try simple string conversion or use empty string
        try:
            str_guild_id = str(guild_id)
        except:
            str_guild_id = ""

    # Verify we have a valid guild ID
    if str_guild_id is None or str_guild_id == "":
        logger.warning("[PREMIUM_DEBUG] Empty guild_id after processing, defaulting to tier 0")
        return (0, PREMIUM_TIERS.get(0, {}))

    logger.info(f"[PREMIUM_DEBUG] Getting premium tier for guild ID: {str_guild_id} (original type: {type(guild_id).__name__})")

    # Generate cache key
    cache_key = f"premium_tier:{str_guild_id}"

    try:
        # CRITICAL FIX: Only use cached tier in debug or restricted environments
        # In production, periodically bypass cache to ensure fresh data
        use_cached_value = True
        try:
            # Every 20% of requests, bypass cache to ensure fresh data
            import random
            if random.random() < 0.2:
                use_cached_value = False
                logger.info(f"[PREMIUM_DEBUG] Bypassing cache for guild {str_guild_id} to ensure fresh data")
        except Exception as e:
            logger.error(f"[PREMIUM_DEBUG] Error in cache bypass logic: {e}")

        if use_cached_value:
            # Check local cache first for ultra-fast lookups
            async with _LOCAL_CACHE_LOCK:
                if cache_key in _LOCAL_PREMIUM_CACHE:
                    value, expiry = _LOCAL_PREMIUM_CACHE[cache_key]
                    if expiry > time.time():
                        logger.info(f"[PREMIUM_DEBUG] Local cache hit for premium tier: {str_guild_id}, tier: {value[0]}")
                        return value[0], value[1]
                    else:
                        # Expired entry, remove it
                        logger.info(f"[PREMIUM_DEBUG] Expired cache entry for {str_guild_id}, removing")
                        _LOCAL_PREMIUM_CACHE.pop(cache_key, None)

        # Clean up expired cache entries periodically
        await cleanup_local_cache()

        # Set a timeout for the database operation
        async with asyncio.timeout(3.0):
            # CRITICAL FIX: Try multiple query approaches for more reliable lookup
            # This helps address potential inconsistencies in how guild_id is stored
            guild_doc = None

            # Approach 1: Try exact string match (most efficient)
            query = {"guild_id": str_guild_id}
            guild_doc = await db.guilds.find_one(query, {"premium_tier": 1, "premium_expires": 1})

            # Approach 2: If ID is numeric, try both string and integer queries
            if guild_doc is None and str_guild_id.isdigit():
                logger.info(f"[PREMIUM_DEBUG] String match failed, trying OR query with int/string for guild {str_guild_id}")
                query = {
                    "$or": [
                        {"guild_id": str_guild_id},
                        {"guild_id": int(str_guild_id)}
                    ]
                }
                guild_doc = await db.guilds.find_one(query, {"premium_tier": 1, "premium_expires": 1})

            # Approach 3: Case-insensitive regex match as last resort
            if guild_doc is None:
                logger.info(f"[PREMIUM_DEBUG] OR query failed, trying case-insensitive regex for guild {str_guild_id}")
                query = {"guild_id": {"$regex": f"^{str_guild_id}$", "$options": "i"}}
                guild_doc = await db.guilds.find_one(query, {"premium_tier": 1, "premium_expires": 1})

            if guild_doc is not None:
                logger.info(f"[PREMIUM_DEBUG] Found guild document for {str_guild_id}: {guild_doc}")
            else:
                logger.warning(f"[PREMIUM_DEBUG] Guild {str_guild_id} not found in database after all query attempts")

            if guild_doc is None:
                logger.warning(f"[PREMIUM_DEBUG] Guild not found in database: {str_guild_id}, defaulting to tier 0")
                # Guild not found, default to tier 0
                result = (0, PREMIUM_TIERS.get(0, {}))

                # Cache the result for a shorter time since it might be a new guild
                shorter_ttl = min(60, PREMIUM_TIER_CACHE_TTL)  # 1 minute or the configured TTL, whichever is shorter
                async with _LOCAL_CACHE_LOCK:
                    _LOCAL_PREMIUM_CACHE[cache_key] = (result, time.time() + shorter_ttl)
                    logger.info(f"[PREMIUM_DEBUG] Caching default tier 0 for {str_guild_id} for {shorter_ttl} seconds")

                return result

            # Extract premium tier information with enhanced error handling
            try:
                premium_tier_raw = guild_doc.get("premium_tier", 0)
                logger.info(f"[PREMIUM_DEBUG] Raw premium_tier from DB for guild {str_guild_id}: {premium_tier_raw}, type: {type(premium_tier_raw).__name__}")

                # Handle None value explicitly
                if premium_tier_raw is None:
                    logger.warning(f"[PREMIUM_DEBUG] NULL premium_tier in database for guild {str_guild_id}, defaulting to 0")
                    premium_tier_raw = 0

                # CRITICAL FIX: More robust type conversion
                if isinstance(premium_tier_raw, int):
                    # Already an integer
                    premium_tier = premium_tier_raw
                    logger.info(f"[PREMIUM_DEBUG] premium_tier is already an integer: {premium_tier}")
                elif isinstance(premium_tier_raw, str) and premium_tier_raw.strip().isdigit():
                    # Convert string to integer
                    premium_tier = int(premium_tier_raw.strip())
                    logger.info(f"[PREMIUM_DEBUG] Converted string premium_tier '{premium_tier_raw}' to integer: {premium_tier}")
                else:
                    # Fallback conversion
                    try:
                        premium_tier = int(premium_tier_raw)
                        logger.info(f"[PREMIUM_DEBUG] Converted {type(premium_tier_raw).__name__} premium_tier to integer: {premium_tier}")
                    except (TypeError, ValueError) as e:
                        logger.error(f"[PREMIUM_DEBUG] Error converting premium_tier '{premium_tier_raw}': {e}, defaulting to 0")
                        premium_tier = 0

                # Constrain premium tier to valid range
                if premium_tier < 0 or premium_tier > 5:
                    logger.warning(f"[PREMIUM_DEBUG] Premium tier {premium_tier} out of range (0-5) for guild {str_guild_id}, clamping")
                    premium_tier = max(0, min(5, premium_tier))

                logger.info(f"[PREMIUM_DEBUG] Retrieved premium tier for guild {str_guild_id}: {premium_tier}")

                # CRITICAL FIX: Update in database if needed
                if not isinstance(premium_tier_raw, int) and premium_tier > 0:
                    try:
                        logger.info(f"[PREMIUM_DEBUG] Updating stored premium_tier format for guild {str_guild_id}: {premium_tier_raw} -> {premium_tier}")
                        await db.guilds.update_one(
                            {"_id": guild_doc["_id"]},
                            {"$set": {"premium_tier": premium_tier}}
                        )
                    except Exception as update_error:
                        logger.error(f"[PREMIUM_DEBUG] Error updating premium tier format: {update_error}")
                        # Continue without failing
            except Exception as e:
                logger.error(f"[PREMIUM_DEBUG] Error processing premium_tier for guild {str_guild_id}: {e}")
                premium_tier = 0  # Safe default

            # Get premium expiration date with enhanced error handling
            try:
                premium_expires = guild_doc.get("premium_expires")
                logger.info(f"[PREMIUM_DEBUG] premium_expires for guild {str_guild_id}: {premium_expires}")

                # Handle None explicitly
                if premium_expires is not None and not isinstance(premium_expires, datetime):
                    logger.warning(f"[PREMIUM_DEBUG] Invalid premium_expires type: {type(premium_expires).__name__} for guild {str_guild_id}")
                    premium_expires = None
            except Exception as e:
                logger.error(f"[PREMIUM_DEBUG] Error processing premium_expires for guild {str_guild_id}: {e}")
                premium_expires = None  # Safe default

            # Check if premium has expired
            if premium_expires is not None and isinstance(premium_expires, datetime):
                if premium_expires < datetime.now():
                    # Premium expired, revert to tier 0
                    logger.info(f"[PREMIUM_DEBUG] Premium expired for guild {str_guild_id}, reverting to tier 0")
                    premium_tier = 0

                    # Update the database
                    try:
                        await db.guilds.update_one(
                            {"_id": guild_doc["_id"]},
                            {"$set": {"premium_tier": 0}}
                        )
                    except Exception as update_error:
                        logger.error(f"[PREMIUM_DEBUG] Error updating expired premium tier: {update_error}")
                        # Continue without failing

            # Get tier data with enhanced error recovery
            tier_data = PREMIUM_TIERS.get(premium_tier)
            if tier_data is None:
                logger.warning(f"[PREMIUM_DEBUG] No tier data found for tier {premium_tier}, using tier 0 as fallback")
                premium_tier = 0
                tier_data = PREMIUM_TIERS.get(0)

                # If even tier 0 doesn't exist, create a minimal fallback structure
                if tier_data is None:
                    logger.error("[PREMIUM_DEBUG] Critical error: Tier 0 not found in PREMIUM_TIERS, using emergency fallback")
                    tier_data = {
                        "name": "Free Tier",
                        "features": [],
                        "max_servers": 1
                    }

            result = (premium_tier, tier_data)

            # Cache the result
            async with _LOCAL_CACHE_LOCK:
                _LOCAL_PREMIUM_CACHE[cache_key] = (result, time.time() + PREMIUM_TIER_CACHE_TTL)
                logger.info(f"[PREMIUM_DEBUG] Cached premium tier {premium_tier} for {str_guild_id} for {PREMIUM_TIER_CACHE_TTL} seconds")

            # Log available features for debugging
            logger.info(f"[PREMIUM_DEBUG] Returning premium tier {premium_tier} for guild {str_guild_id}")
            features = tier_data.get('features', [])
            logger.info(f"[PREMIUM_DEBUG] Features for tier {premium_tier}: {features[:5] if features else 'None'}")

            return result

    except asyncio.TimeoutError:
        logger.error(f"[PREMIUM_DEBUG] Timeout retrieving premium tier for guild {str_guild_id}")
        # Return default tier as fallback with enhanced error handling
        tier_data = PREMIUM_TIERS.get(0)
        if tier_data is None:
            logger.error("[PREMIUM_DEBUG] Critical error: Tier 0 not found in PREMIUM_TIERS during timeout recovery")
            tier_data = {
                "name": "Free Tier",
                "features": [],
                "max_servers": 1
            }
        return (0, tier_data)

    except Exception as e:
        logger.error(f"[PREMIUM_DEBUG] Error retrieving premium tier for guild {str_guild_id}: {e}")
        # Return default tier as fallback with enhanced error handling
        tier_data = PREMIUM_TIERS.get(0)
        if tier_data is None:
            logger.error("[PREMIUM_DEBUG] Critical error: Tier 0 not found in PREMIUM_TIERS during exception recovery")
            tier_data = {
                "name": "Free Tier",
                "features": [],
                "max_servers": 1
            }
        return (0, tier_data)


async def check_tier_access(db, guild_id: Union[str, int, None], required_tier: int) -> Tuple[bool, Optional[str]]:
    """
    Check if a guild has access to a specific premium tier.

    This function implements tier inheritance, ensuring higher tiers have access
    to all features from lower tiers.

    Args:
        db: Database connection
        guild_id: Guild ID (can be string, int, or None)
        required_tier: Minimum tier required

    Returns:
        Tuple[bool, Optional[str]]: (has_access, error_message)
    """
    # Early return for None or invalid guild_id
    if guild_id is None:
        logger.warning("check_tier_access called with None guild_id")
        # Default to access denied with a clear message
        return False, "Guild not found. Please ensure you're running this command in a Discord server."

    # Standardize guild ID with better error handling
    try:
        if isinstance(guild_id, int):
            str_guild_id = str(guild_id)
        elif isinstance(guild_id, str):
            str_guild_id = guild_id.strip()
        else:
            # Handle other types by converting to string
            str_guild_id = str(guild_id)
            logger.warning(f"Unexpected guild_id type in check_tier_access: {type(guild_id).__name__}, value: {guild_id!r}")
    except Exception as e:
        logger.error(f"Error converting guild_id to string in check_tier_access: {e}")
        return False, "Invalid guild ID format. Please contact an administrator."

    # Verify we have a valid guild ID
    if str_guild_id is None or str_guild_id == "":
        logger.warning("Empty guild_id after processing in check_tier_access")
        return False, "Guild ID is empty. Please contact an administrator."

    logger.debug(f"Checking tier access for guild {str_guild_id}, required tier: {required_tier}")

    # Check if the guild exists in the database
    guild_exists = False
    try:
        # Use a simple query to check existence
        guild_doc = await db.guilds.find_one({"guild_id": str_guild_id}, {"_id": 1})
        guild_exists = guild_doc is not None
    except Exception as e:
        logger.warning(f"Error checking if guild exists: {e}")
        # Continue with get_guild_premium_tier which has error handling

    # If guild doesn't exist, create it automatically using Guild.get_or_create
    if guild_exists is None:
        try:
            from models.guild import Guild
            logger.info(f"Guild not found in database during premium check, creating with get_or_create: {str_guild_id}")

            # Use a generic name since we're outside of Discord context
            guild_name = f"Guild {str_guild_id}"

            # Use the new get_or_create method for consistent guild creation
            guild_model = await Guild.get_or_create(db, str_guild_id, guild_name)

            if guild_model is not None:
                logger.info(f"Created guild in database during premium check: {str_guild_id}")
            else:
                logger.error(f"Failed to create guild with get_or_create during premium check: {str_guild_id}")
        except Exception as e:
            logger.error(f"Error creating guild during premium check: {e}", exc_info=True)
            # Continue with get_guild_premium_tier which has error handling for missing guilds

    # Initialize variables with default values to ensure they're always defined
    current_tier = 0
    tier_data = PREMIUM_TIERS.get(0, {})

    # For test environment, check the database directly first to bypass caching issues
    test_direct_db = False
    try:
        # Direct DB query for testing to avoid caching issues
        guild_doc = await db.guilds.find_one({"guild_id": str_guild_id}, {"premium_tier": 1})
        if guild_doc is not None and "premium_tier" in guild_doc:
            db_tier = guild_doc.get("premium_tier", 0)
            if db_tier is not None:
                try:
                    db_tier_int = int(db_tier)
                    logger.info(f"Direct DB check - Guild {str_guild_id} has tier: {db_tier_int}")
                    test_direct_db = True
                    current_tier = db_tier_int
                    # Get tier data
                    tier_data = PREMIUM_TIERS.get(current_tier, {})
                except (ValueError, TypeError):
                    logger.warning(f"Invalid tier value in database: {db_tier}")
    except Exception as e:
        logger.error(f"Error during direct DB tier check: {e}")

    # If direct DB check failed, use the cached approach
    if test_direct_db is None:
        # Get current premium tier
        current_tier, tier_data = await get_guild_premium_tier(db, str_guild_id)

    # Normalize required_tier
    try:
        required_tier = int(required_tier)
    except (TypeError, ValueError):
        logger.warning(f"Invalid required_tier value: {required_tier}, defaulting to 0")
        required_tier = 0

    # Constrain to valid range
    required_tier = max(0, min(5, required_tier))

    # CRITICAL FIX FOR TIER INHERITANCE: 
    # Check if current tier is greater than or equal to the required tier
    # This is the core of tier inheritance - higher tiers automatically have access to lower tier features
    if current_tier >= required_tier:
        logger.info(f"✅ Tier access GRANTED for guild {str_guild_id}: tier {current_tier} >= required {required_tier}")
        return True, None

    # For debugging tier inheritance issues, log detailed checking information
    logger.debug(f"TIER INHERITANCE: Guild {str_guild_id} has tier {current_tier}, but requires tier {required_tier} or higher")

    # Additional data verification
    if tier_data is None:
        tier_data = {}
        logger.error(f"NULL tier data returned for guild {str_guild_id}, using empty dict")

    # Get current tier name with enhanced None handling
    current_tier_name = "Free" if current_tier == 0 else tier_data.get("name")
    if current_tier_name is None:
        current_tier_name = f"Tier {current_tier}"
        logger.warning(f"Missing name for tier {current_tier}, using fallback name: {current_tier_name}")

    # Get required tier name with enhanced None handling
    required_tier_data = PREMIUM_TIERS.get(required_tier)
    if required_tier_data is None:
        required_tier_data = {}
        logger.error(f"Missing data for required tier {required_tier} in PREMIUM_TIERS")

    required_tier_name = required_tier_data.get("name")
    if required_tier_name is None:
        required_tier_name = f"Tier {required_tier}"
        logger.warning(f"Missing name for required tier {required_tier}, using fallback name: {required_tier_name}")

    logger.debug(f"Tier access denied for guild {str_guild_id}: {current_tier_name} < {required_tier_name}")

    # Return detailed error message
    return False, (
        f"⚠️ **Premium Tier Required** ⚠️\n"
        f"This feature requires the **{required_tier_name}** tier or higher.\n"
        f"Your server is currently on the **{current_tier_name}** tier.\n\n"
        f"Use `/premium info` to learn more about premium features."
    )