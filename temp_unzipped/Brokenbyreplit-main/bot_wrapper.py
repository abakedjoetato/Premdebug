
#!/usr/bin/env python3
"""
Robust wrapper script for the Discord bot with enhanced auto-restart capabilities.
This script provides:
1. Error handling for crashes and exceptions
2. Automatic restart with smart backoff on failure
3. Detailed logging of crash causes
4. Memory usage monitoring and mitigation
5. Comprehensive diagnostics to identify recurring issues
"""
import os
import sys
import time
import logging
import subprocess
import signal
import psutil
import traceback
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_wrapper.log')
    ]
)
logger = logging.getLogger('bot_wrapper')

# Constants
MAX_RESTART_DELAY = 300  # 5 minutes max backoff
MAX_RESTARTS_IN_WINDOW = 5  # Maximum number of restarts in time window
RESTART_WINDOW = 600  # 10 minute window for restart tracking
MEMORY_WARNING_THRESHOLD_MB = 400  # Memory threshold in MB for warnings
MEMORY_CRITICAL_THRESHOLD_MB = 800  # Memory threshold in MB for emergency action
DIAGNOSTICS_DIR = "diagnostics"

# Track restarts
restart_history = []
current_delay = 1  # Start with 1 second delay
crash_patterns = {}  # Track patterns of crashes

# Ensure diagnostics directory exists
os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)

