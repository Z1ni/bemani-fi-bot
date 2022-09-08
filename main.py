import json
import logging
import os
import subprocess
from typing import Dict
import discord
from discord import Client, SelectOption, Interaction, Intents, ButtonStyle, Embed, Message, DMChannel
from discord.ui import Select, View, Button
from discord.app_commands import CommandTree


class BotClient(Client):
    def __init__(self, nick, guild, game_roles, area_roles) -> None:
        intents = Intents.default()
        super().__init__(intents=intents)

        self.tree = CommandTree(self)

        self.game_roles = {}
        self.area_roles = {}

        self._nick = nick
        self._guild = guild
        self._game_roles = game_roles
        self._area_roles = area_roles

        self._logger = logging.getLogger("bot.client")

    async def on_ready(self):
        self._logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

        # Set nick
        self._logger.info(f"Changing nick to \"{self._nick}\"")
        await self.user.edit(username=self._nick)

        guild = self.guilds[0]

        # Check that the configured roles match with the guild roles
        for game_role in self._game_roles:
            role_id = int(game_role["id"])
            role = guild.get_role(role_id)
            if role is None:
                self._logger.warning(f"No role with ID {role_id} in guild {guild}")
            else:
                self._logger.debug(f"Found role \"{role.name}\" with ID {role_id} in guild {guild}")
            self.game_roles[role_id] = {
                "name": game_role["name"],
                "description": game_role["description"],
                "role": role
            }

        for area_role in self._area_roles:
            role_id = int(area_role["id"])
            role = guild.get_role(role_id)
            if role is None:
                self._logger.warning(f"No role with ID {role_id} in guild {guild}")
            else:
                self._logger.debug(f"Found role \"{role.name}\" with ID {role_id} in guild {guild}")
            self.area_roles[role_id] = {
                "name": area_role["name"],
                "description": area_role["description"],
                "role": role
            }

        self._logger.info("Ready")

    async def setup_hook(self) -> None:
        await self.tree.sync(guild=self._guild)


class RoleSelector(Select):
    def __init__(self, roles: Dict[int, Dict[str, str]], add_roles: bool) -> None:
        self._logger = logging.getLogger("bot.client.rolesel")
        self._add_roles = add_roles

        role_opts = []
        for role_id, role in roles.items():
            opt = SelectOption(label=role["name"], value=role_id, description=role["description"])
            role_opts.append(opt)

        super().__init__(placeholder="Select role(s)", min_values=1, max_values=len(role_opts), options=role_opts)

    async def callback(self, interaction: Interaction):
        self._logger.debug(f"User {interaction.user} selected: {self.values}")
        roles = []
        for role_id_str in self.values:
            role = interaction.user.guild.get_role(int(role_id_str))
            roles.append(role)

        if self._add_roles:
            self._logger.info(f"Adding role(s) to {interaction.user}: {roles}")
            await interaction.user.add_roles(*roles)
            self._logger.info(f"Roles added to user {interaction.user}")
        else:
            self._logger.info(f"Removing role(s) from {interaction.user}: {roles}")
            await interaction.user.remove_roles(*roles)
            self._logger.info(f"Roles removed from user {interaction.user}")

        # Get the updated user
        user = await client.guilds[0].fetch_member(interaction.user.id)
        # Create a new role manager view to replace the completed view flow
        text, emb, view = create_role_manager_view(user)

        await interaction.response.edit_message(content=text, embed=emb, view=view)


class AddRolesButton(Button):

    def __init__(self, label, roles, enabled):
        super().__init__(style=ButtonStyle.primary, label=label, disabled=not enabled)
        self._roles = roles

    async def callback(self, interaction: Interaction):
        role_view = AddRolesView(self._roles)
        await interaction.response.edit_message(content="**Add roles**", embed=None, view=role_view)


class RemoveRolesButton(Button):

    def __init__(self, label, roles, enabled):
        super().__init__(style=ButtonStyle.danger, label=label, disabled=not enabled)
        self._roles = roles

    async def callback(self, interaction: Interaction):
        role_view = RemoveRolesView(self._roles)
        await interaction.response.edit_message(content="**Remove roles**", embed=None, view=role_view)


class AddRolesView(View):
    def __init__(self, roles):
        super().__init__(timeout=None)

        self.add_item(RoleSelector(roles, True))


class RemoveRolesView(View):
    def __init__(self, roles):
        super().__init__(timeout=None)

        self.add_item(RoleSelector(roles, False))


