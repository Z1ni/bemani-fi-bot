# Discord bot for Bemani Finland

## Requirements
* Python 3.5.3+
* discord.py 1.* (currently pinned to 1.3.2)

## Installation
### Docker (recommended)
1. Install Docker
2. Create bemani.conf and edit it (see below)
```bash
$ cp bemani.conf.example bemani.conf
$ vim bemani.conf
```
3. Build image
```bash
# Use build script to populate !version command git commit hash
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
