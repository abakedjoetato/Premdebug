"""
Test script to verify the player upsert functionality with name changes
"""
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Import the necessary modules
        from motor.motor_asyncio import AsyncIOMotorClient
        from datetime import datetime
        
        # Connect to MongoDB
        mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emeralds_killfeed
        
        # Test player data
        player_id = "TEST_PLAYER_123456"
        server_id = "TEST_SERVER_123456"
        
        # First, let's create a player
        first_name = "PlayerOriginalName"
        now = datetime.utcnow()
        
        logger.info(f"Creating player with name: {first_name}")
        
        # Create player with original name
        player_data = {
            "player_id": player_id,
            "server_id": server_id,
            "name": first_name,
            "display_name": first_name,
            "last_seen": now,
            "created_at": now,
            "updated_at": now
        }
        
        # Remove created_at from player_data
        player_data_for_insert = player_data.copy()
        if 'created_at' in player_data_for_insert:
            del player_data_for_insert['created_at']
        
        # Insert or update player
        result = await db.players.update_one(
            {"player_id": player_id},
            {
                "$set": player_data_for_insert,
                "$setOnInsert": {"created_at": now}
            },
            upsert=True
        )
        
        logger.info(f"Player created/updated: {result.modified_count} modified, {result.upserted_id is not None}")
        
        # Now update with a new name
        second_name = "PlayerNewName"
        logger.info(f"Updating player with new name: {second_name}")
        
        # Get existing player
        existing_player = await db.players.find_one({"player_id": player_id})
        logger.info(f"Existing player: {existing_player}")
        
        # Setup known_aliases
        known_aliases = []
        if existing_player is not None and "known_aliases" in existing_player and existing_player["known_aliases"]:
            known_aliases = existing_player["known_aliases"]
            
        # Add old name to aliases if not already there
        if existing_player is not None and existing_player["name"] and existing_player["name"] not in known_aliases:
            known_aliases.append(existing_player["name"])
            
        # Update player data with new name
        player_data = {
            "player_id": player_id,
            "server_id": server_id,
            "name": second_name,
            "display_name": second_name,
            "last_seen": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "known_aliases": known_aliases
        }
        
        # Update player
        result = await db.players.update_one(
            {"player_id": player_id},
            {"$set": player_data},
        )
        
        logger.info(f"Player updated with new name: {result.modified_count} modified")
        
        # Retrieve updated player
        updated_player = await db.players.find_one({"player_id": player_id})
        logger.info(f"Updated player: {updated_player}")
        
        # Clean up test data
        await db.players.delete_one({"player_id": player_id})
        logger.info("Test player deleted")
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    asyncio.run(main())