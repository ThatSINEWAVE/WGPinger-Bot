import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import aiohttp
import socket
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="/", intents=intents)

# Regional API URLs
WG_API_URLS = {
    "EU": "https://api.worldoftanks.eu/wgn/servers/info/",
    "NA": "https://api.worldoftanks.com/wgn/servers/info/",
    "ASIA": "https://api.worldoftanks.asia/wgn/servers/info/"
}
WG_APPLICATION_ID = os.getenv("WG_APPLICATION_ID")

# Server code to name mapping
SERVER_CODE_MAPPING = {
    "203": "EU3",
    "204": "EU4",
    "304": "LATAM",
    "303": "USC",
    "501": "ASIA"
}

# Load the clusters.json file into a list of server dictionaries
try:
    with open('clusters.json', 'r') as file:
        clusters_list = json.load(file)['list']
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading clusters.json: {e}")
    clusters_list = []

# Create a session that will be used for all HTTP requests
session = None


async def get_session():
    """Get or create the aiohttp session"""
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session


async def ping_host(host, count=4, timeout=2):
    """Ping a host using socket instead of pythonping to avoid exceptions"""
    try:
        # Extract just the hostname without port if present
        hostname = host.split(':')[0]

        # Try to resolve the hostname
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            print(f"Could not resolve hostname: {hostname}")
            return None

        # Use asyncio.open_connection which is non-blocking
        total_time = 0
        success_count = 0

        for _ in range(count):
            try:
                start_time = asyncio.get_event_loop().time()
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip_address, 80),
                    timeout=timeout
                )
                end_time = asyncio.get_event_loop().time()
                writer.close()
                await writer.wait_closed()

                rtt = (end_time - start_time) * 1000  # Convert to ms
                total_time += rtt
                success_count += 1
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                continue

        if success_count == 0:
            return None

        return round(total_time / success_count, 2)  # Average RTT in ms
    except Exception as e:
        print(f"Error pinging {host}: {e}")
        return None


async def get_wg_server_stats(region):
    """Fetch server stats for a specific region using aiohttp."""
    try:
        session = await get_session()
        url = WG_API_URLS.get(region, WG_API_URLS["EU"])  # Default to EU if region is not specified
        params = {'application_id': WG_APPLICATION_ID, 'game': 'wot'}

        try:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Failed to fetch WG server stats for {region}, status code: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching WG server stats for {region}: {e}")
            return None
    except Exception as e:
        print(f"Error in get_wg_server_stats for {region}: {e}")
        return None


@bot.tree.command(name="wgstats", description="Get Wargaming server statistics")
@app_commands.choices(region=[
    app_commands.Choice(name="EU", value="EU"),
    app_commands.Choice(name="NA", value="NA"),
    app_commands.Choice(name="ASIA", value="ASIA"),
    app_commands.Choice(name="ALL", value="ALL")
])
async def wg_stats(interaction: discord.Interaction, region: str = "EU"):
    await interaction.response.defer()

    try:
        if region.upper() == "ALL":
            # Create a combined embed for all regions
            embed = discord.Embed(title="Wargaming Server Statistics - All Regions", color=0x00ff00)

            # Process all regions concurrently for better performance
            tasks = [get_wg_server_stats(reg) for reg in ["EU", "NA", "ASIA"]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            regions_processed = 0
            for idx, stats in enumerate(results):
                reg = ["EU", "NA", "ASIA"][idx]

                if isinstance(stats, Exception):
                    print(f"Error fetching stats for {reg}: {stats}")
                    continue

                if stats and stats.get('status') == 'ok' and 'data' in stats and 'wot' in stats['data']:
                    regions_processed += 1
                    for server in stats['data']['wot']:
                        server_code = server['server']
                        server_name = SERVER_CODE_MAPPING.get(server_code, server_code)
                        players_online = server['players_online']
                        embed.add_field(name=f"{reg} - {server_name}", value=f"Players Online: {players_online}",
                                        inline=True)

            if regions_processed == 0:
                embed.description = "Failed to retrieve server statistics for any region."
                embed.color = 0xff0000  # Red for error

            await interaction.followup.send(embed=embed)
        else:
            # Get stats for a specific region
            stats = await get_wg_server_stats(region.upper())
            if stats and stats.get('status') == 'ok' and 'data' in stats and 'wot' in stats['data']:
                embed = discord.Embed(title=f"Wargaming Server Statistics - {region.upper()}", color=0x00ff00)
                for server in stats['data']['wot']:
                    server_code = server['server']
                    server_name = SERVER_CODE_MAPPING.get(server_code, server_code)
                    players_online = server['players_online']
                    embed.add_field(name=server_name, value=f"Players Online: {players_online}", inline=False)
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Error - {region.upper()}",
                    description=f"Failed to retrieve WG server statistics for region {region.upper()}.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in wg_stats command: {e}")
        await interaction.followup.send(f"An error occurred while processing your request: {str(e)}")


