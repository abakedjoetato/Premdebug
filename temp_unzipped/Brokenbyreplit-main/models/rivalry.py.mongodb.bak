"""
Rivalry model for tracking player-vs-player relationships
"""
import logging
from typing import Dict, Any, List, Optional, Union, cast
from datetime import datetime

from models.base_model import BaseModel

logger = logging.getLogger("rivalry_model")

class Rivalry(BaseModel):
    """Rivalry model with improved type handling and validation"""

    collection_name = "rivalries"

    @classmethod
    async def create(cls, db, data: Dict[str, Any]) -> 'Rivalry':
        """
        Create a new rivalry with proper validation

        Args:
            db: Database connection
            data: Rivalry data

        Returns:
            New Rivalry instance

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ["player1_id", "player2_id", "guild_id", "server_id"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Ensure guild_id is stored as a string
        if "guild_id" in data:
            data["guild_id"] = str(data["guild_id"])

        # Initialize default values
        now = datetime.utcnow()

        defaults = {
            "player1_kills": 0,
            "player2_kills": 0,
            "player1_headshots": 0,
            "player2_headshots": 0,
            "player1_weapons": {},
            "player2_weapons": {},
            "last_updated": now,
            "created_at": now,
            "status": "active",
            "intensity": 0,  # 0-100 scale of rivalry intensity
            "last_kill_timestamp": None,
            "last_killer_id": None,
            "last_killer_weapon": None,
            "history": []  # Recent kill events
        }

        # Merge defaults with provided data
        for key, value in defaults.items():
            if key not in data:
                data[key] = value

        # Create the rivalry in the database
        try:
            result = await db[cls.collection_name].insert_one(data)
            data["_id"] = result.inserted_id
            logger.info(f"Created rivalry between {data['player1_id']} and {data['player2_id']} (guild={data['guild_id']})")
            return cls(db, data)
        except Exception as e:
            logger.error(f"Failed to create rivalry: {str(e)}")
            raise

    @classmethod
    async def find_between_players(cls, db, player1_id: str, player2_id: str, guild_id: Union[str, int], server_id: str) -> Optional['Rivalry']:
        """
        Find a rivalry between two players

        Args:
            db: Database connection
            player1_id: First player ID
            player2_id: Second player ID
            guild_id: Discord guild ID
            server_id: Game server ID

        Returns:
            Rivalry instance or None if not found
        """
        # Convert guild_id to string for consistency
        guild_id_str = str(guild_id)

        # Try both player orders
        rivalry_data = await db[cls.collection_name].find_one({
            "player1_id": player1_id,
            "player2_id": player2_id,
            "guild_id": guild_id_str,
            "server_id": server_id
        })

        if not rivalry_data:
            # Try reversed player order
            rivalry_data = await db[cls.collection_name].find_one({
                "player1_id": player2_id,
                "player2_id": player1_id,
                "guild_id": guild_id_str,
                "server_id": server_id
            })

        if rivalry_data:
            return cls(db, rivalry_data)
        return None

    @classmethod
    async def find_or_create(cls, db, player1_id: str, player2_id: str, guild_id: Union[str, int], server_id: str) -> tuple['Rivalry', bool]:
        """
        Find a rivalry or create if not found

        Args:
            db: Database connection
            player1_id: First player ID
            player2_id: Second player ID
            guild_id: Discord guild ID
            server_id: Game server ID

        Returns:
            Tuple of (Rivalry, created) where created is True if a new rivalry was created
        """
        # Convert guild_id to string for consistency
        guild_id_str = str(guild_id)

        # Find existing rivalry
        rivalry = await cls.find_between_players(db, player1_id, player2_id, guild_id_str, server_id)

        if rivalry:
            return rivalry, False
        else:
            # Create new rivalry
            rivalry_data = {
                "player1_id": player1_id,
                "player2_id": player2_id,
                "guild_id": guild_id_str,
                "server_id": server_id
            }
            rivalry = await cls.create(db, rivalry_data)
            return rivalry, True

    @classmethod
    async def find_for_player(cls, db, player_id: str, guild_id: Union[str, int], server_id: Optional[str] = None, limit: int = 10) -> List['Rivalry']:
        """
        Find all rivalries for a player

        Args:
            db: Database connection
            player_id: Player ID
            guild_id: Discord guild ID
            server_id: Optional game server ID
            limit: Maximum number of rivalries to return

        Returns:
            List of Rivalry instances
        """
        # Convert guild_id to string for consistency
        guild_id_str = str(guild_id)

        # Build query
        query = {
            "$or": [
                {"player1_id": player_id},
                {"player2_id": player_id}
            ],
            "guild_id": guild_id_str
        }

        # Add server_id if provided
        if server_id:
            query["server_id"] = server_id

        # Find rivalries
        cursor = db[cls.collection_name].find(query).sort("intensity", -1).limit(limit)

        rivalries = []
        async for doc in cursor:
            rivalries.append(cls(db, doc))

        return rivalries

    async def update(self, data: Dict[str, Any]) -> 'Rivalry':
        """
        Update rivalry

        Args:
            data: Data to update

        Returns:
            Updated Rivalry instance
        """
        # Don't allow updating critical fields
        for field in ["_id", "guild_id", "player1_id", "player2_id", "server_id"]:
            if field in data:
                del data[field]

        # Set last_updated timestamp
        data["last_updated"] = datetime.utcnow()

        # Update in database
        try:
            await self.db[self.collection_name].update_one(
                {"_id": self.data["_id"]},
                {"$set": data}
            )

            # Update local data
            for key, value in data.items():
                self.data[key] = value

            return self
        except Exception as e:
            logger.error(f"Failed to update rivalry: {str(e)}")
            raise

    async def record_kill(self, killer_id: str, victim_id: str, weapon: Optional[str] = None, headshot: bool = False) -> 'Rivalry':
        """
        Record a kill in this rivalry

        Args:
            killer_id: ID of the killer
            victim_id: ID of the victim
            weapon: Weapon used (optional)
            headshot: Whether it was a headshot

        Returns:
            Updated Rivalry instance

        Raises:
            ValueError: If killer or victim is not part of this rivalry
        """
        # Validate killer and victim
        if killer_id not in [self.data["player1_id"], self.data["player2_id"]]:
            raise ValueError(f"Killer {killer_id} is not part of this rivalry")

        if victim_id not in [self.data["player1_id"], self.data["player2_id"]]:
            raise ValueError(f"Victim {victim_id} is not part of this rivalry")

        # Determine which player is the killer
        is_player1_killer = killer_id == self.data["player1_id"]

        # Build update data
        now = datetime.utcnow()
        data = {
            "last_updated": now,
            "last_kill_timestamp": now,
            "last_killer_id": killer_id,
            "last_killer_weapon": weapon
        }

        # Update kill counts
        if is_player1_killer:
            data["player1_kills"] = self.data.get("player1_kills", 0) + 1

            # Update headshot count if applicable
            if headshot:
                data["player1_headshots"] = self.data.get("player1_headshots", 0) + 1

            # Update weapon stats if provided
            if weapon:
                # Initialize weapons dict if needed
                player1_weapons = self.data.get("player1_weapons", {})

                # Initialize this weapon if needed
                if weapon not in player1_weapons:
                    player1_weapons[weapon] = 0

                # Increment weapon usage
                player1_weapons[weapon] += 1
                data["player1_weapons"] = player1_weapons
        else:
            data["player2_kills"] = self.data.get("player2_kills", 0) + 1

            # Update headshot count if applicable
            if headshot:
                data["player2_headshots"] = self.data.get("player2_headshots", 0) + 1

            # Update weapon stats if provided
            if weapon:
                # Initialize weapons dict if needed
                player2_weapons = self.data.get("player2_weapons", {})

                # Initialize this weapon if needed
                if weapon not in player2_weapons:
                    player2_weapons[weapon] = 0

                # Increment weapon usage
                player2_weapons[weapon] += 1
                data["player2_weapons"] = player2_weapons

        # Calculate rivalry intensity
        total_kills = (self.data.get("player1_kills", 0) + data.get("player1_kills", 0) + 
                      self.data.get("player2_kills", 0) + data.get("player2_kills", 0))

        # Function to calculate intensity based on kill distribution and recency
        intensity = self._calculate_intensity(
            player1_kills=self.data.get("player1_kills", 0) + data.get("player1_kills", 0) - self.data.get("player1_kills", 0),
            player2_kills=self.data.get("player2_kills", 0) + data.get("player2_kills", 0) - self.data.get("player2_kills", 0),
            total_kills=total_kills,
            last_kill_timestamp=now
        )
        data["intensity"] = intensity

        # Add to history (maintain last 10 kills)
        history = self.data.get("history", [])
        history.append({
            "killer_id": killer_id,
            "victim_id": victim_id,
            "weapon": weapon,
            "headshot": headshot,
            "timestamp": now
        })

        # Keep only last 10 kills
        if len(history) > 10:
            history = history[-10:]

        data["history"] = history

        # Update rivalry
        return await self.update(data)

    def _calculate_intensity(self, player1_kills: int, player2_kills: int, total_kills: int, last_kill_timestamp: datetime) -> int:
        """
        Calculate rivalry intensity

        Args:
            player1_kills: Player 1 kill count
            player2_kills: Player 2 kill count
            total_kills: Total kill count
            last_kill_timestamp: Timestamp of last kill

        Returns:
            Intensity score (0-100)
        """
        # Base intensity from total kills
        if total_kills < 5:
            base_score = total_kills * 5  # 0-25 for 0-5 kills
        elif total_kills < 20:
            base_score = 25 + (total_kills - 5)  # 25-40 for 5-20 kills
        else:
            base_score = 40 + min(20, (total_kills - 20) // 2)  # 40-60 for 20+ kills

        # Bonus for balanced rivalry (both players have kills)
        if player1_kills > 0 and player2_kills > 0:
            # Calculate how balanced the rivalry is (0-20)
            min_kills = min(player1_kills, player2_kills)
            max_kills = max(player1_kills, player2_kills)

            # Perfect balance = 20 points, completely one-sided = 0 points
            if max_kills > 0:
                balance_score = int(20 * (min_kills / max_kills))
            else:
                balance_score = 0

            base_score += balance_score

        # Recency bonus (max 20 points)
        now = datetime.utcnow()
        days_since_last_kill = (now - last_kill_timestamp).total_seconds() / (24 * 3600)

        if days_since_last_kill < 1:
            recency_score = 20  # Last 24 hours
        elif days_since_last_kill < 3:
            recency_score = 15  # Last 3 days
        elif days_since_last_kill < 7:
            recency_score = 10  # Last week
        elif days_since_last_kill < 30:
            recency_score = 5   # Last month
        else:
            recency_score = 0   # Older than a month

        base_score += recency_score

        # Ensure score is within 0-100 range
        return max(0, min(100, base_score))

    def is_nemesis(self, player_id: str) -> bool:
        """
        Check if a player is the nemesis (has more kills) in this rivalry

        Args:
            player_id: Player ID to check

        Returns:
            True if player is the nemesis, False otherwise
        """
        if player_id not in [self.data["player1_id"], self.data["player2_id"]]:
            return False

        if player_id == self.data["player1_id"]:
            return self.data.get("player1_kills", 0) > self.data.get("player2_kills", 0)
        else:
            return self.data.get("player2_kills", 0) > self.data.get("player1_kills", 0)

    def get_nemesis_id(self) -> Optional[str]:
        """
        Get the ID of the nemesis (player with more kills) in this rivalry

        Returns:
            Player ID of the nemesis, or None if kills are equal
        """
        player1_kills = self.data.get("player1_kills", 0)
        player2_kills = self.data.get("player2_kills", 0)

        if player1_kills > player2_kills:
            return self.data["player1_id"]
        elif player2_kills > player1_kills:
            return self.data["player2_id"]
        else:
            return None  # Equal kills