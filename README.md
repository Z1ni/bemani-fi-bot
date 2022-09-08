# Discord bot for Bemani Finland

Single-guild bot for Bemani Finland.

## Requirements
* Python 3.8+
* discord.py 2.* (currently pinned to 2.0.1)

## Installation
### Docker (recommended)
1. Install Docker
2. Create `config.json` and edit it (see below)
```bash
$ cp config.json.example config.json
$ vim config.json
```
3. Build image
```bash
# Use build script to populate version command git commit hash
$ ./docker-build.sh --tag=bemanifibot .
# Or build without version information
$ docker build --tag=bemanifibot .
```
4. Run
```bash
# Interactive
$ docker run -it bemanifibot
# Daemon
$ docker run -d bemanifibot
```

### Virtualenv
1. Setup virtualenv
```bash
$ virtualenv venv
$ source venv/bin/activate
```
2. Install requirements
```bash
(venv) $ pip install -r requirements.txt
```
3. Create config and edit it (see below)
```bash
(venv) $ cp config.json.example config.json
(venv) $ vim config.json
```
4. Run
```bash
(venv) $ ./main.py
```

## Configuration
The bot always reads `config.json` for configuration. See `config.json.example` for an example configuration.

The token key must have a Discord bot token in it as a value.

The bot must have access to the privileged message content intent. Enable it in the Discord Developer Portal.

### Roles
Role IDs must be provided in the config. The names don't need to match with the server roles.

## Quick help

The role handling is performed with a `/roles` application slash command that creates an ephemeral message with message
components (buttons and select menus), so the role handling does not pollute any channel nor does it need direct
messages with the bot.

If in the future Discord allows select menus in modals, this will be refactored to use those.
