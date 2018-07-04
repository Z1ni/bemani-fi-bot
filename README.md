# Discord bot for Bemani Finland

## Requirements
* Python 3.5+
* discord.py

## Installation
1. Setup virtualenv
```bash
$ virtualenv venv
$ . venv/bin/activate
```
2. Install requirements
```bash
(venv) $ pip install -r requirements.txt
```
3. Create config and edit it (see below)
```bash
(venv) $ cp bemani.conf.example bemani.conf
(venv) $ vim bemani.conf
```
4. Run
```bash
(venv) $ ./main.py
```

## Configuration
The bot always reads `bemani.conf` for configuration. See `bemani.conf.example` for an example configuration.

The token key must have a Discord bot token in it as a value.

### Game roles
Role names must be provided in the config. For example for server roles named `SDVX`, `IIDX` and `Pop'n` the config file will have the following:
```
roles = [SDVX, IIDX, Pop'n]
```
