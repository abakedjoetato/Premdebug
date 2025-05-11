"""
Test script to verify the historical CSV parsing with our fixes
"""
import asyncio
import os
import sys

async def main():
    try:
        # Import the bot modules
        from cogs.csv_processor import CSVProcessorCog
        from bot import initialize_bot
        
        # Initialize the bot
        bot = await initialize_bot()
        
        # Get the CSV processor cog
        csv_processor = None
        for name, cog in bot.cogs.items():
            if name.lower() == 'csvprocessor' or name.lower() == 'csv_processor':
                csv_processor = cog
                break
        
        if not csv_processor:
            print("ERROR: Could not find CSV processor cog")
            return
            
        print(f"Found CSV processor cog, testing historical parse...")
        
        # Run a historical parse for the server
        server_id = "61a9d32b-f5e3-4a0f-8bc2-8b3054f074a0"  # Use current server ID
        result = await csv_processor.run_historical_parse(server_id, days=7)
        
        print(f"Historical parse result: {result}")
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean exit
        try:
            await bot.close()
        except:
            pass
        
if __name__ == "__main__":
    asyncio.run(main())