#!/usr/bin/env python3

import discord
from discord.ext import commands
import asyncio
import logging
import os
import sys
import traceback
import subprocess

description = """BemaniFiBot"""
bot = commands.Bot(command_prefix="!", description=description)
config = {}
roles = {}
area_roles = {}
logger = None
git_hash = None


################################################################################

@bot.event
async def on_command_error(ctx, exception):
    # Log
    if type(exception) is discord.ext.commands.errors.MissingRequiredArgument:
        logger.warning("User %s did not supply enough arguments for command \"%s\"" % (ctx.author, ctx.command))
        # Add error reaction to the message
        await ctx.message.add_reaction("\u274c")
        return
    elif type(exception) is discord.ext.commands.errors.CommandNotFound:
        logger.warning("User %s tried to run non-existant command \"%s\"" % (ctx.author, ctx.message.content))
        return

    logger.error("Exception in command \"%s\"" % ctx.command)
    trace_str = traceback.format_exception(type(exception), exception, exception.__traceback__)
    for row in trace_str:
        logger.error(row.rstrip())


@bot.event
async def on_ready():
    logger.info("Logged in as %s" % bot.user)

    # Change nick
    nick = config["nick"]
    logger.info("Changing nick to %s" % nick)
    server = discord.utils.get(bot.guilds)
    await bot.user.edit(username=nick)
    # await bot.change_nickname(server.me, nick)

    # Get roles that have names in the config
    game_roles = list(filter(lambda r: r.name in config["roles"], server.roles))
    for role in game_roles:
        roles[role.name.lower()] = role

    # Get area roles
    srv_area_roles = list(filter(lambda r: r.name in config["areas"], server.roles))
    for role in srv_area_roles:
        area_roles[role.name.lower()] = role

    known_roles_str = ", ".join([role.name for role in game_roles]) or "-"
    logger.info("Known game roles: %s" % known_roles_str)

    known_area_roles_str = ", ".join([role.name for role in srv_area_roles]) or "-"
    logger.info("Known area roles: %s" % known_area_roles_str)

    logger.info("Ready")


@bot.group()
async def game(ctx):
    if ctx.invoked_subcommand is None:
        logger.warning("No subcommand given for game command")
        # Add error reaction
        await ctx.message.add_reaction("\u274c")


