import os
import glob

def fix_guild_lookup_in_file(file_path):
    """
    Fix guild lookup in a file to handle both string and integer guild IDs.
    Direct line editing approach for more reliability.
    
    Args:
        file_path: Path to the file to fix
        
    Returns:
        Number of changes made
    """
    # Open file and read lines
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Find pattern and replace
    changes_made = 0
    
    i = 0
    while i < len(lines):
        if i >= len(lines):
            break
            
        # Check for guild lookup pattern with ctx.guild.id
        if "guild_data = await self.bot.db.guilds.find_one({\"guild_id\": ctx.guild.id})" in lines[i]:
            # Skip lines we've already fixed (that have string conversion)
            if i > 0 and "guild_id = ctx.guild.id" in lines[i-1]:
                i += 1
                continue
                
            # Found the line to replace
            original_line = lines[i]
            indent = original_line[:len(original_line) - len(original_line.lstrip())]
            
            # Replace with enhanced version
            new_lines = [
                f"{indent}# Get guild data with enhanced lookup\n",
                f"{indent}guild_id = ctx.guild.id\n",
                f"{indent}\n",
                f"{indent}# Try string conversion of guild ID first\n",
                f"{indent}guild_data = await self.bot.db.guilds.find_one({{\"guild_id\": str(guild_id)}})\n",
                f"{indent}if guild_data is None:\n",
                f"{indent}    # Try with integer ID\n",
                f"{indent}    guild_data = await self.bot.db.guilds.find_one({{\"guild_id\": int(guild_id)}})\n",
                f"{indent}\n"
            ]
            
            # Replace the line
            lines[i:i+1] = new_lines
            changes_made += 1
            i += len(new_lines)  # Skip ahead to avoid processing the newly inserted lines
        
        # Also check for other patterns with direct guild_id parameter
        elif "guild_data = await" in lines[i] and ".db.guilds.find_one({\"guild_id\":" in lines[i] and "str(" not in lines[i]:
            # Skip if we've already fixed this
            if i > 0 and "Try string conversion of guild ID first" in lines[i-1]:
                i += 1
                continue
                
            # Extract the guild_id variable and context
            parts = lines[i].split("guild_id\": ")
            if len(parts) < 2:
                i += 1
                continue
                
            before = parts[0]
            after_parts = parts[1].split("}")
            guild_id_var = after_parts[0]
            after = "}" + "".join(after_parts[1:])
            
            # Don't replace if already using string conversion
            if "str(" in guild_id_var:
                i += 1
                continue
            
            indent = before[:len(before) - len(before.lstrip())]
            
            # Create the new implementation with both string and int lookups
            new_lines = [
                f"{indent}# Try string conversion of guild ID first\n",
                f"{before}guild_id\": str({guild_id_var})}}",
                f"{indent}if guild_data is None:\n",
                f"{indent}    # Try with integer ID\n",
                f"{indent}    guild_data = {before.strip()}guild_id\": int({guild_id_var})}}{after}"
            ]
            
            # Replace the original line
            lines[i:i+1] = new_lines
            changes_made += 1
            i += len(new_lines)
        else:
            i += 1
    
    # Write back to file if changes were made
    if changes_made > 0:
        with open(file_path, 'w') as file:
            file.writelines(lines)
        print(f"Fixed {changes_made} guild lookup instances in {file_path}")
        return changes_made
    else:
        print(f"No changes made to {file_path}")
        return 0

def fix_all_guild_lookups():
    """
    Fix guild lookups in all cog files.
    """
    total_changes = 0
    
    # Process all Python files in the cogs directory
    for file_path in glob.glob("cogs/*.py"):
        # Skip backup files
        if "_backup" in file_path:
            continue
        
        changes = fix_guild_lookup_in_file(file_path)
        total_changes += changes
    
    print(f"Total changes made across all files: {total_changes}")
    return total_changes

if __name__ == "__main__":
    fix_all_guild_lookups()