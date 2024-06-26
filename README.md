<div align="center">

# WGPinger - Server Monitoring Discord Bot

This Discord bot provides server statistics for Wargaming (WG) servers and allows users to check the ping for specific game servers. Additionally, it updates Discord channel names with real-time player counts and ping information.

</div>

<div align="center">

# [Join my discord server](https://discord.gg/2nHHHBWNDw)

</div>

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/WGPinger-Bot.git
```

2. **Install the required Python packages:**

```bash
pip install discord.py discord-py-slash-command pythonping requests
```

3. **Create a Discord bot and obtain the bot token.**

Replace the placeholder token in main.py with your bot token:

```python
bot.run('YOUR_BOT_TOKEN')
```

4. **Run the bot:**

```bash
python main.py
```

## Commands

1. **/wgstats** - Fetches Wargaming server statistics for a specific region.

### Usage:

```bash
/wgstats [region]
```

region (optional): The server region (e.g., "EU", "NA", "ASIA"). Defaults to "EU" if not specified.

2. **/checkping** - Checks the ping for a specific game server or all servers.

### Usage:

```bash
/checkping [server]
```

server: The server API name. Use "ALL" to check ping for all servers.

## Configuration

`clusters.json`

This JSON file contains information about game servers, including their names, addresses

### Automatic Channel Updates

The bot automatically updates Discord channel names with real-time player counts and ping information. The channels are mapped in the channel_mapping dictionary in main.py.

<div align="center">

## ☕ [Support my work on Ko-Fi](https://ko-fi.com/thatsinewave)

</div>

## License

This project is licensed under the MIT License - see the LICENSE file for details.
