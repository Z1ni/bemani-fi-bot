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
admin_role = None
logger = None
git_hash = None


################################################################################

class NotAdminFailure(commands.CheckFailure):
    pass


class NoPublicCommandsFailure(commands.CheckFailure):
    pass


async def admin_check(ctx):
    user = await get_user(ctx)
    if admin_role is None or admin_role in user.roles:
        return True
    raise NotAdminFailure()


async def privmsg_or_botchannel_check(ctx):
    if ctx.guild is None or ctx.message.channel.name == config["bot_channel"]:
        # Private message or in bot channel
        return True
    raise NoPublicCommandsFailure()


async def get_user(ctx):
    user = ctx.author
    if ctx.guild is None:
        # Get the user (Member) from the server
        server = discord.utils.get(bot.guilds)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" %
                         (ctx.author, server))
            await ctx.send("Could not get your user info. Are you on the server?")
    return user


only_admin = commands.check(admin_check)
no_public = commands.check(privmsg_or_botchannel_check)


@bot.event
async def on_command_error(ctx, exception):
    # Log
    if type(exception) is discord.ext.commands.errors.MissingRequiredArgument:
        logger.warning("User %s did not supply enough arguments for command \"%s\"" % (
            ctx.author, ctx.command))
        # Add error reaction to the message
        await ctx.message.add_reaction("\u274c")
        return
    elif type(exception) is discord.ext.commands.errors.CommandNotFound:
        logger.warning("User %s tried to run non-existant command \"%s\"" %
                       (ctx.author, ctx.message.content))
        return
    elif type(exception) is NotAdminFailure:
        logger.warning("User %s tried to run admin command \"%s\"" %
                       (ctx.author, ctx.message.content))
        # Add error reaction to the message
        await ctx.message.add_reaction("\u274c")
        return
    elif type(exception) is NoPublicCommandsFailure:
        logger.warning("User %s tried to execute command \"%s\" in #%s" % (
            ctx.author, ctx.command, ctx.message.channel.name))
        return

    logger.error("Exception in command \"%s\"" % ctx.command)
    trace_str = traceback.format_exception(
        type(exception), exception, exception.__traceback__)
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

    # Get roles that have names in the config
    game_roles = list(
        filter(lambda r: r.name in config["roles"], server.roles))
    for role in game_roles:
        roles[role.name.lower()] = role

    # Get area roles
    srv_area_roles = list(
        filter(lambda r: r.name in config["areas"], server.roles))
    for role in srv_area_roles:
        area_roles[role.name.lower()] = role

    # Get admin role
    global admin_role
    admin_role = discord.utils.get(discord.utils.get(
        bot.guilds).roles, name=config["admin_role"])

    known_roles_str = ", ".join([role.name for role in game_roles]) or "-"
    logger.info("Known game roles: %s" % known_roles_str)

    known_area_roles_str = ", ".join(
        [role.name for role in srv_area_roles]) or "-"
    logger.info("Known area roles: %s" % known_area_roles_str)

    logger.info("Ready")


@bot.group()
async def game(ctx):
    if ctx.invoked_subcommand is None:
        logger.warning("No subcommand given for game command")
        # Add error reaction
        await ctx.message.add_reaction("\u274c")


@game.command()
@no_public
async def add(ctx, game):
    user = await get_user(ctx)

    if ctx.guild is None:
        # Private message
        logger.info("Role add request in private message from %s" % user)

    game = game.lower()
    role = roles.get(game)
    if role is None:
        logger.warning(
            "User %s tried to add nonexistent game role \"%s\"" % (user, game))
        # Add error reaction
        await ctx.message.add_reaction("\u274c")
        return

    # Add the new role
    logger.info("Adding role %s for user %s" % (role.name, user))
    await user.add_roles(role)
    # Add success reaction
    await ctx.message.add_reaction("\u2705")


@game.command()
@no_public
async def remove(ctx, game):
    user = await get_user(ctx)

    if ctx.guild is None:
        # Private message
        logger.info("Role removal request in private message from %s" % user)

    game = game.lower()
    remove_all_game_roles = game == "*"

    if not remove_all_game_roles:
        role = roles.get(game)
        if role is None:
            logger.warning(
                "User %s tried to remove nonexistent game role \"%s\"" % (user, game))
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
@no_public
async def area_add(ctx, area):
    user = await get_user(ctx)

    if ctx.guild is None:
        # Private message
        logger.info("Area add request in private message from %s" % user)

    area = area.lower()
    role = area_roles.get(area)
    if role is None:
        logger.warning(
            "User %s tried to add nonexistent area role \"%s\"" % (user, area))
        # Add error reaction
        await ctx.message.add_reaction("\u274c")
        return

    # Add the new role
    logger.info("Adding role %s for user %s" % (role.name, user))
    await user.add_roles(role)
    # Add success reaction
    await ctx.message.add_reaction("\u2705")


@area.command(name="remove")
@no_public
async def area_remove(ctx, area):
    user = await get_user(ctx)

    if ctx.guild is None:
        # Private message
        logger.info("Area removal request in private message from %s" % user)

    area = area.lower()
    remove_all_area_roles = area == "*"

    if not remove_all_area_roles:
        role = area_roles.get(area)
        if role is None:
            logger.warning(
                "User %s tried to remove nonexistent area role \"%s\"" % (user, area))
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
@no_public
async def version(ctx):
    user = await get_user(ctx)
    logger.info("User %s queried version information" % user)

    # Return version info
    await ctx.send("Git commit: %s" % (git_hash or "?"))


@bot.command()
@only_admin
@no_public
async def quit(ctx):
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
        logger.critical(
            "Config file opening failed! Check that \"%s\" exists." % config_path)
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
                value = [i.strip()
                         for i in value.split("[")[1].split("]")[0].split(",")]
                logger.debug("Parsed list: %s" % value)
        except Exception:
            # Invalid line
            logger.error("Invalid config line at %d" % line_no + 1)
            continue
        config[key] = value
    logger.info("Config read")


if __name__ != "__main__":
    sys.exit(0)

log_to_file = "-l" in sys.argv[1:]

# Setup discord.py logging
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)
discord_handler = logging.StreamHandler()
discord_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
discord_logger.addHandler(discord_handler)
# Log to file
if log_to_file:
    discord_file_handler = logging.FileHandler(
        "discord.log", mode="w", encoding="utf-8")
    discord_file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    discord_logger.addHandler(discord_file_handler)


# Setup own logging
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)
# Log to file
if log_to_file:
    file_handler = logging.FileHandler("bot.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

# Get git hash, if possible
try:
    git_hash = subprocess.check_output(
        ["git", "describe", "--always"]).strip().decode("utf-8")
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
