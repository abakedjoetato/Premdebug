
#!/usr/bin/env python3
"""
Run the premium verification script to ensure tier checks work properly
"""
import asyncio
import os
import subprocess
import sys

async def run_verification():
    """Run the verification script"""
    print("Starting premium verification...")
    
    # Check if verify_premium_fixes.py exists
    if not os.path.exists("verify_premium_fixes.py"):
        print("Error: verify_premium_fixes.py not found!")
        return 1
    
    # Make the script executable
    os.chmod("verify_premium_fixes.py", 0o755)
    
    # Get guild ID from command line or use a default
    guild_id = sys.argv[1] if len(sys.argv) > 1 else "1219706687980568769"
    
    # Run the verification script
    result = subprocess.run(
        [sys.executable, "verify_premium_fixes.py", guild_id],
        capture_output=True,
        text=True
    )
    
    # Display the output
    print("\nVerification script output:")
    print("="*50)
    print(result.stdout)
    
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)
    
    print("="*50)
    
    # Return the exit code from the verification script
    return result.returncode

if __name__ == "__main__":
    exit_code = asyncio.run(run_verification())
    sys.exit(exit_code)
