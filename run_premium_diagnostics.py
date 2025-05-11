
#!/usr/bin/env python3
"""
Run the premium tier diagnostics script to verify fixes are working correctly.
"""
import asyncio
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("diagnostic_runner")

# Run the diagnostic script with the specified guild ID
if len(sys.argv) > 1:
    guild_id = sys.argv[1]
    logger.info(f"Running premium diagnostic with guild ID: {guild_id}")
    subprocess.run(["python", "verify_premium_fixes.py", guild_id])
else:
    logger.info("Running premium diagnostic with default guild ID")
    subprocess.run(["python", "verify_premium_fixes.py"])
#!/usr/bin/env python3
"""
Run the premium tier diagnostics script to verify fixes are working correctly.
"""
import asyncio
import logging
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("diagnostic_runner")

# Run the diagnostic script with the specified guild ID
if len(sys.argv) > 1:
    guild_id = sys.argv[1]
    logger.info(f"Running premium diagnostic with guild ID: {guild_id}")
    subprocess.run(["python", "verify_premium_fixes.py", guild_id])
else:
    logger.info("Running premium diagnostic with default guild ID")
    subprocess.run(["python", "verify_premium_fixes.py"])
