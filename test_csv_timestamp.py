"""
# module: test_csv_timestamp
Test CSV timestamp parsing

This script tests our timestamp parsing code to ensure
it correctly handles the specific format from the screenshot.
"""
import re
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('test_csv_timestamp')

def test_timestamp_parsing():
    """Test parsing of timestamps in the format from the screenshot"""
    # List of timestamp examples to test (directly from screenshot)
    test_filenames = [
        "2025.03.27-00.00.00.csv",
        "2025.05.01-00.00.00.csv",
        "2025.05.03-00.00.00.csv",
        "2025.05.03-01.00.00.csv",
        "2025.05.03-02.00.00.csv",
        "2025.05.03-03.00.00.csv",
        "2025.05.09-11.58.37.csv"
    ]
    
    # Timestamp pattern from our code
    pattern = r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})\.csv$'
    
    # Test each filename
    for filename in test_filenames:
        logger.info(f"Testing filename: {filename}")
        
        # Apply the pattern
        match = re.match(pattern, filename)
        
        if match:
            try:
                # Extract date components
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                hour = int(match.group(4))
                minute = int(match.group(5))
                second = int(match.group(6))
                
                # Create a datetime object
                dt = datetime(year, month, day, hour, minute, second)
                
                logger.info(f"Successfully parsed: {dt}")
            except Exception as e:
                logger.error(f"Error parsing date from {filename}: {e}")
        else:
            logger.error(f"Pattern did not match filename: {filename}")

def test_content_parsing():
    """Test parsing of CSV content with timestamp in first field"""
    # Example CSV lines from a file
    test_lines = [
        "2025.05.09-11.58.37;Player1;12345;Player2;67890;Weapon;123.45;PC;PC",
        "2025.05.09-11.59.22;Player3;24680;Player4;13579;Weapon;75.0;PC;PC"
    ]
    
    # Extract date from first field pattern
    pattern = r'^(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})'
    
    # Test each line
    for line in test_lines:
        logger.info(f"Testing content line: {line}")
        
        # Split the line by the delimiter
        fields = line.split(';')
        
        if len(fields) >= 1:
            # Get the timestamp field
            timestamp_str = fields[0]
            
            # Apply the pattern
            match = re.match(pattern, timestamp_str)
            
            if match:
                try:
                    # Extract date components
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    hour = int(match.group(4))
                    minute = int(match.group(5))
                    second = int(match.group(6))
                    
                    # Create a datetime object
                    dt = datetime(year, month, day, hour, minute, second)
                    
                    logger.info(f"Successfully parsed timestamp: {dt}")
                    
                    # Log the other fields too
                    if len(fields) >= 7:
                        killer = fields[1]
                        killer_id = fields[2]
                        victim = fields[3]
                        victim_id = fields[4]
                        weapon = fields[5]
                        distance = fields[6]
                        
                        logger.info(f"Killer: {killer} ({killer_id})")
                        logger.info(f"Victim: {victim} ({victim_id})")
                        logger.info(f"Weapon: {weapon}")
                        logger.info(f"Distance: {distance}")
                except Exception as e:
                    logger.error(f"Error parsing timestamp from {timestamp_str}: {e}")
            else:
                logger.error(f"Pattern did not match timestamp: {timestamp_str}")
        else:
            logger.error(f"Line does not have enough fields: {line}")

if __name__ == "__main__":
    logger.info("=== TESTING CSV TIMESTAMP PARSING ===")
    test_timestamp_parsing()
    
    logger.info("\n=== TESTING CSV CONTENT PARSING ===")
    test_content_parsing()