def log_restart(message, error=None):
    """Log restart to restart_log.txt with enhanced error tracking
    
    Args:
        message: Restart message
        error: Optional error that caused the restart
    """
    timestamp = datetime.now()
    restart_history.append(timestamp)
    
    # Create restart record with detailed info
    restart_info = {
        "timestamp": timestamp.isoformat(),
        "message": message,
        "memory_usage_mb": get_memory_usage()['rss'],
    }
    
    if error:
        restart_info["error"] = str(error)
        
        # Track error patterns
        error_type = type(error).__name__
        if error_type in crash_patterns:
            crash_patterns[error_type] += 1
        else:
            crash_patterns[error_type] = 1
            
        restart_info["error_type"] = error_type
        restart_info["error_patterns"] = crash_patterns
    
    # Log to screen
    logger.info(f"{message} at {timestamp}")
    if error:
        logger.error(f"Error details: {error}")
    
    # Log to restart file
    try:
        with open("restart_log.txt", "a") as f:
            f.write(f"{timestamp}: {message}\n")
            if error:
                f.write(f"  Error: {error}\n")
    except Exception as e:
        logger.error(f"Failed to record restart: {e}")
    
    # Save detailed diagnostics if we have an error
    if error:
        try:
            diagnostic_file = os.path.join(DIAGNOSTICS_DIR, f"restart_{timestamp.strftime('%Y%m%d_%H%M%S')}.json")
            with open(diagnostic_file, "w") as f:
                json.dump(restart_info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save diagnostics: {e}")

def check_restart_rate():
    """Check if we're restarting too frequently, indicating serious issues
    
    Returns:
        bool: True if restart rate is excessive, False otherwise
    """
    global restart_history
    
    # Clean old restart records
    cutoff_time = datetime.now() - timedelta(seconds=RESTART_WINDOW)
    restart_history = [ts for ts in restart_history if ts > cutoff_time]
    
    # Check if we have too many restarts in our window
    if len(restart_history) > MAX_RESTARTS_IN_WINDOW:
        logger.critical(f"Too many restarts ({len(restart_history)}) in {RESTART_WINDOW/60} minute window!")
        logger.critical("Pausing for extended period to prevent crash loop")
        
        # Save crash pattern analysis
        try:
            with open(os.path.join(DIAGNOSTICS_DIR, "crash_patterns.json"), "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "restart_count": len(restart_history),
                    "window_seconds": RESTART_WINDOW,
                    "crash_patterns": crash_patterns
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save crash patterns: {e}")
            
        return True
    
    return False

def get_memory_usage():
    """Get current memory usage of the process
    
    Returns:
        dict: Memory usage information in MB
    """
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
        }
    except Exception as e:
        logger.error(f"Failed to get memory usage: {e}")
        return {'rss': 0, 'vms': 0}

def signal_handler(signum, frame):
    """Handle termination signals properly"""
    sig_name = signal.Signals(signum).name
    logger.info(f"Received signal {sig_name} ({signum})")
    
    if signum in (signal.SIGINT, signal.SIGTERM):
        logger.info("Wrapper stopping due to termination signal")
        sys.exit(0)

def check_memory_usage():
    """Check and report high memory usage
    
    Returns:
        bool: True if memory usage is high, False otherwise
    """
    try:
        memory = get_memory_usage()
        
        # Only log memory usage if it seems excessive
        if memory['rss'] > MEMORY_WARNING_THRESHOLD_MB:
            logger.warning(f"High memory usage detected: {memory['rss']:.1f} MB")
            
            # Try to get a detailed memory report
            try:
                import tracemalloc
                
                if not tracemalloc.is_tracing():
                    tracemalloc.start()
                
                # Let it collect some data
                time.sleep(1)
                
                # Take snapshot and analyze
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                logger.warning("Top 10 memory allocations:")
                for i, stat in enumerate(top_stats[:10]):
                    logger.warning(f"#{i+1}: {stat}")
                    
                # Save memory profile
                try:
                    with open(os.path.join(DIAGNOSTICS_DIR, f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"), "w") as f:
                        f.write(f"Memory usage: {memory['rss']:.1f} MB\n\n")
                        f.write("Top memory allocations:\n")
                        for i, stat in enumerate(top_stats[:30]):
                            f.write(f"#{i+1}: {stat}\n")
                except Exception as e:
                    logger.error(f"Failed to save memory profile: {e}")
                
                # Emergency garbage collection for critical memory usage
                if memory['rss'] > MEMORY_CRITICAL_THRESHOLD_MB:
                    import gc
                    collected = gc.collect()
                    logger.info(f"Emergency garbage collection freed {collected} objects")
                
            except ImportError:
                logger.warning("tracemalloc not available for memory diagnostics")
            except Exception as e:
                logger.error(f"Error in memory diagnostics: {e}")
                
            return True
            
        return False
    except Exception:
        logger.error("Failed to check memory usage", exc_info=True)
        return False

def get_bot_status():
    """Look for bot status file to understand bot state
    
    Returns:
        dict: Bot status information or None if not available
    """
    try:
        status_file = os.path.join(DIAGNOSTICS_DIR, "bot_status.json")
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read bot status: {e}")
    return None

def run_bot(bot_script="run_production.py"):
    """Run the Discord bot with proper monitoring
    
    Args:
        bot_script: Script to run the bot
    """
    global current_delay
    
    # Print header
    print("=" * 60)
    print("  Discord Bot Launcher with Enhanced Stability Wrapper")
    print("=" * 60)
    print(f"  Starting bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Using script: {bot_script}")
    print("  Press Ctrl+C to stop the bot")
    print("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create a flag file to indicate we're running in a workflow
    with open(".running_in_workflow", "w") as f:
        f.write(f"Started at {datetime.now()}")
        
    # Create a monitoring file for diagnostics
    with open("wrapper_status.txt", "w") as f:
        f.write(f"Wrapper started at {datetime.now()}\n"
                f"Python version: {sys.version}\n"
                f"Initial memory: {get_memory_usage()['rss']:.1f} MB\n")
    
    # Check if the bot script exists
    if not os.path.exists(bot_script):
        logger.critical(f"Bot script {bot_script} not found")
        sys.exit(1)
    
    # Main restart loop
    while True:
        # Check if we need an extended pause due to restart rate
        if check_restart_rate():
            extended_delay = MAX_RESTART_DELAY * 2
            logger.warning(f"Entering extended cooldown period ({extended_delay} seconds)")
            
            # Write to diagnostics
            try:
                with open(os.path.join(DIAGNOSTICS_DIR, "cooldown.txt"), "a") as f:
                    f.write(f"{datetime.now()}: Entered {extended_delay}s cooldown due to excessive restarts\n")
            except Exception:
                pass
                
            time.sleep(extended_delay)  # Double the max delay for cooldown
            current_delay = 1  # Reset delay after cooldown
        
        log_restart("Bot starting")
        
        start_time = time.time()
        logger.info(f"Starting bot process (memory: {get_memory_usage()['rss']:.1f} MB)")
        
        # Check memory before launch
        if check_memory_usage():
            logger.warning("Performing pre-launch memory cleanup due to high usage")
            time.sleep(2)  # Brief pause for cleanup effects
            
        try:
            # Run the bot script
            result = subprocess.run(
                [sys.executable, bot_script],
                check=True, 
                text=True, 
                capture_output=True
            )
            
            # Check memory after run completes
            high_memory = check_memory_usage()
            
            # If we exit normally, reset the backoff delay
            logger.info(f"Bot process exited with code {result.returncode}")
            
            # Save exit output for diagnostics
            try:
                with open(os.path.join(DIAGNOSTICS_DIR, f"bot_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), "w") as f:
                    f.write(f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}")
            except Exception as e:
                logger.error(f"Failed to save bot output: {e}")
            
            # If memory was high, don't immediately reset the delay to prevent rapid restarts
            if not high_memory:
                current_delay = 1
            
            # If the bot requested termination, respect it
            if result.returncode == 0:
                logger.info("Bot exited cleanly, restarting...")
                time.sleep(1)  # Short delay for clean restart
            else:
                logger.warning(f"Bot exited with error code {result.returncode}, restarting with delay...")
                time.sleep(current_delay)
                current_delay = min(current_delay * 2, MAX_RESTART_DELAY)  # Exponential backoff
                
        except subprocess.CalledProcessError as e:
            runtime = time.time() - start_time
            logger.error(f"Bot crashed with return code {e.returncode} after {runtime:.1f} seconds")
            
            # Save error output for diagnostics
            try:
                with open(os.path.join(DIAGNOSTICS_DIR, f"bot_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), "w") as f:
                    f.write(f"Return code: {e.returncode}\n")
                    f.write(f"Runtime: {runtime:.1f} seconds\n\n")
                    f.write(f"=== STDOUT ===\n{e.stdout}\n\n=== STDERR ===\n{e.stderr}")
            except Exception as ex:
                logger.error(f"Failed to save error output: {ex}")
            
            # Apply backoff delay based on how quickly it failed
            if runtime < 10:  # If it failed very quickly
                current_delay = min(current_delay * 2, MAX_RESTART_DELAY)  # Increase backoff faster
            else:
                current_delay = min(current_delay * 1.5, MAX_RESTART_DELAY)  # Slower backoff for longer runs
                
            logger.info(f"Restarting in {current_delay:.1f} seconds (memory: {get_memory_usage()['rss']:.1f} MB)")
            time.sleep(current_delay)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error running bot: {e}")
            logger.error(traceback.format_exc())
            
            # Save error information
            try:
                with open(os.path.join(DIAGNOSTICS_DIR, f"wrapper_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), "w") as f:
                    f.write(f"Error: {e}\n\n")
                    f.write(traceback.format_exc())
            except Exception:
                pass
            
            # More aggressive backoff for unexpected errors
            current_delay = min(current_delay * 3, MAX_RESTART_DELAY)
            logger.info(f"Restarting in {current_delay:.1f} seconds (memory: {get_memory_usage()['rss']:.1f} MB)")
            time.sleep(current_delay)

def main():
    """Main entry point with error handling"""
    # Ensure diagnostics directory exists
    try:
        os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create diagnostics directory: {e}")
    
    # Determine which script to use
    bot_script = "run_production.py"
    if len(sys.argv) > 1:
        bot_script = sys.argv[1]
        
    # Run the bot wrapper
    try:
        run_bot(bot_script)
    except KeyboardInterrupt:
        logger.info("Wrapper stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error in wrapper: {e}")
        logger.error(traceback.format_exc())
        
        # Save the error
        try:
            with open(os.path.join(DIAGNOSTICS_DIR, f"fatal_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), "w") as f:
                f.write(f"Fatal error: {e}\n\n")
                f.write(traceback.format_exc())
        except Exception:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()