class RoleView(View):
    def __init__(self, missing_game_roles, current_game_roles, missing_area_roles, current_area_roles):
        super().__init__(timeout=None)

        has_missing_game_roles = len(missing_game_roles) > 0
        has_missing_area_roles = len(missing_area_roles) > 0
        has_game_roles = len(current_game_roles) > 0
        has_area_roles = len(current_area_roles) > 0

        self.add_item(AddRolesButton("Add game roles", missing_game_roles, has_missing_game_roles))
        self.add_item(RemoveRolesButton("Remove game roles", current_game_roles, has_game_roles))
        self.add_item(AddRolesButton("Add area roles", missing_area_roles, has_missing_area_roles))
        self.add_item(RemoveRolesButton("Remove area roles", current_area_roles, has_area_roles))

###########################################################


# Setup discord.py logging
discord_handler = logging.StreamHandler()
discord_handler.setLevel(logging.INFO)
discord_formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S %z")

# Setup own logging
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S %z"))
logger.addHandler(handler)

# Read config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

token = config["token"]
nick = config["nick"]
conf_game_roles = config["game_roles"]
conf_area_roles = config["area_roles"]
admin_role_id = int(config["admin_role_id"])

guild = discord.Object(int(config["guild_id"]))

git_hash = None
try:
    git_hash = subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
except Exception:
    git_hash = os.environ.get("GIT_COMMIT")
    if not git_hash:
        logger.warning("Could not get Git hash")

if git_hash:
    logger.info(f"Git hash: {git_hash}")

###########################################################

client = BotClient(nick, guild, conf_game_roles, conf_area_roles)


def create_role_manager_view(user):
    missing_game_roles = {}
    for role_id, role in client.game_roles.items():
        if user.get_role(role_id):
            continue
        missing_game_roles[role_id] = role

    current_game_roles = {}
    for role in user.roles:
        if role.id in client.game_roles:
            current_game_roles[role.id] = client.game_roles[role.id]

    missing_area_roles = {}
    for role_id, role in client.area_roles.items():
        if user.get_role(role_id):
            continue
        missing_area_roles[role_id] = role

    current_area_roles = {}
    for role in user.roles:
        if role.id in client.area_roles:
            current_area_roles[role.id] = client.area_roles[role.id]

    current_game_roles_str = ""
    for role_container in current_game_roles.values():
        role = role_container["role"]
        current_game_roles_str += f"- {role.mention}\n"

    current_area_roles_str = ""
    for role_container in current_area_roles.values():
        role = role_container["role"]
        current_area_roles_str += f"- {role.mention}\n"

    text = "**Manage your roles**"

    emb = Embed()
    if current_game_roles:
        emb.add_field(name="Current game roles", value=current_game_roles_str)
    if current_area_roles:
        emb.add_field(name="Current area roles", value=current_area_roles_str)

    if not current_game_roles and not current_area_roles:
        emb = None

    view = RoleView(missing_game_roles, current_game_roles, missing_area_roles, current_area_roles)

    return (text, emb, view)


@client.tree.command(description="Manage your game and area roles", guild=guild)
async def roles(interaction: Interaction):
    logger = logging.getLogger("bot.command")
    logger.info(f"User {interaction.user} wants to manage roles")
    text, emb, view = create_role_manager_view(interaction.user)
    await interaction.response.send_message(text, embed=emb, view=view, ephemeral=True)
    logger.debug(f"User {interaction.user} role manager flow started")


@client.event
async def on_message(msg: Message):
    if not isinstance(msg.channel, DMChannel) or msg.author.id == client.user.id:
        return

    logger.info(f"User {msg.author} sent a direct message")

    # This is a DM
    # Get the roles for this user in the "home guild"
    try:
        member = await client.guilds[0].fetch_member(msg.author.id)
    except discord.NotFound:
        member = None
    if not member:
        logger.warning(f"User {msg.author} is not a member of guild {client.guilds[0]}, ignoring")
        return

    if not member.get_role(admin_role_id):
        logger.warning(f"Non-admin member {member} tried to message us, ignoring")
        return

    # Admin user messaged us something
    msg_lower = msg.content.lower()
    if msg_lower == "quit":
        # Quit
        logger.info(f"Admin member {member} ordered shutdown")
        await client.close()
        return

    if msg_lower == "version":
        logger.info(f"Admin member {member} requested version information")
        await msg.reply(f"Git hash: {git_hash or '?'}")
        return

client.run(token, reconnect=True, log_handler=discord_handler, log_formatter=discord_formatter)
