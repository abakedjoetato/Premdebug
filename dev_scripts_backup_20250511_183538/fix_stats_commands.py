import re

def fix_guild_lookup_function(content):
    """Fix guild lookups to handle both string and integer formats consistently"""
    # Fix problematic indentation and ensure guild lookups work with both string and int
    pattern1 = r'guild_data = await self\.bot\.db\.guilds\.find_one\(\{"guild_id": str\(guild_id\)\}\)\s+if guild_data is None:\s+# Try with integer ID\s+# Try string conversion of guild ID first\s+guild_data = await self\.bot\.db\.guilds\.find_one\(\{"guild_id": int\(guild_id\)\}\)\s+# Try with integer ID\s+'
    replacement1 = 'guild_data = await self.bot.db.guilds.find_one({"guild_id": str(guild_id)})\n                if guild_data is None:\n                    # Try with integer ID\n                    guild_data = await self.bot.db.guilds.find_one({"guild_id": int(guild_id)})\n                \n'
    
    content = re.sub(pattern1, replacement1, content)
    return content

def fix_stats_hybrid_commands(content):
    """Fix hybrid command setup to ensure proper Discord slash command registration"""
    # Make sure we properly define main stats command group and all subcommands
    pattern2 = r'@commands\.hybrid_group\(name="stats", description="Statistics commands"\)\s+@commands\.guild_only\(\)\s+async def stats\(self, ctx\):\s+"""Stats command group"""\s+if not ctx\.invoked_subcommand:\s+await ctx\.send\("Please specify a subcommand\."\)'
    replacement2 = '@commands.hybrid_group(name="stats", description="Statistics commands")\n    @commands.guild_only()\n    async def stats(self, ctx):\n        """Stats command group"""\n        if ctx.invoked_subcommand is None:\n            await ctx.send("Please specify a subcommand.")'
    
    content = re.sub(pattern2, replacement2, content)
    return content

def fix_autocomplete_registration(content):
    """Fix autocomplete function registration in commands"""
    # Ensure autocomplete functions are properly registered
    pattern3 = r'@app_commands\.autocomplete\(\s+server_id=server_id_autocomplete,\s+player_name=player_name_autocomplete\s+\)'
    replacement3 = '@app_commands.autocomplete(server_id=server_id_autocomplete, player_name=player_name_autocomplete)'
    
    content = re.sub(pattern3, replacement3, content)
    return content

with open('cogs/stats.py', 'r') as file:
    content = file.read()

# Apply all fixes
content = fix_guild_lookup_function(content)
content = fix_stats_hybrid_commands(content)
content = fix_autocomplete_registration(content)

with open('cogs/stats.py', 'w') as file:
    file.write(content)

print("Applied fixes to stats.py to ensure proper command loading and autocomplete functionality")
