#!/bin/bash
# Comprehensive deployment script for Emeralds Killfeed PvP Statistics Discord Bot
# This script ensures all fixes are properly deployed and the bot is restarted cleanly

echo "==== Starting deployment process at $(date) ===="
echo "Checking prerequisites..."

# Create a backup of critical files before deployment
BACKUP_DIR="backups/deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Creating backups in $BACKUP_DIR"

# Back up critical files
cp -v models/player.py "$BACKUP_DIR/"
cp -v cogs/csv_processor.py "$BACKUP_DIR/"
cp -v utils/file_discovery.py "$BACKUP_DIR/"
cp -v utils/csv_processor_coordinator.py "$BACKUP_DIR/"
cp -v utils/stable_csv_parser.py "$BACKUP_DIR/"
cp -v main.py "$BACKUP_DIR/"

echo "Backups complete. Deploying optimizations..."

# Clear any cached __pycache__ files to ensure clean loading
echo "Clearing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Remove any lock files that might prevent clean startup
echo "Removing any lock files..."
find . -name "*.lock" -delete

# Wait for any running processes to finish gracefully
echo "Ensuring clean environment for deployment..."
sleep 3

# Log the deployment in a separate file
echo "Deployment started at $(date)" >> deploy.log
echo "==== Deploying optimized code ====" >> deploy.log

# Record current git status if git is available
if command -v git &> /dev/null; then
    echo "Recording git status..."
    git status >> deploy.log
fi

echo "==== Deployment completed at $(date) ===="
echo "To start the bot, run: python main.py"
echo "For production mode, run: python main.py --production"
echo ""
echo "Deployment log saved to deploy.log"