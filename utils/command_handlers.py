"""
Command handling utilities for tracking command usage and error patterns
"""
import logging
import time
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable

import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)

# Command usage tracking
COMMAND_HISTORY = []
ERROR_PATTERNS = {}

# Maximum commands to track
MAX_COMMAND_HISTORY = 1000

def guild_only():
    """
    A check to ensure a command can only be used in a guild context.
    This decorator works for both slash and text commands.
    """
    async def predicate(ctx):
        if isinstance(ctx, discord.Interaction):
            return ctx.guild is not None
        elif isinstance(ctx, commands.Context):
            return ctx.guild is not None
        return False

    return commands.check(predicate)

def handle_interaction_errors(interaction_callback):
    """
    A decorator to handle errors in interaction callbacks with standardized error handling.

    Args:
        interaction_callback: The interaction callback function to wrap

    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(interaction_callback)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            # Record start time for performance tracking
            start_time = time.time()

            # Execute the original callback
            result = await interaction_callback(self, interaction, *args, **kwargs)

            # Record successful command execution
            execution_time = time.time() - start_time
            record_command_usage(
                command_name=interaction_callback.__name__,
                guild_id=str(interaction.guild.id) if interaction.guild else None,
                user_id=str(interaction.user.id),
                success=True,
                execution_time=execution_time
            )

            return result

        except Exception as e:
            # Log the error
            logger.error(f"Error in {interaction_callback.__name__}: {str(e)}", exc_info=True)

            # Record failed command execution
            record_command_usage(
                command_name=interaction_callback.__name__,
                guild_id=str(interaction.guild.id) if interaction.guild else None,
                user_id=str(interaction.user.id),
                success=False,
                error=e
            )

            # Send error message to user
            error_message = f"An error occurred: {str(e)}"

            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)
            except discord.errors.HTTPException:
                # If we can't respond to the interaction (timed out), try to send a DM
                try:
                    await interaction.user.send(f"Error in command {interaction_callback.__name__}: {error_message}")
                except:
                    pass

    return wrapper


def record_command_usage(
    command_name: str, 
    guild_id: Optional[str] = None,
    user_id: Optional[str] = None,
    success: bool = True,
    error: Optional[Exception] = None,
    execution_time: float = 0.0
):
    """Record command usage for monitoring and analytics

    Args:
        command_name: Name of the command
        guild_id: Guild where command was used
        user_id: User who triggered the command
        success: Whether the command executed successfully
        error: Exception if the command failed
        execution_time: Time taken to execute the command
    """
    global COMMAND_HISTORY

    # Create entry
    entry = {
        "command": command_name,
        "guild_id": guild_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "success": success,
        "execution_time": execution_time
    }

    # Add error information if present
    if error:
        error_type = type(error).__name__
        entry["error_type"] = error_type
        entry["error_message"] = str(error)

        # Track error patterns
        error_key = f"{command_name}:{error_type}"
        if error_key not in ERROR_PATTERNS:
            ERROR_PATTERNS[error_key] = []

        ERROR_PATTERNS[error_key].append({
            "timestamp": entry["timestamp"],
            "message": str(error),
            "guild_id": guild_id
        })

    # Add to history and truncate if needed
    COMMAND_HISTORY.append(entry)
    if len(COMMAND_HISTORY) > MAX_COMMAND_HISTORY:
        COMMAND_HISTORY = COMMAND_HISTORY[-MAX_COMMAND_HISTORY:]


async def get_command_stats(hours: int = 24) -> Dict[str, Any]:
    """Get command usage statistics for the specified time period

    Args:
        hours: Number of hours to look back

    Returns:
        Statistics dict with usage metrics
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)

    # Filter commands by timeframe
    recent_commands = [cmd for cmd in COMMAND_HISTORY if cmd["timestamp"] > start_time]

    # Stats to track
    total_commands = len(recent_commands)
    successful = len([cmd for cmd in recent_commands if cmd["success"]])
    failed = total_commands - successful

    # Most used commands
    command_counts = {}
    for cmd in recent_commands:
        command_name = cmd["command"]
        if command_name not in command_counts:
            command_counts[command_name] = 0
        command_counts[command_name] += 1

    most_used = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Error rates
    error_rates = {}
    for cmd_name, count in command_counts.items():
        cmd_list = [cmd for cmd in recent_commands if cmd["command"] == cmd_name]
        success_count = len([cmd for cmd in cmd_list if cmd["success"]])
        error_rates[cmd_name] = {
            "total": count,
            "success": success_count,
            "failed": count - success_count,
            "error_rate": (count - success_count) / count if count > 0 else 0
        }

    return {
        "period_hours": hours,
        "total_commands": total_commands,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total_commands if total_commands > 0 else 1.0,
        "most_used": most_used,
        "error_rates": error_rates,
        "unique_users": len(set(cmd["user_id"] for cmd in recent_commands if cmd["user_id"])),
        "unique_guilds": len(set(cmd["guild_id"] for cmd in recent_commands if cmd["guild_id"]))
    }


