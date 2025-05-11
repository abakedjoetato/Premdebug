"""
Test script to verify player name changes inside the Discord bot context
"""
import asyncio
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Import the bot modules
        from cogs.csv_processor import CSVProcessorCog
        from bot import initialize_bot
        
        # Initialize the bot
        bot = await initialize_bot()
        
        # Test data
        player_id = "test_player_" + str(int(asyncio.get_event_loop().time()))
        server_id = "61a9d32b-f5e3-4a0f-8bc2-8b3054f074a0"  # Use current server ID
        original_name = "OriginalPlayerName"
        new_name = "NewPlayerName"
        
        logger.info(f"Testing player name change for player ID: {player_id}")
        
        # Get the CSV processor cog
        csv_processor = None
        for name, cog in bot.cogs.items():
            logger.info(f"Found cog: {name}")
            if name == "CSVProcessorCog":  # Name is shown from previous output
                csv_processor = cog
                logger.info(f"Found CSV processor cog: {name}")
                break
        
        if not csv_processor:
            logger.error("Could not find CSV processor cog")
            return
        
        logger.info("Creating player with original name")
        original_player = await csv_processor._get_or_create_player(
            server_id=server_id,
            player_id=player_id,
            player_name=original_name
        )
        
        logger.info(f"Created player: {original_player.name} with ID: {original_player.player_id}")
        
        # Now update with a new name
        logger.info("Updating player with new name")
        updated_player = await csv_processor._get_or_create_player(
            server_id=server_id,
            player_id=player_id,
            player_name=new_name
        )
        
        logger.info(f"Updated player: {updated_player.name} with ID: {updated_player.player_id}")
        logger.info(f"Known aliases: {getattr(updated_player, 'known_aliases', [])}")
        
        # Clean up
        result = await bot.db.players.delete_one({"player_id": player_id})
        logger.info(f"Cleaned up test player: {result.deleted_count} documents deleted")
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean exit
        try:
            await bot.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())