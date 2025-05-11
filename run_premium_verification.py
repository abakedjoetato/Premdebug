#!/usr/bin/env python3
"""
Comprehensive verification script for premium features and server stats
"""
import asyncio
import logging
import sys
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def verify_server_stats():
    """Verify server stats functionality works correctly"""
    try:
        # Import required modules
        from utils.database import get_db
        from models.guild import Guild
        from models.server import Server

        # Get database connection
        db = await get_db()
        if not db:
            logger.error("Failed to connect to database")
            return False

        # Check guild_id with a known valid guild
        guild_id = "1219706687980568769"  # Use a known guild ID

        # Test guild retrieval
        logger.info(f"Testing Guild.get_by_guild_id with {guild_id}")
        guild = await Guild.get_by_guild_id(db, guild_id)

        if guild is None:
            logger.error(f"Could not find guild with ID {guild_id}")
            return False

        logger.info(f"Successfully retrieved guild {guild_id}, premium_tier: {guild.premium_tier}")

        # Test feature access checking
        logger.info("Testing check_feature_access method")
        has_stats_access = await guild.check_feature_access("stats")
        logger.info(f"Guild has access to 'stats' feature: {has_stats_access}")

        # Test server retrieval
        if not guild.servers or len(guild.servers) == 0:
            logger.error(f"Guild {guild_id} has no servers")
            return False

        server_data = guild.servers[0]
        server_id = server_data.get("server_id")
        logger.info(f"Using server with ID: {server_id}")

        # Create server object
        server = Server(db, server_data)

        # Test get_server_stats method
        logger.info("Testing server.get_server_stats method")
        server_stats = await server.get_server_stats()

        if not server_stats:
            logger.error("Failed to get server stats")
            return False

        # Log the stats for verification
        logger.info(f"Server name: {server_stats.get('server_name')}")
        logger.info(f"Total kills: {server_stats.get('total_kills')}")
        logger.info(f"Total suicides: {server_stats.get('total_suicides')}")
        logger.info(f"Active players: {server_stats.get('active_players')}")

        # Log top killers
        top_killers = server_stats.get("top_killers", [])
        if top_killers:
            logger.info("Top killers:")
            for i, killer in enumerate(top_killers[:3], 1):
                logger.info(f"  {i}. {killer.get('player_name')}: {killer.get('kills')} kills")

        # All checks passed
        logger.info("Server stats verification completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error in server stats verification: {e}", exc_info=True)
        return False

async def main():
    """Run verification script"""
    success = await verify_server_stats()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)