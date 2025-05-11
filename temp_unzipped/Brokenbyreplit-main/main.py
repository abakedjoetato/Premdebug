
#!/usr/bin/env python3
"""
Main entry point for the Discord bot
This script handles both development and production modes
"""
import os
import sys
import asyncio
import logging
import traceback
from logging.handlers import RotatingFileHandler
from bot import Bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=10000000, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bot_main")

# Extensions to load
EXTENSIONS = [
    "cogs.help",
    "cogs.admin",
    "cogs.csv_processor",
    "cogs.log_processor",
    "cogs.killfeed",
    "cogs.stats",
    "cogs.rivalries",
    "cogs.bounties",
    "cogs.economy",
    "cogs.setup",
    "cogs.events",
    "cogs.premium",
    "cogs.player_links",
    "cogs.factions"
]

async def main():
    """Initialize and run the bot with proper error handling"""
    try:
        # Ensure environment variables are loaded
        if not os.environ.get("DISCORD_TOKEN"):
            logger.error("DISCORD_TOKEN environment variable not set")
            return 1

        # Initialize the bot
        logger.info("Initializing bot...")
        bot = Bot()

        # Connect to database
        logger.info("Connecting to database...")
        db_success = await bot.init_db()
        if db_success is None:
            logger.error("Failed to connect to database")
            return 1

        # Load all extensions
        logger.info("Loading extensions...")
        failed_extensions = []
        for extension in EXTENSIONS:
            try:
                await bot.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                failed_extensions.append(extension)
        
        if failed_extensions:
            logger.warning(f"Failed to load {len(failed_extensions)} extensions: {', '.join(failed_extensions)}")
            if len(failed_extensions) == len(EXTENSIONS):
                logger.critical("All extensions failed to load - aborting")
                return 1
        
        # Start the bot
        logger.info("Starting bot...")
        await bot.start(os.environ["DISCORD_TOKEN"])
        return 0
    except Exception as e:
        logger.critical(f"Fatal error during bot startup: {e}", exc_info=True)
        return 1

# Entry point
if __name__ == "__main__":
    # Handle KeyboardInterrupt gracefully
    exit_code = 1
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
        exit_code = 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        exit_code = 1
    
    sys.exit(exit_code)
