import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Known server mappings (server_id -> numeric_id)
KNOWN_SERVERS = {
    "5251382d-8bce-4abd-8bcb-cdef73698a46": "7020",  # Emerald EU
    "dc1f7c09-dabb-4607-a10d-353f66f1ea20": "7021",  # Emerald US
    "681ef676-f9f6-2ab1-6462-2334000000": "7022",    # Emerald AU
    "681ef676-2c2d-2cd8-7588-2d2a000000": "7023",    # Emerald Asia
    # Add more known mappings here
}

def identify_server(server_id: str, hostname: Optional[str] = None, 
                   server_name: Optional[str] = None, guild_id: Optional[str] = None) -> Tuple[str, bool]:
    """
    Identify a server and return its numeric ID using multiple methods of identification.

    Args:
        server_id: The UUID or numeric ID of the server
        hostname: Optional hostname of the server
        server_name: Optional name of the server
        guild_id: Optional Discord guild ID associated with the server

    Returns:
        Tuple[str, bool]: (numeric_id, is_known_mapping)
            - numeric_id: The numeric ID of the server
            - is_known_mapping: True if this was a known mapping, False if derived
    """
    # First check if this is already a numeric ID
    if server_id is not None and server_id.isdigit():
        logger.debug(f"Server ID {server_id} appears to already be numeric")
        return server_id, False

    # Check if we have a known mapping
    if server_id in KNOWN_SERVERS:
        numeric_id = KNOWN_SERVERS[server_id]
        logger.debug(f"Found known mapping for {server_id} -> {numeric_id}")
        return numeric_id, True

    # Try to extract a numeric part from the UUID
    if server_id is not None:
        # Extract a numeric value from the first part of the UUID
        uuid_parts = server_id.split('-')
        if uuid_parts:
            # Convert the first hex part to a number and use the last 4 digits
            try:
                hex_value = uuid_parts[0]
                numeric_value = int(hex_value, 16)
                # Use the last 4 digits, with a minimum of 1000
                derived_id = max(1000, numeric_value % 10000)
                logger.debug(f"Derived numeric ID {derived_id} from {server_id}")
                return str(derived_id), False
            except (ValueError, IndexError):
                logger.debug(f"Could not derive numeric ID from {server_id}")

    # If hostname is provided, try to extract numeric part
    if hostname:
        # Look for numbers in the hostname
        numbers = re.findall(r'\d+', hostname)
        if numbers:
            # Use the last group of numbers found
            derived_id = numbers[-1]
            logger.debug(f"Extracted numeric ID {derived_id} from hostname {hostname}")
            return derived_id, False

    # Fall back to using the original server_id
    logger.debug(f"Using original server_id as fallback: {server_id}")
    return server_id, False