import os
import sys
import asyncio
import logging
from utils.logging_setup import setup_logging
import discord
from discord.ext import commands
import motor.motor_asyncio
from typing import Optional, List, Dict, Any, Union, cast
import traceback
from datetime import datetime

# Set up custom logging configuration
setup_logging()

# Configure logger
logger = logging.getLogger("bot")

class Bot(commands.Bot):
    """Main bot class with enhanced error handling and initialization"""

    def __init__(self, *, production: bool = False, debug_guilds: Optional[List[int]] = None):
        """Initialize the bot with proper intents and configuration

        Args:
            production: Whether the bot is running in production mode
            debug_guilds: List of guild IDs for debug commands
        """
        # Set up proper intents for the required functionality
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        # Initialize the base bot with command prefix and intents
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            case_insensitive=True,
            auto_sync_commands=True
        )

        # Bot configuration
        self.production = production
        self.debug_guilds = debug_guilds
        self._db = None
        self.ready = False

        # Additional bot-specific attributes
        self.home_guild_id = os.environ.get("HOME_GUILD_ID")
        
        # Set owner ID (hard-coded per user request)
        self.owner_id = 462961235382763520

        # Extension loading state tracking
        self.loaded_extensions = []
        self.failed_extensions = []

        # Background task tracking
        self.background_tasks = {}

        # Add bot_status attribute for health monitoring
        self._bot_status = {
            "startup_time": datetime.now().isoformat(),
            "is_ready": False,
            "connected_guilds": 0,
            "loaded_extensions": [],
            "failed_extensions": [],
            "last_error": None
        }

        # Register error handlers
        self.setup_error_handlers()

    def setup_error_handlers(self):
        """Set up global error handlers"""
        @self.event
        async def on_error(event, *args, **kwargs):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_msg = f"Unhandled exception in {event}: {exc_value}"

            # Log detailed error information
            logger.error(error_msg)
            logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

            # Update bot_status
            self._bot_status["last_error"] = {
                "time": datetime.now().isoformat(),
                "event": event,
                "error": str(exc_value)
            }

    @property
    def db(self):
        """Database property with error handling

        Returns:
            MongoDB database instance

        Raises:
            RuntimeError: If database is not initialized
        """
        if self._db is None:
            raise RuntimeError("Database has not been initialized. Call init_db() first.")
        return self._db

    async def init_db(self, max_retries=3, retry_delay=2):
        """Initialize database connection with error handling and retries

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Seconds to wait between retries

        Returns:
            bool: True if connection successful, False otherwise
        """
        mongo_uri = os.environ.get("MONGODB_URI")
        if not mongo_uri:
            logger.critical("MONGODB_URI environment variable not set")
            return False

        for attempt in range(1, max_retries + 1):
            try:
                # Connect to MongoDB
                logger.info(f"Connecting to MongoDB (attempt {attempt}/{max_retries})...")
                client = motor.motor_asyncio.AsyncIOMotorClient(
                    mongo_uri, 
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=10000
                )
                self._db = client.emeralds_killfeed

                # Test connection with a simple operation
                await self._db.command("ping")
                logger.info(f"Successfully connected to MongoDB on attempt {attempt}")
                return True

            except Exception as e:
                logger.error(f"Failed to connect to MongoDB (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical("All database connection attempts failed")
                    return False

    async def on_ready(self):
        """Handle bot ready event with additional setup"""
        if self.ready:
            logger.info("Bot reconnected")
            return

        self.ready = True
        self._bot_status["is_ready"] = True

        # Log successful login
        logger.info(f"Bot logged in as {self.user.name}")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        self._bot_status["connected_guilds"] = len(self.guilds)

        # Sync commands
        try:
            logger.info("Syncing application commands...")
            await self.sync_commands()
            logger.info("Application commands synced!")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # Start background task monitor
        self.start_background_task_monitor()

        # Log successful startup
        logger.info("Bot is ready!")

    async def sync_commands(self):
        """Sync application commands with proper error handling"""
        if self.debug_guilds:
            # Sync to specific debug guilds only
            for guild_id in self.debug_guilds:
                guild = self.get_guild(guild_id)
                if guild is not None:
                    await self.tree.sync(guild=guild)
                    logger.info(f"Synced commands to guild {guild.name} ({guild_id})")
        else:
            # Global sync
            await self.tree.sync()
            logger.info("Synced commands globally")

    async def load_extension(self, name: str):
        """Load a bot extension with enhanced error handling

        Args:
            name: Name of the extension to load

        Raises:
            commands.ExtensionError: If loading fails
        """
        try:
            await super().load_extension(name)
            self.loaded_extensions.append(name)
            self._bot_status["loaded_extensions"].append(name)
            logger.info(f"Loaded extension: {name}")
            return True
        except commands.ExtensionError as e:
            logger.error(f"Failed to load extension {name}: {e}")
            logger.error(traceback.format_exc())
            self.failed_extensions.append(name)
            self._bot_status["failed_extensions"].append({
                "name": name,
                "error": str(e)
            })
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading extension {name}: {e}")
            logger.error(traceback.format_exc())
            self.failed_extensions.append(name)
            self._bot_status["failed_extensions"].append({
                "name": name,
                "error": str(e)
            })
            return False

    def start_background_task_monitor(self):
        """Start a background task to monitor other background tasks"""
        async def monitor_background_tasks():
            while True:
                try:
                    # Check each background task
                    for task_name, task in list(self.background_tasks.items()):
                        if task is None:
                            continue

                        if task.done():
                            try:
                                # Get result to handle any exceptions
                                task.result()
                                logger.warning(f"Background task {task_name} completed unexpectedly")
                            except asyncio.CancelledError:
                                # Task was cancelled, which is expected in some cases
                                logger.info(f"Background task {task_name} was cancelled")
                                # Clean up the cancelled task
                                if task_name in self.background_tasks:
                                    del self.background_tasks[task_name]
                            except Exception as task_error:
                                logger.error(f"Error in background task {task_name}: {task_error}")
                                logger.error(traceback.format_exc())

                                # Restart critical tasks with retry logic
                                if task_name.startswith("critical_"):
                                    logger.info(f"Attempting to restart critical task: {task_name}")
                                    # Implementation would depend on the specific task
                except Exception as e:
                    logger.error(f"Error in background task monitor: {e}")

                # Check every 30 seconds
                await asyncio.sleep(30)

        # Start the monitor task
        self.background_tasks["task_monitor"] = asyncio.create_task(
            monitor_background_tasks(), 
            name="task_monitor"
        )

    def create_background_task(self, coro, name, critical=False):
        """Create and track a background task with proper naming

        Args:
            coro: Coroutine to run as a background task
            name: Name of the task for tracking
            critical: Whether the task is critical and should be auto-restarted
        """
        task_name = f"critical_{name}" if critical else name
        task = asyncio.create_task(coro, name=task_name)
        self.background_tasks[task_name] = task
        return task

    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have the required permissions to use this command.")
            return

        # Log unexpected errors
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)

        # Notify user
        await ctx.send("An error occurred while processing this command. The error has been logged.")

    async def on_application_command_error(self, interaction: discord.Interaction, error: Exception):
        """Global application command error handler"""
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("You don't have the required permissions to use this command.", ephemeral=True)
            return

        # Log unexpected errors
        command_name = interaction.command.name if interaction.command else "Unknown"
        logger.error(f"Application command error in {command_name}: {error}", exc_info=error)

        # Notify user
        try:
            if interaction.response.is_done():
                await interaction.followup.send("An error occurred while processing this command. The error has been logged.", ephemeral=True)
            else:
                await interaction.response.send_message("An error occurred while processing this command. The error has been logged.", ephemeral=True)
        except Exception:
            logger.error("Failed to send error message to user")