@game.command()
async def add(ctx, game):
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        logger.info("Role add request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return
    elif ctx.message.channel.name != config["bot_channel"]:
        # Only allow this from bot channel
        logger.warning("User %s tried to add game role in #%s" % (user, ctx.message.channel.name))
        return

    game = game.lower()
    role = roles.get(game)
    if role is None:
        logger.warning("User %s tried to add nonexistant game role \"%s\"" % (user, game))
        # Add error reaction
        await ctx.message.add_reaction("\u274c")
        return

    # Add the new role
    logger.info("Adding role %s for user %s" % (role.name, user))
    await user.add_roles(role)
    # Add success reaction
    await ctx.message.add_reaction("\u2705")


@game.command()
async def remove(ctx, game):
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        logger.info("Role removal request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return
    elif ctx.message.channel.name != config["bot_channel"]:
        # Only allow this from bot channel
        logger.warning("User %s tried to remove game role in #%s" % (user, ctx.message.channel.name))
        return

    game = game.lower()
    remove_all_game_roles = game == "*"

    if not remove_all_game_roles:
        role = roles.get(game)
        if role is None:
            logger.warning("User %s tried to remove nonexistant game role \"%s\"" % (user, game))
            # Add error reaction
            await ctx.message.add_reaction("\u274c")
            return

        # Remove role from user
        logger.info("Removing game role %s from user %s" % (role.name, user))
        await user.remove_roles(role)
        # Add success reaction
        await ctx.message.add_reaction("\u2705")
    else:
        # Remove all game roles from user if the game parameter was "*"
        logger.info("Removing all game roles from %s" % user)
        game_roles = [i[1] for i in roles.items()]
        await user.remove_roles(*game_roles)
        # Add success reaction
        await ctx.message.add_reaction("\u2705")


@bot.group()
async def area(ctx):
    if ctx.invoked_subcommand is None:
        logger.warning("No subcommand given for area command")
        # Add error reaction
        await ctx.message.add_reaction("\u274c")


@area.command(name="add")
async def area_add(ctx, area):
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        logger.info("Area add request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return
    elif ctx.message.channel.name != config["bot_channel"]:
        # Only allow this from bot channel
        logger.warning("User %s tried to add area role in #%s" % (user, ctx.message.channel.name))
        return

    area = area.lower()
    role = area_roles.get(area)
    if role is None:
        logger.warning("User %s tried to add nonexistant area role \"%s\"" % (user, area))
        # Add error reaction
        await ctx.message.add_reaction("\u274c")
        return

    # Add the new role
    logger.info("Adding role %s for user %s" % (role.name, user))
    await user.add_roles(role)
    # Add success reaction
    await ctx.message.add_reaction("\u2705")


@area.command(name="remove")
async def area_remove(ctx, area):
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        logger.info("Role removal request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return
    elif ctx.message.channel.name != config["bot_channel"]:
        # Only allow this from bot channel
        logger.warning("User %s tried to remove area role in #%s" % (user, ctx.message.channel.name))
        return

    area = area.lower()
    remove_all_area_roles = area == "*"

    if not remove_all_area_roles:
        role = area_roles.get(area)
        if role is None:
            logger.warning("User %s tried to remove nonexistant area role \"%s\"" % (user, area))
            # Add error reaction
            await ctx.message.add_reaction("\u274c")
            return

        # Remove role from user
        logger.info("Removing area role %s from user %s" % (role.name, user))
        await user.remove_roles(role)
        # Add success reaction
        await ctx.message.add_reaction("\u2705")
    else:
        # Remove all area roles from user if the area parameter was "*"
        logger.info("Removing all area roles from %s" % user)
        area_role_entries = [i[1] for i in area_roles.items()]
        await user.remove_roles(*area_role_entries)
        # Add success reaction
        await ctx.message.add_reaction("\u2705")


@bot.command()
async def version(ctx):
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return
    elif ctx.message.channel.name != config["bot_channel"]:
        # Only allow this from bot channel
        logger.warning("User %s tried to query version info in #%s" % (user, ctx.message.channel.name))
        return

    logger.info("User %s queried version information" % user)

    # Return version info
    await ctx.send("Git commit: %s" % (git_hash or "?"))


@bot.command()
async def quit(ctx):
    # Check if the user is an admin
    user = ctx.author

    if isinstance(ctx.channel, discord.DMChannel):
        # Private message
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
            return

    has_admin_role = False
    admin_role_name = config["admin_role"]
    if len(admin_role_name) > 0:
        # Get admin role
        admin_role = discord.utils.get(discord.utils.get(bot.guilds).roles, name=admin_role_name)
        has_admin_role = admin_role in user.roles
    else:
        logger.debug("No admin role configured, not checking")

    permissions = user.guild_permissions
    permitted = permissions.administrator or has_admin_role

    if not permitted:
        logger.info("User %s tried to quit bot, denied" % user)
        # Add error reaction
        await ctx.message.add_reaction("\u274c")
        return

    logger.info("Quitting")
    await bot.close()

################################################################################


def read_config():
    lines = []
    config_path = "bemani.conf"
    try:
        with open(config_path, "r") as f:
            lines = [l.strip() for l in f.readlines()]
    except Exception:
        # Can't open config
        logger.critical("Config file opening failed! Check that \"%s\" exists." % config_path)
        sys.exit(1)

    for line_no, line in enumerate(lines):
        if len(line.strip()) == 0:
            continue
        if line.startswith("#"):
            continue
        key, value = (None, None)
        try:
            key, value = [s.strip() for s in line.split("=")]
            if value.startswith("["):
                # List, separated by ','
                logger.debug("Config parser encountered a list: %s" % value)
                value = [i.strip() for i in value.split("[")[1].split("]")[0].split(",")]
                logger.debug("Parsed list: %s" % value)
        except Exception:
            # Invalid line
            logger.error("Invalid config line at %d" % line_no + 1)
            continue
        config[key] = value
    logger.info("Config read")


if __name__ != "__main__":
    sys.exit(0)


# Setup discord.py logging
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)
discord_handler = logging.StreamHandler()
discord_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%H:%M:%S"))
discord_logger.addHandler(discord_handler)
# Log to file
discord_file_handler = logging.FileHandler("discord.log", mode="w", encoding="utf-8")
discord_file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%H:%M:%S"))
discord_logger.addHandler(discord_file_handler)


# Setup own logging
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%H:%M:%S"))
logger.addHandler(handler)
# Log to file
file_handler = logging.FileHandler("bot.log", mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%H:%M:%S"))
logger.addHandler(file_handler)

# Get git hash, if possible
try:
    git_hash = subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
except Exception:
    git_hash = os.environ.get("GIT_COMMIT")
    if not git_hash:
        logger.warning("Could not get Git hash")

# Read config
read_config()

# Remove bot help command
bot.remove_command("help")

# Run
logger.info("Current Git commit: %s" % (git_hash or "?"))
logger.info("Starting event loop")
bot.run(config["token"])
logger.info("Event loop ended")
