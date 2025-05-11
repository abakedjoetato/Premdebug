#!/usr/bin/env python3
"""
Test script to verify player name history tracking is working correctly
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Main test function"""
    try:
        # Import the bot initialization code
        from bot import initialize_bot
        
        # Initialize the bot (without starting it)
        bot = await initialize_bot(force_sync=False)
        
        # Wait for bot to be fully initialized
        logger.info("Waiting for bot to initialize...")
        await bot.wait_until_ready()
        logger.info("Bot initialization complete")
        
        # Get the CSV processor cog
        from discord.ext import commands
        csv_processor_cog = bot.get_cog("CSVProcessor")
        
        if not csv_processor_cog:
            logger.error("CSV processor cog not found!")
            return
        
        logger.info("Testing player name history tracking...")
        
        # Test server ID to use for testing
        test_server_id = "test_server_001"
        
        # Test with different player names
        player_id = "test_player_001"
        player_names = [
            "PlayerOriginal",
            "PlayerChanged",
            "PlayerChangedAgain",
            "FinalPlayerName"
        ]
        
        # Simulate name changes
        for i, name in enumerate(player_names):
            logger.info(f"Test {i+1}: Creating/updating player with name {name}")
            player = await csv_processor_cog._get_or_create_player(
                server_id=test_server_id,
                player_id=player_id,
                player_name=name
            )
            
            if player:
                logger.info(f"Player record: {player}")
                known_aliases = getattr(player, 'known_aliases', [])
                logger.info(f"Known aliases: {known_aliases}")
            else:
                logger.error(f"Failed to create/update player: {name}")
        
        # Verify final player record with all name history
        from models.player import Player
        final_player = await Player.get_by_player_id(bot.db, player_id)
        
        if not final_player:
            logger.error(f"Cannot find final player record with ID {player_id}")
            return
            
        logger.info(f"Final player record:")
        logger.info(f"  ID: {final_player.player_id}")
        logger.info(f"  Name: {final_player.name}")
        logger.info(f"  Known aliases: {getattr(final_player, 'known_aliases', [])}")
        
        # Verify all names are in the known_aliases list
        known_aliases = getattr(final_player, 'known_aliases', [])
        missing_names = [name for name in player_names if name not in known_aliases]
        
        if missing_names:
            logger.error(f"Name history tracking failed! Missing names: {missing_names}")
        else:
            logger.info("Name history tracking successful! All player names are properly recorded.")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        await bot.db.players.delete_many({"server_id": test_server_id})
        logger.info("Test completed.")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close the bot
        try:
            await bot.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())