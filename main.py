#!/usr/bin/env python3

import discord
from discord.ext import commands
import asyncio
import logging
import sys
import traceback

description = """BemaniFiBot"""
bot = commands.Bot(command_prefix="!", description=description)
config = {}
roles = {}
logger = None


################################################################################

@bot.event
@asyncio.coroutine
def on_command_error(exception, ctx):
    # Log
    if type(exception) is discord.ext.commands.errors.MissingRequiredArgument:
        logger.warning("User %s did not supply enough arguments for command \"%s\"" % (ctx.message.author, ctx.command))
        # Add error reaction to the message
        yield from bot.add_reaction(ctx.message, "\u274c")
        return
    elif type(exception) is discord.ext.commands.errors.CommandNotFound:
        logger.warning("User %s tried to run non-existant command \"%s\"" % (ctx.message.author, ctx.message.content))
        return

    logger.error("Exception in command \"%s\"" % ctx.command)
    trace_str = traceback.format_exception(type(exception), exception, exception.__traceback__)
    for row in trace_str:
        logger.error(row.rstrip())


@bot.event
@asyncio.coroutine
def on_ready():
    logger.info("Logged in as %s" % bot.user)

    # Change nick
    nick = config["nick"]
    logger.info("Changing nick to %s" % nick)
    server = discord.utils.get(bot.servers)
    yield from bot.change_nickname(server.me, nick)

    # Get roles that have names in the config
    game_roles = list(filter(lambda r: r.name in config["roles"], server.roles))
    for role in game_roles:
        roles[role.name.lower()] = role

    known_roles_str = ", ".join([role.name for role in game_roles]) or "-"
    logger.info("Known roles: %s" % known_roles_str)

    logger.info("Ready")


@bot.group(pass_context=True)
@asyncio.coroutine
def game(ctx):
    if ctx.invoked_subcommand is None:
        logger.warning("No subcommand given for game command")
        # Add error reaction
        yield from bot.add_reaction(ctx.message, "\u274c")


@game.command(pass_context=True)
@asyncio.coroutine
def add(ctx, game):
    user = ctx.message.author

    if ctx.message.channel.is_private:
        # Private message
        logger.info("Role add request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.servers)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.message.author, server))
            yield from bot.say("Could not get your user info. Are you on the server?")
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
        yield from bot.add_reaction(ctx.message, "\u274c")
        return

    # Add the new role
    logger.info("Adding role %s for user %s" % (role.name, user))
    yield from bot.add_roles(user, role)
    # Add success reaction
    yield from bot.add_reaction(ctx.message, "\u2705")


@game.command(pass_context=True)
@asyncio.coroutine
def remove(ctx, game):
    user = ctx.message.author

    if ctx.message.channel.is_private:
        # Private message
        logger.info("Role removal request in private message from %s" % user)
        # Get the user (Member) from the server
        server = discord.utils.get(bot.servers)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.message.author, server))
            yield from bot.say("Could not get your user info. Are you on the server?")
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
            logger.warning("User %s tried to add nonexistant game role \"%s\"" % (user, game))
            # Add error reaction
            yield from bot.add_reaction(ctx.message, "\u274c")
            return

        # Remove role from user
        logger.info("Removing game role %s from user %s" % (role.name, user))
        yield from bot.remove_roles(user, role)
        # Add success reaction
        yield from bot.add_reaction(ctx.message, "\u2705")
    else:
        # Remove all game roles from user if the game parameter was "*"
        logger.info("Removing all game roles from %s" % user)
        game_roles = [i[1] for i in roles.items()]
        yield from bot.remove_roles(user, *game_roles)
        # Add success reaction
        yield from bot.add_reaction(ctx.message, "\u2705")


@bot.command(pass_context=True)
@asyncio.coroutine
def quit(ctx):
    # Check if the user is an admin
    user = ctx.message.author

    if ctx.message.channel.is_private:
        # Private message
        # Get the user (Member) from the server
        server = discord.utils.get(bot.servers)
        user = server.get_member_named(str(user))
        if user is None:
            logger.error("Could not get user %s from server %s" % (ctx.message.author, server))
            yield from bot.say("Could not get your user info. Are you on the server?")
            return

    has_admin_role = False
    admin_role_name = config["admin_role"]
    if len(admin_role_name) > 0:
        # Get admin role
        admin_role = discord.utils.get(discord.utils.get(bot.servers).roles, name=admin_role_name)
        has_admin_role = admin_role in user.roles
    else:
        logger.debug("No admin role configured, not checking")

    permissions = user.server_permissions
    permitted = permissions.administrator or has_admin_role

    if not permitted:
        logger.info("User %s tried to quit bot, denied" % user)
        # Add error reaction
        yield from bot.add_reaction(ctx.message, "\u274c")
        return

    logger.info("Quitting")
    yield from bot.close()

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
            logger.error("Invalid config line at %d" % line_no)
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

# Setup own logging
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(module)s/%(funcName)s] %(message)s", "%H:%M:%S"))
logger.addHandler(handler)

# Read config
read_config()

# Remove bot help command
bot.remove_command("help")

# Run
logger.info("Starting event loop")
bot.run(config["token"])
logger.info("Event loop ended")
