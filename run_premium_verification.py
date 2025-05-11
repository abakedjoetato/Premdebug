
#!/usr/bin/env python3
"""
Script to execute the comprehensive premium verification.
This runs all tests needed to identify premium validation issues.
"""
import asyncio
import logging
import sys
from verify_premium_fixes import verify_all_premium_fixes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    # Get guild ID from command line arguments if provided
    guild_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    logger.info("Starting premium validation verification")
    await verify_all_premium_fixes(guild_id)
    logger.info("Premium validation verification completed")

if __name__ == "__main__":
    asyncio.run(main())
