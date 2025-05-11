"""
# module: verify_csv_fixes
Verify CSV file discovery and parsing fixes

This script directly tests the CSV file discovery and parsing
to ensure our fixes are working correctly.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('csv_test.log')
    ]
)

logger = logging.getLogger('verify_csv_fixes')

# Imports for testing
from utils.sftp import SFTPManager
from utils.file_discovery import FileDiscovery
from utils.stable_csv_parser import StableCSVParser

# Test configuration - Replace with your own server config if needed
TEST_SERVER_CONFIG = {
    'hostname': 'your.server.hostname.com',  # Will be overridden with actual values
    'port': 22,  # Will be overridden with actual values
    'username': 'username',  # Will be overridden with actual values
    'password': 'password',  # Will be overridden with actual values
    'server_id': 'test-server-id',  # Will be overridden with actual values
    'original_server_id': '12345',  # Will be overridden with actual values
    'base_path': 'path/to/deathlogs'  # Will be overridden with actual values
}

async def verify_discovery(config: Dict[str, Any]) -> bool:
    """Verify the CSV file discovery process"""
    logger.info("=== VERIFYING CSV FILE DISCOVERY ===")
    
    # Create an SFTP client with the test config
    sftp = SFTPManager(
        hostname=config['hostname'],
        port=config['port'],
        username=config['username'],
        password=config['password'],
        server_id=config['server_id'],
        original_server_id=config.get('original_server_id', '')
    )
    
    try:
        # Connect to the SFTP server
        connected = await sftp.connect()
        if not connected:
            logger.error("Failed to connect to SFTP server")
            return False
        
        logger.info("Connected to SFTP server")
        
        # Create a FileDiscovery instance
        file_discovery = FileDiscovery()
        
        # Test discovery in historical mode
        logger.info("Testing discovery in historical mode")
        start_date = datetime.now() - timedelta(days=30)
        
        # Discover CSV files
        csv_files, metadata = await file_discovery.discover_csv_files(
            sftp=sftp,
            server_id=config['server_id'],
            start_date=start_date,
            days_back=30,
            historical_mode=True
        )
        
        # Log the results
        logger.info(f"Found {len(csv_files)} CSV files in historical mode")
        logger.info(f"Discovery metadata: {metadata}")
        
        # Show the first few files
        if csv_files:
            logger.info("Sample discovered files:")
            for i, file in enumerate(csv_files[:5]):
                logger.info(f"  {i+1}. {file}")
                
                # Check if we can read this file's content
                try:
                    logger.info(f"Attempting to read file: {file}")
                    content = await sftp.read_file(file)
                    
                    # Handle different content types
                    if content is None:
                        logger.warning(f"    - Could not read file content (returned None)")
                        
                        # Check if file exists
                        logger.info(f"    - Checking if file exists: {file}")
                        file_info = await sftp.get_file_info(file)
                        if file_info:
                            logger.info(f"    - File info: {file_info}")
                        else:
                            logger.warning(f"    - File info not available")
                    elif isinstance(content, bytes):
                        size = len(content)
                        logger.info(f"    - Successfully read {size} bytes")
                        # Try to decode as text
                        try:
                            sample = content[:100].decode('utf-8')
                            logger.info(f"    - First 100 bytes as UTF-8: {sample}")
                        except Exception as e:
                            try:
                                # Try latin-1 as fallback
                                sample = content[:100].decode('latin-1')
                                logger.info(f"    - First 100 bytes as latin-1: {sample}")
                            except Exception:
                                logger.info(f"    - Could not decode as any encoding")
                                
                        # Try parsing with our parser
                        logger.info(f"    - Attempting to parse with StableCSVParser")
                        try:
                            csv_parser = StableCSVParser()
                            try:
                                content_str = content.decode('utf-8')
                            except:
                                try:
                                    content_str = content.decode('latin-1')
                                except:
                                    content_str = content.decode('ascii', errors='replace')
                                
                            events, total_lines = csv_parser.parse_file_content(
                                content=content_str,
                                file_path=file,
                                server_id=config['server_id'],
                                start_line=0
                            )
                            logger.info(f"    - Parser results: {len(events)} events from {total_lines} lines")
                            if events is not None:
                                logger.info(f"    - First event: {events[0]}")
                        except Exception as parse_error:
                            logger.error(f"    - Parser error: {parse_error}")
                            
                    elif isinstance(content, list):
                        lines = len(content)
                        logger.info(f"    - Successfully read {lines} lines")
                        if lines > 0:
                            sample_line = content[0]
                            if isinstance(sample_line, bytes):
                                try:
                                    sample_line = sample_line.decode('utf-8')
                                except:
                                    try:
                                        sample_line = sample_line.decode('latin-1')
                                    except:
                                        sample_line = str(sample_line)
                            logger.info(f"    - First line: {sample_line}")
                            
                        # Try parsing with our parser
                        logger.info(f"    - Attempting to parse with StableCSVParser")
                        try:
                            csv_parser = StableCSVParser()
                            content_str = '\n'.join(str(line) for line in content)
                            
                            events, total_lines = csv_parser.parse_file_content(
                                content=content_str,
                                file_path=file,
                                server_id=config['server_id'],
                                start_line=0
                            )
                            logger.info(f"    - Parser results: {len(events)} events from {total_lines} lines")
                            if events is not None:
                                logger.info(f"    - First event: {events[0]}")
                        except Exception as parse_error:
                            logger.error(f"    - Parser error: {parse_error}")
                    
                    elif isinstance(content, str):
                        size = len(content)
                        logger.info(f"    - Successfully read {size} characters")
                        logger.info(f"    - First 100 characters: {content[:100]}")
                        
                        # Try parsing with our parser
                        logger.info(f"    - Attempting to parse with StableCSVParser")
                        try:
                            csv_parser = StableCSVParser()
                            
                            events, total_lines = csv_parser.parse_file_content(
                                content=content,
                                file_path=file,
                                server_id=config['server_id'],
                                start_line=0
                            )
                            logger.info(f"    - Parser results: {len(events)} events from {total_lines} lines")
                            if events is not None:
                                logger.info(f"    - First event: {events[0]}")
                        except Exception as parse_error:
                            logger.error(f"    - Parser error: {parse_error}")
                            
                    else:
                        logger.info(f"    - Read content of type: {type(content)}")
                        logger.info(f"    - Content representation: {str(content)[:100]}")
                        
                except Exception as e:
                    logger.error(f"    - Error reading file: {e}")
                    
            if len(csv_files) > 5:
                logger.info(f"  ... and {len(csv_files) - 5} more")
        
        return len(csv_files) > 0
    
    except Exception as e:
        logger.error(f"Error in discovery verification: {e}")
        return False
    finally:
        # Disconnect from the SFTP server
        await sftp.disconnect()

async def verify_parsing(config: Dict[str, Any]) -> bool:
    """Verify the CSV file parsing process"""
    logger.info("=== VERIFYING CSV FILE PARSING ===")
    
    # Create an SFTP client with the test config
    sftp = SFTPManager(
        hostname=config['hostname'],
        port=config['port'],
        username=config['username'],
        password=config['password'],
        server_id=config['server_id'],
        original_server_id=config.get('original_server_id', '')
    )
    
    try:
        # Connect to the SFTP server
        connected = await sftp.connect()
        if not connected:
            logger.error("Failed to connect to SFTP server")
            return False
        
        logger.info("Connected to SFTP server")
        
        # Create a FileDiscovery instance
        file_discovery = FileDiscovery()
        
        # Discover CSV files
        csv_files, _ = await file_discovery.discover_csv_files(
            sftp=sftp,
            server_id=config['server_id'],
            start_date=datetime.now() - timedelta(days=30),
            days_back=30,
            historical_mode=True
        )
        
        if not csv_files:
            logger.error("No CSV files discovered to parse")
            return False
        
        logger.info(f"Found {len(csv_files)} CSV files to parse")
        
        # Create a StableCSVParser instance
        csv_parser = StableCSVParser()
        
        # Test parsing the first few files
        success_count = 0
        test_files = csv_files[:3] if len(csv_files) > 3 else csv_files
        
        for file_path in test_files:
            logger.info(f"Testing parsing of file: {file_path}")
            
            # Read the file content
            content = await sftp.read_file(file_path)
            if not content:
                logger.warning(f"Could not read content from file: {file_path}")
                continue
                
            # Convert content to string if needed
            if isinstance(content, bytes):
                try:
                    # Try UTF-8 first
                    content_str = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        # Then try Latin-1
                        content_str = content.decode('latin-1')
                    except UnicodeDecodeError:
                        # Fall back to ascii with replace
                        content_str = content.decode('ascii', errors='replace')
            elif isinstance(content, list):
                content_str = '\n'.join(content)
            else:
                content_str = str(content)
                
            logger.info(f"File content length: {len(content_str)} characters")
            
            # Parse the file content
            events, total_lines = csv_parser.parse_file_content(
                content=content_str,
                file_path=file_path,
                server_id=config['server_id'],
                start_line=0
            )
            
            # Log the results
            logger.info(f"Parsed {len(events)} events from {total_lines} lines in file: {file_path}")
            
            if events is not None:
                success_count += 1
                # Show the first few events
                logger.info("Sample parsed events:")
                for i, event in enumerate(events[:3]):
                    logger.info(f"  {i+1}. {event}")
                if len(events) > 3:
                    logger.info(f"  ... and {len(events) - 3} more")
            else:
                logger.warning(f"No events parsed from file: {file_path}")
        
        return success_count > 0
    
    except Exception as e:
        logger.error(f"Error in parsing verification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # Disconnect from the SFTP server
        await sftp.disconnect()

async def main() -> None:
    """Main entry point"""
    logger.info("Starting CSV fixes verification")
    
    # Get connection details from environment or use defaults for testing
    from os import environ
    
    # Override test config with actual values if available
    if 'SFTP_HOSTNAME' in environ:
        TEST_SERVER_CONFIG['hostname'] = environ['SFTP_HOSTNAME']
    if 'SFTP_PORT' in environ:
        TEST_SERVER_CONFIG['port'] = int(environ['SFTP_PORT'])
    if 'SFTP_USERNAME' in environ:
        TEST_SERVER_CONFIG['username'] = environ['SFTP_USERNAME']
    if 'SFTP_PASSWORD' in environ:
        TEST_SERVER_CONFIG['password'] = environ['SFTP_PASSWORD']
    if 'SERVER_ID' in environ:
        TEST_SERVER_CONFIG['server_id'] = environ['SERVER_ID']
    if 'ORIGINAL_SERVER_ID' in environ:
        TEST_SERVER_CONFIG['original_server_id'] = environ['ORIGINAL_SERVER_ID']
    if 'BASE_PATH' in environ:
        TEST_SERVER_CONFIG['base_path'] = environ['BASE_PATH']
    
    # Log config (excluding password)
    safe_config = {k: v for k, v in TEST_SERVER_CONFIG.items() if k != 'password'}
    logger.info(f"Using test config: {safe_config}")
    
    # Verify discovery
    discovery_success = await verify_discovery(TEST_SERVER_CONFIG)
    logger.info(f"Discovery verification {'PASSED' if discovery_success else 'FAILED'}")
    
    # Verify parsing
    parsing_success = await verify_parsing(TEST_SERVER_CONFIG)
    logger.info(f"Parsing verification {'PASSED' if parsing_success else 'FAILED'}")
    
    # Overall success
    overall_success = discovery_success and parsing_success
    logger.info(f"Overall verification {'PASSED' if overall_success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())