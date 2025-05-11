#!/usr/bin/env python3
"""
Script to optimize CSV processing frequency based on server activity patterns.

This script adds dynamic adjustment of CSV processing intervals:
- If no new events are found in multiple consecutive runs, the interval is gradually increased
- If new events are found, the interval is reset to the default (5 minutes)
- Highly active servers will be checked more frequently than inactive ones
"""
import os
import re

def add_adaptive_processing():
    """
    Add adaptive CSV processing intervals to CSVProcessorCog
    """
    file_path = "cogs/csv_processor.py"
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    print(f"Adding adaptive processing to {file_path}...")
    
    # Read the source file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add new instance variables to __init__
    init_pattern = r"        # Initialize file tracking properties\n"
    init_pattern += r"        self\.map_csv_files_found = \[\]\n"
    init_pattern += r"        self\.map_csv_full_paths_found = \[\]\n"
    init_pattern += r"        self\.found_map_files = False\n"
    init_pattern += r"        self\.files_to_process = \[\]"
    
    init_replacement = """        # Initialize file tracking properties
        self.map_csv_files_found = []
        self.map_csv_full_paths_found = []
        self.found_map_files = False
        self.files_to_process = []
        
        # NEW: For adaptive processing frequency
        self.server_activity_counters = {}  # server_id -> {events_found: int, empty_checks: int}
        self.server_check_intervals = {}  # server_id -> minutes to wait
        self.default_check_interval = 5  # Default: check every 5 minutes
        self.max_check_interval = 30  # Maximum: check every 30 minutes
        self.inactive_threshold = 3  # After 3 empty checks, increase interval"""
        
    content = content.replace(init_pattern, init_replacement)
    
    # 2. Add adaptive adjustment method
    after_save_state_pattern = r"        except Exception as e:\n"
    after_save_state_pattern += r"            logger\.error\(f\"Error saving CSV processor state to database: \{e\}\"\)\n"
    after_save_state_pattern += r"            return False"
    
    after_save_state_replacement = """        except Exception as e:
            logger.error(f"Error saving CSV processor state to database: {e}")
            return False
            
    async def _adjust_server_check_interval(self, server_id, events_processed):
        """
        Dynamically adjust the check interval for a server based on activity
        
        For busy servers with frequent events, we want to check more often.
        For quiet servers with no events, we can gradually increase the interval.
        
        Args:
            server_id: The server ID to adjust
            events_processed: Number of events found in this check
        """
        # Initialize server tracking if not present
        if server_id not in self.server_activity_counters:
            self.server_activity_counters[server_id] = {
                "events_found": 0,
                "empty_checks": 0
            }
            self.server_check_intervals[server_id] = self.default_check_interval
        
        # Update counters
        if events_processed > 0:
            # Reset empty check counter when events are found
            self.server_activity_counters[server_id]["events_found"] += events_processed
            self.server_activity_counters[server_id]["empty_checks"] = 0
            # Reset interval to default when activity is detected
            self.server_check_intervals[server_id] = self.default_check_interval
            logger.debug(f"Server {server_id} is active with {events_processed} events, check interval reset to {self.default_check_interval} minutes")
        else:
            # Increment empty check counter when no events found
            self.server_activity_counters[server_id]["empty_checks"] += 1
            
            # Check if we should increase the interval after several empty checks
            empty_checks = self.server_activity_counters[server_id]["empty_checks"]
            if empty_checks >= self.inactive_threshold:
                # Increase interval but don't exceed max
                current_interval = self.server_check_intervals[server_id]
                new_interval = min(current_interval + 5, self.max_check_interval)
                
                if new_interval != current_interval:
                    self.server_check_intervals[server_id] = new_interval
                    logger.debug(f"Server {server_id} has been inactive for {empty_checks} checks, increasing interval to {new_interval} minutes")
        
        return self.server_check_intervals[server_id]"""
        
    content = content.replace(after_save_state_pattern, after_save_state_replacement)
    
    # 3. Update the process_csv_files_task method to use adaptive intervals
    task_pattern = r"    @tasks.loop\(minutes=5\)\n"
    task_pattern += r"    async def process_csv_files_task\(self\):"
    
    task_replacement = """    @tasks.loop(minutes=5)
    async def process_csv_files_task(self):
        \"\"\"Background task for processing CSV files with adaptive intervals

        This task dynamically adjusts the interval between runs based on server activity:
        - Active servers are checked more frequently (default: every 5 minutes)
        - Inactive servers are checked less frequently (up to max_check_interval minutes)
        \"\"\"
        # Store the original next iteration time
        original_next_run = self.process_csv_files_task.next_iteration"""
    
    content = content.replace(task_pattern, task_replacement)
    
    # 4. Add adaptive interval adjustment at the end of the process_csv_files_task
    end_task_pattern = r"        logger\.info\(f\"CSV processing completed in \{total_time:.2f\} seconds\. Processed \{total_files\} CSV files with \{total_events\} events\.\"\)"
    
    end_task_replacement = """        logger.info(f"CSV processing completed in {total_time:.2f} seconds. Processed {total_files} CSV files with {total_events} events.")
        
        # Apply adaptive interval adjustments based on activity
        for server_id, files_count in processed_servers.items():
            events_count = 0
            # Get the event count for this server if available
            if server_id in processed_events:
                events_count = processed_events[server_id]
                
            # Adjust this server's check interval based on activity
            interval = await self._adjust_server_check_interval(server_id, events_count)
            
            # If server is inactive, we'll use a longer interval next time
            if interval != self.default_check_interval:
                logger.debug(f"Server {server_id} will be checked less frequently (every {interval} minutes)")
                
        # Find the next server to check based on interval
        next_check_time = None
        for server_id, interval in self.server_check_intervals.items():
            # Skip if interval is default (these are handled by the task loop)
            if interval == self.default_check_interval:
                continue
                
            # Calculate when this server should be checked next
            from datetime import datetime, timedelta
            timestamp = datetime.utcnow()
            if server_id in self.last_processed:
                timestamp = self.last_processed[server_id]
            next_check = timestamp + timedelta(minutes=interval)
            
            # Update next check time if this one is sooner
            if next_check_time is None or next_check < next_check_time:
                next_check_time = next_check
        
        # No need to adjust if no inactive servers or all are on default schedule
        if next_check_time is None:
            return
            
        # Adjust the next iteration time if needed
        current_next_run = self.process_csv_files_task.next_iteration
        if next_check_time < current_next_run:
            # Cancel current task and restart with modified timing
            self.process_csv_files_task.cancel()
            time_diff = (next_check_time - datetime.utcnow()).total_seconds()
            # Ensure we don't schedule too soon
            if time_diff < 60:  # At least 1 minute
                time_diff = 60
            # Schedule the next check
            self.process_csv_files_task.change_interval(seconds=time_diff)
            self.process_csv_files_task.start()
            logger.debug(f"Adjusted next CSV check to happen in {time_diff/60:.1f} minutes")"""
    
    content = content.replace(end_task_pattern, end_task_replacement)
    
    # 5. Update the _process_server_csv_files method to track events processed per server
    server_files_pattern = r"        return files_processed, events_processed"
    
    server_files_replacement = """        # Keep track of this server's events for adaptive processing
        if events_processed > 0:
            if 'processed_events' not in self.__dict__:
                self.processed_events = {}
            self.processed_events[server_id] = events_processed
            
        return files_processed, events_processed"""
    
    content = content.replace(server_files_pattern, server_files_replacement)
    
    # Write back the changes
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Successfully added adaptive CSV processing to cogs/csv_processor.py")
    
    # Add processed_servers and processed_events to the beginning of process_csv_files_task
    # This requires more context to find the right spot
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    task_start_pattern = re.compile(r'async def process_csv_files_task\(self\):.*?\n        # Prevent running multiple instances simultaneously', re.DOTALL)
    task_start_match = task_start_pattern.search(content)
    
    if task_start_match:
        task_text = task_start_match.group(0)
        modified_task = task_text.replace(
            '        # Prevent running multiple instances simultaneously',
            '        # Initialize tracking for this run\n        processed_servers = {}\n        processed_events = {}\n\n        # Prevent running multiple instances simultaneously'
        )
        content = content.replace(task_text, modified_task)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Added tracking variables to process_csv_files_task")
    else:
        print("Warning: Could not locate task start pattern")
        
if __name__ == "__main__":
    add_adaptive_processing()