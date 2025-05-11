with open('cogs/stats.py', 'r') as file:
    content = file.read()

content = content.replace('guild_data = await self.bot.db.guilds.find_one({"guild_id": str(int(guild_id))}                    if guild_data is None:', 'guild_data = await self.bot.db.guilds.find_one({"guild_id": int(guild_id)})')
content = content.replace('guild_data = guild_data = await self.bot.db.guilds.find_one({"guild_id": int(int(guild_id))}})','')

with open('cogs/stats.py', 'w') as file:
    file.write(content)

print("Fixed syntax errors in stats.py")
