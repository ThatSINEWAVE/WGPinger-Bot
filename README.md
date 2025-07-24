<div align="center">

# WGPinger - Server Monitoring Discord Bot

This Discord bot provides server statistics for Wargaming (WG) servers and allows users to check the ping for specific game servers. Additionally, it updates Discord channel names with real-time player counts and ping information.

</div>

<div align="center">

# [Join my discord server](https://thatsinewave.github.io/Discord-Redirect/)

</div>

## Features

- Get real-time Wargaming server statistics (player counts) by region
- Check ping to specific game servers 
- Automatically update Discord channel names with server stats and ping information
- Support for multiple regions: EU, NA, ASIA, and more
- Easy configuration using environment variables

<div align="center">

## ☕ [Support my work on Ko-Fi](https://ko-fi.com/thatsinewave)

</div>

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/WGPinger-Bot.git
cd WGPinger-Bot
```

2. **Install the required Python packages:**

```bash
pip install discord.py python-dotenv aiohttp
```

3. **Set up your environment variables:**

Copy the example environment file and edit it with your credentials:

```bash
cp .env.example .env
```

Then edit the `.env` file with the following information:
- Your Discord bot token
- Your Wargaming Application ID
- Channel IDs for server stats display

4. **Run the bot:**

```bash
python main.py
```

## Environment Configuration

The bot uses environment variables for all configuration settings:

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `WG_APPLICATION_ID`: Your Wargaming application ID
- Server channel mappings (for each server):
  - `SERVER_PLAYERS_CHANNEL_ID`: Channel to display player count
  - `SERVER_PING_CHANNEL_ID`: Channel to display ping

Example for the `.env` file:

```
DISCORD_BOT_TOKEN=your_discord_bot_token_here
WG_APPLICATION_ID=your_wargaming_application_id_here

# Channel IDs
EU1_PLAYERS_CHANNEL_ID=123456789012345678
EU1_PING_CHANNEL_ID=123456789012345678
```

## Commands

1. **/wgstats** - Fetches Wargaming server statistics for a specific region.

### Usage:

```
/wgstats [region]
```

`region` (optional): The server region ("EU", "NA", "ASIA", or "ALL"). Defaults to "EU" if not specified.

2. **/checkping** - Checks the ping for a specific game server or all servers.

### Usage:

```
/checkping [server]
```

`server`: The server API name or "ALL" to check ping for all servers.

<div align="center">

# [Join my discord server](https://discord.gg/2nHHHBWNDw)

</div>

## Server Configuration

Server information is stored in `clusters.json`. This file contains details about each game server:
- Server name
- Location
- Connection address
- API identifier
- Color code for display

## Automatic Channel Updates

The bot automatically updates Discord channel names with:
- Current player counts for each server
- Current ping times in milliseconds

These updates occur every 5 minutes to avoid Discord API rate limits.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
