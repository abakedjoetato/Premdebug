with open('cogs/stats.py', 'r') as file:
    content = file.read()

# Fix specific player name extraction error in leaderboard function
content = content.replace('    player_name = entry.get(\'player_name\', entry.get(\'name\', entry.get(\'_id\', \'Unknown Player\')))',
                        '                player_name = entry.get(\'player_name\', entry.get(\'name\', entry.get(\'_id\', \'Unknown Player\')))')

with open('cogs/stats.py', 'w') as file:
    file.write(content)

print("Fixed indentation in stats.py")
