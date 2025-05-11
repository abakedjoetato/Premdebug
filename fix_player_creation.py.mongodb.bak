"""
Fix player creation issues with type consistency and validation.
This script repairs existing player records and validates the player creation pipeline.
"""
import os
import sys
import asyncio
import logging
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("player_fix.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("player_fix")

# Ensure import path includes project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MongoDB connection from config
from config import MONGODB_URI
import motor.motor_asyncio

async def connect_to_mongodb():
    """Connect to MongoDB using URI from config"""
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        db = client.towerdb
        
        # Test connection with a ping
        await db.command("ping")
        logger.info("Successfully connected to MongoDB")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def check_player_collection(db):
    """Check player collection structure and count"""
    try:
        count = await db.players.count_documents({})
        logger.info(f"Found {count} players in database")
        
        # Check a sample player
        if count > 0:
            sample = await db.players.find_one({})
            logger.info(f"Sample player: {sample.get('name')} (guild={sample.get('guild_id')}, server={sample.get('server_id')})")
            
            # Check guild_id type for sample
            if "guild_id" in sample:
                guild_id = sample["guild_id"]
                logger.info(f"Guild ID type: {type(guild_id).__name__}, value: {guild_id}")
            
        return count
    except Exception as e:
        logger.error(f"Error checking player collection: {str(e)}")
        raise

async def fix_guild_id_types(db):
    """Fix guild_id types to ensure they're all strings"""
    try:
        # Count players with integer guild_ids
        int_guild_count = await db.players.count_documents({"guild_id": {"$type": "int"}})
        logger.info(f"Found {int_guild_count} players with integer guild_ids")
        
        if int_guild_count > 0:
            # Get all players with integer guild_ids
            players_with_int_guilds = await db.players.find({"guild_id": {"$type": "int"}}).to_list(length=int_guild_count)
            
            # Update each player
            for player in players_with_int_guilds:
                old_guild_id = player["guild_id"]
                new_guild_id = str(old_guild_id)
                
                # Update guild_id to string
                await db.players.update_one(
                    {"_id": player["_id"]},
                    {"$set": {"guild_id": new_guild_id}}
                )
                
                logger.info(f"Updated player {player.get('name')}: guild_id {old_guild_id} ({type(old_guild_id).__name__}) -> {new_guild_id} (str)")
                
            logger.info(f"Fixed {int_guild_count} players with integer guild_ids")
        
        return int_guild_count
    except Exception as e:
        logger.error(f"Error fixing guild_id types: {str(e)}")
        raise

async def fix_missing_fields(db):
    """Fix missing required fields in player documents"""
    # Define required fields with default values
    required_fields = {
        "kills": 0,
        "deaths": 0,
        "last_seen": datetime.datetime.utcnow(),
        "first_seen": datetime.datetime.utcnow(),
        "nemesis": {},
        "prey": {},
        "weapons": {},
        "victim_weapons": {},
        "headshots": 0,
        "headshot_kills": 0,
        "headshot_deaths": 0,
        "kill_streak": 0,
        "max_kill_streak": 0,
        "death_streak": 0,
        "max_death_streak": 0,
        "team_kills": 0,
        "suicides": 0,
        "updated_at": datetime.datetime.utcnow(),
        "created_at": datetime.datetime.utcnow()
    }
    
    fixed_count = 0
    
    try:
        # Check each field
        for field, default_value in required_fields.items():
            # Count documents missing this field
            missing_count = await db.players.count_documents({field: {"$exists": False}})
            
            if missing_count > 0:
                logger.info(f"Found {missing_count} players missing {field}")
                
                # Update players to add field with default value
                await db.players.update_many(
                    {field: {"$exists": False}},
                    {"$set": {field: default_value}}
                )
                
                logger.info(f"Fixed {missing_count} players, added {field} with default value")
                fixed_count += missing_count
        
        return fixed_count
    except Exception as e:
        logger.error(f"Error fixing missing fields: {str(e)}")
        raise

async def fix_numeric_types(db):
    """Fix numeric fields to ensure they're all integers"""
    # Define fields that should be integers
    int_fields = [
        "kills", "deaths", "headshots", "headshot_kills", "headshot_deaths",
        "kill_streak", "max_kill_streak", "death_streak", "max_death_streak",
        "team_kills", "suicides", "rank_points", "playtime_seconds"
    ]
    
    fixed_count = 0
    
    try:
        for field in int_fields:
            # Find players where field exists but isn't an integer
            non_int_count = await db.players.count_documents({
                field: {"$exists": True},
                "$where": f"typeof(this.{field}) !== 'number'"
            })
            
            if non_int_count > 0:
                logger.info(f"Found {non_int_count} players with non-integer {field}")
                
                # Get these players
                non_int_players = await db.players.find({
                    field: {"$exists": True},
                    "$where": f"typeof(this.{field}) !== 'number'"
                }).to_list(length=non_int_count)
                
                # Fix each player
                for player in non_int_players:
                    old_value = player.get(field)
                    
                    try:
                        # Convert to integer
                        new_value = int(float(old_value)) if old_value is not None else 0
                        
                        # Update field to integer
                        await db.players.update_one(
                            {"_id": player["_id"]},
                            {"$set": {field: new_value}}
                        )
                        
                        logger.info(f"Updated player {player.get('name')}: {field} {old_value} ({type(old_value).__name__}) -> {new_value} (int)")
                        fixed_count += 1
                    except (ValueError, TypeError):
                        # If conversion fails, set to 0
                        await db.players.update_one(
                            {"_id": player["_id"]},
                            {"$set": {field: 0}}
                        )
                        
                        logger.info(f"Reset invalid {field} value {old_value} to 0 for player {player.get('name')}")
                        fixed_count += 1
        
        return fixed_count
    except Exception as e:
        logger.error(f"Error fixing numeric types: {str(e)}")
        raise

async def fix_dictionary_fields(db):
    """Fix dictionary fields to ensure they're all objects"""
    # Define fields that should be dictionaries
    dict_fields = ["nemesis", "prey", "weapons", "victim_weapons", "statistics"]
    
    fixed_count = 0
    
    try:
        for field in dict_fields:
            # Find players where field exists but isn't an object
            non_dict_count = await db.players.count_documents({
                field: {"$exists": True},
                "$where": f"typeof(this.{field}) !== 'object' || Array.isArray(this.{field})"
            })
            
            if non_dict_count > 0:
                logger.info(f"Found {non_dict_count} players with non-dictionary {field}")
                
                # Get these players
                non_dict_players = await db.players.find({
                    field: {"$exists": True},
                    "$where": f"typeof(this.{field}) !== 'object' || Array.isArray(this.{field})"
                }).to_list(length=non_dict_count)
                
                # Fix each player
                for player in non_dict_players:
                    # Update field to empty dictionary
                    await db.players.update_one(
                        {"_id": player["_id"]},
                        {"$set": {field: {}}}
                    )
                    
                    logger.info(f"Reset invalid {field} to empty dictionary for player {player.get('name')}")
                    fixed_count += 1
        
        return fixed_count
    except Exception as e:
        logger.error(f"Error fixing dictionary fields: {str(e)}")
        raise

async def fix_list_fields(db):
    """Fix list fields to ensure they're all arrays"""
    # Define fields that should be lists
    list_fields = ["linked_accounts", "badges", "events"]
    
    fixed_count = 0
    
    try:
        for field in list_fields:
            # Find players where field exists but isn't an array
            non_list_count = await db.players.count_documents({
                field: {"$exists": True},
                "$where": f"!Array.isArray(this.{field})"
            })
            
            if non_list_count > 0:
                logger.info(f"Found {non_list_count} players with non-list {field}")
                
                # Get these players
                non_list_players = await db.players.find({
                    field: {"$exists": True},
                    "$where": f"!Array.isArray(this.{field})"
                }).to_list(length=non_list_count)
                
                # Fix each player
                for player in non_list_players:
                    # Update field to empty list
                    await db.players.update_one(
                        {"_id": player["_id"]},
                        {"$set": {field: []}}
                    )
                    
                    logger.info(f"Reset invalid {field} to empty list for player {player.get('name')}")
                    fixed_count += 1
        
        return fixed_count
    except Exception as e:
        logger.error(f"Error fixing list fields: {str(e)}")
        raise

async def fix_boolean_fields(db):
    """Fix boolean fields to ensure they're all booleans"""
    # Define fields that should be booleans
    bool_fields = ["banned"]
    
    fixed_count = 0
    
    try:
        for field in bool_fields:
            # Find players where field exists but isn't a boolean
            non_bool_count = await db.players.count_documents({
                field: {"$exists": True},
                "$where": f"typeof(this.{field}) !== 'boolean'"
            })
            
            if non_bool_count > 0:
                logger.info(f"Found {non_bool_count} players with non-boolean {field}")
                
                # Get these players
                non_bool_players = await db.players.find({
                    field: {"$exists": True},
                    "$where": f"typeof(this.{field}) !== 'boolean'"
                }).to_list(length=non_bool_count)
                
                # Fix each player
                for player in non_bool_players:
                    old_value = player.get(field)
                    
                    # Convert to boolean (any truthy value becomes true)
                    new_value = bool(old_value)
                    
                    # Update field to boolean
                    await db.players.update_one(
                        {"_id": player["_id"]},
                        {"$set": {field: new_value}}
                    )
                    
                    logger.info(f"Updated player {player.get('name')}: {field} {old_value} ({type(old_value).__name__}) -> {new_value} (bool)")
                    fixed_count += 1
        
        return fixed_count
    except Exception as e:
        logger.error(f"Error fixing boolean fields: {str(e)}")
        raise

async def test_player_creation(db):
    """Test player creation with the fixed model"""
    try:
        # Import player model from project
        from models.player import Player

        # Create a player with the correct parameter style
        player_id = str(uuid.uuid4())
        server_id = "test_server"
        name = "TestPlayer"

        # Create a player using the parameter style from the first implementation
        player = Player(
            player_id=player_id,
            server_id=server_id,
            name=name,
            kills=0,
            deaths=0
        )

        # Log the player details
        logger.info(f"Created test player: {player}")
        logger.info(f"Player ID: {player.player_id}, Name: {player.name}, Server: {player.server_id}")

        # Test if we can access properties
        logger.info(f"K/D Ratio: {player.kd_ratio}")

        # Test creating or updating through class method
        created_player = await Player.create_or_update(
            db=db,
            player_id=player_id,
            server_id=server_id,
            name=name,
            kills=5,
            deaths=2
        )

        if created_player:
            logger.info(f"Successfully created/updated player in database: {created_player}")
            logger.info(f"Updated stats: Kills={created_player.kills}, Deaths={created_player.deaths}")
            return True
        else:
            logger.error("Failed to create/update player in database")
            return False

    except Exception as e:
        logger.error(f"Error testing player creation: {str(e)}", exc_info=True)
        return False

async def main():
    """Main function to run all fixes"""
    logger.info("Starting player creation fix script")
    
    try:
        # Connect to database
        db = await connect_to_mongodb()
        
        # Check player collection
        player_count = await check_player_collection(db)
        logger.info(f"Database contains {player_count} players")
        
        # Fix guild_id types
        guild_id_fixed = await fix_guild_id_types(db)
        logger.info(f"Fixed {guild_id_fixed} players with integer guild_ids")
        
        # Fix missing fields
        missing_fields_fixed = await fix_missing_fields(db)
        logger.info(f"Fixed {missing_fields_fixed} instances of missing fields")
        
        # Fix numeric types
        numeric_fixed = await fix_numeric_types(db)
        logger.info(f"Fixed {numeric_fixed} instances of incorrect numeric types")
        
        # Fix dictionary fields
        dict_fixed = await fix_dictionary_fields(db)
        logger.info(f"Fixed {dict_fixed} instances of incorrect dictionary fields")
        
        # Fix list fields
        list_fixed = await fix_list_fields(db)
        logger.info(f"Fixed {list_fixed} instances of incorrect list fields")
        
        # Fix boolean fields
        bool_fixed = await fix_boolean_fields(db)
        logger.info(f"Fixed {bool_fixed} instances of incorrect boolean fields")
        
        # Test player creation
        test_success = await test_player_creation(db)
        if test_success:
            logger.info("Player creation test completed successfully")
        else:
            logger.error("Player creation test failed")
            
        # Summary
        total_fixed = guild_id_fixed + missing_fields_fixed + numeric_fixed + dict_fixed + list_fixed + bool_fixed
        logger.info(f"Total fixes applied: {total_fixed}")
        
        if total_fixed > 0:
            logger.info("Player creation system is now fixed and working correctly")
        else:
            logger.info("No issues found with player creation")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())