async def get_latest_command_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """Get the latest command errors

    Args:
        limit: Maximum number of errors to return

    Returns:
        List of error details
    """
    errors = [cmd for cmd in COMMAND_HISTORY if not cmd["success"]]
    return sorted(errors, key=lambda e: e["timestamp"], reverse=True)[:limit]


async def get_recurring_error_patterns() -> Dict[str, Any]:
    """Get recurring error patterns

    This identifies systemic issues based on error patterns.

    Returns:
        Dict with error patterns
    """
    patterns = {}

    for error_key, errors in ERROR_PATTERNS.items():
        # Skip if fewer than 3 occurrences
        if len(errors) < 3:
            continue

        # Check for patterns in the last hour
        now = datetime.utcnow()
        recent_errors = [e for e in errors if now - e["timestamp"] < timedelta(hours=1)]

        if len(recent_errors) >= 3:
            command_name, error_type = error_key.split(":", 1)
            patterns[error_key] = {
                "command": command_name,
                "error_type": error_type,
                "count": len(recent_errors),
                "first_seen": min(e["timestamp"] for e in recent_errors),
                "last_seen": max(e["timestamp"] for e in recent_errors),
                "sample_message": recent_errors[-1]["message"]
            }

    return patterns


# Add decorator functions here
def guild_only():
    """
    Decorator that checks if the command is being invoked in a guild.
    """
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return False
        return True
    return commands.check(predicate)

async def handle_interaction_errors(interaction, error):
    """
    Handle errors that occur during interaction processing.

    Args:
        interaction: The discord interaction
        error: The exception that occurred
    """
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "You don't have the required permissions to use this command.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"An error occurred: {error}",
            ephemeral=True
        )
        logging.error(f"Error in command: {error}", exc_info=error)

def register_global_error_handlers(bot: commands.Bot):
    """Register global error handlers for the bot

    This sets up global error handling for all commands.

    Args:
        bot: Discord.py Bot instance
    """
    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for traditional commands"""
        # Unwrap CommandInvokeError
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Skip if already handled
        if hasattr(ctx.command, 'on_error'):
            return

        # Skip if command not found and we have a similar command
        if isinstance(error, commands.CommandNotFound):
            similar_commands = find_similar_commands(bot, ctx.invoked_with)
            if similar_commands:
                suggestions = ", ".join(f"`{cmd}`" for cmd in similar_commands[:3])
                await ctx.send(f"Command not found. Did you mean: {suggestions}?")
            return

        # Log error
        command_name = ctx.command.name if ctx.command else ctx.invoked_with
        logger.error(
            f"Error in command {command_name}: {error}",
            exc_info=error
        )

        # Record error metrics if not already done by decorator
        if not any(command_name == cmd["command"] and cmd["timestamp"] > datetime.utcnow() - timedelta(seconds=5) 
                  for cmd in COMMAND_HISTORY if not cmd["success"]):
            record_command_usage(
                command_name=command_name,
                guild_id=str(ctx.guild.id) if ctx.guild else None,
                user_id=str(ctx.author.id),
                success=False,
                error=error
            )

        # Handle different error types
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I don't have permission to execute this command.")
        else:
            # Generic error message
            await ctx.send(f"An error occurred: {error}")


def find_similar_commands(bot: commands.Bot, command_name: str) -> List[str]:
    """Find similar commands based on string similarity

    Args:
        bot: Discord.py Bot instance
        command_name: Command name to find similar commands for

    Returns:
        List of similar command names
    """
    from difflib import SequenceMatcher

    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    all_commands = [cmd.name for cmd in bot.commands]
    scores = [(cmd, similarity(command_name, cmd)) for cmd in all_commands]

    # Return commands with similarity > 0.6
    return [cmd for cmd, score in sorted(scores, key=lambda x: x[1], reverse=True) 
            if score > 0.6]


class CommandTimer:
    """Context manager for timing command execution"""

    def __init__(self, command_name: str, ctx=None):
        self.command_name = command_name
        self.ctx = ctx
        self.start_time = None
        self.execution_time = 0

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.execution_time = time.time() - self.start_time

        # Record command usage
        if self.ctx:
            record_command_usage(
                command_name=self.command_name,
                guild_id=str(self.ctx.guild.id) if self.ctx.guild else None,
                user_id=str(self.ctx.author.id) if self.ctx.author else None,
                success=exc_type is None,
                error=exc_val,
                execution_time=self.execution_time
            )