"""
Fix Premium Tier Checks

This script updates all premium tier decorators to use feature names instead of hard-coded tier numbers,
ensuring consistent premium feature checks across the codebase.
"""
import os
import re
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Map of feature names to their tier requirements (from premium.py)
PREMIUM_FEATURES = {
    # Base features (tier 0 - Scavenger)
    "killfeed": 0,
    
    # Tier 1 features (Survivor)
    "basic_stats": 1,
    "stats": 1,  # Alias for basic_stats
    "leaderboards": 1,
    
    # Tier 2 features (Mercenary)
    "rivalries": 2,
    "bounties": 2,
    "bounty_notifications": 2,
    "player_links": 2,
    "economy": 2,
    "advanced_analytics": 2,
    
    # Tier 3 features (Warlord)
    "factions": 3,
    "events": 3,
    "connections": 3,
}

# Patterns to search for
tier_decorator_pattern = re.compile(r'@premium_tier_required\((\d+)\).*?#.*?')

# Map of tier numbers to feature names (for replacement)
tier_to_feature_map = {
    0: "killfeed",
    1: "stats",
    2: "rivalries",  # Most common tier 2 feature
    3: "factions",   # Most common tier 3 feature
}

# Feature name mappings based on file context
file_to_feature_map = {
    "rivalries.py": "rivalries",
    "stats.py": "stats",
    "factions.py": "factions",
    "bounties.py": "bounties",
    "events.py": "events",
    "economy.py": "economy",
    "killfeed.py": "killfeed",
    "player_links.py": "player_links",
}

def fix_file(file_path):
    """Fix premium tier decorators in a file"""
    logger.info(f"Checking file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the base filename for context
        filename = os.path.basename(file_path)
        feature_name = file_to_feature_map.get(filename)
        
        # Find tier decorator patterns
        matches = tier_decorator_pattern.findall(content)
        if not matches:
            logger.info(f"  No tier decorators found in {filename}")
            return False
        
        logger.info(f"  Found {len(matches)} tier decorators in {filename}")
        
        # Replace each decorator
        for tier_number in matches:
            tier = int(tier_number)
            
            # Determine appropriate feature name based on context
            if feature_name:
                replacement_feature = feature_name
            else:
                replacement_feature = tier_to_feature_map.get(tier, "stats")
            
            # Create pattern for this specific tier
            pattern = f'@premium_tier_required({tier})'
            replacement = f'@premium_tier_required(feature_name="{replacement_feature}")'
            
            logger.info(f"  Replacing {pattern} with {replacement}")
            content = content.replace(pattern, replacement)
        
        # Write updated content back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"  Updated {filename}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix premium tier decorators"""
    cogs_dir = Path('cogs')
    utils_dir = Path('utils')
    
    # Create list of files to process
    files_to_process = list(cogs_dir.glob('*.py'))
    files_to_process.extend(utils_dir.glob('*.py'))
    
    logger.info(f"Found {len(files_to_process)} Python files to check")
    
    # Process each file
    fixed_files = 0
    for file_path in files_to_process:
        if fix_file(file_path):
            fixed_files += 1
    
    logger.info(f"Fixed premium tier decorators in {fixed_files} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())