@bot.tree.command(name="checkping", description="Check ping for a specific game server")
async def check_ping(interaction: discord.Interaction, server: str):
    await interaction.response.defer()

    try:
        if server.upper() == "ALL":
            embed = discord.Embed(title="Server Ping Results", color=0x00ff00)

            # Create tasks for all pings to run concurrently
            ping_tasks = []
            for cluster in clusters_list:
                if 'address' in cluster and cluster['address']:
                    ping_tasks.append((cluster, ping_host(cluster['address'])))

            # Process the results as they complete
            for cluster, ping_task in ping_tasks:
                ping_result = await ping_task

                cluster_name = cluster.get('api', '') or cluster.get('name', 'Unknown')
                cluster_place = cluster.get('place', 'Unknown')

                if ping_result is not None:
                    embed.add_field(name=f"{cluster_name} - {cluster_place}",
                                    value=f"{ping_result} ms", inline=False)
                else:
                    embed.add_field(name=f"{cluster_name} - {cluster_place}",
                                    value="Cannot ping right now", inline=False)

            await interaction.followup.send(embed=embed)
        else:
            # Find the cluster with the matching API name
            cluster = next((item for item in clusters_list if item.get('api') == server.upper()), None)
            if cluster and 'address' in cluster:
                ping_result = await ping_host(cluster['address'])

                if ping_result is not None:
                    embed = discord.Embed(title=f"Ping to {cluster['api']} - {cluster.get('place', 'Unknown')}",
                                          description=f"**{ping_result} ms**", color=0x00ff00)
                    await interaction.followup.send(embed=embed)
                else:
                    embed = discord.Embed(title=f"Ping to {cluster['api']} - {cluster.get('place', 'Unknown')}",
                                          description="Cannot ping right now", color=0xff0000)
                    await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Server not found. Please use a valid server API name.")
    except Exception as e:
        print(f"Error in check_ping command: {e}")
        await interaction.followup.send(f"An error occurred while processing your request: {str(e)}")


# Load channel mapping from environment variables
def load_channel_mapping():
    channel_mapping = {}

    # List of server IDs to look for in environment variables
    server_ids = [
        "EU1", "EU2", "EU3", "EU4", "LATAM", "USC", "RU1", "RU2", "RU4",
        "RU6", "RU7", "RU8", "RU9", "PT1", "CH1", "CH2", "ASIA",
        "CT1", "CT2", "PCW0", "PCW1", "PCW2", "XVM"
    ]

    for server_id in server_ids:
        players_channel_id = os.getenv(f"{server_id}_PLAYERS_CHANNEL_ID")
        ping_channel_id = os.getenv(f"{server_id}_PING_CHANNEL_ID")

        channel_mapping[server_id] = {
            "players": players_channel_id or "CHANNEL_ID",
            "ping": ping_channel_id or "CHANNEL_ID"
        }

    return channel_mapping


# Get channel mapping
channel_mapping = load_channel_mapping()


async def update_channel_names():
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            # Collect player count data
            server_data = {}

            # Gather all region data concurrently
            region_tasks = [get_wg_server_stats(region) for region in WG_API_URLS.keys()]
            region_results = await asyncio.gather(*region_tasks, return_exceptions=True)

            for idx, stats in enumerate(region_results):
                region = list(WG_API_URLS.keys())[idx]

                if isinstance(stats, Exception):
                    print(f"Error fetching stats for {region} in update_channel_names: {stats}")
                    continue

                if stats and stats.get('status') == 'ok' and 'data' in stats and 'wot' in stats['data']:
                    for server in stats['data']['wot']:
                        server_code = server['server']
                        server_name = SERVER_CODE_MAPPING.get(server_code, server_code)
                        players_online = server['players_online']
                        server_data[server_name] = players_online

            # Prepare ping tasks for all clusters
            ping_tasks = {}
            for cluster in clusters_list:
                server_name = cluster.get('api')
                if server_name and 'address' in cluster and server_name in channel_mapping:
                    ping_tasks[server_name] = ping_host(cluster['address'])

            # Await all ping tasks
            ping_results = {}
            for server_name, task in ping_tasks.items():
                ping_results[server_name] = await task

            # Rate limit to avoid hitting Discord API limits
            for server_name, ping_result in ping_results.items():
                if server_name in channel_mapping:
                    channels = channel_mapping[server_name]
                    players_online = server_data.get(server_name, "N/A")

                    # Update players channel
                    if 'players' in channels and channels['players'] != "CHANNEL_ID":
                        try:
                            players_channel = bot.get_channel(int(channels['players']))
                            if players_channel:
                                await players_channel.edit(name=f"{server_name} Players: {players_online}")
                                # Rate limit to avoid hitting Discord API limits
                                await asyncio.sleep(5)
                        except Exception as e:
                            print(f"Failed to update players channel for {server_name}: {e}")

                    # Update ping channel
                    if 'ping' in channels and channels['ping'] != "CHANNEL_ID":
                        try:
                            ping_channel = bot.get_channel(int(channels['ping']))
                            if ping_channel:
                                ping_value = f"{ping_result} ms" if ping_result is not None else "Error"
                                await ping_channel.edit(name=f"{server_name} Ping: {ping_value}")
                                # Rate limit to avoid hitting Discord API limits
                                await asyncio.sleep(5)
                        except Exception as e:
                            print(f"Failed to update ping channel for {server_name}: {e}")

        except Exception as e:
            print(f"Error in update_channel_names: {e}")

        # Wait for 5 minutes before the next update to avoid rate limits
        await asyncio.sleep(300)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Sync the application commands
    await bot.tree.sync()
    print('Synced application commands')
    # Start the channel update task
    bot.loop.create_task(update_channel_names())


async def cleanup():
    """Close the aiohttp session when the bot is shutting down."""
    global session
    if session is not None and not session.closed:
        await session.close()


# Get the bot token from environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    finally:
        # Ensure we clean up resources
        asyncio.run(cleanup())