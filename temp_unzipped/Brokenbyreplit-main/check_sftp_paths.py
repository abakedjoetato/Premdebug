"""
SFTP Path Checker

This script checks the available files and directories on the SFTP server.
It helps diagnose path-related issues for the log processor.
"""
import asyncio
import logging
import os
import asyncssh
from pprint import pformat

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('sftp_check')

async def list_directory_recursive(sftp, path, max_depth=3, current_depth=0):
    """
    List directory contents recursively up to max_depth
    """
    if current_depth > max_depth:
        return []
    
    try:
        # List directory contents
        items = await sftp.listdir(path)
        result = []
        
        for item in items:
            item_path = f"{path}/{item}"
            try:
                # Get file info
                info = await sftp.stat(item_path)
                
                if info.type == asyncssh.FILETYPE_DIRECTORY:
                    # Add directory and recursively list contents
                    result.append({
                        "type": "directory",
                        "path": item_path,
                        "contents": await list_directory_recursive(sftp, item_path, max_depth, current_depth + 1)
                    })
                else:
                    # Add file
                    result.append({
                        "type": "file",
                        "path": item_path,
                        "size": info.size
                    })
            except asyncssh.SFTPError as e:
                result.append({
                    "type": "error",
                    "path": item_path,
                    "error": str(e)
                })
        
        return result
    
    except asyncssh.SFTPError as e:
        logger.error(f"Error listing directory {path}: {e}")
        return []

async def check_sftp_paths():
    """Check SFTP paths for the server"""
    try:
        # Get server info from MongoDB
        import motor.motor_asyncio
        client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('MONGODB_URI'))
        db = client.emeralds_killfeed
        
        # Get server info
        server = await db.servers.find_one({"sftp_enabled": True})
        if server is None:
            logger.error("No SFTP-enabled server found in the database")
            return False
        
        logger.info(f"Using server: {server.get('server_name')} ({server.get('_id')})")
        logger.info(f"SFTP config: {server.get('sftp_host')}:{server.get('sftp_port')} ({server.get('sftp_username')})")
        
        # Extract server details
        hostname = server.get('sftp_host')
        port = server.get('sftp_port', 22)
        username = server.get('sftp_username')
        password = server.get('sftp_password')
        server_id = server.get('server_id')
        original_server_id = server.get('original_server_id')
        
        logger.info(f"Connecting to SFTP server: {hostname}:{port} as {username}")
        logger.info(f"Server ID: {server_id}, Original ID: {original_server_id}")
        
        # Connect to SFTP server
        async with asyncssh.connect(
            hostname, 
            port=port,
            username=username,
            password=password,
            known_hosts=None  # Skip host key verification for testing
        ) as conn:
            logger.info("Connected to SFTP server successfully")
            
            # Create SFTP client
            async with conn.start_sftp_client() as sftp:
                logger.info("SFTP client started successfully")
                
                # List root directory
                logger.info("Listing root directory...")
                root_items = await list_directory_recursive(sftp, '/', max_depth=1)
                logger.info(f"Root directory contents:\n{pformat(root_items)}")
                
                # Check expected paths
                for path in [
                    f"/79.127.236.1_{original_server_id}",
                    f"/79.127.236.1_{original_server_id}/Logs",
                    f"/79.127.236.1_{original_server_id}/actual1",
                    f"/79.127.236.1_{original_server_id}/actual1/deathlogs",
                    "/Logs",
                    f"/{original_server_id}",
                    f"/{original_server_id}/game",
                    f"/{original_server_id}/game/Logs"
                ]:
                    try:
                        logger.info(f"Checking path: {path}")
                        info = await sftp.stat(path)
                        logger.info(f"Path {path} exists, type: {info.type}")
                        
                        if info.type == asyncssh.FILETYPE_DIRECTORY:
                            items = await sftp.listdir(path)
                            logger.info(f"Directory contents: {items}")
                    except asyncssh.SFTPError as e:
                        logger.warning(f"Path {path} does not exist or is not accessible: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking SFTP paths: {e}")
        return False

async def main():
    """Main entry point"""
    logger.info("Checking SFTP paths...")
    success = await check_sftp_paths()
    if success:
        logger.info("SFTP path check completed successfully")
    else:
        logger.error("SFTP path check failed")

if __name__ == "__main__":
    asyncio.run(main())