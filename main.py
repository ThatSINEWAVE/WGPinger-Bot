import discord
from discord.ext import commands
from pythonping import ping
import requests
import json
import asyncio

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# Regional API URLs
WG_API_URLS = {
    "EU": "http://api.worldoftanks.eu/wgn/servers/info/",
    "NA": "http://api.worldoftanks.com/wgn/servers/info/",
    "ASIA": "http://api.worldoftanks.asia/wgn/servers/info/"
}
WG_APPLICATION_ID = "YOUR_WG_APP_ID"


# Server code to name mapping
SERVER_CODE_MAPPING = {
    "203": "EU3",
    "204": "EU4",
    "304": "LATAM",
    "303": "USC",
    "501": "ASIA"
}


async def get_wg_server_stats(region):
    """Fetch server stats for a specific region."""
    url = WG_API_URLS.get(region, WG_API_URLS["EU"])  # Default to EU if region is not specified
    params = {'application_id': WG_APPLICATION_ID, 'game': 'wot'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch WG server stats for {region}")
        return None


@bot.slash_command(name="wgstats", description="Get Wargaming server statistics")
async def wg_stats(ctx, region: str = "EU"):
    stats = await get_wg_server_stats(region.upper())
    if stats and stats['status'] == 'ok':
        embed = discord.Embed(title=f"Wargaming Server Statistics - {region.upper()}", color=0x00ff00)
        for server in stats['data']['wot']:
            server_code = server['server']
            server_name = SERVER_CODE_MAPPING.get(server_code, server_code)  # Default to server code if not mapped
            players_online = server['players_online']
            embed.add_field(name=server_name, value=f"Players Online: {players_online}", inline=False)
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("Failed to retrieve WG server statistics.")


# Load the clusters.json file into a list of server dictionaries
with open('clusters.json', 'r') as file:
    clusters_list = json.load(file)['list']


# Revised check_ping function to iterate over clusters_list
@bot.slash_command(name="checkping", description="Check ping for a specific game server")
async def check_ping(ctx, server: str):
    await ctx.defer()
    if server.upper() == "ALL":
        embed = discord.Embed(title="Server Ping Results", color=0x00ff00)
        for cluster in clusters_list:
            try:
                response = ping(cluster['address'], count=4)
                embed.add_field(name=f"{cluster['api'] if cluster['api'] else cluster['name']} - {cluster['place']}",
                                value=f"{response.rtt_avg_ms} ms", inline=False)
            except Exception:
                embed.add_field(name=f"{cluster['api'] if cluster['api'] else cluster['name']} - {cluster['place']}",
                                value="Cannot ping right now.", inline=False)
        await ctx.followup.send(embed=embed)
    else:
        cluster = next((item for item in clusters_list if item['api'] == server.upper()), None)
        if cluster:
            try:
                response = ping(cluster['address'], count=4)
                embed = discord.Embed(title=f"Ping to {cluster['api']} - {cluster['place']}",
                                      description=f"**{response.rtt_avg_ms} ms**", color=0x00ff00)
                await ctx.respond(embed=embed)
            except Exception:
                embed = discord.Embed(title=f"Ping to {cluster['api']} - {cluster['place']}",
                                      description="Cannot ping right now.", color=0xff0000)
                await ctx.respond(embed=embed)
        else:
            await ctx.respond("Server not found. Please use a valid server API name.")


# Mapping of server identifiers to their corresponding Discord channel IDs
channel_mapping = {
    "EU1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "EU2": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "EU3": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "EU4": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "LATAM": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "USC": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU2": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU4": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU6": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU7": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU8": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "RU9": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "PT1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "CH1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "CH2": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "ASIA": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "CT1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "CT2": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "PCW0": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "PCW1": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "PCW2": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
    "XVM": {"players": "CHANNEL_ID", "ping": "CHANNEL_ID"},
}


async def update_channel_names():
    await bot.wait_until_ready()
    while not bot.is_closed():
        # Collect ping and player count data
        server_data = {}
        for region in WG_API_URLS.keys():
            stats = await get_wg_server_stats(region)
            if stats and stats['status'] == 'ok':
                for server in stats['data']['wot']:
                    server_code = server['server']
                    server_name = SERVER_CODE_MAPPING.get(server_code, server_code)
                    players_online = server['players_online']
                    server_data[server_name] = players_online

        # Update channel names with the collected data
        for cluster in clusters_list:
            server_name = SERVER_CODE_MAPPING.get(cluster['api'], cluster['api'])
            players_online = server_data.get(server_name, "N/A")
            ping_ms = "Error"
            try:
                response = ping(cluster['address'], count=4)
                ping_ms = f"{response.rtt_avg_ms} ms"
            except Exception as e:
                print(f"Failed to ping {server_name}: {e}")

            # Update channels
            if server_name in channel_mapping:
                channels = channel_mapping[server_name]
                if 'players' in channels:
                    players_channel = bot.get_channel(channels['players'])
                    await players_channel.edit(name=f"{server_name} Players: {players_online}")
                if 'ping' in channels:
                    ping_channel = bot.get_channel(channels['ping'])
                    await ping_channel.edit(name=f"{server_name} Ping: {ping_ms}")

        await asyncio.sleep(60)  # Wait for 1 minute before the next update


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    bot.loop.create_task(update_channel_names())


@bot.event
async def on_application_command_error(ctx, error):
    print(f'Error occurred in command {ctx.command}: {error}')

# Run the bot
bot.run('YOUR_BOT_TOKEN')
