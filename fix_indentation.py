with open('cogs/stats.py', 'r') as file:
    lines = file.readlines()

# Fix lines around 1034-1037
if len(lines) >= 1037:
    # Remove the empty line and fix indentation
    if "# Try with integer ID" in lines[1034]:
        lines[1035:1037] = []  # Remove the extra lines

with open('cogs/stats.py', 'w') as file:
    file.writelines(lines)

print("Fixed indentation in stats.py")
